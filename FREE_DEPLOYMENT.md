# Free client-preview deployment

This project can be shared as a free preview with:

- React frontend on Vercel or a Render Static Site
- Django API on a Render Free Web Service
- PostgreSQL on Supabase Free using `DATABASE_URL`

This is suitable for a demo or pilot, not production accounting data. Render Free services sleep after inactivity, and Supabase Free projects can pause after seven days of low activity and have a 500 MB database limit. Keep backups before importing client data.

## Deploy the backend

1. Push this repository to a Git provider.
2. In Render, create a Blueprint from the repository. The included `render.yaml` uses `backend` as the service root.
3. Create a Supabase Free project and copy its IPv4-compatible pooler connection string into Render as `DATABASE_URL`.
4. After the frontend is deployed, set these two Render variables to the exact HTTPS frontend URL:

```text
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
```

The API URL will be similar to `https://setustock-api.onrender.com/api`.

## Deploy the frontend

1. Import the same repository into Vercel.
2. Set the project root directory to `frontend`.
3. Use `npm run build` as the build command and `dist` as the output directory.
4. Add this environment variable before deploying:

```text
VITE_API_URL=https://setustock-api.onrender.com/api
```

The existing `frontend/vercel.json` keeps React routes working after refresh.

## Client handoff

Share the Vercel URL with the client. Create a normal owner account through the registration screen, then invite team members from the Team module. Do not share database credentials, API keys or the Render/Supabase dashboards.

The free preview currently uses console email delivery. Password reset and MFA emails will not reach users until an HTTP email provider is configured. For a real client pilot, configure an email provider, object storage for uploads and a paid database with backups.
