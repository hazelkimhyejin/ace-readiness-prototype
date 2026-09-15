# ACE Readiness — Streamlit prototype

A working prototype of the full ACE Readiness flow: sign in, upload real site
documents, run an assessment, and see results derived from what you actually
uploaded. Built for the Monetising Pre-Sales hackathon.

## What actually works vs. what's simulated

- **Login** — a working sign-in screen and session. It accepts any work email
  and password to keep the demo frictionless; it is *not* production
  authentication (no password hashing, no user database). Swap in
  `streamlit-authenticator` or an SSO provider before using this outside a demo.
- **Document upload** — fully functional drag-and-drop for M&E drawings,
  O&M documents (PDF/images) and a BMS point export (CSV/Excel).
- **Processing** — real: PDF page counts and BMS row counts are read directly
  from your uploaded files. What's simulated: the Brick-ontology modelling,
  BMS reconciliation and optimisation estimate are a deterministic model
  seeded from your inputs, not OctaiPipe's production Planner engine — that
  lives in Planner's own backend and isn't something a prototype can call.
- **Session history** — each signed-in session keeps a list of assessments
  you've run, browsable from the sidebar. This resets on logout or when the
  app restarts — there's no database. Ask if you want a persistent version
  (e.g. backed by Streamlit's `st.connection` to a real database).
- **Report export** — a real Markdown report you can download per assessment.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy it for free on Streamlit Community Cloud

1. Push `app.py` and `requirements.txt` to a GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **"New app"**, pick the repo/branch, set the main file to `app.py`.
4. Click **Deploy** — you'll get a public URL like
   `https://your-app-name.streamlit.app`.

Every push to the repo redeploys the live app automatically.
