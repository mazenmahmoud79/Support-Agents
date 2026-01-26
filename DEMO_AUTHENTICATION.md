# Demo Authentication System

## Overview

This project now uses a simplified **demo-only authentication system**. Users can only log in using pre-generated demo IDs from a static JSON file.

## Key Features

- ✅ **No Registration**: Users cannot create their own accounts
- ✅ **No API Keys**: Traditional API key authentication has been removed
- ✅ **Pre-Generated IDs**: 100 demo IDs are available in `backend/demo_ids.json`
- ✅ **Single Tenant**: All demo users access the same "Mohr Software Solutions" tenant
- ✅ **Simple Login**: Users enter their demo ID and instantly access the system

## Demo IDs

All 100 demo IDs follow the format: `DEMO-XXXXXX`

Examples:
- `DEMO-A1B2C3`
- `DEMO-D4E5F6`
- `DEMO-G7H8I9`
- `DEMO-J0K1L2`
- ...and 96 more

**File Location**: `backend/demo_ids.json`

## Architecture

### Backend Changes

#### 1. Authentication Route (`backend/app/api/routes/auth.py`)

- **Removed Endpoints**:
  - `POST /auth/register` - User registration
  - `POST /auth/login` - API key login

- **Updated Endpoint**:
  - `POST /auth/login` - Now validates demo IDs against JSON file
    - Loads `demo_ids.json` on each request
    - Validates demo ID exists in the list
    - Returns or creates the "Mohr Software Solutions" tenant
    - Returns tenant credentials including API key for subsequent requests

#### 2. Demo Configuration (`backend/demo_ids.json`)

```json
{
  "tenant_name": "Mohr Software Solutions",
  "tenant_id": "mohr_software",
  "demo_ids": [
    "DEMO-A1B2C3",
    "DEMO-D4E5F6",
    ...100 total IDs
  ]
}
```

### Frontend Changes

#### 1. Login Page (`frontend/src/pages/LoginPage.tsx`)

- **Removed**:
  - Registration form
  - API key login option
  - Toggle between demo/API modes
  
- **Simplified UI**:
  - Single input field for demo ID
  - Auto-uppercase transformation
  - 11-character limit (DEMO-XXXXXX)
  - Clear error messages

#### 2. Auth Service (`frontend/src/services/authService.ts`)

- **Removed Methods**:
  - `register()` - User registration
  - `login()` - API key login
  
- **Kept Method**:
  - `demoLogin(demoId: string)` - Demo ID authentication

#### 3. Auth Store (`frontend/src/hooks/useAuth.ts`)

- **Removed State**:
  - `login()` action
  - `register()` action
  
- **Simplified State**:
  - Only `demoLogin()` and `logout()` actions
  - Stores demo ID in localStorage for persistence

#### 4. Navigation (`frontend/src/App.tsx`, `frontend/src/components/layout/Layout.tsx`)

- **Removed**:
  - Demo Users page route
  - Demo Users navigation link

## Usage

### For End Users

1. Navigate to the login page
2. Enter one of the 100 pre-generated demo IDs
3. Click "Access Demo"
4. Instant access to the AI Support Agent

### For Administrators

Demo IDs are managed by the product owner. To add or modify IDs:

1. Edit `backend/demo_ids.json`
2. Add/remove demo IDs from the `demo_ids` array
3. Restart the backend server (IDs are loaded on each login request)

**Note**: The tenant (`mohr_software`) is automatically created on first demo login.

## Security Considerations

1. **Demo IDs are NOT secrets**: They are meant for demo/testing purposes only
2. **All demo users share the same tenant**: Data is shared across all demo sessions
3. **No expiration**: Demo IDs don't expire (can be added if needed)
4. **Rate limiting**: Consider adding rate limiting to prevent abuse

## API Flow

```
1. User enters demo ID in UI
   ↓
2. Frontend sends POST /auth/login with { demo_id: "DEMO-A1B2C3" }
   ↓
3. Backend loads demo_ids.json
   ↓
4. Backend validates demo ID exists in list
   ↓
5. Backend retrieves or creates "mohr_software" tenant
   ↓
6. Backend returns tenant info + API key
   ↓
7. Frontend stores API key and navigates to chat
   ↓
8. Subsequent requests use API key in X-API-Key header
```

## Database

The `demo_users` table is **no longer used**. Demo authentication is purely JSON-based. The table can be dropped in future migrations.

The `tenants` table still maintains the "Mohr Software Solutions" tenant record.

## Test Data

The system includes test data for the Mohr Software Solutions tenant:

- `backend/test_data/mohr_product_guide.txt` - Product documentation
- `backend/test_data/mohr_faq.txt` - Frequently asked questions
- `backend/test_data/mohr_pricing.txt` - Pricing information
- `backend/test_data/mohr_troubleshooting.txt` - Technical support guide
- `backend/test_data/mohr_security.txt` - Security and compliance documentation

Upload these documents through the UI to populate the knowledge base.

## Future Enhancements

Potential improvements for the demo system:

1. **Expiration Dates**: Add expiration to demo IDs
2. **Usage Tracking**: Track how many times each demo ID is used
3. **Rate Limiting**: Limit requests per demo ID
4. **Multiple Tenants**: Support demo IDs for different demo tenants
5. **Admin Dashboard**: UI for viewing demo ID usage statistics

## Migration Notes

If you're upgrading from the previous multi-tenant system:

1. Existing API keys will still work (validate against `tenants` table)
2. Old demo users (from `demo_users` table) will no longer authenticate
3. The frontend will only show the simplified login UI
4. To access existing tenants, you'll need their API key (not supported in UI)

## Environment Variables

No new environment variables are required for demo authentication. The system uses:

- `DATABASE_URL` - For tenant storage
- `QDRANT_URL` - For vector storage
- `GROQ_API_KEY` - For LLM inference

Demo configuration is in `backend/demo_ids.json` (no environment variables needed).
