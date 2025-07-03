"""
Authentication module for EdutainmentForge.

Provides Azure AD B2C integration with support for both Microsoft organizational
and personal accounts.
"""

from .auth_service import AuthService
from .decorators import require_auth
from .config import AuthConfig

__all__ = ['AuthService', 'require_auth', 'AuthConfig']
