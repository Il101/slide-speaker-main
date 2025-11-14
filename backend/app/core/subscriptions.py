"""Subscription tiers and rate limiting"""
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, extract
import logging

from .database import get_db, User, Lesson

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionPlan:
    """Subscription plan configuration"""
    
    FREE = {
        "name": "Free",
        "presentations_per_month": 3,
        "max_slides": 10,
        "max_file_size_mb": 10,
        "ai_quality": "basic",
        "export_formats": ["mp4"],
        "priority": "low",
        "custom_voices": False,
        "api_access": False,
        "concurrent_processing": 1,
        "features": [
            "3 presentations per month",
            "Up to 10 slides per presentation",
            "Basic AI quality",
            "MP4 export only"
        ]
    }
    
    PRO = {
        "name": "Professional",
        "price_monthly": 29.99,
        "presentations_per_month": 50,
        "max_slides": 100,
        "max_file_size_mb": 50,
        "ai_quality": "premium",
        "export_formats": ["mp4", "webm", "gif"],
        "priority": "high",
        "custom_voices": True,
        "api_access": False,
        "concurrent_processing": 3,
        "features": [
            "50 presentations per month",
            "Up to 100 slides per presentation",
            "Premium AI quality",
            "Multiple export formats",
            "High priority processing",
            "Custom voice selection"
        ]
    }
    
    ENTERPRISE = {
        "name": "Enterprise",
        "price_monthly": 99.99,
        "presentations_per_month": -1,  # Unlimited
        "max_slides": 500,
        "max_file_size_mb": 200,
        "ai_quality": "premium",
        "export_formats": ["mp4", "webm", "gif", "scorm"],
        "priority": "critical",
        "custom_voices": True,
        "api_access": True,
        "concurrent_processing": 10,
        "features": [
            "Unlimited presentations",
            "Up to 500 slides per presentation",
            "Premium AI quality",
            "All export formats including SCORM",
            "Critical priority processing",
            "Custom voices",
            "API access",
            "Dedicated support"
        ]
    }
    
    @classmethod
    def get_plan(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get plan configuration for a tier"""
        if tier == SubscriptionTier.FREE:
            return cls.FREE
        elif tier == SubscriptionTier.PRO:
            return cls.PRO
        elif tier == SubscriptionTier.ENTERPRISE:
            return cls.ENTERPRISE
        else:
            return cls.FREE
    
    @classmethod
    def get_all_plans(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available plans"""
        return {
            "free": cls.FREE,
            "pro": cls.PRO,
            "enterprise": cls.ENTERPRISE
        }


class SubscriptionManager:
    """Manage user subscriptions and limits"""
    
    @staticmethod
    async def get_user_usage(user_id: str, db: AsyncSession) -> Dict[str, int]:
        """
        Get user's actual usage statistics from database
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Usage statistics
        """
        # Get current month presentations count
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        result = await db.execute(
            select(func.count(Lesson.id))
            .where(Lesson.user_id == user_id)
            .where(extract('month', Lesson.created_at) == current_month)
            .where(extract('year', Lesson.created_at) == current_year)
        )
        presentations_this_month = result.scalar_one()
        
        # Get current concurrent processing
        concurrent_result = await db.execute(
            select(func.count(Lesson.id))
            .where(Lesson.user_id == user_id)
            .where(Lesson.status == "processing")
        )
        current_concurrent = concurrent_result.scalar_one()
        
        return {
            "presentations_this_month": presentations_this_month,
            "current_concurrent": current_concurrent
        }
    
    @staticmethod
    async def get_user_subscription(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Get user's subscription information
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Subscription info including tier, usage, and limits
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get tier (default to FREE if not set)
        tier = SubscriptionTier(getattr(user, 'subscription_tier', 'free'))
        plan = SubscriptionPlan.get_plan(tier)
        
        # Get real usage from database
        usage = await SubscriptionManager.get_user_usage(user_id, db)
        
        return {
            "user_id": user_id,
            "tier": tier.value,
            "plan": plan,
            "usage": usage,
            "expires_at": None  # Lifetime subscription - no expiration
        }
    
    @staticmethod
    async def check_presentation_limit(
        user_id: str,
        db: AsyncSession,
        slides_count: Optional[int] = None,
        file_size_mb: Optional[float] = None
    ) -> bool:
        """
        Check if user can create a new presentation
        
        Args:
            user_id: User ID
            db: Database session
            slides_count: Number of slides (optional)
            file_size_mb: File size in MB (optional)
            
        Returns:
            True if allowed, raises HTTPException if limit exceeded
        """
        subscription = await SubscriptionManager.get_user_subscription(user_id, db)
        plan = subscription["plan"]
        usage = subscription["usage"]
        
        # Check monthly limit
        if plan["presentations_per_month"] != -1:  # -1 means unlimited
            if usage["presentations_this_month"] >= plan["presentations_per_month"]:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Monthly limit reached ({plan['presentations_per_month']} presentations). "
                           f"Upgrade to {SubscriptionTier.PRO.value} or {SubscriptionTier.ENTERPRISE.value} for more."
                )
        
        # Check slides limit
        if slides_count and slides_count > plan["max_slides"]:
            raise HTTPException(
                status_code=400,
                detail=f"Presentation has {slides_count} slides, but your plan allows maximum "
                       f"{plan['max_slides']} slides. Please upgrade your plan."
            )
        
        # Check file size limit
        if file_size_mb and file_size_mb > plan["max_file_size_mb"]:
            raise HTTPException(
                status_code=400,
                detail=f"File size is {file_size_mb:.1f}MB, but your plan allows maximum "
                       f"{plan['max_file_size_mb']}MB. Please upgrade your plan."
            )
        
        # Check concurrent processing limit
        if usage["current_concurrent"] >= plan["concurrent_processing"]:
            raise HTTPException(
                status_code=429,  # Too Many Requests
                detail=f"You have reached your concurrent processing limit "
                       f"({plan['concurrent_processing']}). Please wait for current "
                       "presentations to complete or upgrade your plan."
            )
        
        return True
    
    @staticmethod
    async def check_feature_access(
        user_id: str,
        feature: str,
        db: AsyncSession
    ) -> bool:
        """
        Check if user has access to a specific feature
        
        Args:
            user_id: User ID
            feature: Feature name (e.g., "custom_voices", "api_access")
            db: Database session
            
        Returns:
            True if has access, False otherwise
        """
        subscription = await SubscriptionManager.get_user_subscription(user_id, db)
        plan = subscription["plan"]
        
        return plan.get(feature, False)
    
    @staticmethod
    async def get_processing_priority(user_id: str, db: AsyncSession) -> str:
        """
        Get processing priority for user's tier
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Priority level: "low", "high", or "critical"
        """
        subscription = await SubscriptionManager.get_user_subscription(user_id, db)
        return subscription["plan"]["priority"]
    
    @staticmethod
    async def increment_usage(user_id: str, db: AsyncSession):
        """
        Increment user's presentation usage count
        
        Note: Usage is automatically tracked through Lesson creation,
        so this method just logs for monitoring purposes.
        
        Args:
            user_id: User ID
            db: Database session
        """
        usage = await SubscriptionManager.get_user_usage(user_id, db)
        logger.info(
            f"User {user_id} usage: "
            f"{usage['presentations_this_month']} presentations this month, "
            f"{usage['current_concurrent']} concurrent processing"
        )


# Dependency to require subscription tier
async def require_tier(
    min_tier: SubscriptionTier,
    user: dict = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency to require minimum subscription tier
    
    Args:
        min_tier: Minimum required tier
        user: Current user (from auth)
        db: Database session
        
    Raises:
        HTTPException if user doesn't have required tier
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    subscription = await SubscriptionManager.get_user_subscription(user["user_id"], db)
    user_tier = SubscriptionTier(subscription["tier"])
    
    # Define tier hierarchy
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 1,
        SubscriptionTier.ENTERPRISE: 2
    }
    
    if tier_order[user_tier] < tier_order[min_tier]:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"This feature requires {min_tier.value} tier or higher. "
                   f"You are currently on {user_tier.value} tier."
        )
    
    return subscription


# Dependency to check and enforce limits
async def enforce_limits(
    request: Request,
    user: dict = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """
    Middleware dependency to enforce subscription limits
    
    Args:
        request: FastAPI request
        user: Current user
        db: Database session
    """
    if not user:
        # Allow unauthenticated access to public endpoints
        return
    
    # For presentation upload/creation endpoints, check limits
    if request.method == "POST" and "/upload" in str(request.url):
        await SubscriptionManager.check_presentation_limit(
            user["user_id"],
            db
        )
    
    return


# Subscription tier middleware
class SubscriptionMiddleware:
    """Middleware to add subscription info to requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Add subscription tier to request state if user is authenticated
        if hasattr(request.state, 'user'):
            try:
                user_id = request.state.user.get('user_id')
                if user_id:
                    # Get subscription (cached or from DB)
                    # For now, just set a default
                    request.state.subscription_tier = SubscriptionTier.FREE
            except Exception as e:
                logger.warning(f"Failed to load subscription: {e}")
        
        response = await call_next(request)
        return response
