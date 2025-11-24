"""Subscription management for free and premium tiers."""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SubscriptionTier(str, Enum):
    """Subscription tier types."""
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionLimits(BaseModel):
    """Limits for each subscription tier."""
    
    tier: SubscriptionTier
    daily_tasks: int
    word_limit: int
    max_search_rounds: int
    advanced_fact_checking: bool
    multi_round_search: bool
    citation_styles: list[str]
    export_formats: list[str]
    priority_queue: bool
    
    @classmethod
    def get_limits(cls, tier: SubscriptionTier) -> "SubscriptionLimits":
        """Get limits for a specific tier."""
        
        if tier == SubscriptionTier.FREE:
            return cls(
                tier=SubscriptionTier.FREE,
                daily_tasks=5,
                word_limit=2000,
                max_search_rounds=1,
                advanced_fact_checking=False,
                multi_round_search=False,
                citation_styles=["basic"],
                export_formats=["pdf", "markdown"],
                priority_queue=False
            )
        else:  # PREMIUM
            return cls(
                tier=SubscriptionTier.PREMIUM,
                daily_tasks=-1,  # Unlimited
                word_limit=5000,
                max_search_rounds=3,
                advanced_fact_checking=True,
                multi_round_search=True,
                citation_styles=["APA", "MLA", "IEEE"],
                export_formats=["pdf", "docx", "markdown"],
                priority_queue=True
            )


class UserSubscription(BaseModel):
    """User subscription information."""
    
    user_id: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    tasks_used_today: int = 0
    last_reset: datetime = Field(default_factory=datetime.now)
    total_tasks: int = 0
    
    def can_execute_task(self) -> tuple[bool, Optional[str]]:
        """
        Check if user can execute a task.
        
        Returns:
            (allowed, error_message)
        """
        
        # Reset daily counter if needed
        if (datetime.now() - self.last_reset).days >= 1:
            self.tasks_used_today = 0
            self.last_reset = datetime.now()
        
        limits = SubscriptionLimits.get_limits(self.tier)
        
        # Check daily limit
        if limits.daily_tasks > 0 and self.tasks_used_today >= limits.daily_tasks:
            return False, f"Daily limit reached ({limits.daily_tasks} tasks). Upgrade to Premium for unlimited access."
        
        # Check subscription expiry
        if self.end_date and datetime.now() > self.end_date:
            return False, "Subscription expired. Please renew your Premium subscription."
        
        return True, None
    
    def increment_usage(self):
        """Increment task usage counter."""
        self.tasks_used_today += 1
        self.total_tasks += 1
    
    def get_limits(self) -> SubscriptionLimits:
        """Get limits for this subscription."""
        return SubscriptionLimits.get_limits(self.tier)
    
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return self.tier == SubscriptionTier.PREMIUM
    
    def upgrade_to_premium(self, duration_days: int = 30):
        """Upgrade to premium subscription."""
        self.tier = SubscriptionTier.PREMIUM
        self.start_date = datetime.now()
        self.end_date = datetime.now() + timedelta(days=duration_days)
        self.tasks_used_today = 0
    
    def downgrade_to_free(self):
        """Downgrade to free tier."""
        self.tier = SubscriptionTier.FREE
        self.end_date = None
        self.tasks_used_today = 0


class SubscriptionManager:
    """Manages user subscriptions and enforces limits."""
    
    def __init__(self):
        self.subscriptions: Dict[str, UserSubscription] = {}
    
    def get_subscription(self, user_id: str) -> UserSubscription:
        """
        Get or create user subscription.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserSubscription object
        """
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = UserSubscription(user_id=user_id)
        
        return self.subscriptions[user_id]
    
    def check_access(
        self,
        user_id: str,
        feature: str = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can access a feature.
        
        Args:
            user_id: User identifier
            feature: Optional feature to check
            
        Returns:
            (allowed, error_message)
        """
        subscription = self.get_subscription(user_id)
        
        # Check if can execute task
        can_execute, error = subscription.can_execute_task()
        if not can_execute:
            return False, error
        
        # Check specific feature access
        if feature:
            limits = subscription.get_limits()
            
            if feature == "advanced_fact_checking" and not limits.advanced_fact_checking:
                return False, "Advanced fact-checking is only available in Premium tier."
            
            if feature == "multi_round_search" and not limits.multi_round_search:
                return False, "Multi-round search is only available in Premium tier."
            
            if feature == "docx_export" and "docx" not in limits.export_formats:
                return False, "DOCX export is only available in Premium tier."
        
        return True, None
    
    def record_usage(self, user_id: str):
        """Record a task execution."""
        subscription = self.get_subscription(user_id)
        subscription.increment_usage()
    
    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        subscription = self.get_subscription(user_id)
        limits = subscription.get_limits()
        
        return {
            "tier": subscription.tier.value,
            "tasks_used_today": subscription.tasks_used_today,
            "daily_limit": limits.daily_tasks if limits.daily_tasks > 0 else "unlimited",
            "total_tasks": subscription.total_tasks,
            "subscription_active": subscription.end_date is None or datetime.now() <= subscription.end_date,
            "days_remaining": (subscription.end_date - datetime.now()).days if subscription.end_date else None
        }
