# Developer Setup Guide - Manual Startup

This guide is for developers who want to run the project locally with hot reload for active development.

## Overview

For development, you'll run:
- **Backend**: Python with hot reload (uvicorn --reload)
- **Frontend**: Vite dev server with HMR (Hot Module Replacement)
- **Databases**: Docker containers (easiest) OR local installations

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker Desktop** (for databases) OR PostgreSQL + Qdrant installed locally
- **Groq API Key**

---

## Option 1: Hybrid Setup (Recommended for Developers)

**Run databases in Docker, backend & frontend locally for hot reload**

### Step 1: Start Only the Databases with Docker

Create a `docker-compose.dev.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: support-agent-postgres-dev
    environment:
      POSTGRES_USER: support_agent
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: support_agent_db
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - dev-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: support-agent-qdrant-dev
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_dev_data:/qdrant/storage
    networks:
      - dev-network

  redis:
    image: redis:7-alpine
    container_name: support-agent-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - dev-network

volumes:
  postgres_dev_data:
  qdrant_dev_data:
  redis_dev_data:

networks:
  dev-network:
    driver: bridge
```

**Start the databases:**
```powershell
docker-compose -f docker-compose.dev.yml up -d
```

### Step 2: Setup Backend for Development

```powershell
# Navigate to backend
cd d:\Work\Zadaai\Support_Agent\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional but recommended)
pip install ipython black pytest
```

**Configure `.env` for local development:**
```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Local Qdrant (Docker)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Local PostgreSQL (Docker)
DATABASE_URL=postgresql://support_agent:dev_password@localhost:5432/support_agent_db

# Redis (Docker)
REDIS_URL=redis://localhost:6379

# Development mode
DEBUG=true
```

