# ACE Readiness — Streamlit prototype

A working prototype of the ACE Readiness portal: a pricing calculator and a
sample deliverables dashboard, built for the Monetising Pre-Sales hackathon.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy it for free on Streamlit Community Cloud

1. Create a new GitHub repo (public or private) and push these two files
   to it: `app.py` and `requirements.txt`.
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click **"New app"**, pick the repo, branch (usually `main`), and set the
   main file path to `app.py`.
4. Click **Deploy**. Streamlit installs `requirements.txt` and starts the
   app automatically.
5. You'll get a public URL like `https://your-app-name.streamlit.app` —
   share that with anyone; no login is needed to view it.

Any time you push a new commit to the repo, the live app redeploys
automatically.
