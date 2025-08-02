from django.db import models
from django.contrib.auth.models import User
from accounts.models import SocialMediaAccount


class TwitterProfile(models.Model):
    """Twitter-specific profile data"""
    social_account = models.OneToOneField(SocialMediaAccount, on_delete=models.CASCADE, related_name='twitter_profile')
    
    # Twitter specific fields
    screen_name = models.CharField(max_length=15)  # Twitter handle without @
    description = models.CharField(max_length=160, blank=True)  # Bio
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Account metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)  # Total likes received
    
    # Account settings
    is_verified = models.BooleanField(default=False)
    is_protected = models.BooleanField(default=False)  # Private account
    created_at_twitter = models.DateTimeField(null=True, blank=True)  # When Twitter account was created
    
    # Profile media
    profile_image_url = models.URLField(blank=True)
    profile_banner_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Twitter Profile: @{self.screen_name}"


class Tweet(models.Model):
    """Store tweets for analytics"""
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='tweets')
    
    # Tweet identification
    tweet_id = models.CharField(max_length=100, unique=True)
    tweet_url = models.URLField(blank=True)
    
    # Tweet content
    text = models.CharField(max_length=280)  # Twitter character limit
    has_media = models.BooleanField(default=False)
    has_video = models.BooleanField(default=False)
    has_image = models.BooleanField(default=False)
    has_gif = models.BooleanField(default=False)
    has_poll = models.BooleanField(default=False)
    
    # Tweet type
    is_retweet = models.BooleanField(default=False)
    is_quote_tweet = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    
    # Referenced tweets
    retweeted_tweet_id = models.CharField(max_length=100, blank=True)
    quoted_tweet_id = models.CharField(max_length=100, blank=True)
    replied_to_tweet_id = models.CharField(max_length=100, blank=True)
    
    # Engagement metrics
    retweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)
    impression_count = models.IntegerField(default=0)
    
    # Tweet metadata
    published_at = models.DateTimeField()
    language = models.CharField(max_length=10, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['social_account', 'published_at']),
            models.Index(fields=['tweet_id']),
            models.Index(fields=['is_retweet', 'is_quote_tweet', 'is_reply']),
        ]

    def __str__(self):
        return f"Tweet: {self.text[:50]}..."


class TwitterFollower(models.Model):
    """Track Twitter followers"""
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='twitter_followers')
    
    # Follower details
    follower_id = models.CharField(max_length=100)
    username = models.CharField(max_length=15)
    display_name = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=160, blank=True)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    
    # Follower metadata
    is_verified = models.BooleanField(default=False)
    is_protected = models.BooleanField(default=False)
    profile_image_url = models.URLField(blank=True)
    
    # Tracking data
    followed_at = models.DateTimeField()
    unfollowed_at = models.DateTimeField(null=True, blank=True)
    is_currently_following = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['social_account', 'follower_id']
        indexes = [
            models.Index(fields=['social_account', 'followed_at']),
            models.Index(fields=['is_currently_following']),
        ]

    def __str__(self):
        return f"Twitter Follower: @{self.username}"


class TwitterHashtag(models.Model):
    """Track hashtag usage and performance"""
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='twitter_hashtags')
    
    # Hashtag data
    hashtag = models.CharField(max_length=100)  # Without the # symbol
    
    # Usage metrics
    usage_count = models.IntegerField(default=1)
    total_impressions = models.IntegerField(default=0)
    total_engagements = models.IntegerField(default=0)
    avg_engagement_rate = models.FloatField(default=0.0)
    
    # Performance tracking
    best_performing_tweet_id = models.CharField(max_length=100, blank=True)
    first_used = models.DateTimeField()
    last_used = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['social_account', 'hashtag']
        indexes = [
            models.Index(fields=['hashtag']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return f"#{self.hashtag} (used {self.usage_count} times)"
