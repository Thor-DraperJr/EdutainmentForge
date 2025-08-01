"""
Authentication configuration for Azure AD integration.
"""

import os
from typing import Optional


class AuthConfig:
    """Configuration class for Azure AD authentication."""
    
    def __init__(self):
        """Initialize auth configuration from environment variables."""
        # Azure AD Configuration
        self.tenant_id = self._get_config_value(
            'AZURE_AD_TENANT_ID', 
            'azure-ad-tenant-id',
            'Azure AD tenant ID'
        )
        
        self.client_id = self._get_config_value(
            'AZURE_AD_CLIENT_ID',
            'azure-ad-client-id', 
            'Azure AD client ID'
        )
        
        self.client_secret = self._get_config_value(
            'AZURE_AD_CLIENT_SECRET',
            'azure-ad-client-secret',
            'Azure AD client secret'
        )
        
        # Flask session configuration
        self.flask_secret_key = self._get_config_value(
            'FLASK_SECRET_KEY',
            'flask-secret-key',
            'Flask session secret key'
        )
        
        # Use 'common' authority to support both personal and work Microsoft accounts
        # This allows both @outlook.com/@hotmail.com AND @microsoft.com/@company.com
        self.authority = "https://login.microsoftonline.com/common"
        
        # Request scopes - use User.Read for basic profile info
        # Don't use 'openid', 'profile' as they are reserved in MSAL
        self.scopes = ["User.Read"]
        
        # Redirect URIs (will be set based on environment)
        self.redirect_path = "/auth/callback"
        
        # Public URL for production (Azure Container Apps)
        self.public_url = os.getenv('PUBLIC_URL', 'https://edutainmentforge-app.happymeadow-088e7533.eastus.azurecontainerapps.io')
        
    def _get_config_value(self, env_var: str, keyvault_secret: str, description: str, default: Optional[str] = None) -> str:
        """
        Get configuration value from environment variables or Key Vault.
        
        Args:
            env_var: Environment variable name
            keyvault_secret: Key Vault secret name  
            description: Human-readable description for error messages
            default: Default value if not found
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required configuration is missing
        """
        value = os.getenv(env_var, default)
        
        if not value:
            # In production, this would attempt to get from Key Vault
            # For now, we'll raise an error with helpful message
            raise ValueError(
                f"Missing {description}. "
                f"Set environment variable {env_var} or ensure Key Vault secret '{keyvault_secret}' exists."
            )
            
        return value
    
    def get_redirect_uri(self, base_url: str = None) -> str:
        """
        Get the full redirect URI for the current environment.
        
        Args:
            base_url: Base URL of the application (optional, will use public_url if not provided)
            
        Returns:
            Full redirect URI
        """
        # Use public URL if available and in production, otherwise use provided base_url
        if self.public_url and (not base_url or 'localhost' not in base_url):
            effective_url = self.public_url
        else:
            effective_url = base_url or 'http://localhost:5000'
            
        return f"{effective_url.rstrip('/')}{self.redirect_path}"
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        required_fields = [
            ('tenant_id', 'Azure AD B2C tenant ID'),
            ('client_id', 'Azure AD B2C client ID'),
            ('client_secret', 'Azure AD B2C client secret'),
            ('flask_secret_key', 'Flask session secret key')
        ]
        
        for field_name, description in required_fields:
            if not getattr(self, field_name, None):
                raise ValueError(f"Missing required configuration: {description}")
                
        return True
