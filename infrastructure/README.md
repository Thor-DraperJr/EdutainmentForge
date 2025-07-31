# EdutainmentForge Infrastructure

This folder contains the Azure infrastructure templates and deployment scripts for EdutainmentForge.

## Files

### 🚀 **Main Infrastructure**
- `azure-infrastructure.bicep` - Main Bicep template using RBAC and system-assigned managed identity
- `azure-container-app.yaml` - Container App configuration (for reference/manual deployment)
- `azure.yaml` - Azure Developer CLI configuration
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions and troubleshooting
- `setup-secrets.sh` - Interactive script to set up Key Vault secrets

### 📁 **Archive**
- `archive/azure-infrastructure-legacy.bicep` - Legacy template (not recommended)

## Quick Start

1. **Deploy Infrastructure**:
   ```bash
   az deployment group create --resource-group edutainmentforge-rg --template-file azure-infrastructure.bicep
   ```

2. **Set Up Secrets**:
   ```bash
   ./setup-secrets.sh
   ```

3. **Deploy Application**:
   ```bash
   # Build and push container
   ../scripts/build-container.sh
   ```

## Security Architecture

### ✅ **Modern RBAC Approach (Current)**
- RBAC-enabled Key Vault (`enableRbacAuthorization: true`)
- System-assigned managed identity
- Network-restricted Key Vault
- Minimal permissions (Key Vault Secrets User role)

### ❌ **Legacy Access Policies (Archived)**
- Traditional access policies
- User-assigned managed identity
- Less granular permissions

## Required Permissions

To deploy and manage this infrastructure, you need:

| Role | Scope | Purpose |
|------|-------|---------|
| `Contributor` or `Owner` | Resource Group | Deploy Azure resources |
| `Key Vault Secrets Officer` | Key Vault | Manage secrets |

## Monitoring & Troubleshooting

- **Application Logs**: Azure Container Apps logs
- **Key Vault Access**: Azure Activity Log
- **Performance**: Azure Monitor metrics
- **Security**: Azure Security Center recommendations

For detailed troubleshooting, see `DEPLOYMENT_GUIDE.md`.

## Architecture Decision Records

### Why RBAC over Access Policies?
- **Modern Security**: RBAC is the current Azure best practice
- **Granular Permissions**: More precise control than access policies
- **Audit Trail**: Better logging and monitoring capabilities
- **Future-Proof**: Microsoft's recommended approach going forward

### Why System-Assigned over User-Assigned Identity?
- **Simpler Management**: Automatically tied to container app lifecycle
- **Reduced Complexity**: No separate identity resource to manage
- **Security**: Cannot be accidentally deleted or misconfigured
- **Matches Current Setup**: Aligns with existing working deployment

## Cost Optimization

- Container Apps scale to zero when not in use
- Standard tier Key Vault and Storage for cost efficiency
- Log Analytics with 30-day retention
- Basic Container Registry tier

Estimated monthly cost: $20-50 USD for light usage.
