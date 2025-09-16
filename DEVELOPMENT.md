# Development vs Production Configuration

## 🔧 Local Development Setup

For local testing of the feedback system:

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Enable development mode** (add to `.env`):
   ```
   DISABLE_AUTH_FOR_TESTING=true
   DEV_MODE=true
   FLASK_ENV=development
   ```

3. **Create sample podcasts** (optional):
   ```bash
   python -c "
   import wave, struct, math, os
   os.makedirs('output', exist_ok=True)
   # Create sample files for testing
   "
   ```

## 🚀 Production Deployment

For production deployment:

1. **Use production template:**
   ```bash
   cp .env.production.template .env
   ```

2. **Fill in real Azure credentials** in `.env`:
   - Azure OpenAI API keys
   - Azure Speech Service keys
   - Azure AD B2C configuration
   - Strong Flask secret key

3. **Ensure production environment:**
   ```
   FLASK_ENV=production
   # DO NOT SET: DISABLE_AUTH_FOR_TESTING=true
   # DO NOT SET: DEV_MODE=true
   ```

## 🛡️ Production Safety Features

The application includes several safeguards:

1. **Development Mode Detection**: Only activates with explicit environment variables
2. **Authentication Bypass Protection**: Blocks auth bypass in production environment
3. **File Filtering**: Excludes development test files from production API
4. **Startup Warnings**: Logs clear warnings when development features are active
5. **Environment Validation**: Fails to start if unsafe configuration detected

## ⚠️ Critical Production Rules

**NEVER set these in production:**
- `DISABLE_AUTH_FOR_TESTING=true`
- `DEV_MODE=true`
- Dummy credentials like `dummy-key-for-local-testing`

**Always set in production:**
- `FLASK_ENV=production`
- Real Azure service credentials
- Secure Flask secret key
- Proper Azure AD B2C configuration

## 🧪 Testing the Feedback System

In development mode, the application:
- Creates sample Azure-themed podcasts
- Enables authentication bypass
- Shows development mode notice
- Allows testing of thumbs up/down features

In production, the application:
- Uses real Azure services
- Requires proper authentication
- Filters out development files
- Logs security warnings for unsafe configurations