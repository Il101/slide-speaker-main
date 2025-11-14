"""Analytics tracking API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
from user_agents import parse

from ..core.database import get_db, AnalyticsEvent, UserSession, DailyMetrics, CostLog, User, Lesson, Subscription, Export
from ..core.auth import get_current_user, require_admin
from pydantic import BaseModel, Field

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Request schemas
class TrackEventRequest(BaseModel):
    """Request to track an analytics event"""
    event_name: str = Field(..., description="Name of the event")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    session_id: str = Field(..., description="Session ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties")
    timestamp: str = Field(..., description="Event timestamp")
    user_agent: Optional[str] = Field(None, description="User agent string")
    page: Optional[str] = Field(None, description="Page path")
    referrer: Optional[str] = Field(None, description="Referrer URL")
    screen_resolution: Optional[str] = Field(None, description="Screen resolution")

class TrackSessionRequest(BaseModel):
    """Request to track a user session"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    landing_page: Optional[str] = Field(None, description="Landing page")
    referrer: Optional[str] = Field(None, description="Referrer URL")
    utm_source: Optional[str] = Field(None, description="UTM source")
    utm_medium: Optional[str] = Field(None, description="UTM medium")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign")

class AnalyticsResponse(BaseModel):
    """Response for analytics requests"""
    success: bool
    message: Optional[str] = None

# Helper functions
def parse_user_agent(user_agent_string: Optional[str]) -> Dict[str, Optional[str]]:
    """Parse user agent string"""
    if not user_agent_string:
        return {"device": "desktop", "browser": None, "os": None}
    
    ua = parse(user_agent_string)
    device = "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
    
    return {
        "device": device,
        "browser": f"{ua.browser.family} {ua.browser.version_string}",
        "os": f"{ua.os.family} {ua.os.version_string}"
    }

def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

async def update_daily_metrics(db: AsyncSession, event_name: str, user_id: Optional[str] = None):
    """Update daily metrics based on events"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get or create daily metrics
    result = await db.execute(
        select(DailyMetrics).where(DailyMetrics.date == today)
    )
    metrics = result.scalar_one_or_none()
    
    if not metrics:
        metrics = DailyMetrics(
            id=str(uuid.uuid4()),
            date=today
        )
        db.add(metrics)
        await db.flush()
    
    # Update counters based on event type
    if event_name == "User Signed Up":
        metrics.new_users += 1
    elif event_name == "Lecture Generation Completed":
        metrics.lectures_created += 1
    elif event_name == "Presentation Uploaded":
        metrics.presentations_uploaded += 1
    elif event_name == "Lecture Downloaded":
        metrics.downloads_count += 1
    
    await db.commit()

# API Endpoints
@router.post("/track", response_model=AnalyticsResponse)
async def track_event(
    event: TrackEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Track an analytics event"""
    try:
        # Parse user agent
        ua_info = parse_user_agent(event.user_agent)
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Create event
        # Parse timestamp and convert to naive UTC datetime
        timestamp_str = event.timestamp.replace('Z', '+00:00')
        timestamp_dt = datetime.fromisoformat(timestamp_str)
        # Convert to naive UTC datetime
        if timestamp_dt.tzinfo is not None:
            timestamp_dt = timestamp_dt.replace(tzinfo=None)
        
        analytics_event = AnalyticsEvent(
            id=str(uuid.uuid4()),
            event_name=event.event_name,
            user_id=event.user_id,
            session_id=event.session_id,
            properties=event.properties,
            timestamp=timestamp_dt,
            user_agent=event.user_agent,
            ip_address=ip_address,
            device=ua_info["device"],
            browser=ua_info["browser"],
            os=ua_info["os"]
        )
        
        db.add(analytics_event)
        await db.commit()
        
        # Update daily metrics asynchronously (don't await to keep response fast)
        await update_daily_metrics(db, event.event_name, event.user_id)
        
        return AnalyticsResponse(success=True)
    except Exception as e:
        print(f"Analytics error: {e}")
        return AnalyticsResponse(success=False, message=str(e))

