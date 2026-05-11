# MediFlow AI

MediFlow AI is now a full-stack healthcare triage demo with:

- a React + Vite frontend
- a FastAPI backend
- Google ADK orchestration
- A2A communication through a remote ADK safety agent
- ChromaDB persistence for guidance snippets and prior case memory
- Vertex AI Gemini configuration through environment variables

## Environment

Copy the values from [.env.example](/home/edgeproc/srivathsa/mediflow-ai/.env.example:1) into a local `.env`.

The backend is configured to use:

- `GOOGLE_GENAI_USE_VERTEXAI=1`
- `GOOGLE_CLOUD_PROJECT=rapid-idiom-488010-b2`
- `GOOGLE_CLOUD_LOCATION=us-central1`
- `GEMINI_MODEL=gemini-2.5-pro-preview`
- `PORT=8000`
- `A2A_SAFETY_PORT=8001`

For local Vertex AI access, Google’s official ADK and Gen AI docs require Application Default Credentials:

```bash
gcloud auth application-default login
```

## Run locally

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
python -m backend.run_local
```

In a second terminal:

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm run dev
```

## Build the frontend

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm run build
```

The production frontend assets are generated in `dist/`.

## Deploy

The Vite frontend is ready for Vercel with [vercel.json](/home/edgeproc/srivathsa/mediflow-ai/vercel.json:1).

The FastAPI + ADK + A2A backend is better suited to a long-running Python host such as Cloud Run, Render, or Railway because it uses:

- a main FastAPI API on port `8000`
- a separate remote A2A ADK service on port `8001`

## Important files

- [src/App.jsx](/home/edgeproc/srivathsa/mediflow-ai/src/App.jsx:1): frontend UI and backend API integration
- [backend/app/api.py](/home/edgeproc/srivathsa/mediflow-ai/backend/app/api.py:1): FastAPI endpoints
- [backend/app/agents.py](/home/edgeproc/srivathsa/mediflow-ai/backend/app/agents.py:1): ADK orchestration and A2A client flow
- [backend/app/a2a_server.py](/home/edgeproc/srivathsa/mediflow-ai/backend/app/a2a_server.py:1): remote safety agent exposed with `to_a2a()`
- [backend/app/chroma_store.py](/home/edgeproc/srivathsa/mediflow-ai/backend/app/chroma_store.py:1): ChromaDB storage

## Note

This project is a healthcare demo and must not be used as medical advice.
