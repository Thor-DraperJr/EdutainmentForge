"""
Authentication decorators for protecting routes.
"""

from functools import wraps
from flask import session, redirect, url_for, request, current_app
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    If the user is not authenticated, redirects to login page.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that checks authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user' not in session or not session['user'].get('user_id'):
            logger.info(f"Unauthenticated access attempt to {request.endpoint}")
            
            # Store the intended destination
            session['next_url'] = request.url
            
            # Redirect to login
            return redirect(url_for('auth_login'))
        
        # Check if user is revoked (placeholder for future implementation)
        user_id = session['user'].get('user_id')
        if _is_user_revoked(user_id):
            logger.warning(f"Revoked user attempted access: {user_id}")
            session.clear()
            return redirect(url_for('auth_login', error='access_revoked'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges for a route.
    
    This is a placeholder for future admin functionality.
    Currently, all authenticated users are treated as admins.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that checks admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is authenticated
        if 'user' not in session or not session['user'].get('user_id'):
            logger.info(f"Unauthenticated admin access attempt to {request.endpoint}")
            session['next_url'] = request.url
            return redirect(url_for('auth_login'))
        
        # TODO: Implement proper admin role checking
        # For now, all authenticated users have admin access
        # In production, this could check:
        # 1. Azure AD B2C group membership
        # 2. Custom claims in the token
        # 3. Local admin user list
        
        user_email = session['user'].get('email', '')
        logger.info(f"Admin access granted to: {user_email}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def _is_user_revoked(user_id: str) -> bool:
    """
    Check if a user's access has been revoked.
    
    This is a placeholder for future implementation.
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if user is revoked, False otherwise
    """
    # TODO: Implement user revocation checking
    # This could involve:
    # 1. Checking a local blacklist
    # 2. Querying Azure AD B2C user status
    # 3. Checking custom claims or group membership
    
    return False
