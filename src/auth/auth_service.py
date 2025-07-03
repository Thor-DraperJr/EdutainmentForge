"""
Authentication service for Azure AD B2C integration.
"""

import msal
from flask import session, request, url_for
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Azure AD B2C authentication service using MSAL."""
    
    def __init__(self, config):
        """
        Initialize the authentication service.
        
        Args:
            config: AuthConfig instance with Azure AD B2C settings
        """
        self.config = config
        self._msal_app = None
        
    def _get_msal_app(self):
        """Get or create MSAL application instance."""
        if self._msal_app is None:
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=self.config.client_secret,
                authority=self.config.authority
            )
        return self._msal_app
    
    def get_auth_url(self, base_url: str = None) -> str:
        """
        Generate authentication URL for Azure AD login.
        
        Args:
            base_url: Base URL of the application (optional)
            
        Returns:
            Authentication URL to redirect user to
        """
        redirect_uri = self.config.get_redirect_uri(base_url)
        
        auth_result = self._get_msal_app().initiate_auth_code_flow(
            scopes=self.config.scopes,
            redirect_uri=redirect_uri
        )
        
        # Store the auth flow state in session
        session['auth_flow'] = auth_result
        
        return auth_result['auth_uri']
    
    def handle_callback(self, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Handle the authentication callback from Azure AD B2C.
        
        Args:
            base_url: Base URL of the application
            
        Returns:
            User information if authentication successful, None otherwise
        """
        try:
            # Get the auth flow from session
            auth_flow = session.get('auth_flow', {})
            
            if not auth_flow:
                logger.error("No auth flow found in session")
                return None
            
            # Complete the authentication flow
            redirect_uri = self.config.get_redirect_uri(base_url)
            
            result = self._get_msal_app().acquire_token_by_auth_code_flow(
                auth_code_flow=auth_flow,
                auth_response=request.args
            )
            
            if 'error' in result:
                logger.error(f"Authentication error: {result.get('error_description', result['error'])}")
                return None
            
            # Extract user information from the ID token
            user_info = {
                'user_id': result.get('id_token_claims', {}).get('sub'),
                'email': result.get('id_token_claims', {}).get('email', ''),
                'name': result.get('id_token_claims', {}).get('name', ''),
                'given_name': result.get('id_token_claims', {}).get('given_name', ''),
                'family_name': result.get('id_token_claims', {}).get('family_name', ''),
                'access_token': result.get('access_token'),
                'id_token': result.get('id_token')
            }
            
            # Store user session
            session['user'] = user_info
            session.permanent = True
            
            # Clear auth flow from session
            session.pop('auth_flow', None)
            
            logger.info(f"User authenticated successfully: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error handling authentication callback: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if the current user is authenticated.
        
        Returns:
            True if user is authenticated, False otherwise
        """
        return 'user' in session and session['user'].get('user_id') is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticated user's information.
        
        Returns:
            User information if authenticated, None otherwise
        """
        if self.is_authenticated():
            return session['user']
        return None
    
    def logout(self) -> str:
        """
        Log out the current user and return logout URL.
        
        Returns:
            Logout URL for Azure AD B2C
        """
        # Clear session
        session.clear()
        
        # Construct logout URL
        # Azure AD B2C logout URL format
        logout_url = (
            f"https://{self.config.tenant_id}.b2clogin.com/"
            f"{self.config.tenant_id}.onmicrosoft.com/"
            f"{self.config.policy_name}/oauth2/v2.0/logout"
        )
        
        return logout_url
    
    def revoke_user_access(self, user_id: str) -> bool:
        """
        Admin function to revoke a user's access.
        
        Note: This is a placeholder for admin functionality.
        In a full implementation, this would maintain a blacklist
        or integrate with Azure AD B2C user management APIs.
        
        Args:
            user_id: User ID to revoke access for
            
        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement user access revocation
        # This could involve:
        # 1. Maintaining a local blacklist of revoked users
        # 2. Using Azure AD B2C Graph API to disable users
        # 3. Custom claims or group membership checks
        
        logger.warning(f"User access revocation not implemented for user: {user_id}")
        return False
    
    def get_user_count(self) -> int:
        """
        Admin function to get total registered user count.
        
        Note: This is a placeholder for admin functionality.
        In a full implementation, this would query Azure AD B2C.
        
        Returns:
            Number of registered users
        """
        # TODO: Implement user count retrieval
        # This could involve Azure AD B2C Graph API calls
        
        logger.warning("User count retrieval not implemented")
        return 0
