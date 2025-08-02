from django.db import models
from django.contrib.auth.models import User
from accounts.models import SocialMediaAccount


class LinkedInProfile(models.Model):
    """LinkedIn-specific profile data"""
    social_account = models.OneToOneField(SocialMediaAccount, on_delete=models.CASCADE, related_name='linkedin_profile')
    
    # LinkedIn specific fields
    industry = models.CharField(max_length=200, blank=True)
    headline = models.CharField(max_length=220, blank=True)  # LinkedIn headline limit
    summary = models.TextField(blank=True)
    current_position = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    public_profile_url = models.URLField(blank=True)
    
    # Connection metrics
    connection_count = models.IntegerField(default=0)
    
    # Profile completeness
    profile_picture_url = models.URLField(blank=True)
    background_image_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"LinkedIn Profile: {self.social_account.username}"


class LinkedInPost(models.Model):
    """Store LinkedIn posts for analytics"""
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='linkedin_posts')
    
    # Post identification
    post_id = models.CharField(max_length=100, unique=True)
    post_url = models.URLField(blank=True)
    
    # Post content
    text = models.TextField(blank=True)
    has_image = models.BooleanField(default=False)
    has_video = models.BooleanField(default=False)
    has_document = models.BooleanField(default=False)
    
    # Engagement metrics
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    impression_count = models.IntegerField(default=0)
    
    # Post metadata
    published_at = models.DateTimeField()
    is_shared = models.BooleanField(default=False)  # True if this is a share/repost
    original_post_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['social_account', 'published_at']),
            models.Index(fields=['post_id']),
        ]

    def __str__(self):
        return f"LinkedIn Post: {self.post_id[:20]}..."


class LinkedInConnection(models.Model):
    """Track LinkedIn connections"""
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='linkedin_connections')
    
    # Connection details
    connection_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    headline = models.CharField(max_length=220, blank=True)
    industry = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_url = models.URLField(blank=True)
    
    # Connection metadata
    connected_at = models.DateTimeField()
    connection_type = models.CharField(max_length=20, default='standard')  # standard, premium, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['social_account', 'connection_id']
        indexes = [
            models.Index(fields=['social_account', 'connected_at']),
        ]

    def __str__(self):
        return f"LinkedIn Connection: {self.first_name} {self.last_name}"