@router.post("/session", response_model=AnalyticsResponse)
async def track_session(
    session: TrackSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Track or update a user session"""
    try:
        # Get client IP
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Check if session exists
        result = await db.execute(
            select(UserSession).where(UserSession.session_id == session.session_id)
        )
        existing_session = result.scalar_one_or_none()
        
        if existing_session:
            # Update existing session
            existing_session.last_activity = datetime.utcnow()
            existing_session.page_views += 1
            if session.user_id and not existing_session.user_id:
                existing_session.user_id = session.user_id
        else:
            # Create new session
            new_session = UserSession(
                id=str(uuid.uuid4()),
                session_id=session.session_id,
                user_id=session.user_id,
                landing_page=session.landing_page,
                referrer=session.referrer,
                utm_source=session.utm_source,
                utm_medium=session.utm_medium,
                utm_campaign=session.utm_campaign,
                user_agent=user_agent,
                ip_address=ip_address,
                page_views=1
            )
            db.add(new_session)
        
        await db.commit()
        return AnalyticsResponse(success=True)
    except Exception as e:
        print(f"Session tracking error: {e}")
        return AnalyticsResponse(success=False, message=str(e))

@router.get("/admin/dashboard")
async def get_analytics_dashboard(
    time_range: str = "30d",
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(require_admin)
):
    """Get analytics dashboard data (admin only)"""
    try:
        # Parse time range
        days = 7 if time_range == "7d" else 30 if time_range == "30d" else 90
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Fetch all data in parallel
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        # Active users (last 30 days)
        active_date = datetime.utcnow() - timedelta(days=30)
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.updated_at >= active_date)
        )
        active_users = active_users_result.scalar() or 0
        
        # Paid users
        paid_users_result = await db.execute(
            select(func.count(User.id)).where(User.subscription_tier != "free")
        )
        paid_users = paid_users_result.scalar() or 0
        
        # Total lectures
        lectures_result = await db.execute(
            select(func.count(Lesson.id)).where(Lesson.created_at >= start_date)
        )
        total_lectures = lectures_result.scalar() or 0
        
        # Daily metrics for charts
        daily_metrics_result = await db.execute(
            select(DailyMetrics)
            .where(DailyMetrics.date >= start_date)
            .order_by(DailyMetrics.date)
        )
        daily_metrics = list(daily_metrics_result.scalars().all())
        
        # Top events
        top_events_result = await db.execute(
            select(
                AnalyticsEvent.event_name,
                func.count(AnalyticsEvent.id).label('count')
            )
            .where(AnalyticsEvent.timestamp >= start_date)
            .group_by(AnalyticsEvent.event_name)
            .order_by(desc('count'))
            .limit(10)
        )
        top_events = [{"name": row[0], "count": row[1]} for row in top_events_result]
        
        # User acquisition sources
        acquisition_result = await db.execute(
            select(
                UserSession.utm_source,
                func.count(UserSession.id).label('count')
            )
            .where(UserSession.start_time >= start_date)
            .group_by(UserSession.utm_source)
            .order_by(desc('count'))
            .limit(10)
        )
        acquisition = acquisition_result.all()
        total_sessions = sum(row[1] for row in acquisition)
        acquisition_data = [
            {
                "source": row[0] or "Direct",
                "count": row[1],
                "percentage": round((row[1] / total_sessions * 100), 1) if total_sessions > 0 else 0
            }
            for row in acquisition
        ]
        
        # Cost data
        costs_result = await db.execute(
            select(func.sum(CostLog.cost))
            .where(CostLog.timestamp >= start_date)
        )
        total_costs = float(costs_result.scalar() or 0)
        
        # Cost breakdown
        cost_breakdown_result = await db.execute(
            select(
                CostLog.operation,
                func.sum(CostLog.cost).label('total')
            )
            .where(CostLog.timestamp >= start_date)
            .group_by(CostLog.operation)
        )
        cost_breakdown_raw = cost_breakdown_result.all()
        cost_breakdown = {
            "ocr": 0.0,
            "ai": 0.0,
            "tts": 0.0,
            "storage": 0.0,
            "other": 0.0
        }
        for operation, cost in cost_breakdown_raw:
            if operation in cost_breakdown:
                cost_breakdown[operation] = float(cost)
            else:
                cost_breakdown["other"] += float(cost)
        
        # Calculate MRR from actual subscription prices
        mrr_result = await db.execute(
            select(func.sum(Subscription.price))
            .where(
                and_(
                    Subscription.status == "active",
                    Subscription.billing_cycle == "monthly"
                )
            )
        )
        mrr = float(mrr_result.scalar() or 0)
        
        # For yearly subscriptions, divide by 12 to get MRR
        yearly_mrr_result = await db.execute(
            select(func.sum(Subscription.price))
            .where(
                and_(
                    Subscription.status == "active",
                    Subscription.billing_cycle == "yearly"
                )
            )
        )
        yearly_total = float(yearly_mrr_result.scalar() or 0)
        mrr += yearly_total / 12
        
        # Calculate MRR growth from historical data
        last_month_date = datetime.utcnow() - timedelta(days=30)
        last_month_mrr_result = await db.execute(
            select(DailyMetrics.mrr)
            .where(DailyMetrics.date <= last_month_date)
            .order_by(desc(DailyMetrics.date))
            .limit(1)
        )
        last_month_mrr = float(last_month_mrr_result.scalar() or 0)
        mrr_growth = round(((mrr - last_month_mrr) / last_month_mrr * 100), 1) if last_month_mrr > 0 else 0.0
        
        # Calculate user growth
        last_month_users_result = await db.execute(
            select(func.count(User.id))
            .where(User.created_at <= last_month_date)
        )
        last_month_users = last_month_users_result.scalar() or 0
        user_growth_percent = round(((total_users - last_month_users) / last_month_users * 100), 1) if last_month_users > 0 else 0.0
        user_growth = f"+{user_growth_percent}%" if user_growth_percent >= 0 else f"{user_growth_percent}%"
        
        conversion_rate = round((paid_users / total_users * 100), 1) if total_users > 0 else 0
        cost_per_user = round(total_costs / active_users, 3) if active_users > 0 else 0
        cost_per_lecture = round(total_costs / total_lectures, 3) if total_lectures > 0 else 0
        margin = round(((mrr - total_costs) / mrr * 100), 1) if mrr > 0 else 0
        
        # Prepare chart data
        metrics_count = len(daily_metrics) if daily_metrics else 0
        user_growth_chart = {
            "labels": [metric.date.strftime("%Y-%m-%d") for metric in daily_metrics],
            "data": [sum(dm.new_users for dm in daily_metrics[:i+1]) for i in range(metrics_count)]
        }
        
        revenue_chart = {
            "labels": [m.date.strftime("%Y-%m-%d") for m in daily_metrics],
            "data": [float(m.mrr) for m in daily_metrics]
        }
        
        lecture_activity_chart = {
            "labels": [m.date.strftime("%Y-%m-%d") for m in daily_metrics],
            "data": [m.lectures_created for m in daily_metrics]
        }
        
        # Plan distribution - query real subscription tiers
        plan_dist_result = await db.execute(
            select(
                User.subscription_tier,
                func.count(User.id).label('count')
            )
            .group_by(User.subscription_tier)
        )
        plan_counts = {tier: count for tier, count in plan_dist_result.all()}
        
        plan_distribution = [
            plan_counts.get('free', 0),
            plan_counts.get('starter', 0),
            plan_counts.get('pro', 0),
            plan_counts.get('business', 0)
        ]
        
        # Funnel - use real data
        signups = total_users
        
        # Email verified - query from users table
        email_verified_result = await db.execute(
            select(func.count(User.id))
            .where(User.email_verified == True)
        )
        email_verified = email_verified_result.scalar() or 0
        
        # Users who created lectures
        has_lectures_result = await db.execute(
            select(func.count(func.distinct(Lesson.user_id)))
        )
        has_lectures = has_lectures_result.scalar() or 0
        
        # Users who downloaded - query from exports table
        has_downloads_result = await db.execute(
            select(func.count(func.distinct(Export.user_id)))
            .where(and_(Export.status == "completed", Export.user_id.isnot(None)))
        )
        has_downloads = has_downloads_result.scalar() or 0
        
        funnel = [
            {"step": "Signed Up", "count": signups, "rate": 100, "isLast": False},
            {"step": "Email Verified", "count": email_verified, "rate": round(email_verified / signups * 100, 1) if signups > 0 else 0, "isLast": False},
            {"step": "Created Lecture", "count": has_lectures, "rate": round(has_lectures / signups * 100, 1) if signups > 0 else 0, "isLast": False},
            {"step": "Downloaded", "count": has_downloads, "rate": round(has_downloads / signups * 100, 1) if signups > 0 else 0, "isLast": False},
            {"step": "Upgraded to Paid", "count": paid_users, "rate": conversion_rate, "isLast": True}
        ]
        
        # AI Insights
        insights = generate_insights({
            "conversion_rate": conversion_rate,
            "activation_rate": funnel[2]["rate"],
            "cost_per_user": cost_per_user,
            "margin": margin,
            "lectures_per_user": total_lectures / active_users if active_users > 0 else 0
        })
        
        return {
            "overview": {
                "totalUsers": total_users,
                "activeUsers": active_users,
                "mrr": round(mrr, 2),
                "mrrGrowth": mrr_growth,
                "userGrowth": user_growth,
                "totalLectures": total_lectures,
                "conversionRate": conversion_rate
            },
            "charts": {
                "userGrowth": user_growth_chart,
                "revenue": revenue_chart,
                "lectureActivity": lecture_activity_chart,
                "planDistribution": plan_distribution
            },
            "funnel": funnel,
            "topEvents": top_events,
            "acquisition": acquisition_data,
            "costs": {
                "total": round(total_costs, 2),
                "perUser": cost_per_user,
                "perLecture": cost_per_lecture,
                "margin": margin,
                "breakdown": cost_breakdown
            },
            "insights": insights
        }
    except Exception as e:
        import traceback
        print(f"Dashboard error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

def generate_insights(data: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate AI-powered insights"""
    insights = []
    
    # Low activation rate
    if data["activation_rate"] < 30:
        insights.append({
            "type": "warning",
            "title": "Low Activation Rate",
            "description": f"Only {data['activation_rate']:.1f}% of users create a lecture. This is below the 30% target.",
            "action": "Improve onboarding flow or add tutorial video"
        })
    
    # Low conversion
    if data["conversion_rate"] < 2:
        insights.append({
            "type": "warning",
            "title": "Low Free→Paid Conversion",
            "description": f"Conversion rate is {data['conversion_rate']:.1f}%, below the 2-5% target.",
            "action": "Consider adding more value to paid plans or reducing free tier limits"
        })
    
    # High costs
    if data["cost_per_user"] > 0.5:
        insights.append({
            "type": "warning",
            "title": "High Cost Per User",
            "description": f"Cost per user is ${data['cost_per_user']:.2f}, which is high for your pricing.",
            "action": "Investigate cost optimization opportunities or consider price increase"
        })
    
    # Good margin
    if data["margin"] > 90:
        insights.append({
            "type": "success",
            "title": "Excellent Margins",
            "description": f"Your gross margin of {data['margin']:.1f}% is exceptional for a SaaS business.",
            "action": "Consider investing in growth marketing"
        })
    
    # Power users
    if data["lectures_per_user"] > 5:
        insights.append({
            "type": "info",
            "title": "High User Engagement",
            "description": f"Users create {data['lectures_per_user']:.1f} lectures on average - great engagement!",
            "action": "Create case studies from power users"
        })
    
    return insights
