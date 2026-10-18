# MicroOrder MVP

Flask + Supabase Postgres + Resend MVP for explicit client change-order approvals.

## Local setup

```sh
uv venv --python 3.15 .venv
uv pip install --python .venv/bin/python -r requirements.txt
set -a; source .env; set +a
./.venv/bin/python app.py
```

`DATABASE_URL` must be a Supabase Postgres connection string. The application passes it directly to psycopg; it does not parse or rewrite the URL. If the database password contains reserved URL characters, percent-encode them in the connection string. Supabase documents this requirement.

`RESEND_API_KEY` and `RESEND_FROM` enable decision notifications. Without them, the decision is stored but no email is sent.

## Flow

Contractor creates order → shares public link → client approves or declines → private owner link shows status and invoice line item. This does not process payments, verify identity, provide authentication, or claim legal enforceability.

## Production start

```sh
gunicorn --bind 0.0.0.0:$PORT app:app
```

Hosted secrets: `DATABASE_URL`, `RESEND_API_KEY`, `RESEND_FROM`, and a strong `FLASK_SECRET_KEY`.

## Deploy to Render

1. Push this repository to GitHub.
2. In Render, choose **New → Web Service** and connect the `algorithiclabs/MicroOrder` repository.
3. Use the detected `render.yaml`, or configure manually:
   - Runtime: `Python`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`
4. Add these environment variables in Render:
   - `DATABASE_URL`: Supabase server-side Postgres connection string
   - `RESEND_API_KEY`: Resend API key
   - `RESEND_FROM`: verified Resend sender, for example `MicroOrder <updates@your-domain.com>`
   - `FLASK_SECRET_KEY`: generate a strong random value
5. Deploy. Check the Render logs for a successful boot, then open the assigned `onrender.com` URL.

Before testing real users, verify the complete flow on the hosted URL: create order, receive recovery email, open the client link in a second browser, approve and decline separate orders, and confirm the rows/events in Supabase and delivery status in Resend.

Do not commit `.env`, database files, or the Gemini brainstorming transcript.
