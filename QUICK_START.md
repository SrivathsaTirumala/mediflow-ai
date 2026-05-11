# MediFlow AI Quick Start

This repo now contains:

- a Vite frontend
- a FastAPI backend
- Google ADK orchestration
- a separate A2A safety agent
- ChromaDB persistence

## 1. Prepare the environment

Create `.env` from `.env.example`, then authenticate for Vertex AI locally:

```bash
gcloud auth application-default login
```

## 2. Start the backend

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
python -m backend.run_local
```

This launches:

- FastAPI on `http://127.0.0.1:8000`
- A2A safety agent on `http://127.0.0.1:8001`

## 3. Start the frontend

In a second terminal:

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm run dev
```

## 4. Build the frontend

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm run build
```

## 5. Deploy

Frontend:

- ready for Vercel
- build command: `npm run build`
- output directory: `dist`

Backend:

- uses a long-running FastAPI API plus a separate A2A service
- better deployed to Cloud Run, Render, Railway, or another Python host

## 6. Suggested test cases

1. Moderate respiratory visit
   - Age: `35`
   - Symptoms: `Fever`, `Cough`, `Sore throat`
   - Duration: `3-5 days`

2. High-risk escalation
   - Age: `45`
   - Symptoms: `Fever`, `Cough`, `Chest pain`, `Shortness of breath`
   - Duration: `5+ days`

3. Safety warning
   - Age: `28`
   - Symptoms: `Fever`, `Headache`
   - Allergies: `Penicillin`
