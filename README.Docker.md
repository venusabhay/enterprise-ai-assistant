# Docker Setup Guide

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Individual Service Management

### Backend Only
```bash
docker-compose up backend
```

### Frontend Only
```bash
docker-compose up frontend
```

## Development

The Docker setup includes volume mounts for hot-reloading:
- Backend: Changes to Python files trigger automatic reload
- Frontend: Changes to React files trigger HMR (Hot Module Replacement)

## Production Build

For production, create optimized builds:

### Backend Production
```bash
docker build -t enterprise-ai-backend:prod ./backend
docker run -p 8000:8000 enterprise-ai-backend:prod
```

### Frontend Production
Build static files and serve with nginx (create `ui/Dockerfile.prod`):
```bash
docker build -f ui/Dockerfile.prod -t enterprise-ai-frontend:prod ./ui
docker run -p 80:80 enterprise-ai-frontend:prod
```

## Troubleshooting

### Port Conflicts
If ports 5173 or 8000 are in use, modify `docker-compose.yml`:
```yaml
ports:
  - "3000:5173"  # Change host port
```

### Clear Volumes
```bash
docker-compose down -v
```

### Rebuild from Scratch
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Health Check
```bash
curl http://localhost:8000/health/
```

## Environment Variables

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```
