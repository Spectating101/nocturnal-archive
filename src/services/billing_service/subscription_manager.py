# src/services/billing_service/subscription_manager.py

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import stripe
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """Subscription tiers with their limits and features."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class SubscriptionManager:
    """
    Production-grade subscription and billing manager with Stripe integration.
    
    Features:
    - Stripe payment processing
    - Subscription tier management
    - Usage tracking and limits
    - Invoice generation
    - Refund processing
    - Tax handling
    """
    
    def __init__(self, stripe_secret_key: str):
        """
        Initialize subscription manager.
        
        Args:
            stripe_secret_key: Stripe secret key
        """
        self.stripe = stripe
        self.stripe.api_key = stripe_secret_key
        
        # Subscription tier configurations
        self.tier_configs = {
            SubscriptionTier.FREE: {
                "name": "Free",
                "price_id": None,
                "monthly_price": 0,
                "searches_per_month": 5,
                "features": ["basic_search", "simple_export"],
                "api_calls_per_month": 10,
                "support_level": "community"
            },
            SubscriptionTier.PRO: {
                "name": "Pro",
                "price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
                "monthly_price": 49,
                "searches_per_month": 100,
                "features": ["advanced_search", "analytics", "team_collaboration", "priority_support"],
                "api_calls_per_month": 1000,
                "support_level": "email"
            },
            SubscriptionTier.BUSINESS: {
                "name": "Business",
                "price_id": os.getenv("STRIPE_BUSINESS_PRICE_ID"),
                "monthly_price": 149,
                "searches_per_month": 500,
                "features": ["all_pro_features", "api_access", "custom_integrations", "dedicated_support"],
                "api_calls_per_month": 10000,
                "support_level": "phone"
            },
            SubscriptionTier.ENTERPRISE: {
                "name": "Enterprise",
                "price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
                "monthly_price": 0,  # Custom pricing
                "searches_per_month": -1,  # Unlimited
                "features": ["all_features", "white_label", "custom_deployment", "sla_guarantee"],
                "api_calls_per_month": -1,  # Unlimited
                "support_level": "dedicated"
            }
        }
        
        logger.info("SubscriptionManager initialized successfully")
    
    async def create_customer(self, email: str, name: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Stripe customer ID
        """
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create customer")
    
    async def create_subscription(self, customer_id: str, tier: SubscriptionTier, payment_method_id: str = None) -> Dict[str, Any]:
        """
        Create a new subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            tier: Subscription tier
            payment_method_id: Payment method ID (optional)
            
        Returns:
            Subscription data
        """
        try:
            tier_config = self.tier_configs[tier]
            
            if tier == SubscriptionTier.FREE:
                # Free tier doesn't require Stripe subscription
                return {
                    "subscription_id": f"free_{customer_id}",
                    "status": "active",
                    "tier": tier.value,
                    "current_period_start": datetime.utcnow().isoformat(),
                    "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
                }
            
            if not tier_config["price_id"]:
                raise HTTPException(status_code=400, detail="Invalid subscription tier")
            
            # Create subscription
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": tier_config["price_id"]}],
                "payment_behavior": "default_incomplete",
                "expand": ["latest_invoice.payment_intent"]
            }
            
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id
            
            subscription = self.stripe.Subscription.create(**subscription_data)
            
            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "tier": tier.value,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "latest_invoice": subscription.latest_invoice.id if subscription.latest_invoice else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create subscription")
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription data or None
        """
        try:
            if subscription_id.startswith("free_"):
                # Handle free tier
                return {
                    "subscription_id": subscription_id,
                    "status": "active",
                    "tier": "free",
                    "current_period_start": datetime.utcnow().isoformat(),
                    "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
                }
            
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "tier": self._get_tier_from_price_id(subscription.items.data[0].price.id),
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription: {str(e)}")
            return None
    
    async def cancel_subscription(self, subscription_id: str, cancel_at_period_end: bool = True) -> bool:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            cancel_at_period_end: Whether to cancel at period end
            
        Returns:
            Success status
        """
        try:
            if subscription_id.startswith("free_"):
                # Free tier can be cancelled immediately
                return True
            
            if cancel_at_period_end:
                subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = self.stripe.Subscription.cancel(subscription_id)
            
            logger.info(f"Cancelled subscription: {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            return False
    
    async def update_subscription(self, subscription_id: str, tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Update subscription to a different tier.
        
        Args:
            subscription_id: Stripe subscription ID
            tier: New subscription tier
            
        Returns:
            Updated subscription data
        """
        try:
            if subscription_id.startswith("free_"):
                # Upgrade from free tier
                return await self.create_subscription(
                    customer_id=subscription_id.replace("free_", ""),
                    tier=tier
                )
            
            tier_config = self.tier_configs[tier]
            
            if not tier_config["price_id"]:
                raise HTTPException(status_code=400, detail="Invalid subscription tier")
            
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription.items.data[0].id,
                    "price": tier_config["price_id"]
                }],
                proration_behavior="create_prorations"
            )
            
            logger.info(f"Updated subscription: {subscription_id} to tier: {tier.value}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "tier": tier.value,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update subscription")
    
    async def create_invoice(self, customer_id: str, amount: int, currency: str = "usd", description: str = None) -> str:
        """
        Create an invoice for a customer.
        
        Args:
            customer_id: Stripe customer ID
            amount: Amount in cents
            currency: Currency code
            description: Invoice description
            
        Returns:
            Invoice ID
        """
        try:
            invoice = self.stripe.Invoice.create(
                customer=customer_id,
                description=description or "Nocturnal Archive usage",
                auto_advance=False
            )
            
            self.stripe.InvoiceItem.create(
                customer=customer_id,
                invoice=invoice.id,
                amount=amount,
                currency=currency,
                description=description or "API usage"
            )
            
            invoice = self.stripe.Invoice.finalize_invoice(invoice.id)
            
            logger.info(f"Created invoice: {invoice.id} for customer: {customer_id}")
            return invoice.id
            
        except Exception as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create invoice")
    
    async def process_refund(self, payment_intent_id: str, amount: int = None, reason: str = "requested_by_customer") -> str:
        """
        Process a refund for a payment.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Refund amount in cents (None for full refund)
            reason: Refund reason
            
        Returns:
            Refund ID
        """
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason
            }
            
            if amount:
                refund_data["amount"] = amount
            
            refund = self.stripe.Refund.create(**refund_data)
            
            logger.info(f"Processed refund: {refund.id} for payment: {payment_intent_id}")
            return refund.id
            
        except Exception as e:
            logger.error(f"Failed to process refund: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process refund")
    
    def get_tier_limits(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Get limits for a subscription tier.
        
        Args:
            tier: Subscription tier
            
        Returns:
            Tier limits
        """
        return self.tier_configs[tier]
    
    def check_usage_limit(self, tier: SubscriptionTier, current_usage: int, usage_type: str = "searches") -> bool:
        """
        Check if usage is within tier limits.
        
        Args:
            tier: Subscription tier
            current_usage: Current usage count
            usage_type: Type of usage (searches, api_calls)
            
        Returns:
            True if within limits
        """
        tier_config = self.tier_configs[tier]
        
        if usage_type == "searches":
            limit = tier_config["searches_per_month"]
        elif usage_type == "api_calls":
            limit = tier_config["api_calls_per_month"]
        else:
            return False
        
        # -1 means unlimited
        if limit == -1:
            return True
        
        return current_usage < limit
    
    def _get_tier_from_price_id(self, price_id: str) -> str:
        """
        Get tier name from Stripe price ID.
        
        Args:
            price_id: Stripe price ID
            
        Returns:
            Tier name
        """
        for tier, config in self.tier_configs.items():
            if config["price_id"] == price_id:
                return tier.value
        
        return "unknown"

# Global subscription manager instance
subscription_manager = SubscriptionManager(
    stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "")
)
