# Backend

This directory contains the backend Python package and a Dockerfile for building the backend service container.

Build and run locally (Windows PowerShell):

```powershell
# Build image
docker build -t domain-monitoring-backend:local -f backend/Dockerfile .

# Run container (maps port 8080)
docker run --rm -p 8080:8080 domain-monitoring-backend:local
```

Note: The backend expects to find `UsersData/` at the repository root. Ensure it's present and contains user JSON files.
