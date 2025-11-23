# Docker Compose Examples

This directory contains example Docker Compose configurations for different use cases.

## Production Deployment

Use `docker-compose.yml` for production deployment with pre-built images from GitHub Container Registry.

```bash
cd examples
docker compose up -d
```

This will:
- Pull the latest image from GHCR
- Run the container on port 8000
- Restart automatically unless stopped manually

**Configuration:**
Edit the `FRONTEND_ORIGINS` environment variable to match your frontend URL.

## Development Setup

Use `docker-compose.dev.yml` for local development with hot reload.

```bash
# Run from project root
docker compose -f examples/docker-compose.dev.yml up
```

This will:
- Build the image locally
- Mount source code as volumes for hot reload
- Enable auto-reload on code changes
- Connect to your local frontend at http://localhost:5173

**Note:** Run this from the project root directory, not from the `examples` directory.

## Stopping Services

```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```
