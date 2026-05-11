from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.llm_agent import Agent

from backend.app.config import apply_google_runtime_env, get_settings
from backend.app.genai_compat import apply_google_genai_cleanup_patch


apply_google_genai_cleanup_patch()
settings = get_settings()
apply_google_runtime_env(settings)

safety_agent = Agent(
    model=settings.gemini_model,
    name="mediflow_safety_agent",
    description="Remote safety and escalation reviewer for healthcare triage.",
    instruction=(
        "You review a patient triage payload and return strict JSON only. "
        "Use keys risk_level, care_level, summary, safety_flags, emergency_flags. "
        "Keep the advice conservative and prioritize emergency escalation for chest pain, "
        "shortness of breath, confusion, or combined allergy and breathing symptoms."
    ),
)

a2a_app = to_a2a(
    safety_agent,
    host=settings.a2a_agent_host,
    port=settings.a2a_safety_port,
)
