"""
Subscription Management API

Provides endpoints for:
- Get subscription information
- Get available plans
- Usage tracking
- Upgrade subscription
- Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import os

from ..core.auth import get_current_user
from ..core.database import get_db, User
from ..core.subscriptions import SubscriptionManager, SubscriptionTier, SubscriptionPlan
from ..models.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["subscriptions"])

# Initialize subscription manager
subscription_manager = SubscriptionManager()

# Stripe configuration
STRIPE_ENABLED = os.getenv("STRIPE_SECRET_KEY") is not None
if STRIPE_ENABLED:
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        logger.info("Stripe integration enabled")
    except ImportError:
        logger.warning("Stripe library not installed, payment features disabled")
        STRIPE_ENABLED = False
else:
    logger.info("Stripe not configured (STRIPE_SECRET_KEY not set)")


# Request/Response models
class UpgradeRequest(BaseModel):
    tier: str  # "pro" or "enterprise"


class CheckoutSessionResponse(BaseModel):
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    message: Optional[str] = None


@router.get("/info")
async def get_subscription_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user's subscription information
    
    Returns:
        - user_id
        - tier (free/pro/enterprise)
        - plan details
        - usage statistics
        - expiration date (if applicable)
    """
    try:
        # Get full user object from database
        user_id = current_user["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's subscription tier from database
        tier_str = getattr(user, 'subscription_tier', 'free')
        try:
            tier = SubscriptionTier(tier_str)
        except ValueError:
            tier = SubscriptionTier.FREE
        
        # Get plan details
        plan = SubscriptionPlan.get_plan(tier)
        
        # Get real usage statistics from database
        usage = await subscription_manager.get_user_usage(user_id, db)
        
        return {
            "user_id": str(user.id),
            "tier": tier.value,
            "plan": plan,
            "usage": usage,
            "expires_at": None  # Lifetime subscription - no expiration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_subscription_plans() -> Dict[str, Any]:
    """
    Get all available subscription plans
    
    Public endpoint - no authentication required
    """
    return {
        "free": SubscriptionPlan.get_plan(SubscriptionTier.FREE),
        "pro": SubscriptionPlan.get_plan(SubscriptionTier.PRO),
        "enterprise": SubscriptionPlan.get_plan(SubscriptionTier.ENTERPRISE)
    }


@router.post("/check-limits")
async def check_subscription_limits(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if user has reached their subscription limits
    
    Returns:
        - can_create: bool
        - reason: str (if can_create is False)
        - limits: current plan limits
    """
    try:
        # Get full user object from database
        user_id = current_user["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's subscription tier
        tier_str = getattr(user, 'subscription_tier', 'free')
        try:
            tier = SubscriptionTier(tier_str)
        except ValueError:
            tier = SubscriptionTier.FREE
            
        plan = SubscriptionPlan.get_plan(tier)
        
        # Get actual usage from database
        usage = await subscription_manager.get_user_usage(user_id, db)
        presentations_this_month = usage["presentations_this_month"]
        
        # Check if user can create (unlimited = -1, or within limit)
        monthly_limit = plan["presentations_per_month"]
        can_create = monthly_limit == -1 or presentations_this_month < monthly_limit
        
        return {
            "can_create": can_create,
            "reason": None if can_create else f"Monthly limit of {plan['presentations_per_month']} presentations reached",
            "limits": {
                "presentations_per_month": plan["presentations_per_month"],
                "max_slides": plan["max_slides"],
                "max_file_size_mb": plan["max_file_size_mb"]
            },
            "usage": usage
        }
        
    except Exception as e:
        logger.error(f"Error checking limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upgrade")
async def upgrade_subscription(
    upgrade_request: UpgradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upgrade user's subscription tier
    
    Note: In production, this should only be called after successful payment
    or by admins. For now, this is used for testing.
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate tier
        try:
            new_tier = SubscriptionTier(upgrade_request.tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {upgrade_request.tier}")
        
        # Update user's subscription tier
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(subscription_tier=new_tier.value)
        )
        await db.commit()
        
        logger.info(f"User {user_id} upgraded to {new_tier.value}")
        
        return {
            "success": True,
            "tier": new_tier.value,
            "message": f"Successfully upgraded to {new_tier.value}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-checkout")
async def create_checkout_session(
    upgrade_request: UpgradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CheckoutSessionResponse:
    """
    Create Stripe checkout session for subscription upgrade
    
    Returns:
        - session_id: Stripe checkout session ID
        - session_url: URL to redirect user to Stripe checkout
    """
    if not STRIPE_ENABLED:
        return CheckoutSessionResponse(
            message="Payment system is not configured. Please contact administrator."
        )
    
    try:
        user_id = current_user["user_id"]
        
        # Validate tier
        try:
            new_tier = SubscriptionTier(upgrade_request.tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {upgrade_request.tier}")
        
        # Get plan details
        plan = SubscriptionPlan.get_plan(new_tier)
        
        # Create Stripe checkout session
        # Note: You need to create products and prices in Stripe dashboard first
        # For now, using a test mode with dynamic pricing
        
        price_map = {
            "pro": "price_pro_monthly",  # Replace with actual Stripe price ID
            "enterprise": "price_enterprise_monthly"  # Replace with actual Stripe price ID
        }
        
        price_id = price_map.get(upgrade_request.tier)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.get("email"),
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/subscription?success=true",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/subscription?canceled=true",
            metadata={
                "user_id": user_id,
                "tier": upgrade_request.tier
            }
        )
        
        logger.info(f"Created checkout session for user {user_id}: {checkout_session.id}")
        
        return CheckoutSessionResponse(
            session_id=checkout_session.id,
            session_url=checkout_session.url
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment system error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Handle Stripe webhook events
    
    This endpoint receives notifications from Stripe about:
    - payment_intent.succeeded
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    if not STRIPE_ENABLED:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event["type"]
    logger.info(f"Received Stripe webhook: {event_type}")
    
    try:
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            tier = session["metadata"]["tier"]
            
            # Update user's subscription
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    subscription_tier=tier,
                    # Add subscription_expires_at if needed
                )
            )
            await db.commit()
            
            logger.info(f"User {user_id} subscription updated to {tier} via webhook")
            
        elif event_type == "customer.subscription.deleted":
            session = event["data"]["object"]
            # Downgrade user to free tier when subscription is canceled
            # You would need to store customer_id in User table to match
            logger.info(f"Subscription deleted: {session['id']}")
            
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
