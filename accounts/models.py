from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json


class UserProfile(models.Model):
    """Extended user profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    email_notifications = models.BooleanField(default=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='light'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class SocialMediaAccount(models.Model):
    """Store social media account information and tokens"""
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Token Expired'),
        ('revoked', 'Access Revoked'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_user_id = models.CharField(max_length=100)  # Social platform's user ID
    username = models.CharField(max_length=100)
    display_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    profile_url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    
    # Token information (encrypted)
    access_token = models.TextField()  # Encrypted access token
    refresh_token = models.TextField(blank=True, null=True)  # Encrypted refresh token
    token_expires_at = models.DateTimeField(blank=True, null=True)
    scope = models.TextField(blank=True)  # OAuth scopes granted
    
    # Account status and metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    last_sync = models.DateTimeField(blank=True, null=True)
    follower_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    
    # Additional platform-specific data (JSON field)
    extra_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'platform', 'platform_user_id']
        indexes = [
            models.Index(fields=['user', 'platform']),
            models.Index(fields=['status']),
            models.Index(fields=['last_sync']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.platform} ({self.username})"

    def is_token_expired(self):
        """Check if the access token is expired"""
        if not self.token_expires_at:
            return False
        return timezone.now() > self.token_expires_at
    
    def disconnect(self):
        """Safely disconnect this social media account"""
        # Clear sensitive data before deletion
        self.access_token = ''
        self.refresh_token = ''
        self.status = 'inactive'
        self.save()
        
        # Delete the account (cascading will handle related data)
        self.delete()


class APICallLog(models.Model):
    """Log API calls for monitoring and rate limiting"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_calls')
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='api_calls')
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField()  # Response time in seconds
    rate_limit_remaining = models.IntegerField(blank=True, null=True)
    rate_limit_reset = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['social_account', 'created_at']),
            models.Index(fields=['endpoint', 'created_at']),
        ]

    def __str__(self):
        return f"{self.social_account.platform} API call - {self.endpoint} ({self.status_code})"


class UserAnalytics(models.Model):
    """Store user analytics and engagement metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='analytics')
    
    # Date for which these metrics are recorded
    date = models.DateField()
    
    # Engagement metrics
    likes_received = models.IntegerField(default=0)
    comments_received = models.IntegerField(default=0)
    shares_received = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    
    # Activity metrics
    posts_published = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    comments_made = models.IntegerField(default=0)
    
    # Follower metrics
    followers_gained = models.IntegerField(default=0)
    followers_lost = models.IntegerField(default=0)
    following_gained = models.IntegerField(default=0)
    following_lost = models.IntegerField(default=0)
    
    # Platform-specific metrics (JSON field for flexibility)
    custom_metrics = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['social_account', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['social_account', 'date']),
        ]

    def __str__(self):
        return f"{self.social_account.platform} analytics for {self.date}"


class SessionData(models.Model):
    """Store session-related data for persistent state"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_data')
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='session_data', null=True, blank=True)
    
    # OAuth state and session information
    oauth_state = models.CharField(max_length=255, blank=True)
    code_verifier = models.CharField(max_length=255, blank=True)  # For PKCE
    redirect_uri = models.URLField(blank=True)
    
    # Temporary data storage
    temp_data = models.JSONField(default=dict, blank=True)
    
    # Session metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
            models.Index(fields=['oauth_state']),
        ]

    def __str__(self):
        platform = self.social_account.platform if self.social_account else 'General'
        return f"Session data for {self.user.username} - {platform}"

    def is_expired(self):
        """Check if session data is expired"""
        return timezone.now() > self.expires_at
