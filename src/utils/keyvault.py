"""
Azure Key Vault integration for secure credential management.

Provides functions to retrieve secrets from Azure Key Vault using managed identity.
"""

import os
from typing import Optional, Dict
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from utils.logger import get_logger

logger = get_logger(__name__)


class KeyVaultError(Exception):
    """Custom exception for Key Vault operations."""
    pass


class AzureKeyVaultClient:
    """Client for interacting with Azure Key Vault."""
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize Key Vault client.
        
        Args:
            vault_url: Key Vault URL. If None, uses AZURE_KEY_VAULT_URL env var
        """
        self.vault_url = vault_url or os.getenv('AZURE_KEY_VAULT_URL')
        self.client = None
        
        if self.vault_url:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Key Vault client with appropriate credentials."""
        try:
            # Try managed identity first (for Azure-hosted environments)
            try:
                credential = ManagedIdentityCredential()
                self.client = SecretClient(vault_url=self.vault_url, credential=credential)
                # Test the connection
                self.client.get_secret_names()
                logger.info("Successfully initialized Key Vault client with managed identity")
                return
            except ClientAuthenticationError:
                logger.debug("Managed identity not available, trying default credential")
            
            # Fallback to default credential (local development)
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            # Test the connection
            self.client.get_secret_names()
            logger.info("Successfully initialized Key Vault client with default credential")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Key Vault client: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Retrieve a secret from Key Vault.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Secret value if found, None otherwise
        """
        if not self.client:
            logger.warning("Key Vault client not initialized")
            return None
        
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Successfully retrieved secret: {secret_name}")
            return secret.value
        except ResourceNotFoundError:
            logger.warning(f"Secret not found in Key Vault: {secret_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None
    
    def get_secrets(self, secret_names: list) -> Dict[str, Optional[str]]:
        """
        Retrieve multiple secrets from Key Vault.
        
        Args:
            secret_names: List of secret names to retrieve
            
        Returns:
            Dictionary mapping secret names to their values
        """
        secrets = {}
        for name in secret_names:
            secrets[name] = self.get_secret(name)
        return secrets
    
    def is_available(self) -> bool:
        """Check if Key Vault is available and accessible."""
        return self.client is not None


def get_secrets_from_keyvault(vault_url: str = None) -> Dict[str, Optional[str]]:
    """
    Retrieve all application secrets from Key Vault.
    
    Args:
        vault_url: Key Vault URL. If None, uses environment variable
        
    Returns:
        Dictionary of secret names to values
    """
    # Default vault URL for EdutainmentForge
    if not vault_url:
        vault_url = os.getenv('AZURE_KEY_VAULT_URL', 'https://edutainmentforge-kv.vault.azure.net/')
    
    client = AzureKeyVaultClient(vault_url)
    
    if not client.is_available():
        logger.warning("Key Vault not available, falling back to environment variables")
        return {}
    
    # List of secrets to retrieve
    secret_names = [
        'azure-speech-key',
        'azure-speech-region',
        'azure-openai-endpoint',
        'azure-openai-api-key',
        'azure-openai-api-version',
        'azure-openai-deployment-name'
    ]
    
    secrets = client.get_secrets(secret_names)
    logger.info(f"Retrieved {len([v for v in secrets.values() if v])} secrets from Key Vault")
    
    return secrets


def get_secret_with_fallback(secret_name: str, env_var_name: str = None, vault_url: str = None) -> Optional[str]:
    """
    Get a secret from Key Vault with environment variable fallback.
    
    Args:
        secret_name: Name of the secret in Key Vault
        env_var_name: Environment variable name for fallback. Defaults to secret_name.upper().replace('-', '_')
        vault_url: Key Vault URL
        
    Returns:
        Secret value from Key Vault or environment variable
    """
    if not env_var_name:
        env_var_name = secret_name.upper().replace('-', '_')
    
    # Try Key Vault first
    if vault_url or os.getenv('AZURE_KEY_VAULT_URL'):
        client = AzureKeyVaultClient(vault_url)
        if client.is_available():
            value = client.get_secret(secret_name)
            if value:
                logger.debug(f"Retrieved {secret_name} from Key Vault")
                return value
    
    # Fallback to environment variable
    value = os.getenv(env_var_name)
    if value:
        logger.debug(f"Retrieved {secret_name} from environment variable {env_var_name}")
        return value
    
    logger.warning(f"Secret {secret_name} not found in Key Vault or environment variable {env_var_name}")
    return None
