# Deployment

## Backend: Render

Deploy this repository as a Python web service on Render.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

The model files in `saved_summary_model/` must be included in the deployed repository.

Set this Render environment variable:

```text
ALLOWED_ORIGINS=https://text-summarizer.vercel.app
```

Replace the value with your real Vercel frontend URL after Vercel creates it.

## Frontend: Vercel

Deploy the `web/` folder as the Vercel project root. That folder contains only the static frontend files, so Vercel will not try to interpret the repository as a FastAPI app.

Update `config.js` with your real Render backend URL:

```js
window.SUMMARIZER_API_URL = "https://text-summarizer-api.onrender.com";
```

If Render gives you a different service URL, use that exact URL without a trailing slash.

In the Vercel dashboard, set the project root directory to `web`.
