# Azure Container Apps Management for EdutainmentForge

This document describes how to manage the EdutainmentForge Azure Container Apps deployment for cost optimization and automatic maintenance.

## Overview

The EdutainmentForge application runs on Azure Container Apps, which provides automatic scaling and cost-effective hosting. This guide covers:

- **Auto-scaling**: Automatically scale based on usage patterns
- **Cost optimization**: Reduce costs during low-usage periods
- **Podcast cleanup**: Automatically remove old podcasts to manage storage
- **Monitoring**: Track usage and costs

## Container Management Script

The `scripts/manage-container.sh` script provides easy management of the container app:

### Basic Commands

```bash
# Start the application
./scripts/manage-container.sh start

# Stop the application (scale to 0 replicas)
./scripts/manage-container.sh stop

# Restart the application
./scripts/manage-container.sh restart

# Check status
./scripts/manage-container.sh status

# Scale manually
./scripts/manage-container.sh scale 1 3  # Min 1, Max 3 replicas
```

### Auto-scaling Commands

```bash
# Auto-scale based on time of day
./scripts/manage-container.sh auto-scale

# Set up scheduled operations
./scripts/manage-container.sh schedule
```

## Automatic Scaling Strategy

### Business Hours Scaling (Recommended for Hackathon)

The application automatically scales based on usage patterns:

- **Business Hours** (8 AM - 6 PM): Scale 1-5 replicas
- **Off Hours** (6 PM - 8 AM): Scale 0-2 replicas  
- **Weekends** (Optional): Complete shutdown to save costs

### Cost Optimization

- **Scale to Zero**: During off-hours, scale to 0 replicas (no compute costs)
- **Quick Startup**: Container Apps start in seconds when traffic arrives
- **Pay-per-use**: Only pay for active compute time

## Podcast Cleanup

### Automatic Cleanup Script

The `scripts/cleanup_podcasts.py` script manages storage by removing old podcasts:

```bash
# Clean up podcasts older than 7 days
python scripts/cleanup_podcasts.py

# Keep only the latest 50 podcasts
python scripts/cleanup_podcasts.py --max-files 50

# Show what would be deleted (dry run)
python scripts/cleanup_podcasts.py --dry-run

# Show current statistics
python scripts/cleanup_podcasts.py --stats-only
```

### Cleanup Configuration

- **Default retention**: 7 days
- **Maximum files**: 50 podcasts
- **File types cleaned**: `.wav` audio files and `_script.txt` files
- **Preserved files**: Demo files and system files are kept

## Scheduled Operations

### Setting Up Automated Management

Add these cron jobs for automatic management:

```bash
# Edit crontab
crontab -e

# Add these lines for automatic management:

# Scale down at 7 PM on weekdays (save costs)
0 19 * * 1-5 /path/to/manage-container.sh auto-scale

# Scale up at 8 AM on weekdays (ready for users)
0 8 * * 1-5 /path/to/manage-container.sh auto-scale

# Clean up old podcasts daily at 2 AM
0 2 * * * /path/to/cleanup_podcasts.py --max-age-days 7

# Optional: Complete shutdown on weekends
0 20 * * 5 /path/to/manage-container.sh stop    # Friday 8 PM
0 8 * * 1 /path/to/manage-container.sh start    # Monday 8 AM
```

### Azure Logic Apps Alternative

For enterprise scenarios, consider using Azure Logic Apps for scheduling:

1. **Time-based triggers** for scaling operations
2. **HTTP calls** to Azure REST APIs
3. **Integration** with Azure Monitor for metrics-based scaling
4. **Notifications** when operations complete

## Monitoring and Alerts

### Key Metrics to Monitor

- **Active replicas**: Current number of running instances
- **CPU/Memory usage**: Resource utilization per replica
- **Request count**: Number of incoming requests
- **Response time**: Application performance
- **Storage usage**: Podcast file storage consumption

### Cost Monitoring

```bash
# Monitor costs using Azure CLI
az consumption usage list --start-date 2024-01-01 --end-date 2024-01-31

# Get container app metrics
az monitor metrics list --resource /subscriptions/.../containerApps/edutainmentforge-app
```

### Setting Up Alerts

Create Azure Monitor alerts for:

- **High CPU usage** (> 80% for 5 minutes)
- **Memory pressure** (> 90% for 5 minutes)
- **Cost thresholds** (daily/monthly limits)
- **Storage usage** (approaching limits)

## Hackathon-Specific Configuration

### Recommended Settings for Hackathon

```bash
# During hackathon event (high usage expected)
./scripts/manage-container.sh scale 2 10

# After hackathon (cost optimization)
./scripts/manage-container.sh scale 0 3

# Emergency scale up for demo
./scripts/manage-container.sh scale 3 10
```

### Cost Control for Hackathon

1. **Set spending limits** in Azure portal
2. **Monitor usage** daily during event
3. **Scale down immediately** after event
4. **Clean up demos** and test podcasts

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
az containerapp logs show --name edutainmentforge-app --resource-group edutainmentforge-rg

# Restart the app
./scripts/manage-container.sh restart
```

**High costs:**
```bash
# Scale down immediately
./scripts/manage-container.sh scale 0 1

# Check current usage
./scripts/manage-container.sh status
```

**Storage full:**
```bash
# Clean up old podcasts
python scripts/cleanup_podcasts.py --max-files 20

# Check storage usage
python scripts/cleanup_podcasts.py --stats-only
```

### Emergency Procedures

**Stop all resources:**
```bash
./scripts/manage-container.sh stop
```

**Cost emergency:**
```bash
# Stop the app completely
az containerapp update --name edutainmentforge-app --resource-group edutainmentforge-rg --min-replicas 0 --max-replicas 0
```

## Best Practices

### Development
- **Test scaling** in development environment first
- **Monitor costs** during development and testing
- **Use resource tags** for cost tracking

### Production
- **Gradual scaling** changes to avoid disruption
- **Regular cleanup** to manage storage costs
- **Backup important** podcasts before cleanup
- **Document changes** for team awareness

### Security
- **Secure scripts** with proper permissions
- **Use managed identity** for Azure operations
- **Audit operations** for compliance
- **Monitor access** to management scripts

## Azure Container Apps Features

### Built-in Features Used

- **Auto-scaling**: Based on HTTP requests and CPU/memory
- **Zero-downtime deployments**: For application updates
- **HTTPS termination**: Automatic SSL/TLS handling
- **Managed identity**: Secure access to Azure services
- **Log aggregation**: Centralized logging and monitoring

### Advanced Configuration

```yaml
# Container app scaling rules (azure-container-app.yaml)
scale:
  minReplicas: 0
  maxReplicas: 10
  rules:
  - name: "http-rule"
    http:
      concurrent: 100
  - name: "cpu-rule"  
    custom:
      type: "cpu"
      metadata:
        type: "Utilization"
        value: "70"
```

This configuration provides automatic cost optimization while maintaining performance during usage spikes.
