from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.app.care_discovery import build_nearby_care_options, discover_nearby_care
from backend.app.chroma_store import ChromaStore
from backend.app.config import Settings
from backend.app.knowledge import FACILITY_CATALOG
from backend.app.logic import build_heuristic_assessment
from backend.app.schemas import AnalysisRequest


APP_NAME = "mediflow-ai"


def has_vertex_credentials() -> bool:
    if os.getenv("MEDIFLOW_FORCE_HEURISTIC", "0") == "1":
        return False
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and Path(credentials_path).exists():
        return True
    adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    return adc_path.exists()


def extract_json_payload(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def extract_text_from_event(event) -> str:
    if not getattr(event, "content", None):
        return ""
    parts = getattr(event.content, "parts", []) or []
    text_parts = [
        part.text
        for part in parts
        if getattr(part, "text", None) and not getattr(part, "thought", False)
    ]
    return "".join(text_parts).strip()


async def ensure_session(
    session_service: InMemorySessionService,
    app_name: str,
    user_id: str,
    session_id: str,
) -> None:
    existing = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if existing is None:
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )


async def run_agent_for_json(runner: Runner, prompt: str, user_id: str) -> dict:
    session_id = str(uuid4())
    runner_app_name = getattr(runner, "app_name", None) or getattr(runner, "_app_name", APP_NAME)
    await ensure_session(
        runner.session_service,
        app_name=runner_app_name,
        user_id=user_id,
        session_id=session_id,
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_text = ""
    best_text = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        text = extract_text_from_event(event)
        if text and len(text) >= len(best_text):
            best_text = text
        if event.is_final_response() and text:
            final_text = text

    parsed_text = final_text or best_text
    if not parsed_text:
        raise ValueError("Agent returned no final text response.")
    return extract_json_payload(parsed_text)


def build_remote_safety_agent(settings: Settings) -> RemoteA2aAgent:
    return RemoteA2aAgent(
        name="mediflow_safety_remote",
        description="Remote A2A safety reviewer for risk escalation, emergency flags, and medication cautions.",
        agent_card=settings.safety_agent_card_url,
        timeout=5.0,
        use_legacy=False,
    )


def build_local_orchestrator(settings: Settings, store: ChromaStore) -> Agent:
    def search_medical_knowledge(query: str) -> list[str]:
        return store.search_guidance(query=query, limit=3)

    def search_prior_cases(query: str) -> list[str]:
        return store.search_cases(query=query, limit=2)

    def get_nearby_care(care_level: str) -> list[str]:
        return FACILITY_CATALOG.get(care_level, FACILITY_CATALOG["routine"])

    symptom_agent = Agent(
        model=settings.gemini_model,
        name="symptom_pattern_agent",
        description="Identifies the most likely symptom patterns and patient-friendly explanation.",
        instruction=(
            "You analyze symptom combinations for non-diagnostic triage support. "
            "Respond in concise plain language and focus on likely patterns, not final diagnosis."
        ),
    )

    follow_up_agent = Agent(
        model=settings.gemini_model,
        name="follow_up_planning_agent",
        description="Suggests tests, nearby care, and next-step timelines.",
        instruction=(
            "You produce follow-up plans, nearby care recommendations, and suggested diagnostics. "
            "Keep guidance conservative and safety-first."
        ),
        tools=[get_nearby_care],
    )

    return Agent(
        model=settings.gemini_model,
        name="mediflow_orchestrator",
        description="Coordinates symptom review, context retrieval, and follow-up planning for MediFlow AI.",
        instruction=(
            "You are MediFlow AI's orchestration agent. "
            "Use the provided safety assessment, knowledge context, and prior cases to prepare a triage summary. "
            "Return strict JSON only with keys: "
            "risk_level, care_level, summary, differentials, medication_support, safety_flags, emergency_flags, "
            "suggested_tests, nearby_care, follow_up, reasoning. "
            "Each differential must contain condition, confidence, and reason. "
            "Never recommend prescription drugs. Only provide OTC or supportive-care guidance."
        ),
        sub_agents=[symptom_agent, follow_up_agent],
        tools=[search_medical_knowledge, search_prior_cases, get_nearby_care],
    )


class MediFlowAgentService:
    def __init__(self, settings: Settings, store: ChromaStore):
        self.settings = settings
        self.store = store
        self.orchestrator = build_local_orchestrator(settings, store)
        self.safety_remote = build_remote_safety_agent(settings)
        self.orchestrator_runner = Runner(
            app_name=APP_NAME,
            agent=self.orchestrator,
            session_service=InMemorySessionService(),
        )
        self.safety_runner = Runner(
            app_name=f"{APP_NAME}-a2a-safety-client",
            agent=self.safety_remote,
            session_service=InMemorySessionService(),
        )

    async def invoke_remote_safety(self, payload: AnalysisRequest) -> dict:
        prompt = (
            "Review this patient payload for safety and escalation. "
            "Return strict JSON with keys risk_level, care_level, summary, safety_flags, emergency_flags.\n\n"
            f"{payload.model_dump_json(indent=2)}"
        )
        return await run_agent_for_json(self.safety_runner, prompt=prompt, user_id="mediflow-safety")

    async def analyze(self, payload: AnalysisRequest) -> dict:
        heuristic = build_heuristic_assessment(payload)
        symptom_query = " ".join(payload.symptoms) or payload.notes or "general triage"
        knowledge_hits = self.store.search_guidance(symptom_query, limit=3)
        prior_cases = self.store.search_cases(symptom_query, limit=2)
        nearby_care = heuristic["nearby_care"]
        nearby_care_note = heuristic.get("agent_outputs", {}).get(
            "nearby_care_agent",
            "Fallback facilities were used.",
        )

        try:
            nearby_care, nearby_care_note = await discover_nearby_care(
                payload.location_query,
                heuristic["care_level"],
                payload.gender,
            )
        except Exception as exc:  # pragma: no cover - network fallback
            nearby_care_note = f"Live nearby-care lookup failed, so fallback facilities were used: {exc}"

        if not has_vertex_credentials():
            heuristic["memory_context"] = knowledge_hits + prior_cases
            heuristic["nearby_care"] = nearby_care
            heuristic["nearby_care_options"] = build_nearby_care_options(
                nearby_care,
                payload.location_query,
            )
            heuristic["agent_outputs"]["nearby_care_agent"] = nearby_care_note
            heuristic["session_id"] = str(uuid4())
            heuristic["used_a2a"] = False
            heuristic["agent_status"] = "heuristic-fallback: Vertex AI credentials not configured"
            return heuristic

        safety_data = None
        used_a2a = False
        agent_status = "ok"

        try:
            safety_data = await self.invoke_remote_safety(payload)
            used_a2a = True
        except Exception as exc:  # pragma: no cover - live dependency fallback
            safety_data = {
                "risk_level": heuristic["risk_level"],
                "care_level": heuristic["care_level"],
                "summary": heuristic["summary"],
                "safety_flags": heuristic["safety_flags"],
                "emergency_flags": heuristic["emergency_flags"],
            }
            agent_status = f"a2a-fallback: {exc}"

        prompt = (
            "Prepare a structured triage response for the following patient.\n\n"
            f"Patient input:\n{payload.model_dump_json(indent=2)}\n\n"
            f"Heuristic baseline:\n{json.dumps(heuristic, indent=2)}\n\n"
            f"Remote safety assessment:\n{json.dumps(safety_data, indent=2)}\n\n"
            f"Nearby care discovery:\n{json.dumps({'nearby_care': nearby_care, 'note': nearby_care_note}, indent=2)}\n\n"
            f"Knowledge context:\n{json.dumps(knowledge_hits, indent=2)}\n\n"
            f"Similar prior cases:\n{json.dumps(prior_cases, indent=2)}"
        )

        try:
            response = await run_agent_for_json(
                self.orchestrator_runner,
                prompt=prompt,
                user_id="mediflow-api",
            )
            response["agent_status"] = agent_status
        except Exception as exc:  # pragma: no cover - live dependency fallback
            response = dict(heuristic)
            response["agent_status"] = f"heuristic-fallback: {exc}"

        response["risk_level"] = safety_data.get("risk_level", response.get("risk_level", heuristic["risk_level"]))
        response["care_level"] = safety_data.get("care_level", response.get("care_level", heuristic["care_level"]))
        response["safety_flags"] = list(
            dict.fromkeys(safety_data.get("safety_flags", []) + response.get("safety_flags", []))
        )
        response["emergency_flags"] = list(
            dict.fromkeys(safety_data.get("emergency_flags", []) + response.get("emergency_flags", []))
        )
        response["nearby_care"] = nearby_care
        response["nearby_care_options"] = build_nearby_care_options(
            nearby_care,
            payload.location_query,
        )
        response["agent_outputs"] = response.get("agent_outputs", {})
        response["agent_outputs"]["nearby_care_agent"] = nearby_care_note
        response["agent_outputs"]["test_recommendation_agent"] = (
            "Recommended diagnostics: " + ", ".join(response.get("suggested_tests", []))
            if response.get("suggested_tests")
            else "No immediate tests were suggested for the current symptom pattern."
        )
        response["memory_context"] = knowledge_hits + prior_cases
        response["session_id"] = str(uuid4())
        response["used_a2a"] = used_a2a
        return response
