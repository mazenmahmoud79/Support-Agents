# Quick Restart Guide

## Current Setup
You're running in **local development mode** with:
- Infrastructure (Postgres, Qdrant, Redis) in Docker via `docker-compose.dev.yml`
- Backend running locally in terminal (uvicorn)
- Frontend running locally in terminal (vite dev server)

## Do You Need to Restart?

**NO - Docker Compose**: Keep `docker-compose.dev.yml` running (infrastructure services)
**YES - Backend & Frontend**: Restart to apply authentication changes

---

## Restart Instructions

### Option 1: Quick Restart (Recommended)

#### Terminal 1 - Backend (uvicorn terminal)
```powershell
# Stop: Press Ctrl+C

# Restart backend
cd D:\Work\Zadaai\Support_Agent\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend (esbuild terminal)
```powershell
# Stop: Press Ctrl+C

# Restart frontend
cd D:\Work\Zadaai\Support_Agent\frontend
npm run dev
```

Backend will be at: http://localhost:8000
Frontend will be at: http://localhost:5173

---

### Option 2: Full Docker Restart (If Needed)

If you want to run everything in Docker instead:

```powershell
# Stop current docker-compose
docker-compose -f docker-compose.dev.yml down

# Start full production compose
docker-compose up --build -d

# Check logs
docker-compose logs -f backend
```

---

## Verify Demo Authentication

### Test Demo Login:
1. Open http://localhost:5173 (or http://localhost if using full docker)
2. Enter demo ID: `DEMO-A1B2C3`
3. Click "Access Demo"
4. Should redirect to chat page

### Test Backend Directly:
```powershell
# Test demo config loading
cd D:\Work\Zadaai\Support_Agent
python test_demo_auth.py

# Test demo login endpoint
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"demo_id": "DEMO-A1B2C3"}'
```

---

## Files Cleaned Up

### Removed:
- ✓ `frontend/src/pages/DemoUsersPage.tsx` - Old demo management UI
- ✓ `frontend/src/pages/DemoUsersPage.css` - UI styles
- ✓ `backend/create_demo_users_table.py` - Old migration script
- ✓ Old test files: `check_qdrant.py`, `debug_qdrant_full.py`, `inspect_collection.py`, `test_qdrant_*.py`, `test_reranking.py`

### Kept:
- ✓ `test_demo_auth.py` - Validates demo authentication system
- ✓ `sample_faq.txt` - Sample data for testing
- ✓ Essential documentation (README, DEMO_IDS, DEMO_AUTHENTICATION, LOCAL_SETUP)

---

## Next Steps

1. **Restart backend and frontend** (see Terminal 1 & 2 above)
2. **Test demo login** with any ID from [DEMO_IDS.md](DEMO_IDS.md)
3. **Upload test documents** from `data-to-upload/` folder if you have data
4. **Start chatting** with the AI!

---

## Troubleshooting

**Backend won't start?**
```powershell
# Check if port 8000 is in use
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# If needed, find and kill process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

**Frontend won't start?**
```powershell
# Check if port 5173 is in use
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

# Install dependencies if needed
cd D:\Work\Zadaai\Support_Agent\frontend
npm install
```

**Docker services not running?**
```powershell
# Check docker status
docker-compose -f docker-compose.dev.yml ps

# Restart docker services
docker-compose -f docker-compose.dev.yml restart
```

**Demo login fails?**
- Check backend logs for errors
- Verify `backend/demo_ids.json` exists
- Try running: `python test_demo_auth.py`
- Check API endpoint: http://localhost:8000/docs
