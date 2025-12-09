## Supabase + Vercel setup

The project is ready to use Supabase for Postgres + Storage and to deploy to Vercel's Python runtime.

### 1) Configure Supabase
- Create a Supabase project and database.
- Copy the `postgresql://` connection string (include `sslmode=require`) into `DATABASE_URL` in your `.env`.
- Grab `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` from the API settings.
- Optional: create a storage bucket (defaults to `media`) if you want to upload files.

### 2) Local development
- Duplicate `.env.example` to `.env` and fill the Supabase and Django secrets.
- Install deps: `pip install -r requirements.txt`.
- Run migrations: `python manage.py migrate`.
- Start the server: `python manage.py runserver`.

### 3) Deploy to Vercel
- Ensure the Vercel CLI is logged in (`vercel login`) and linked (`vercel link`).
- Set env vars in Vercel (Project Settings → Environment Variables or `vercel env`):
  - `DATABASE_URL` (Supabase), `DB_SSL_REQUIRE=1`
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`
  - `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS=.vercel.app`, `CSRF_TRUSTED_ORIGINS=https://*.vercel.app`
- Deploy: `vercel deploy --prod`.

### 4) Using Supabase storage in code
`core/supabase_client.py` exposes helpers:

```python
from core.supabase_client import upload_bytes, create_signed_url

public_url = upload_bytes(path="uploads/example.txt", content=b"hello", content_type="text/plain")
signed_url = create_signed_url(path="uploads/example.txt", expires_in=3600)
```
