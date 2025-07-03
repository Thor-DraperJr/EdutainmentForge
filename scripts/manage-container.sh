#!/bin/bash

# Azure Container Apps Management Script for EdutainmentForge
# This script helps manage the container app lifecycle including:
# - Auto-scaling based on usage
# - Automatic cleanup of old podcasts
# - Cost optimization by shutting down during low usage

set -e

# Configuration
RESOURCE_GROUP="edutainmentforge-rg"
CONTAINER_APP_NAME="edutainmentforge-app"
STORAGE_ACCOUNT_NAME="edutainment52052"
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"
MAX_PODCAST_AGE_DAYS=7
MAX_REPLICAS=5
MIN_REPLICAS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to check if Azure CLI is logged in
check_azure_login() {
    if ! az account show &>/dev/null; then
        error "Not logged into Azure CLI. Please run 'az login' first."
        exit 1
    fi
    
    if [ -n "$SUBSCRIPTION_ID" ]; then
        az account set --subscription "$SUBSCRIPTION_ID"
        log "Using subscription: $SUBSCRIPTION_ID"
    fi
}

# Function to get container app status
get_app_status() {
    local status=$(az containerapp show \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.runningStatus" \
        --output tsv 2>/dev/null || echo "NotFound")
    echo "$status"
}

# Function to scale container app
scale_app() {
    local min_replicas=$1
    local max_replicas=$2
    
    log "Scaling container app: min=$min_replicas, max=$max_replicas"
    
    az containerapp update \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --min-replicas "$min_replicas" \
        --max-replicas "$max_replicas" \
        --output none
    
    log "Container app scaled successfully"
}

# Function to stop container app (scale to 0)
stop_app() {
    log "Stopping container app (scaling to 0 replicas)"
    scale_app 0 0
}

# Function to start container app
start_app() {
    log "Starting container app"
    scale_app 1 "$MAX_REPLICAS"
}

# Function to clean up old podcasts
cleanup_podcasts() {
    log "Cleaning up podcasts older than $MAX_PODCAST_AGE_DAYS days"
    
    # Get current date in epoch seconds
    local cutoff_date=$(date -d "$MAX_PODCAST_AGE_DAYS days ago" +%s)
    
    # Note: This is a placeholder for podcast cleanup
    # In a full implementation, this would:
    # 1. Connect to the storage account
    # 2. List files in the podcasts container/directory
    # 3. Delete files older than the cutoff date
    
    warn "Podcast cleanup not yet implemented - this would clean files older than $MAX_PODCAST_AGE_DAYS days"
    
    # Example implementation (commented out):
    # az storage blob list \
    #     --account-name "$STORAGE_ACCOUNT_NAME" \
    #     --container-name "podcasts" \
    #     --query "[?properties.lastModified < '$cutoff_date'].name" \
    #     --output tsv | \
    # while read blob_name; do
    #     az storage blob delete \
    #         --account-name "$STORAGE_ACCOUNT_NAME" \
    #         --container-name "podcasts" \
    #         --name "$blob_name"
    #     log "Deleted old podcast: $blob_name"
    # done
}

# Function to check resource usage and auto-scale
auto_scale() {
    log "Checking resource usage for auto-scaling"
    
    # Get current hour (0-23)
    local current_hour=$(date +%H)
    
    # Business hours: 8 AM to 6 PM (scale up)
    # Off hours: scale down to save costs
    if [ "$current_hour" -ge 8 ] && [ "$current_hour" -le 18 ]; then
        log "Business hours detected - ensuring app is scaled up"
        scale_app 1 "$MAX_REPLICAS"
    else
        log "Off hours detected - scaling down for cost optimization"
        scale_app 0 2
    fi
}

# Function to get app metrics
get_metrics() {
    log "Getting container app metrics"
    
    local status=$(get_app_status)
    local replicas=$(az containerapp show \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.template.scale.minReplicas" \
        --output tsv 2>/dev/null || echo "0")
    
    echo "Status: $status"
    echo "Current min replicas: $replicas"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Container App: $CONTAINER_APP_NAME"
}

# Function to schedule automatic operations
schedule_operations() {
    log "Setting up scheduled operations"
    
    # Create a simple cron-like scheduler
    # This would typically be run as a cron job or Azure Logic App
    
    cat << 'EOF' > /tmp/edutainmentforge-scheduler.sh
#!/bin/bash
# EdutainmentForge Scheduled Operations
# Add this to crontab for automatic management:
# 
# # Scale down at 7 PM (19:00) on weekdays
# 0 19 * * 1-5 /path/to/manage-container.sh auto-scale
# 
# # Scale up at 8 AM (08:00) on weekdays  
# 0 8 * * 1-5 /path/to/manage-container.sh auto-scale
# 
# # Clean up old podcasts daily at 2 AM
# 0 2 * * * /path/to/manage-container.sh cleanup
# 
# # Stop completely on weekends to save costs (optional)
# 0 20 * * 5 /path/to/manage-container.sh stop    # Friday 8 PM
# 0 8 * * 1 /path/to/manage-container.sh start    # Monday 8 AM

EOF

    log "Scheduler template created at /tmp/edutainmentforge-scheduler.sh"
    log "To enable automatic management, add the cron jobs to your system crontab"
}

# Main script logic
case "$1" in
    "start")
        check_azure_login
        start_app
        ;;
    "stop")
        check_azure_login
        stop_app
        ;;
    "restart")
        check_azure_login
        stop_app
        sleep 30
        start_app
        ;;
    "scale")
        check_azure_login
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "Usage: $0 scale <min_replicas> <max_replicas>"
            exit 1
        fi
        scale_app "$2" "$3"
        ;;
    "auto-scale")
        check_azure_login
        auto_scale
        ;;
    "cleanup")
        check_azure_login
        cleanup_podcasts
        ;;
    "status")
        check_azure_login
        get_metrics
        ;;
    "schedule")
        schedule_operations
        ;;
    "help"|"--help"|"-h")
        echo "EdutainmentForge Container Management Script"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  start               Start the container app"
        echo "  stop                Stop the container app (scale to 0)"
        echo "  restart             Restart the container app"
        echo "  scale <min> <max>   Scale app to specific replica range"
        echo "  auto-scale          Automatically scale based on time of day"
        echo "  cleanup             Clean up old podcasts"
        echo "  status              Show current app status and metrics"
        echo "  schedule            Show how to set up automatic scheduling"
        echo "  help                Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start the app"
        echo "  $0 scale 0 3                # Scale between 0-3 replicas"
        echo "  $0 auto-scale               # Auto-scale based on time"
        echo "  $0 cleanup                  # Clean old podcasts"
        echo ""
        echo "Environment Variables:"
        echo "  AZURE_SUBSCRIPTION_ID      Azure subscription to use"
        echo ""
        ;;
    *)
        error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

log "Operation completed successfully"
