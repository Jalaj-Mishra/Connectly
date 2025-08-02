import requests
import base64
import hashlib
import secrets
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from urllib.parse import urlencode
from accounts.utils import TokenManager, SessionManager, APIClient
from accounts.models import SocialMediaAccount, SessionData
from .models import TwitterProfile


@login_required
def twitter_profile(request):
    """Display Twitter profile page with account status"""
    
    # Use the utility function to get user's social account
    social_account = TokenManager.get_user_social_account(request.user, 'twitter')
    
    if not social_account:
        context = {
            'is_connected': False,
            'message': 'Click the link below to connect your Twitter account'
        }
        return render(request, 'twitter/profile.html', context)
    
    twitter_profile = getattr(social_account, 'twitter_profile', None)
    
    if twitter_profile:
        # Format profile data to match template expectations
        profile_data = {
            'id': social_account.platform_user_id,
            'name': social_account.display_name,
            'username': social_account.username,
            'description': twitter_profile.description,
            'profile_image_url': twitter_profile.profile_image_url,
            'public_metrics': {
                'followers_count': twitter_profile.followers_count,
                'following_count': twitter_profile.following_count,
                'tweet_count': twitter_profile.tweet_count,
                'listed_count': 0,  # Not stored in our model yet
            }
        }
        
        context = {
            'success': True,
            'profile': profile_data,
            'social_account': social_account,
            'twitter_profile': twitter_profile,
            'is_connected': True
        }
    else:
        context = {
            'is_connected': True,
            'message': 'Twitter account connected but profile data is being loaded...'
        }
    
    return render(request, 'twitter/profile.html', context)


@login_required
@never_cache
def twitter_login(request):
    """Initiate Twitter OAuth flow with PKCE"""
    
    # Clean up any existing sessions for this user and platform
    SessionData.objects.filter(
        user=request.user,
        temp_data__platform='twitter'
    ).delete()
    
    # Generate PKCE parameters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    state = secrets.token_urlsafe(32)
    timestamp = str(int(timezone.now().timestamp()))
    
    # Create session data with PKCE parameters
    SessionManager.create_oauth_session(
        user=request.user,
        platform='twitter',
        redirect_uri=settings.TWITTER_REDIRECT_URI,
        state=state,
        code_verifier=code_verifier
    )
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': settings.TWITTER_CLIENT_ID,
        'redirect_uri': settings.TWITTER_REDIRECT_URI,
        'scope': 'tweet.read users.read follows.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'force_login': 'true',  # Force fresh login/consent
        '_t': timestamp,  # Cache busting parameter
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(auth_params)}"
    
    # Create redirect response with cache-busting headers
    response = redirect(auth_url)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def twitter_callback(request):
    """Handle Twitter OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    state = request.GET.get('state')
    
    if error:
        messages.error(request, f'Twitter authorization failed: {error}')
        return redirect('dashboard')
    
    if not code or not state:
        messages.error(request, 'Invalid Twitter callback')
        return redirect('dashboard')
    
    # Verify state parameter and get session data
    session_data = SessionManager.get_oauth_session(state)
    if not session_data or session_data.user != request.user:
        messages.error(request, 'Invalid session state')
        return redirect('dashboard')
    
    try:
        # Exchange code for access token
        token_url = "https://api.twitter.com/2/oauth2/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.TWITTER_REDIRECT_URI,
            'client_id': settings.TWITTER_CLIENT_ID,
            'code_verifier': session_data.code_verifier,
        }
        
        # Create Basic Auth header
        credentials = f"{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        token_response = requests.post(token_url, data=token_data, headers=headers)
        
        if token_response.status_code != 200:
            messages.error(request, 'Failed to get access token from Twitter')
            return redirect('dashboard')
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in')
        
        if not access_token:
            messages.error(request, 'No access token received from Twitter')
            return redirect('dashboard')
        
        # Get user profile information
        profile_response = requests.get(
            'https://api.twitter.com/2/users/me?user.fields=description,location,profile_image_url,public_metrics,verified,created_at',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if profile_response.status_code != 200:
            messages.error(request, 'Failed to get profile information from Twitter')
            return redirect('dashboard')
        
        profile_data = profile_response.json().get('data', {})
        
        # Store tokens and user data
        user_data = {
            'id': profile_data.get('id'),
            'username': profile_data.get('username', ''),
            'name': profile_data.get('name', ''),
            'profile_url': f"https://twitter.com/{profile_data.get('username', '')}",
            'avatar_url': profile_data.get('profile_image_url', ''),
            'description': profile_data.get('description', ''),
            'location': profile_data.get('location', ''),
            'verified': profile_data.get('verified', False),
            'created_at': profile_data.get('created_at', ''),
            'public_metrics': profile_data.get('public_metrics', {}),
        }
        
        social_account = TokenManager.store_tokens(
            user=request.user,
            platform='twitter',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=token_info.get('scope', ''),
            user_data=user_data
        )
        
        # Create or update Twitter profile
        public_metrics = profile_data.get('public_metrics', {})
        twitter_profile, created = TwitterProfile.objects.get_or_create(
            social_account=social_account,
            defaults={
                'screen_name': profile_data.get('username', ''),
                'description': profile_data.get('description', ''),
                'location': profile_data.get('location', ''),
                'followers_count': public_metrics.get('followers_count', 0),
                'following_count': public_metrics.get('following_count', 0),
                'tweet_count': public_metrics.get('tweet_count', 0),
                'like_count': public_metrics.get('like_count', 0),
                'is_verified': profile_data.get('verified', False),
                'profile_image_url': profile_data.get('profile_image_url', ''),
            }
        )
        
        if not created:
            # Update existing profile
            twitter_profile.screen_name = profile_data.get('username', '')
            twitter_profile.description = profile_data.get('description', '')
            twitter_profile.location = profile_data.get('location', '')
            twitter_profile.followers_count = public_metrics.get('followers_count', 0)
            twitter_profile.following_count = public_metrics.get('following_count', 0)
            twitter_profile.tweet_count = public_metrics.get('tweet_count', 0)
            twitter_profile.like_count = public_metrics.get('like_count', 0)
            twitter_profile.is_verified = profile_data.get('verified', False)
            twitter_profile.profile_image_url = profile_data.get('profile_image_url', '')
            twitter_profile.save()
        
        # Clean up session data
        session_data.delete()
        
        messages.success(request, 'Twitter account connected successfully!')
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f'Error connecting Twitter account: {str(e)}')
        return redirect('dashboard')


@login_required
def twitter_disconnect(request):
    """Disconnect Twitter account"""
@login_required
def twitter_disconnect(request):
    """Disconnect Twitter account"""
    if request.method == 'POST':
        success = TokenManager.disconnect_account(request.user, 'twitter')
        if success:
            messages.success(request, '✅ Twitter account disconnected successfully! All data has been removed.')
        else:
            messages.warning(request, '⚠️ No Twitter account found to disconnect.')
    else:
        messages.error(request, '❌ Invalid request method.')
    
    # Create response with cache-busting headers and disconnected parameter
    response = redirect('twitter_profile')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    # Clear any Twitter-related cookies
    response.delete_cookie('twitter_oauth_state')
    response.delete_cookie('twitter_session')
    
    # Add query parameter to trigger JavaScript cache clearing
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    
    redirect_url = reverse('twitter_profile')
    params = urlencode({'disconnected': 'true', '_': str(int(timezone.now().timestamp()))})
    full_url = f"{redirect_url}?{params}"
    
    response = HttpResponseRedirect(full_url)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response
