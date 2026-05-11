from __future__ import annotations

from backend.app.care_discovery import build_nearby_care_options, prioritize_facilities_for_gender
from backend.app.knowledge import FACILITY_CATALOG, SYMPTOM_LABELS
from backend.app.schemas import AnalysisRequest


CONDITION_PATTERNS = [
    (
        "Viral upper respiratory infection",
        ["fever", "cough", "sore-throat", "fatigue"],
        "The symptom mix fits a common upper respiratory pattern with supportive care needs.",
    ),
    (
        "Influenza-like illness",
        ["fever", "cough", "headache", "fatigue"],
        "Systemic symptoms with cough suggest a flu-like pattern that still needs monitoring.",
    ),
    (
        "Pneumonia concern",
        ["fever", "cough", "shortness-breath", "chest-pain"],
        "Breathing symptoms alongside fever raise concern for lower respiratory involvement.",
    ),
    (
        "Gastroenteritis / dehydration risk",
        ["vomiting", "abdominal-pain", "dizziness", "fatigue"],
        "Digestive symptoms plus dizziness can reflect dehydration risk.",
    ),
    (
        "Allergic reaction",
        ["rash", "shortness-breath", "dizziness"],
        "Rash with breathing issues increases concern for an allergic process.",
    ),
]

SYMPTOM_WEIGHTS = {
    "fever": 2,
    "cough": 2,
    "sore-throat": 1,
    "shortness-breath": 5,
    "chest-pain": 5,
    "headache": 1,
    "vomiting": 2,
    "abdominal-pain": 3,
    "dizziness": 2,
    "fatigue": 1,
    "rash": 2,
    "confusion": 5,
}


def score_condition(selected: list[str], pattern: list[str]) -> int:
    hits = len([item for item in pattern if item in selected])
    if not hits:
        return 0
    return round((hits / len(pattern)) * 100)


def build_heuristic_assessment(payload: AnalysisRequest) -> dict:
    symptoms = payload.symptoms
    age = payload.age or 0
    conditions = set(payload.conditions)
    allergies = [item.strip().lower() for item in payload.allergies.split(",") if item.strip()]

    symptom_weight = sum(SYMPTOM_WEIGHTS.get(item, 0) for item in symptoms)
    emergency_flags: list[str] = []
    safety_flags: list[str] = []

    if "chest-pain" in symptoms:
        emergency_flags.append("Chest pain requires urgent in-person assessment.")
    if "shortness-breath" in symptoms:
        emergency_flags.append("Shortness of breath can indicate a respiratory emergency.")
    if "confusion" in symptoms:
        emergency_flags.append("Confusion is a high-risk symptom and should be escalated.")
    if "rash" in symptoms and "shortness-breath" in symptoms:
        emergency_flags.append("Rash with breathing difficulty may represent a severe allergic reaction.")

    risk_level = "Low"
    if emergency_flags or symptom_weight >= 9 or (age >= 65 and symptom_weight >= 6):
        risk_level = "High"
    elif symptom_weight >= 5 or len(symptoms) >= 3:
        risk_level = "Moderate"

    care_level = "routine"
    if risk_level == "High":
        care_level = "emergency"
    elif risk_level == "Moderate":
        care_level = "urgent"

    if "ulcer" in conditions:
        safety_flags.append("Avoid ibuprofen and other NSAIDs because of ulcer history.")
    if "pregnancy" in conditions:
        safety_flags.append("Pregnancy requires clinician review before using new medications.")
    if "asthma" in conditions and "shortness-breath" in symptoms:
        safety_flags.append("Known asthma with breathing symptoms should be reviewed promptly.")
    if any("penicillin" in allergy for allergy in allergies):
        safety_flags.append("Penicillin allergy noted for future prescribing decisions.")

    medication_support: list[str] = []
    if "fever" in symptoms or "headache" in symptoms:
        medication_support.append("Acetaminophen for fever or headache support")
    if "cough" in symptoms or "sore-throat" in symptoms:
        medication_support.append("Warm fluids, throat lozenges, and honey if age appropriate")
    if "vomiting" in symptoms:
        medication_support.append("Oral rehydration fluids in small, frequent sips")
    if not medication_support:
        medication_support.append("Rest, hydration, and symptom monitoring")

    suggested_tests: list[str] = []
    if "fever" in symptoms and payload.duration != "Today":
        suggested_tests.append("CBC to evaluate infection or inflammation")
    if "sore-throat" in symptoms and "fever" in symptoms:
        suggested_tests.append("Rapid strep test if throat symptoms worsen")
    if "cough" in symptoms and "shortness-breath" in symptoms:
        suggested_tests.append("Chest X-ray to assess lower respiratory involvement")
    if "chest-pain" in symptoms:
        suggested_tests.append("ECG and clinician-directed cardiac evaluation")
    if "vomiting" in symptoms:
        suggested_tests.append("Electrolyte panel if dehydration symptoms persist")

    follow_up = "Re-check symptoms in 72 hours or sooner if anything worsens."
    if risk_level == "Moderate":
        follow_up = "Arrange follow-up within 24 to 48 hours if symptoms are not improving."
    if risk_level == "High":
        follow_up = "Seek immediate in-person care now. Do not rely on software for emergency treatment."

    nearby_care = prioritize_facilities_for_gender(FACILITY_CATALOG[care_level], payload.gender)

    differentials = []
    for name, pattern, reason in CONDITION_PATTERNS:
        confidence = score_condition(symptoms, pattern)
        if confidence:
            differentials.append(
                {
                    "condition": name,
                    "confidence": confidence,
                    "reason": reason,
                }
            )
    differentials.sort(key=lambda item: item["confidence"], reverse=True)
    differentials = differentials[:3]

    summary = (
        differentials[0]["reason"]
        if differentials
        else "Symptoms need clinician review because the pattern is not strongly matched."
    )

    return {
        "risk_level": risk_level,
        "care_level": care_level,
        "summary": summary,
        "differentials": differentials,
        "medication_support": medication_support,
        "safety_flags": safety_flags,
        "emergency_flags": emergency_flags,
        "suggested_tests": suggested_tests,
        "nearby_care": nearby_care,
        "nearby_care_options": build_nearby_care_options(
            nearby_care,
            payload.location_query,
        ),
        "follow_up": follow_up,
        "reasoning": f"Symptoms reviewed: {', '.join(SYMPTOM_LABELS.get(item, item) for item in symptoms) or 'none'}.",
        "agent_outputs": {
            "test_recommendation_agent": (
                "Recommended diagnostics: " + ", ".join(suggested_tests)
                if suggested_tests
                else "No immediate tests were suggested for the current symptom pattern."
            ),
            "nearby_care_agent": "Fallback facilities were used because live location lookup was not requested.",
        },
    }
