# Docker Compose Examples

This directory contains example Docker Compose configurations for different use cases.

## Production Deployment

Use `docker-compose.yml` for production deployment with pre-built images from GitHub Container Registry.

```bash
cd examples
docker compose up -d
```

This will:
- Start a PostgreSQL database container
- Pull the latest backend image from GHCR
- Run database migrations automatically on startup
- Run the backend container on port 8000
- Restart automatically unless stopped manually
- Persist database data in a Docker volume

**Configuration:**
Edit the `FRONTEND_ORIGINS` environment variable to match your frontend URL.

**Database:**
- PostgreSQL data is stored in the `postgres_data` volume
- Default credentials: `reversi:reversi` (change in production)
- Database migrations run automatically when the backend starts

## Development Setup

Use `docker-compose.dev.yml` for local development with hot reload.

```bash
# Run from project root
docker compose -f examples/docker-compose.dev.yml up
```

This will:
- Start a PostgreSQL database container (exposed on port 5432)
- Build the backend image locally
- Run database migrations automatically on startup
- Mount source code as volumes for hot reload
- Enable auto-reload on code changes
- Connect to your local frontend at http://localhost:5173

**Note:** Run this from the project root directory, not from the `examples` directory.

**Development Database:**
- PostgreSQL is accessible on `localhost:5432`
- You can connect with database tools using credentials: `reversi:reversi`
- Useful for inspecting game statistics during development

## Stopping Services

```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```
