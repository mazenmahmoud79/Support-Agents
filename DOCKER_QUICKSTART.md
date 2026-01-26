# 🚀 Quick Start with Docker (Recommended)

Running with Docker is **the easiest way** - everything is automated!

## Prerequisites

Only 2 things needed:
1. **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop))
2. **Your Groq API key** ([Get free key here](https://console.groq.com))

---

## Step 1: Configure Environment (30 seconds)

1. **Make sure your `.env` file exists** (you already have it)

2. **Add your Groq API key** to `.env`:
   ```env
   GROQ_API_KEY=gsk_your_actual_api_key_here
   ```

3. **That's it!** All other settings work automatically with Docker.

---

## Step 2: Start Everything (One Command!)

Open PowerShell in the project folder and run:

```powershell
cd d:\Work\Zadaai\Support_Agent
docker-compose up --build
```

**What this does automatically:**
- ✅ Builds the backend Docker image
- ✅ Builds the frontend Docker image
- ✅ Downloads and starts PostgreSQL
- ✅ Downloads and starts Qdrant
- ✅ Downloads and starts Redis
- ✅ Creates all databases and tables
- ✅ Connects everything together
- ✅ Starts all services with health checks

**First time:** Takes 5-10 minutes to download images and build.  
**Subsequent runs:** Takes 30 seconds to start.

---

## Step 3: Access Your Application

Once you see:
```
support-agent-frontend-1  | ready - started server on 0.0.0.0:80
support-agent-backend-1   | Application startup complete
```

**Open your browser:**
- **Frontend:** http://localhost
- **API Docs:** http://localhost:8000/docs
- **Qdrant Dashboard:** http://localhost:6333/dashboard

---

## That's It! 🎉

Three steps:
1. Install Docker Desktop
2. Add Groq API key to `.env`
3. Run `docker-compose up --build`

---

## Common Commands

### Start all services (detached mode - runs in background):
```powershell
docker-compose up -d
```

### View logs:
```powershell
docker-compose logs -f
```

### Stop all services:
```powershell
docker-compose down
```

### Stop and remove all data (clean restart):
```powershell
docker-compose down -v
```

### Rebuild after code changes:
```powershell
docker-compose up --build
```

### Check service status:
```powershell
docker-compose ps
```

---

## Troubleshooting

### Port already in use (80, 8000, 5432, 6333)

**Option 1: Stop conflicting services**
```powershell
# If PostgreSQL is running locally
Stop-Service postgresql-x64-15  # or your PostgreSQL service name

# If something is using port 80
netstat -ano | findstr :80
# Kill the process using the PID shown
```

**Option 2: Change ports in `docker-compose.yml`**
```yaml
frontend:
  ports:
    - "3000:80"  # Change 80 to 3000 or any free port

backend:
  ports:
    - "8001:8000"  # Change 8000 to 8001
```

### Docker Desktop not running

Click the Docker Desktop icon to start it, then retry.

### Build fails or takes too long

```powershell
# Clear Docker cache and rebuild
docker-compose build --no-cache
docker-compose up
```

---

## Why Docker is Better for This Project

| Aspect | Docker | Local Setup |
|--------|--------|-------------|
| **Setup Time** | 5-10 min (one time) | 30-60 min |
| **Commands** | 1 command | 3-4 terminals |
| **Dependencies** | Auto-installed | Manual install |
| **Database Setup** | Automatic | Manual creation |
| **Service Isolation** | Perfect | Can conflict |
| **Production Ready** | Yes | No |
| **Team Sharing** | Easy | Complex |

---

## First Time Usage After Docker Start

1. **Go to** http://localhost

2. **Click "Register"**

3. **Enter your company name**

4. **SAVE THE API KEY** shown (you'll need it to login)

5. **Login** with the API key

6. **Upload documents** (PDF, DOCX, TXT, CSV)

7. **Start chatting!**

---

## Development with Docker

If you want to develop and see changes instantly:

### Backend Hot Reload
The backend automatically reloads when you change Python files because of this in `docker-compose.yml`:
```yaml
volumes:
  - ./backend/app:/app/app  # Live code sync
```

### Frontend Development
For frontend changes, you have two options:

**Option 1:** Run frontend locally (easier for development)
```powershell
# Stop just the frontend container
docker-compose stop frontend

# Run frontend in dev mode
cd frontend
npm install
npm run dev
# Access at http://localhost:5173
```

**Option 2:** Rebuild frontend container
```powershell
docker-compose up --build frontend
```

---

## What's Running?

When Docker Compose is up, you have:

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 80 | React app with Nginx |
| **Backend** | 8000 | FastAPI server |
| **PostgreSQL** | 5432 | Metadata database |
| **Qdrant** | 6333 | Vector database |
| **Redis** | 6379 | Caching (optional) |

All services are connected via a Docker network and can talk to each other.

---

## Pro Tips

1. **Use detached mode** for normal use:
   ```powershell
   docker-compose up -d
   ```

2. **View logs of specific service**:
   ```powershell
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

3. **Restart single service**:
   ```powershell
   docker-compose restart backend
   ```

4. **Shell into a container** for debugging:
   ```powershell
   docker-compose exec backend bash
   docker-compose exec postgres psql -U support_agent -d support_agent_db
   ```

5. **Clean everything and start fresh**:
   ```powershell
   docker-compose down -v
   docker-compose up --build
   ```

---

## Estimated Times

- **First time setup:** 5-10 minutes (downloading images, building)
- **Subsequent starts:** 20-30 seconds
- **Stopping:** 5-10 seconds
- **Rebuilding:** 2-3 minutes

---

## Summary

**Docker = Easiest Option**
```powershell
# Literally just:
docker-compose up --build

# And you're done! 🎉
```

Everything else is automated. No manual database setup, no Python environments, no dependency management.
