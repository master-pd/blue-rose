#!/bin/bash
# Blue Rose Bot - Deployment Script

set -e  # Exit on error

echo "🚀 Starting Blue Rose Bot Deployment"
echo "===================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and fill in your values."
    exit 1
fi

# Load environment variables
source .env

# Check required variables
required_vars=("BOT_TOKEN" "BOT_OWNER_ID" "WEBHOOK_DOMAIN" "WEBHOOK_SECRET" "ADMIN_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done

echo "✅ Environment variables loaded"

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Check for SSL certificates
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo "⚠️  SSL certificates not found in ssl/ directory"
    echo "Please place your SSL certificates:"
    echo "  - ssl/cert.pem"
    echo "  - ssl/key.pem"
    exit 1
fi

echo "✅ SSL certificates found"

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if bot is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ All services are running!"
    
    # Show service status
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    # Show logs
    echo ""
    echo "📝 Recent logs:"
    docker-compose logs --tail=10 blue-rose-bot
    
    # Show access information
    echo ""
    echo "🌐 Access Information:"
    echo "Webhook URL: https://$WEBHOOK_DOMAIN/webhook"
    echo "Health Check: https://$WEBHOOK_DOMAIN/health"
    echo "Dashboard: https://$WEBHOOK_DOMAIN/dashboard"
    
else
    echo "❌ Some services failed to start"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "Check logs: docker-compose logs -f blue-rose-bot"
echo "Stop services: docker-compose down"