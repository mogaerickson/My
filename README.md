# My Dream Journey — Stage 1

A Flask + SQLite fantasy-adventure web prototype with account registration, login,
character creation, and a starter adventure page.

## Run locally

1. Install Python 3.10+.
2. In the project folder, run:

   ```bash
   python -m venv .venv
   ```

3. Activate the environment:

   - Windows: `.venv\\Scripts\\activate`
   - macOS/Linux: `source .venv/bin/activate`

4. Install dependencies and run:

   ```bash
   pip install -r requirements.txt
   python app.py
   ```

5. Open `http://127.0.0.1:5000`.

## Environment variables

- `SECRET_KEY`: Set a long, random secret in deployment. The built-in fallback is
  for local development only.
- `DATABASE_PATH`: Optional path to a SQLite database file for local use.

## Deployment note

The included `vercel.json` prepares the Flask app for Vercel's Python runtime.
However, SQLite stored in the app's local filesystem is **not durable on Vercel's
serverless runtime**. Accounts and characters may not persist reliably between
deployments/instances. Before using this as a real hosted app, connect a persistent
hosted database (for example, a managed PostgreSQL service) and set its connection
details as environment variables. This package does not configure an external DB.

This is a Stage 1 prototype, not a finished multiplayer game.
