#!/bin/bash

# Jenkins Deployment Script
# This script automates the deployment of Jenkins Master and Slave using Docker Compose

set -e

echo "========================================"
echo "Jenkins Automated Deployment Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${RED}Please edit .env file with your credentials before continuing!${NC}"
    echo "After editing, run this script again."
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"

# Load environment variables
source .env

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed. Please install it and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose is installed${NC}"
echo ""

# Stop and remove existing containers
echo "Stopping existing Jenkins containers (if any)..."
docker-compose down -v 2>/dev/null || true

echo ""
echo "Building and starting Jenkins..."
echo "This may take a few minutes on first run (downloading images and installing plugins)..."
echo ""

# Build and start containers
docker-compose up -d --build

echo ""
echo "Waiting for Jenkins to start..."
echo "This can take 2-3 minutes while plugins are installed..."
echo ""

# Wait for Jenkins to be ready
JENKINS_URL=${JENKINS_URL:-http://localhost:8080}
MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf ${JENKINS_URL}/login > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Jenkins is ready!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 5
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗ Jenkins failed to start within expected time${NC}"
    echo "Check logs with: docker-compose logs jenkins-master"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}Jenkins Deployment Completed!${NC}"
echo "========================================"
echo ""
echo "Jenkins URL: ${JENKINS_URL}"
echo ""
echo "Users created:"
echo "  - admin     (password: ${JENKINS_ADMIN_PASSWORD})"
echo "  - devops    (password: ${JENKINS_DEVOPS_PASSWORD})"
echo "  - developer (password: ${JENKINS_DEV_PASSWORD})"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop Jenkins:     docker-compose stop"
echo "  Start Jenkins:    docker-compose start"
echo "  Restart Jenkins:  docker-compose restart"
echo "  Remove Jenkins:   docker-compose down -v"
echo ""
echo -e "${YELLOW}Note: Jenkins is configured with JCasC - no manual setup required!${NC}"
echo ""
