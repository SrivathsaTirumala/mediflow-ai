from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.agents import MediFlowAgentService
from backend.app.chroma_store import ChromaStore
from backend.app.config import apply_google_runtime_env, get_settings
from backend.app.genai_compat import apply_google_genai_cleanup_patch
from backend.app.schemas import AnalysisRequest, AnalysisResponse


apply_google_genai_cleanup_patch()
settings = get_settings()
apply_google_runtime_env(settings)
store = ChromaStore(path=str(settings.chroma_persist_dir))
agent_service = MediFlowAgentService(settings=settings, store=store)

app = FastAPI(title="MediFlow AI Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "project": settings.google_cloud_project,
        "location": settings.google_cloud_location,
        "model": settings.gemini_model,
        "a2a_agent_card": settings.safety_agent_card_url,
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    response = await agent_service.analyze(request)
    store.store_case(request.model_dump(), response)
    return AnalysisResponse.model_validate(response)
