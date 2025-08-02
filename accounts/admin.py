from django.contrib import admin
from .models import UserProfile, SocialMediaAccount, APICallLog, UserAnalytics, SessionData


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'theme_preference', 'email_notifications', 'created_at')
    list_filter = ('theme_preference', 'email_notifications', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'username', 'status', 'follower_count', 'last_sync', 'created_at')
    list_filter = ('platform', 'status', 'created_at', 'last_sync')
    search_fields = ('user__username', 'username', 'display_name', 'email')
    readonly_fields = ('created_at', 'updated_at', 'access_token', 'refresh_token')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'platform', 'platform_user_id', 'username', 'display_name', 'email')
        }),
        ('Profile Data', {
            'fields': ('profile_url', 'avatar_url', 'status', 'last_sync')
        }),
        ('Metrics', {
            'fields': ('follower_count', 'following_count', 'posts_count')
        }),
        ('Token Information', {
            'fields': ('access_token', 'refresh_token', 'token_expires_at', 'scope'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ('social_account', 'endpoint', 'method', 'status_code', 'response_time', 'created_at')
    list_filter = ('social_account__platform', 'method', 'status_code', 'created_at')
    search_fields = ('endpoint', 'social_account__username')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('social_account', 'user')


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('social_account', 'date', 'likes_received', 'comments_received', 'posts_published', 'followers_gained')
    list_filter = ('social_account__platform', 'date')
    search_fields = ('social_account__username', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('social_account', 'user')


@admin.register(SessionData)
class SessionDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'social_account', 'oauth_state', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('user__username', 'oauth_state')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'social_account')
