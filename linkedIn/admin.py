from django.contrib import admin
from .models import LinkedInProfile, LinkedInPost, LinkedInConnection


@admin.register(LinkedInProfile)
class LinkedInProfileAdmin(admin.ModelAdmin):
    list_display = ('social_account', 'headline', 'company', 'location', 'connection_count', 'updated_at')
    list_filter = ('industry', 'updated_at', 'created_at')
    search_fields = ('social_account__username', 'headline', 'company', 'industry')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('social_account', 'headline', 'summary', 'industry')
        }),
        ('Professional Details', {
            'fields': ('current_position', 'company', 'location')
        }),
        ('Profile Media', {
            'fields': ('profile_picture_url', 'background_image_url', 'public_profile_url')
        }),
        ('Metrics', {
            'fields': ('connection_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(LinkedInPost)
class LinkedInPostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'social_account', 'text_preview', 'like_count', 'comment_count', 'published_at')
    list_filter = ('social_account', 'has_image', 'has_video', 'is_shared', 'published_at')
    search_fields = ('post_id', 'text', 'social_account__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'published_at'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'


@admin.register(LinkedInConnection)
class LinkedInConnectionAdmin(admin.ModelAdmin):
    list_display = ('social_account', 'full_name', 'headline', 'industry', 'location', 'connected_at')
    list_filter = ('social_account', 'industry', 'connection_type', 'connected_at')
    search_fields = ('first_name', 'last_name', 'headline', 'industry', 'social_account__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'connected_at'
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = 'Full Name'