**Run backend with hot reload:**
```powershell
# Make sure you're in backend folder with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

**You should see:**
```
INFO:     Will watch for changes in these directories: ['D:\\Work\\Zadaai\\Support_Agent\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Backend is now running with:**
- ✅ Hot reload on code changes
- ✅ Debug logging
- ✅ API docs at http://localhost:8000/docs

### Step 3: Setup Frontend for Development

**Open a NEW terminal/PowerShell window:**

```powershell
# Navigate to frontend
cd d:\Work\Zadaai\Support_Agent\frontend

# Install dependencies (first time only)
npm install

# Run dev server with HMR
npm run dev
```

**You should see:**
```
VITE v5.0.11  ready in 234 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h to show help
```

**Frontend is now running with:**
- ✅ Hot Module Replacement (instant updates)
- ✅ Fast refresh for React
- ✅ TypeScript type checking
- ✅ Source maps for debugging

### Step 4: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## Option 2: Fully Local Setup (No Docker)

### Install Dependencies Manually

#### 1. **Install PostgreSQL**
- Download from https://www.postgresql.org/download/windows/
- During installation, set password and remember it
- Default port: 5432

**Create database:**
```sql
-- Connect to PostgreSQL as postgres user
CREATE DATABASE support_agent_db;
CREATE USER support_agent WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE support_agent_db TO support_agent;
```

#### 2. **Install Qdrant**
Download binary:
```powershell
Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-pc-windows-msvc.zip" -OutFile "qdrant.zip"
Expand-Archive -Path "qdrant.zip" -DestinationPath "qdrant"
```

**Run Qdrant:**
```powershell
cd qdrant
.\qdrant.exe
```

#### 3. **Redis (Optional)**
Download from https://github.com/microsoftarchive/redis/releases

### Then follow Step 2 & 3 from Option 1

---

## Development Workflow

### Terminal Setup

You'll need **3-4 terminal windows**:

#### Terminal 1: Database Services (if using Docker)
```powershell
cd d:\Work\Zadaai\Support_Agent
docker-compose -f docker-compose.dev.yml up
```

#### Terminal 2: Backend
```powershell
cd d:\Work\Zadaai\Support_Agent\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 3: Frontend
```powershell
cd d:\Work\Zadaai\Support_Agent\frontend
npm run dev
```

#### Terminal 4: Optional - Python Shell for Testing
```powershell
cd d:\Work\Zadaai\Support_Agent\backend
.\venv\Scripts\Activate.ps1
ipython
```

### Hot Reload Behavior

**Backend (Python):**
- Edit any `.py` file → Server automatically restarts
- Changes typically reflect in 1-2 seconds
- Console shows reload messages

**Frontend (React):**
- Edit any `.tsx`, `.ts`, `.css` file → Instant update in browser
- No page refresh needed
- State is preserved when possible
- Changes reflect in < 1 second

---

## Debugging

### Backend Debugging (VS Code)

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

**Set breakpoints** in your Python code and press F5!

### Frontend Debugging (Browser)

1. Open Chrome DevTools (F12)
2. Go to **Sources** tab
3. Find your `.tsx` files in `webpack://` → `.` → `src`
4. Set breakpoints directly in TypeScript code
5. Source maps work automatically with Vite

### Database Debugging

**PostgreSQL:**
```powershell
# Connect to database
docker exec -it support-agent-postgres-dev psql -U support_agent -d support_agent_db

# Or use pgAdmin or DBeaver GUI
```

**Qdrant:**
- Dashboard: http://localhost:6333/dashboard
- View collections, points, and run queries

---

## Common Development Tasks

### Reset Database
```powershell
# Stop containers
docker-compose -f docker-compose.dev.yml down -v

# Start fresh
docker-compose -f docker-compose.dev.yml up -d

# Backend will auto-create tables on next start
```

### Clear Qdrant Collections
```python
# In Python shell (backend venv activated)
from app.services.vector_store import get_vector_store
import asyncio

async def clear_collection(tenant_id):
    vs = get_vector_store()
    await vs.delete_collection(tenant_id)

# Run it
asyncio.run(clear_collection("your_tenant_id_here"))
```

### Test Backend API
```powershell
# Install HTTPie (optional but nice)
pip install httpx

# Or use curl
curl http://localhost:8000/api/admin/health
```

### Format Code
```powershell
# Backend (install black first: pip install black)
cd backend
black app/

# Frontend
cd frontend
npm run lint  # if you add eslint
```

---

## Environment Variables for Development

Create `.env` in project root:

```env
# Development mode
DEBUG=true
APP_ENV=development

# Groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Local services
QDRANT_HOST=localhost
QDRANT_PORT=6333
DATABASE_URL=postgresql://support_agent:dev_password@localhost:5432/support_agent_db
REDIS_URL=redis://localhost:6379

# Security (use simple values for dev)
SECRET_KEY=dev_secret_key_not_for_production
ALGORITHM=HS256

# CORS (allow dev server)
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"]

# Document processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_UPLOAD_SIZE=10485760
```

---

## Performance Tips

### Speed Up First Run

The first time you send a chat message or upload a document, the embedding model (~90MB) will download. To pre-download:

```python
# In Python shell
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Model is now cached
```

### Reduce Logging Noise

In `backend/app/config.py`, add:

```python
# For development
if DEBUG:
    import logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
```

---

## Troubleshooting

### "Module not found" errors (Backend)
```powershell
# Make sure you're in backend folder and venv is activated
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "Cannot find module" errors (Frontend)
```powershell
cd frontend
rm -rf node_modules
rm package-lock.json  # if exists
npm install
```

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Frontend can't connect to backend
- Check backend is running on port 8000
- Check `frontend/src/services/api.ts` has correct URL
- Check CORS settings in `backend/app/main.py`

---

## Quick Reference

### Start Everything (Development)
```powershell
# Terminal 1 - Databases
docker-compose -f docker-compose.dev.yml up

# Terminal 2 - Backend
cd backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload

# Terminal 3 - Frontend  
cd frontend && npm run dev
```

### Stop Everything
```powershell
# Ctrl+C in each terminal, then:
docker-compose -f docker-compose.dev.yml down
```

### Full Clean Restart
```powershell
# Stop and remove all data
docker-compose -f docker-compose.dev.yml down -v

# Clear Python cache
cd backend && Remove-Item -Recurse -Force __pycache__, app/__pycache__

# Clear Node cache
cd frontend && Remove-Item -Recurse -Force node_modules, dist

# Reinstall
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Start fresh
# ... follow "Start Everything" steps above
```

---

## Next Steps

1. **Read the code**: Start with [`backend/app/main.py`](file:///d:/Work/Zadaai/Support_Agent/backend/app/main.py) and [`frontend/src/App.tsx`](file:///d:/Work/Zadaai/Support_Agent/frontend/src/App.tsx)
2. **Make a change**: Edit a file and watch it hot reload
3. **Test the API**: Visit http://localhost:8000/docs
4. **Build a feature**: Add new endpoints, components, etc.

Happy coding! 🚀
