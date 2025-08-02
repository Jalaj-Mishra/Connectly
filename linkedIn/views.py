import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import never_cache
from accounts.utils import TokenManager, SessionManager, APIClient
from accounts.models import SocialMediaAccount, SessionData
from .models import LinkedInProfile
import secrets


@login_required
def linkedin_profile(request):
    """Display LinkedIn profile page with account status"""
    
    # Use the utility function to get user's social account
    social_account = TokenManager.get_user_social_account(request.user, 'linkedin')
    
    if not social_account:
        context = {
            'is_connected': False,
            'message': 'Click the link below to connect your LinkedIn account'
        }
        return render(request, 'linkedin/profile.html', context)
    
    linkedin_profile = getattr(social_account, 'linkedin_profile', None)
    
    if linkedin_profile and social_account.extra_data:
        # Format profile data to match template expectations
        extra_data = social_account.extra_data
        profile_data = {
            'sub': social_account.platform_user_id,
            'name': social_account.display_name,
            'given_name': extra_data.get('given_name', ''),
            'family_name': extra_data.get('family_name', ''),
            'email': social_account.email,
            'picture': social_account.avatar_url,
            'locale': extra_data.get('locale', 'Not available'),
            'profile': social_account.profile_url,
        }
        
        context = {
            'success': True,
            'profile': profile_data,
            'social_account': social_account,
            'linkedin_profile': linkedin_profile,
            'is_connected': True
        }
    elif social_account:
        # Account exists but missing profile data - create basic profile data
        profile_data = {
            'sub': social_account.platform_user_id,
            'name': social_account.display_name or 'Name not available',
            'given_name': 'Not available',
            'family_name': 'Not available',
            'email': social_account.email or 'Email not available',
            'picture': social_account.avatar_url,
            'locale': 'Not available',
            'profile': social_account.profile_url,
        }
        
        context = {
            'success': True,
            'profile': profile_data,
            'social_account': social_account,
            'linkedin_profile': linkedin_profile,
            'is_connected': True
        }
    else:
        context = {
            'is_connected': True,
            'message': 'LinkedIn account connected but profile data is being loaded...'
        }
    
    return render(request, 'linkedin/profile.html', context)


