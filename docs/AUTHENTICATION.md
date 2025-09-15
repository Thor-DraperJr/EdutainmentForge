# Azure AD B2C Authentication for EdutainmentForge

This document explains how to set up and use Azure AD B2C authentication in EdutainmentForge.

## Overview

EdutainmentForge now requires user authentication before accessing the application. We use Azure AD B2C to provide:

- **Email-based registration** for all users
- **Support for both Microsoft organizational and personal accounts** (outlook.com, etc.)
- **Admin control** over user registration and access
- **Azure-native integration** with existing infrastructure

## Quick Setup

1. **Run the setup script:**
   ```bash
   ./scripts/setup-auth.sh
   ```

2. **Follow the interactive prompts** to:
   - Create Azure AD B2C tenant
   - Register the application
   - Create user flows
   - Store secrets in Key Vault

3. **Update your .env file** with Azure Speech and OpenAI keys

4. **Test locally:**
   ```bash
   python app.py
   ```

## Manual Setup (Alternative)

If you prefer to set up manually or need more control:

### 1. Create Azure AD B2C Tenant

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure AD B2C" and create a new tenant
3. Choose "Create a new Azure AD B2C Tenant"
4. Organization name: `EdutainmentForge`
5. Initial domain name: `edutainmentforge` (or similar)
6. Location: `United States`

### 2. Create App Registration

1. In your B2C tenant, go to "App registrations"
2. Click "New registration"
3. Name: `EdutainmentForge Web App`
4. Supported account types: "Accounts in any identity provider or organizational directory"
5. Redirect URI: `Web` - `http://localhost:5000/auth/callback`
6. After creation, add production redirect URI in Authentication:
   - `https://your-production-domain.com/auth/callback`

### 3. Create Client Secret

1. In your app registration, go to "Certificates & secrets"
2. Click "New client secret"
3. Description: `EdutainmentForge Production Secret`
4. Expires: `24 months`
5. Copy the secret VALUE (not the ID)

### 4. Create User Flow

1. In your B2C tenant, go to "User flows"
2. Click "New user flow"
3. Select "Sign up and sign in"
4. Version: `Recommended`
5. Name: `SignUpSignIn`
6. Identity providers: `Email signup`
7. User attributes and claims:
   - **Collect:** Email Address, Display Name, Given Name, Surname
   - **Return:** Email Addresses, Display Name, Given Name, Surname, User's Object ID

### 5. Configure Secrets

Store the following secrets in Azure Key Vault:

```bash
# Using Azure CLI
az keyvault secret set --vault-name edutainmentforge-kv --name "azure-ad-b2c-tenant-id" --value "your-tenant-name"
az keyvault secret set --vault-name edutainmentforge-kv --name "azure-ad-b2c-client-id" --value "your-client-id"
az keyvault secret set --vault-name edutainmentforge-kv --name "azure-ad-b2c-client-secret" --value "your-client-secret"
az keyvault secret set --vault-name edutainmentforge-kv --name "azure-ad-b2c-policy-name" --value "B2C_1_SignUpSignIn"
az keyvault secret set --vault-name edutainmentforge-kv --name "flask-secret-key" --value "$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

## Configuration

### Environment Variables

For local development, create a `.env` file:

```env
# Azure AD B2C Configuration
AZURE_AD_B2C_TENANT_ID=your-tenant-name
AZURE_AD_B2C_CLIENT_ID=your-client-id
AZURE_AD_B2C_CLIENT_SECRET=your-client-secret
AZURE_AD_B2C_POLICY_NAME=B2C_1_SignUpSignIn

# Flask Configuration
FLASK_SECRET_KEY=your-random-secret-key

