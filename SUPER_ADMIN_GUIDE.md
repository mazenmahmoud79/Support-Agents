# Super Admin Guide: Adding Demo Users

## Access Route
- Super Admin Login: `/super-admin`
- Super Admin Dashboard: `/super-admin/dashboard`

## Steps to Add Demo Users

1. **Log in as Super Admin**:
   - Navigate to the Super Admin login page.
   - Enter the super admin password (default: `admin123` or check environment variable `SUPER_ADMIN_PASSWORD`).

2. **Access Tenant Management**:
   - After login, you will be on the Super Admin dashboard showing tenant statistics and list.

3. **Create a New Tenant**:
   - Click the "Create Tenant" button or plus icon.
   - Enter a name for the new tenant (e.g., "Demo Company").

4. **Submit and Generate Demo User**:
   - Click "Create" to submit.
   - The system will automatically:
     - Create a new tenant in the database.
     - Generate a unique demo ID (format: `DEMO-XXXXXX`).
     - Create an admin demo user for the tenant.

5. **Copy the Demo ID**:
   - The new tenant will appear in the list with its demo ID.
   - Click the copy icon next to the demo ID to copy it for sharing.

## Notes
- Each tenant gets exactly one demo user (admin) upon creation.
- Demo users are tied to specific tenants and cannot access other tenants.
- Use the tenant management features to activate/deactivate or delete tenants as needed.