"""
Utility functions for social media integrations
"""
import base64
import json
import hashlib
import secrets
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from accounts.models import SocialMediaAccount, APICallLog, SessionData
import time


class TokenManager:
    """Manage OAuth tokens securely"""
    
    @staticmethod
    def encrypt_token(token):
        """Simple token encryption using Django's SECRET_KEY"""
        if not token:
            return ""
        
        # Use Django's SECRET_KEY for encryption
        key = settings.SECRET_KEY.encode()
        token_bytes = token.encode()
        
        # Simple XOR encryption (for production, use proper encryption)
        encrypted = bytes(a ^ b for a, b in zip(token_bytes, key * (len(token_bytes) // len(key) + 1)))
        return base64.b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_token(encrypted_token):
        """Decrypt token"""
        if not encrypted_token:
            return ""
        
        try:
            key = settings.SECRET_KEY.encode()
            encrypted_bytes = base64.b64decode(encrypted_token.encode())
            
            # Decrypt using XOR
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key * (len(encrypted_bytes) // len(key) + 1)))
            return decrypted.decode()
        except Exception:
            return ""
    
    @staticmethod
    def store_tokens(user, platform, access_token, refresh_token=None, expires_in=None, scope=None, user_data=None):
        """Store OAuth tokens for a user"""
        
        # Calculate expiration time
        expires_at = None
        if expires_in:
            expires_at = timezone.now() + timedelta(seconds=int(expires_in))
        
        # Ensure we have user_data and platform_user_id
        if not user_data or not user_data.get('id'):
            raise ValueError(f"Missing user_data or platform user ID for {platform}")
        
        platform_user_id = str(user_data.get('id'))
        
        # Get or create social media account - use more specific matching
        try:
            # First try to get existing account for this specific user and platform
            social_account = SocialMediaAccount.objects.get(
                user=user,
                platform=platform,
                platform_user_id=platform_user_id
            )
            # Update existing account
            social_account.username = user_data.get('username', social_account.username)
            social_account.display_name = user_data.get('name', social_account.display_name)
            social_account.email = user_data.get('email', social_account.email)
            social_account.profile_url = user_data.get('profile_url', social_account.profile_url)
            social_account.avatar_url = user_data.get('avatar_url', social_account.avatar_url)
            social_account.access_token = TokenManager.encrypt_token(access_token)
            social_account.refresh_token = TokenManager.encrypt_token(refresh_token) if refresh_token else ''
            social_account.token_expires_at = expires_at
            social_account.scope = scope or ''
            social_account.status = 'active'
            social_account.last_sync = timezone.now()
            social_account.extra_data.update(user_data)
            social_account.save()
            
        except SocialMediaAccount.DoesNotExist:
            # Create new account
            social_account = SocialMediaAccount.objects.create(
                user=user,
                platform=platform,
                platform_user_id=platform_user_id,
                username=user_data.get('username', ''),
                display_name=user_data.get('name', ''),
                email=user_data.get('email', ''),
                profile_url=user_data.get('profile_url', ''),
                avatar_url=user_data.get('avatar_url', ''),
                access_token=TokenManager.encrypt_token(access_token),
                refresh_token=TokenManager.encrypt_token(refresh_token) if refresh_token else '',
                token_expires_at=expires_at,
                scope=scope or '',
                status='active',
                extra_data=user_data
            )
        
        return social_account
    
    @staticmethod
    def disconnect_account(user, platform):
        """Disconnect a social media account for a user"""
        try:
            social_account = SocialMediaAccount.objects.get(
                user=user,
                platform=platform
            )
            
            print(f"🔥 Disconnecting {platform} account for user {user.username}")
            
            # Revoke tokens on the platform side before local cleanup
            TokenManager._revoke_platform_token(social_account, platform)
            
            # Delete related data first (cascading will handle some, but we'll be explicit)
            from accounts.models import APICallLog, UserAnalytics, SessionData
            
            # Clean up API call logs
            api_logs_deleted = APICallLog.objects.filter(social_account=social_account).count()
            APICallLog.objects.filter(social_account=social_account).delete()
            print(f"🗑️ Deleted {api_logs_deleted} API call logs")
            
            # Clean up analytics data
            analytics_deleted = UserAnalytics.objects.filter(social_account=social_account).count()
            UserAnalytics.objects.filter(social_account=social_account).delete()
            print(f"📊 Deleted {analytics_deleted} analytics records")
            
            # Clean up session data
            session_data_deleted = SessionData.objects.filter(social_account=social_account).count()
            SessionData.objects.filter(social_account=social_account).delete()
            print(f"🔑 Deleted {session_data_deleted} session records")
            
            # Clean up platform-specific sessions
            SessionManager.cleanup_user_platform_sessions(user, platform)
            
            # Delete platform-specific profile data
            if platform == 'linkedin':
                try:
                    from linkedIn.models import LinkedInProfile
                    linkedin_profiles_deleted = LinkedInProfile.objects.filter(social_account=social_account).count()
                    LinkedInProfile.objects.filter(social_account=social_account).delete()
                    print(f"💼 Deleted {linkedin_profiles_deleted} LinkedIn profiles")
                except ImportError:
                    print("⚠️ LinkedIn models not available")
            elif platform == 'twitter':
                try:
                    from twitter.models import TwitterProfile, Tweet, TwitterFollower, TwitterHashtag
                    twitter_profiles_deleted = TwitterProfile.objects.filter(social_account=social_account).count()
                    tweets_deleted = Tweet.objects.filter(social_account=social_account).count()
                    followers_deleted = TwitterFollower.objects.filter(social_account=social_account).count()
                    hashtags_deleted = TwitterHashtag.objects.filter(social_account=social_account).count()
                    
                    TwitterProfile.objects.filter(social_account=social_account).delete()
                    Tweet.objects.filter(social_account=social_account).delete()
                    TwitterFollower.objects.filter(social_account=social_account).delete()
                    TwitterHashtag.objects.filter(social_account=social_account).delete()
                    
                    print(f"🐦 Deleted {twitter_profiles_deleted} profiles, {tweets_deleted} tweets, {followers_deleted} followers, {hashtags_deleted} hashtags")
                except ImportError:
                    print("⚠️ Twitter models not available")
            
            # Finally, delete the social media account
            account_id = social_account.id
            social_account.delete()
            print(f"✅ Successfully deleted social media account {account_id}")
            
            return True
        except SocialMediaAccount.DoesNotExist:
            print(f"❌ No {platform} account found for user {user.username}")
            return False
        except Exception as e:
            print(f"💥 Error disconnecting {platform} account: {str(e)}")
            return False
    
    @staticmethod
    def _revoke_platform_token(social_account, platform):
        """Revoke access token on the platform side"""
        try:
            access_token = TokenManager.decrypt_token(social_account.access_token)
            if not access_token:
                print(f"⚠️ No access token to revoke for {platform}")
                return
            
            if platform == 'linkedin':
                # LinkedIn token revocation
                revoke_url = "https://www.linkedin.com/oauth/v2/revoke"
                data = {
                    'token': access_token,
                    'client_id': settings.LINKEDIN_CLIENT_ID,
                    'client_secret': settings.LINKEDIN_CLIENT_SECRET
                }
                response = requests.post(revoke_url, data=data)
                if response.status_code == 200:
                    print(f"✅ Successfully revoked LinkedIn token")
                else:
                    print(f"⚠️ Failed to revoke LinkedIn token: {response.status_code}")
                    
            elif platform == 'twitter':
                # Twitter token revocation
                revoke_url = "https://api.twitter.com/2/oauth2/revoke"
                data = {
                    'token': access_token,
                    'client_id': settings.TWITTER_CLIENT_ID
                }
                # Create Basic Auth header
                credentials = f"{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers = {
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                response = requests.post(revoke_url, data=data, headers=headers)
                if response.status_code == 200:
                    print(f"✅ Successfully revoked Twitter token")
                else:
                    print(f"⚠️ Failed to revoke Twitter token: {response.status_code}")
                    
        except Exception as e:
            print(f"💥 Error revoking {platform} token: {str(e)}")
    
    @staticmethod
    def get_user_social_account(user, platform):
        """Get active social media account for user and platform"""
        try:
            return SocialMediaAccount.objects.get(
                user=user,
                platform=platform,
                status='active'
            )
        except SocialMediaAccount.DoesNotExist:
            return None
    
    @staticmethod
    def get_valid_token(social_account):
        """Get a valid access token, refreshing if necessary"""
        
        # Check if token is expired
        if social_account.is_token_expired():
            # Try to refresh token
            if social_account.refresh_token:
                new_tokens = TokenManager.refresh_access_token(social_account)
                if new_tokens:
                    return TokenManager.decrypt_token(social_account.access_token)
            
            # Mark as expired if refresh failed
            social_account.status = 'expired'
            social_account.save()
            return None
        
        return TokenManager.decrypt_token(social_account.access_token)
    
    @staticmethod
    def refresh_access_token(social_account):
        """Refresh access token using refresh token"""
        # This is platform-specific and should be implemented for each platform
        # For now, return None - implement in platform-specific handlers
        return None


class APIClient:
    """Generic API client for social media platforms"""
    
    def __init__(self, social_account):
        self.social_account = social_account
        self.base_url = self._get_base_url()
    
    def _get_base_url(self):
        """Get base URL for the platform's API"""
        urls = {
            'linkedin': 'https://api.linkedin.com/v2',
            'twitter': 'https://api.twitter.com/2',
            'facebook': 'https://graph.facebook.com/v18.0',
        }
        return urls.get(self.social_account.platform, '')
    
    def make_request(self, endpoint, method='GET', params=None, data=None, headers=None):
        """Make authenticated API request"""
        
        # Get valid access token
        access_token = TokenManager.get_valid_token(self.social_account)
        if not access_token:
            return None
        
        # Prepare headers
        if headers is None:
            headers = {}
        
        # Add authorization header (platform-specific)
        if self.social_account.platform == 'linkedin':
            headers['Authorization'] = f'Bearer {access_token}'
        elif self.social_account.platform == 'twitter':
            headers['Authorization'] = f'Bearer {access_token}'
        elif self.social_account.platform == 'facebook':
            if params is None:
                params = {}
            params['access_token'] = access_token
        
        # Make request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, params=params, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            # Log API call
            self._log_api_call(endpoint, method, response.status_code, response_time, response.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self._log_api_call(endpoint, method, response.status_code, response_time, 
                                 response.headers, error_message=response.text)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self._log_api_call(endpoint, method, 0, response_time, {}, error_message=str(e))
            return None
    
    def _log_api_call(self, endpoint, method, status_code, response_time, headers, error_message=''):
        """Log API call for monitoring"""
        
        # Extract rate limit info from headers
        rate_limit_remaining = None
        rate_limit_reset = None
        
        if self.social_account.platform == 'linkedin':
            rate_limit_remaining = headers.get('X-Restli-Protocol-Version')
        elif self.social_account.platform == 'twitter':
            rate_limit_remaining = headers.get('x-rate-limit-remaining')
            reset_timestamp = headers.get('x-rate-limit-reset')
            if reset_timestamp:
                rate_limit_reset = datetime.fromtimestamp(int(reset_timestamp))
        
        APICallLog.objects.create(
            user=self.social_account.user,
            social_account=self.social_account,
            endpoint=endpoint,
            method=method.upper(),
            status_code=status_code,
            response_time=response_time,
            rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
            rate_limit_reset=rate_limit_reset,
            error_message=error_message
        )


class SessionManager:
    """Manage OAuth sessions and temporary data"""
    
    @staticmethod
    def create_oauth_session(user, platform, redirect_uri, state=None, code_verifier=None):
        """Create OAuth session data"""
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        expires_at = timezone.now() + timedelta(minutes=30)  # 30 minute expiration
        
        session_data = SessionData.objects.create(
            user=user,
            oauth_state=state,
            code_verifier=code_verifier or '',
            redirect_uri=redirect_uri,
            temp_data={'platform': platform},
            expires_at=expires_at
        )
        
        return session_data
    
    @staticmethod
    def get_oauth_session(state):
        """Get OAuth session by state"""
        try:
            session = SessionData.objects.get(oauth_state=state)
            if session.is_expired():
                session.delete()
                return None
            return session
        except SessionData.DoesNotExist:
            return None
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired session data"""
        SessionData.objects.filter(expires_at__lt=timezone.now()).delete()
    
    @staticmethod
    def cleanup_user_platform_sessions(user, platform):
        """Clean up sessions for a specific user and platform"""
        SessionData.objects.filter(
            user=user,
            temp_data__platform=platform
        ).delete()


class AnalyticsCollector:
    """Collect and store analytics data"""
    
    @staticmethod
    def update_profile_metrics(social_account, metrics_data):
        """Update profile metrics"""
        if social_account.platform == 'linkedin':
            social_account.follower_count = metrics_data.get('connection_count', 0)
        elif social_account.platform == 'twitter':
            social_account.follower_count = metrics_data.get('followers_count', 0)
            social_account.following_count = metrics_data.get('following_count', 0)
            social_account.posts_count = metrics_data.get('tweet_count', 0)
        
        social_account.last_sync = timezone.now()
        social_account.save()
    
    @staticmethod
    def collect_daily_analytics(social_account, date=None):
        """Collect daily analytics for a social account"""
        if date is None:
            date = timezone.now().date()
        
        # This would be implemented with platform-specific logic
        # For now, create placeholder analytics
        from accounts.models import UserAnalytics
        
        analytics, created = UserAnalytics.objects.get_or_create(
            user=social_account.user,
            social_account=social_account,
            date=date,
            defaults={
                'likes_received': 0,
                'comments_received': 0,
                'shares_received': 0,
                'profile_views': 0,
                'posts_published': 0,
            }
        )
        
        return analytics