@login_required
@never_cache
def linkedin_login(request):
    """Initiate LinkedIn OAuth flow"""
    
    # Clean up any existing sessions for this user and platform
    SessionData.objects.filter(
        user=request.user,
        temp_data__platform='linkedin'
    ).delete()
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    timestamp = str(int(timezone.now().timestamp()))
    
    # Create session data
    SessionManager.create_oauth_session(
        user=request.user,
        platform='linkedin',
        redirect_uri=settings.LINKEDIN_REDIRECT_URI,
        state=state
    )
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={settings.LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={settings.LINKEDIN_REDIRECT_URI}"
        f"&scope=openid%20profile%20email"
        f"&state={state}"
        f"&prompt=consent"  # Force fresh consent screen
        f"&approval_prompt=force"  # Force approval
        f"&access_type=offline"  # Request offline access
        f"&_t={timestamp}"  # Cache busting parameter
    )
    
    # Create redirect response with cache-busting headers
    response = redirect(auth_url)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def linkedin_callback(request):
    """Handle LinkedIn OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    state = request.GET.get('state')
    
    if error:
        messages.error(request, f'LinkedIn authorization failed: {error}')
        return redirect('dashboard')
    
    if not code or not state:
        messages.error(request, 'Invalid LinkedIn callback')
        return redirect('dashboard')
    
    # Verify state parameter and ensure session belongs to current user
    session_data = SessionManager.get_oauth_session(state)
    if not session_data:
        messages.error(request, 'Invalid or expired session state')
        return redirect('dashboard')
    
    if session_data.user != request.user:
        messages.error(request, 'Session does not belong to current user')
        session_data.delete()  # Clean up invalid session
        return redirect('dashboard')
    
    try:
        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            messages.error(request, 'Failed to get access token from LinkedIn')
            return redirect('dashboard')
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        expires_in = token_info.get('expires_in')
        
        if not access_token:
            messages.error(request, 'No access token received from LinkedIn')
            return redirect('dashboard')
        
        # Get user profile information
        profile_response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if profile_response.status_code != 200:
            messages.error(request, 'Failed to get profile information from LinkedIn')
            return redirect('dashboard')
        
        profile_data = profile_response.json()
        
        # Store tokens and user data
        user_data = {
            'id': profile_data.get('sub'),
            'username': profile_data.get('email', '').split('@')[0],
            'name': profile_data.get('name', ''),
            'email': profile_data.get('email', ''),
            'profile_url': profile_data.get('profile', ''),
            'avatar_url': profile_data.get('picture', ''),
            'given_name': profile_data.get('given_name', ''),
            'family_name': profile_data.get('family_name', ''),
        }
        
        social_account = TokenManager.store_tokens(
            user=request.user,
            platform='linkedin',
            access_token=access_token,
            expires_in=expires_in,
            scope=token_info.get('scope', ''),
            user_data=user_data
        )
        
        # Create or update LinkedIn profile
        linkedin_profile, created = LinkedInProfile.objects.get_or_create(
            social_account=social_account,
            defaults={
                'headline': '',  # Will be updated with additional API calls
                'summary': '',
                'industry': '',
                'location': profile_data.get('locale', ''),
            }
        )
        
        # Clean up session data
        session_data.delete()
        
        messages.success(request, 'LinkedIn account connected successfully!')
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f'Error connecting LinkedIn account: {str(e)}')
        return redirect('dashboard')
    
    # Handle OAuth errors
    if error:
        return render(request, 'linkedIn/profile.html', {
            'error': f'LinkedIn OAuth error: {error}'
        })
    
    if not code:
        return render(request, 'linkedIn/profile.html', {
            'error': 'No authorization code received from LinkedIn'
        })

    token_url = 'https://www.linkedin.com/oauth/v2/accessToken'

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'client_secret': settings.LINKEDIN_CLIENT_SECRET
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return render(request, 'linkedIn/profile.html', {
                'error': 'Failed to obtain access token from LinkedIn'
            })

        # Get profile info using OpenID Connect userinfo endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        profile_url = 'https://api.linkedin.com/v2/userinfo'
        
        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # Extract email from the userinfo response
        email = profile_data.get('email', 'Email not available')

        return render(request, 'linkedIn/profile.html', {
            'profile': profile_data,
            'email': email
        })
        
    except requests.exceptions.RequestException as e:
        return render(request, 'linkedIn/profile.html', {
            'error': f'Network error occurred: {str(e)}'
        })
    except (KeyError, ValueError) as e:
        return render(request, 'linkedIn/profile.html', {
            'error': f'Error processing LinkedIn response: {str(e)}'
        })


@login_required
def linkedin_disconnect(request):
    """Disconnect LinkedIn account"""
    if request.method == 'POST':
        success = TokenManager.disconnect_account(request.user, 'linkedin')
        if success:
            messages.success(request, '✅ LinkedIn account disconnected successfully! All data has been removed.')
        else:
            messages.warning(request, '⚠️ No LinkedIn account found to disconnect.')
    else:
        messages.error(request, '❌ Invalid request method.')
    
    # Create response with cache-busting headers and disconnected parameter
    response = redirect('linkedin_profile')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    # Clear any LinkedIn-related cookies
    response.delete_cookie('linkedin_oauth_state')
    response.delete_cookie('linkedin_session')
    
    # Add query parameter to trigger JavaScript cache clearing
    from django.http import HttpResponseRedirect
    from urllib.parse import urlencode
    
    redirect_url = reverse('linkedin_profile')
    params = urlencode({'disconnected': 'true', '_': int(timezone.now().timestamp())})
    full_url = f"{redirect_url}?{params}"
    
    response = HttpResponseRedirect(full_url)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

