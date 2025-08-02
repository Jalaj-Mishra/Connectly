from django.contrib import admin
from .models import TwitterProfile, Tweet, TwitterFollower, TwitterHashtag


@admin.register(TwitterProfile)
class TwitterProfileAdmin(admin.ModelAdmin):
    list_display = ('screen_name', 'social_account', 'followers_count', 'following_count', 'tweet_count', 'is_verified')
    list_filter = ('is_verified', 'is_protected', 'created_at_twitter', 'updated_at')
    search_fields = ('screen_name', 'description', 'location', 'social_account__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('social_account', 'screen_name', 'description', 'location', 'website')
        }),
        ('Account Metrics', {
            'fields': ('followers_count', 'following_count', 'tweet_count', 'like_count')
        }),
        ('Account Settings', {
            'fields': ('is_verified', 'is_protected', 'created_at_twitter')
        }),
        ('Profile Media', {
            'fields': ('profile_image_url', 'profile_banner_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('tweet_id', 'social_account', 'text_preview', 'tweet_type', 'retweet_count', 'like_count', 'published_at')
    list_filter = ('social_account', 'is_retweet', 'is_quote_tweet', 'is_reply', 'has_media', 'published_at')
    search_fields = ('tweet_id', 'text', 'social_account__screen_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'published_at'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'
    
    def tweet_type(self, obj):
        if obj.is_retweet:
            return 'Retweet'
        elif obj.is_quote_tweet:
            return 'Quote Tweet'
        elif obj.is_reply:
            return 'Reply'
        else:
            return 'Original Tweet'
    tweet_type.short_description = 'Type'


@admin.register(TwitterFollower)
class TwitterFollowerAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'social_account', 'followers_count', 'is_verified', 'is_currently_following', 'followed_at')
    list_filter = ('social_account', 'is_verified', 'is_protected', 'is_currently_following', 'followed_at')
    search_fields = ('username', 'display_name', 'description', 'social_account__screen_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'followed_at'


@admin.register(TwitterHashtag)
class TwitterHashtagAdmin(admin.ModelAdmin):
    list_display = ('hashtag', 'social_account', 'usage_count', 'avg_engagement_rate', 'total_impressions', 'last_used')
    list_filter = ('social_account', 'last_used', 'first_used')
    search_fields = ('hashtag', 'social_account__screen_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-usage_count', '-avg_engagement_rate')
