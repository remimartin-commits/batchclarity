# Step 8 Frontend Prep (Operational)

This project already contains a React/TypeScript frontend shell. To keep delivery stable, run this prep sequence before adding new pages.

## 1) Environment

- Copy `frontend/.env.example` to `frontend/.env`.
- Confirm API URL points to the backend dev host:
  - `VITE_API_BASE_URL=http://127.0.0.1:8001`

## 2) Auth/session behavior

- Axios client now reads `VITE_API_BASE_URL`.
- On `401`, client attempts a single token refresh (`/auth/refresh`) and retries once.
- If refresh fails, user is logged out and redirected to `/login`.

## 3) Step 8 page targets

The base routing shell already exists. Implement or refine these pages in this order:

1. `/login` (username/password, optional MFA prompt)
2. `/change-password` (enforce `must_change_password`)
3. `/security` (MFA enroll + verify flow)
4. `/dashboard` (module cards + summary metrics)
5. `/admin/users` (create/update/deactivate users, assign/revoke roles, search/filter/page)
6. `/admin/roles` (create/update role permissions, search/page)

## 4) Validation command

Backend automated checks:

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\scripts\run-checks.ps1
```

Frontend smoke run:

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\frontend"
npm run dev
```

API smoke run (automation-first, no browser):

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\.venv\Scripts\python.exe .\scripts\smoke_auth_admin.py --username admin --password "YOUR_PASSWORD"
```
