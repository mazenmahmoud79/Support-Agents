# Google Drive Integration Troubleshooting Guide

## Issue: "Failed to download files from Google Drive"

### Root Cause
The `react-google-drive-picker` library (v1.2.2) authenticates users and opens the picker successfully, but doesn't properly expose the OAuth access token needed to download file contents via the Google Drive API.

### Current Implementation
The code attempts 5 different methods to retrieve the access token:
1. From `authResponse` (hook's second return value)
2. From `data.oauthToken` in the callback
3. From `gapi.auth2.getAuthInstance().currentUser.get().getAuthResponse()`
4. From `gapi.auth.getToken()` (legacy method)
5. From `gapi.client.getToken()`

### Debug Steps

1. **Open Browser Console** and click "Select from Google Drive"
2. **Look for these console logs:**
   - `Drive picker callback:` - Shows the picker action
   - `Auth response from hook:` - Shows if authResponse is available
   - `✓ Using token from...` - Shows which method successfully retrieved a token
   - `✗ No access token found` - Indicates all token retrieval methods failed

3. **Check the gapi object:**
   ```javascript
   console.log('gapi:', window.gapi);
   console.log('auth2:', window.gapi?.auth2);
   console.log('auth2 instance:', window.gapi?.auth2?.getAuthInstance());
   ```

### Possible Solutions

#### Solution 1: Verify Google Cloud Project Configuration

The Google Cloud Project needs proper OAuth configuration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services > OAuth consent screen**
4. Ensure scopes include:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`

5. Navigate to **APIs & Services > Credentials**
6. Click on your OAuth 2.0 Client ID
7. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5173`
   - `http://localhost:3000`
   - Your production domain

8. Under **Authorized redirect URIs**, add:
   - `http://localhost:5173`
   - Your production domain

#### Solution 2: Update OAuth Scopes in Code

If the token is being retrieved but file download fails with 401/403, you may need to explicitly request additional scopes. Currently using default scopes from the library.

To add explicit scopes, you'd need to upgrade to a newer version of `react-google-drive-picker` or use Google's OAuth library directly.

#### Solution 3: Alternative Implementation (Recommended if issue persists)

Replace `react-google-drive-picker` with direct Google API integration:

```typescript
// Load Google API client
const loadGoogleApi = () => {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://apis.google.com/js/api.js';
    script.onload = resolve;
    document.body.appendChild(script);
  });
};

// Initialize and authenticate
const initializeGoogleDrive = async () => {
  await loadGoogleApi();
  
  await (window as any).gapi.load('client:auth2:picker', async () => {
    await (window as any).gapi.client.init({
      apiKey: VITE_GOOGLE_DRIVE_API_KEY,
      clientId: VITE_GOOGLE_DRIVE_CLIENT_ID,
      discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'],
      scope: 'https://www.googleapis.com/auth/drive.readonly'
    });
  });
};
```

#### Solution 4: Use Backend Proxy (Most Reliable)

Instead of client-side file downloads:

1. User selects files from Drive picker
2. Frontend sends file IDs to backend
3. Backend uses a service account or OAuth token to download files
4. Backend returns file contents to frontend

This approach is more secure and reliable for production use.

### Testing Checklist

- [ ] Environment variables are set in `/frontend/.env`
- [ ] Dev server was restarted after adding `.env` file
- [ ] Google Drive picker opens (credentials work)
- [ ] Browser console shows detailed logs
- [ ] OAuth consent screen has correct scopes configured
- [ ] Authorized origins include your dev/prod domains
- [ ] Test with a simple text file first
- [ ] Check Network tab for failed API requests
- [ ] Verify token exists in any of the 5 methods

### Expected Console Output (Success)

```
Drive picker callback: picked
Auth response from hook: {...}
✓ Using token from gapi.auth2.getAuthInstance()
Fetching file from Drive: test.txt (abc123xyz)
Successfully downloaded: test.txt
Added 1 file(s) from Google Drive
```

### Expected Console Output (Failure)

```
Drive picker callback: picked
Auth response from hook: undefined
✗ No access token found for Drive fetch
Available gapi object: {...}
Failed to download files from Google Drive. Please check permissions and try again.
```

### Next Steps

1. Check browser console logs to identify which method (if any) retrieves the token
2. If no token is retrieved, verify OAuth configuration in Google Cloud Console
3. If token is retrieved but download fails, check the HTTP response status code and error message
4. Consider implementing backend proxy solution for production reliability
