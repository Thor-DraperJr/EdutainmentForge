#!/bin/bash

# EdutainmentForge Docker Helper Script

set -e

# Function to display usage
usage() {
    echo "Usage: $0 [build|run|stop|logs|shell|clean]"
    echo ""
    echo "Commands:"
    echo "  build    - Build the Docker image"
    echo "  run      - Run the container with docker-compose"
    echo "  stop     - Stop the running container"
    echo "  logs     - View container logs"
    echo "  shell    - Open shell in running container"
    echo "  clean    - Remove stopped containers and unused images"
    exit 1
}

# Build Docker image
build() {
    echo "🏗️  Building EdutainmentForge Docker image..."
    docker build -t edutainmentforge:latest .
    echo "✅ Build completed!"
}

# Run with docker-compose
run() {
    echo "🚀 Starting EdutainmentForge..."
    docker-compose up -d
    echo "✅ EdutainmentForge is running at http://localhost:5000"
    echo "📝 Use 'docker-compose logs -f' to view logs"
}

# Stop containers
stop() {
    echo "🛑 Stopping EdutainmentForge..."
    docker-compose down
    echo "✅ Stopped!"
}

# View logs
logs() {
    docker-compose logs -f edutainment-forge
}

# Open shell in container
shell() {
    docker-compose exec edutainment-forge /bin/bash
}

# Clean up
clean() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down
    docker system prune -f
    echo "✅ Cleanup completed!"
}

# Main script logic
case "${1:-}" in
    build)
        build
        ;;
    run)
        run
        ;;
    stop)
        stop
        ;;
    logs)
        logs
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    *)
        usage
        ;;
esac