# Other existing configuration...
AZURE_SPEECH_KEY=your-speech-key
AZURE_OPENAI_API_KEY=your-openai-key
```

### Production (Azure Container Apps)

In production, the application automatically loads secrets from Azure Key Vault using managed identity. No additional configuration needed.

## User Experience

### Login Flow

1. User visits the application
2. If not authenticated, redirected to `/auth/login`
3. Azure AD B2C login page appears with options:
   - Sign in with existing account
   - Sign up for new account
   - Use Microsoft personal account (outlook.com, hotmail.com)
   - Use Microsoft organizational account (company Azure AD)
4. After successful authentication, user is redirected back to the application

### Navigation

When authenticated, users see:
- **Profile** - View account information
- **Logout** - Sign out of the application

When not authenticated, users see:
- **Login** - Sign in or register

### User Profile

Users can view their profile information at `/auth/profile`:
- Name and email from Azure AD B2C
- Account type (personal vs organizational)
- Option to logout

## Admin Features

### User Management (Future)

Placeholder functions exist for admin features:

- `auth_service.revoke_user_access(user_id)` - Revoke a user's access
- `auth_service.get_user_count()` - Get total registered users

These can be implemented using:
1. **Local blacklist** - Maintain a list of revoked users
2. **Azure AD B2C Graph API** - Programmatically manage users
3. **Custom claims** - Add admin flags to user tokens

### Admin Routes

Use the `@admin_required` decorator for admin-only functionality:

```python
from auth import admin_required

@app.route('/admin/users')
@admin_required
def admin_users():
    # Admin-only functionality
    pass
```

Currently, all authenticated users have admin access. Implement proper role checking as needed.

## Security Features

### Session Management

- **Secure sessions** using Flask-Session
- **24-hour session lifetime** for security
- **Automatic logout** when session expires
- **CSRF protection** through session tokens

### Token Validation

- **ID token validation** ensures authentic Azure AD B2C tokens
- **Access token storage** for future API calls
- **Proper error handling** for authentication failures

### Secret Management

- **No hardcoded secrets** in application code
- **Azure Key Vault integration** for production secrets
- **Environment variable fallback** for local development
- **Managed identity** authentication in production

## Troubleshooting

### Common Issues

1. **"Missing Azure AD B2C configuration" error**
   - Ensure all environment variables are set
   - Check that secrets exist in Key Vault
   - Verify Key Vault permissions

2. **"Authentication failed" after callback**
   - Check redirect URI matches exactly
   - Verify client secret is correct
   - Ensure user flow is published

3. **"Access denied" in Azure portal**
   - Ensure you're in the correct B2C tenant
   - Check that you have proper permissions
   - Try signing out and back in to Azure portal

### Debug Mode

Enable debug logging by setting:

```env
FLASK_DEBUG=true
```

This will show detailed authentication flow information in the console.

### Testing Authentication

1. **Local testing:**
   ```bash
   python app.py
   # Visit http://localhost:5000/auth/login
   ```

2. **Check configuration:**
   ```bash
   # Verify secrets in Key Vault
   az keyvault secret list --vault-name edutainmentforge-kv --query "[?contains(name, 'azure-ad-b2c')].name" -o table
   ```

3. **Test user flow:**
   Visit the user flow URL directly:
   ```
   https://your-tenant.b2clogin.com/your-tenant.onmicrosoft.com/B2C_1_SignUpSignIn/oauth2/v2.0/authorize?client_id=your-client-id&response_type=code&redirect_uri=http://localhost:5000/auth/callback&scope=openid
   ```

## Deployment

### Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Set up `.env` file with authentication configuration
3. Run: `python app.py`
4. Test authentication at `http://localhost:5000/auth/login`

### Azure Container Apps

Deployments are handled by the GitHub Actions workflow on pushes to `main`.

If you need a manual redeploy (rare):
```bash
docker build -t edutainmentforge:latest .
az acr login --name edutainmentforge
docker tag edutainmentforge:latest edutainmentforge.azurecr.io/edutainmentforge:latest
docker push edutainmentforge.azurecr.io/edutainmentforge:latest
az containerapp update \
   --name edutainmentforge-app \
   --resource-group edutainmentforge-rg \
   --image edutainmentforge.azurecr.io/edutainmentforge:latest
```

### Continuous Integration

The authentication system is fully compatible with CI/CD pipelines:
- No secrets in code repository
- Environment-specific configuration
- Graceful fallback when authentication is not configured

## Next Steps

1. **Test with multiple account types** (personal and organizational)
2. **Implement admin user management** features
3. **Add audit logging** for authentication events
4. **Configure custom branding** in Azure AD B2C
5. **Set up monitoring** and alerts for authentication failures

For more information, see:
- [Azure AD B2C Documentation](https://docs.microsoft.com/en-us/azure/active-directory-b2c/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Flask-Session Documentation](https://flask-session.readthedocs.io/)
