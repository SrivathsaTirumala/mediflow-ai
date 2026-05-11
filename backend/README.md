# MediFlow AI Backend

This backend uses:

- `FastAPI` for the application API
- `google-adk` for local agent orchestration
- `RemoteA2aAgent` plus `to_a2a()` for ADK A2A communication
- `ChromaDB` for persistent knowledge and case storage
- Gemini on Vertex AI through the environment variables in the repo root `.env`

## Expected environment

Use the root `.env.example` values:

```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=rapid-idiom-488010-b2
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-pro-preview
PORT=8000
A2A_SAFETY_PORT=8001
```

For local Vertex AI auth, Google’s ADK and Gen AI docs require Application Default Credentials:

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

Main API:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/analyze`

Remote A2A agent card:

- `http://127.0.0.1:8001/.well-known/agent-card.json`
