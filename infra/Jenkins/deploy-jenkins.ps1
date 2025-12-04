# Jenkins Deployment Script for Windows
# This script automates the deployment of Jenkins Master and Slave using Docker Compose

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins Automated Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-Not (Test-Path .env)) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please edit .env file with your credentials before continuing!" -ForegroundColor Red
    Write-Host "After editing, run this script again."
    exit 1
}

Write-Host "✓ .env file found" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is installed
try {
    docker-compose version | Out-Null
    Write-Host "✓ docker-compose is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ docker-compose is not installed. Please install it and try again." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Stop and remove existing containers
Write-Host "Stopping existing Jenkins containers (if any)..." -ForegroundColor Yellow
docker-compose down -v 2>$null

Write-Host ""
Write-Host "Building and starting Jenkins..." -ForegroundColor Cyan
Write-Host "This may take a few minutes on first run (downloading images and installing plugins)..." -ForegroundColor Yellow
Write-Host ""

# Build and start containers
docker-compose up -d --build

Write-Host ""
Write-Host "Waiting for Jenkins to start..." -ForegroundColor Yellow
Write-Host "This can take 2-3 minutes while plugins are installed..." -ForegroundColor Yellow
Write-Host ""

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        Set-Variable -Name $matches[1] -Value $matches[2] -Scope Script
    }
}

$jenkinsUrl = if ($JENKINS_URL) { $JENKINS_URL } else { "http://localhost:8080" }
$maxAttempts = 60
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "$jenkinsUrl/login" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host ""
            Write-Host "✓ Jenkins is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Ignore errors and continue waiting
    }
    $attempt++
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 5
}

if ($attempt -eq $maxAttempts) {
    Write-Host ""
    Write-Host "✗ Jenkins failed to start within expected time" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs jenkins-master"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins Deployment Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Jenkins URL: $jenkinsUrl" -ForegroundColor White
Write-Host ""
Write-Host "Users created:" -ForegroundColor White
Write-Host "  - admin     (password: $JENKINS_ADMIN_PASSWORD)" -ForegroundColor White
Write-Host "  - devops    (password: $JENKINS_DEVOPS_PASSWORD)" -ForegroundColor White
Write-Host "  - developer (password: $JENKINS_DEV_PASSWORD)" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View logs:        docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop Jenkins:     docker-compose stop" -ForegroundColor Gray
Write-Host "  Start Jenkins:    docker-compose start" -ForegroundColor Gray
Write-Host "  Restart Jenkins:  docker-compose restart" -ForegroundColor Gray
Write-Host "  Remove Jenkins:   docker-compose down -v" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Jenkins is configured with JCasC - no manual setup required!" -ForegroundColor Yellow
Write-Host ""
