import { useEffect, useMemo, useState } from "react";

const symptomCatalog = [
  { id: "fever", label: "Fever", weight: 2, cluster: "infectious" },
  { id: "cough", label: "Cough", weight: 2, cluster: "respiratory" },
  { id: "sore-throat", label: "Sore throat", weight: 1, cluster: "infectious" },
  { id: "shortness-breath", label: "Shortness of breath", weight: 5, cluster: "respiratory" },
  { id: "chest-pain", label: "Chest pain", weight: 5, cluster: "critical" },
  { id: "headache", label: "Headache", weight: 1, cluster: "neuro" },
  { id: "vomiting", label: "Vomiting", weight: 2, cluster: "digestive" },
  { id: "abdominal-pain", label: "Abdominal pain", weight: 3, cluster: "digestive" },
  { id: "dizziness", label: "Dizziness", weight: 2, cluster: "neuro" },
  { id: "fatigue", label: "Fatigue", weight: 1, cluster: "general" },
  { id: "rash", label: "Rash", weight: 2, cluster: "allergy" },
  { id: "confusion", label: "Confusion", weight: 5, cluster: "critical" },
];

const conditionCatalog = [
  {
    name: "Viral upper respiratory infection",
    matches: ["fever", "cough", "sore-throat", "fatigue"],
    note: "Pattern aligns with a common self-limited viral illness.",
  },
  {
    name: "Influenza-like illness",
    matches: ["fever", "cough", "headache", "fatigue"],
    note: "Systemic symptoms with cough can fit flu-like illness.",
  },
  {
    name: "Pneumonia concern",
    matches: ["fever", "cough", "shortness-breath", "chest-pain"],
    note: "Breathing symptoms plus fever raise concern for lower respiratory infection.",
  },
  {
    name: "Gastroenteritis / dehydration risk",
    matches: ["vomiting", "abdominal-pain", "dizziness", "fatigue"],
    note: "Digestive symptoms may lead to dehydration and require fluids.",
  },
  {
    name: "Allergic reaction",
    matches: ["rash", "shortness-breath", "dizziness"],
    note: "Rash with breathing symptoms may suggest a significant allergic response.",
  },
  {
    name: "Cardiopulmonary evaluation needed",
    matches: ["chest-pain", "shortness-breath", "dizziness", "fatigue"],
    note: "Chest symptoms warrant urgent professional assessment.",
  },
];

const agentSequence = [
  "Patient Intake Agent",
  "Symptom Understanding Agent",
  "Differential Diagnosis Agent",
  "Medication Recommendation Agent",
  "Drug Interaction & Safety Agent",
  "Emergency Escalation Agent",
  "Nearby Care Recommendation Agent",
  "Test Recommendation Agent",
  "Follow-up Planning Agent",
];

const AGENT_STEP_MS = 1100;

const agentLoadingMessages = {
  "Patient Intake Agent": "Collecting the patient snapshot and validating the submitted context.",
  "Symptom Understanding Agent": "Normalizing symptoms into structured clinical signals.",
  "Differential Diagnosis Agent": "Ranking the most likely condition patterns from the symptom set.",
  "Medication Recommendation Agent": "Preparing supportive medication and self-care guidance.",
  "Drug Interaction & Safety Agent": "Reviewing allergies, contraindications, and medication safety.",
  "Emergency Escalation Agent": "Checking for red-flag symptoms that need urgent escalation.",
  "Nearby Care Recommendation Agent": "Looking up the most relevant nearby care options for this location.",
  "Test Recommendation Agent": "Generating diagnostic test recommendations for the current presentation.",
  "Follow-up Planning Agent": "Building the follow-up plan and final care summary.",
};

const initialForm = {
  name: "",
  age: "",
  gender: "",
  duration: "",
  symptoms: [],
  conditions: [],
  allergies: "",
  location_query: "",
  notes: "",
};

const facilityCatalog = {
  emergency: [
    "CityCare Emergency Center - 1.8 mi",
    "Mercy General Hospital - 3.2 mi",
    "Riverside Trauma Unit - 4.9 mi",
  ],
  urgent: [
    "Northside Urgent Care - 1.1 mi",
    "QuickVisit Clinic - 2.4 mi",
    "WellSpring Family Care - 2.9 mi",
  ],
  routine: [
    "Greenfield Primary Care - 0.9 mi",
    "Harbor Family Medicine - 2.0 mi",
    "Downtown Community Clinic - 2.7 mi",
  ],
};

const womenCareKeywords = [
  "women",
  "woman",
  "maternity",
  "maternal",
  "obstetric",
  "obstetrics",
  "gynecology",
  "gynaecology",
  "gynecologic",
  "mother",
];

function prioritizeFacilitiesForGender(facilities, gender = "") {
  if (gender !== "female") {
    return facilities;
  }
  const womenFocused = facilities.filter((facility) =>
    womenCareKeywords.some((keyword) => facility.toLowerCase().includes(keyword)),
  );
  const remaining = facilities.filter(
    (facility) => !womenCareKeywords.some((keyword) => facility.toLowerCase().includes(keyword)),
  );
  return [...womenFocused, ...remaining];
}

function buildGoogleMapsUrl(query) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

function buildFacilityOptions(facilities, locationQuery = "") {
  return facilities.map((facility) => {
    const name = facility.split(" - ", 1)[0].trim();
    const searchQuery = locationQuery ? `${name}, ${locationQuery}` : name || facility;
    return {
      label: facility,
      googleMapsUrl: buildGoogleMapsUrl(searchQuery),
    };
  });
}

function GoogleMapsPinIcon() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <path
        d="M32 6C18.4 6 7 17.2 7 31c0 16.4 18 31.7 23.2 35.9a2.9 2.9 0 0 0 3.6 0C39 62.7 57 47.4 57 31 57 17.2 45.6 6 32 6Z"
        fill="#ffffff"
      />
      <path d="M32 10c-7.5 0-14 3.2-18.6 8.3L32 37.1l9.4-9.4L46.5 11A24 24 0 0 0 32 10Z" fill="#4285F4" />
      <path d="M13.4 18.3A20.8 20.8 0 0 0 10 31c0 3.2.8 6.4 2.4 9.7L32 37.1Z" fill="#EA4335" />
      <path d="M12.4 40.7c3.4 7 10.2 15.1 19.6 23.3 5.6-4.9 10.3-9.8 13.8-14.6L32 37.1Z" fill="#34A853" />
      <path d="M45.8 49.4C52.7 40 54 34.5 54 31c0-7.5-3.3-14.2-8.6-18.8L32 37.1Z" fill="#FBBC05" />
      <circle cx="32" cy="29" r="9" fill="#ffffff" />
    </svg>
  );
}

const defaultAssessment = {
  risk: "Low",
  summary: "Capture symptoms and run the backend analysis to generate a care summary.",
  differentials: [],
  medicationSuggestions: ["Rest, hydration, and symptom monitoring"],
  safetyFlags: [],
  emergencyFlags: [],
  recommendedTests: [],
  facilities: facilityCatalog.routine,
  facilityOptions: buildFacilityOptions(facilityCatalog.routine),
  followUp: "Re-check symptoms in 72 hours or sooner if anything worsens.",
  agentOutputs: {
    test_recommendation_agent: "No analysis has been run yet.",
    nearby_care_agent: "Live nearby-care discovery has not run yet.",
  },
  memoryContext: [],
  agentStatus: "ready",
};

const loadingAssessment = {
  risk: "Low",
  summary: "Running the multi-agent clinical analysis for this patient profile.",
  differentials: [],
  medicationSuggestions: ["Medication guidance is being prepared."],
  safetyFlags: ["Safety screening is in progress."],
  emergencyFlags: [],
  recommendedTests: [],
  facilities: [],
  facilityOptions: [],
  followUp: "Follow-up planning is being prepared.",
  agentOutputs: {
    test_recommendation_agent: "Test Recommendation Agent is generating its output.",
    nearby_care_agent: "Nearby Care Agent is looking up care options.",
  },
  memoryContext: [],
  agentStatus: "analyzing",
};

function getSafeAgentStatusLabel(agentStatus) {
  if (!agentStatus || agentStatus === "ok") {
    return "Completed";
  }
  if (agentStatus === "analyzing") {
    return "Analyzing";
  }
  if (
    agentStatus.startsWith("a2a-fallback") ||
    agentStatus.startsWith("heuristic-fallback") ||
    agentStatus === "frontend-fallback"
  ) {
    return "Completed";
  }
  return "Completed";
}

function getSafeNearbyCareMessage(message) {
  if (!message) {
    return "Nearby care options were prepared for the selected location.";
  }
  if (message.startsWith("Found ")) {
    return "Nearby care options were found for the selected location.";
  }
  if (message.includes("fallback facilities were used")) {
    return "Nearby care options are currently using fallback facilities for this location.";
  }
  if (message.includes("No location provided")) {
    return "Add a location to enable live nearby-care lookup.";
  }
  return "Nearby care options were prepared for the selected location.";
}

function formatLabel(id) {
  return symptomCatalog.find((item) => item.id === id)?.label ?? id;
}

function scoreCondition(selectedSymptoms, condition) {
  const hits = condition.matches.filter((match) => selectedSymptoms.includes(match)).length;
  if (!hits) {
    return 0;
  }

  return Math.round((hits / condition.matches.length) * 100);
}

function buildAssessment(form) {
  const age = Number(form.age || 0);
  const selectedSymptoms = form.symptoms;
  const allergies = form.allergies
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
  const conditions = new Set(form.conditions);

  const symptomWeight = selectedSymptoms.reduce((sum, symptomId) => {
    const symptom = symptomCatalog.find((item) => item.id === symptomId);
    return sum + (symptom?.weight ?? 0);
  }, 0);

  const emergencyFlags = [];

  if (selectedSymptoms.includes("chest-pain")) {
    emergencyFlags.push("Chest pain requires urgent clinical evaluation.");
  }
  if (selectedSymptoms.includes("shortness-breath")) {
    emergencyFlags.push("Shortness of breath can signal a respiratory emergency.");
  }
  if (selectedSymptoms.includes("confusion")) {
    emergencyFlags.push("Confusion may indicate a neurological or systemic emergency.");
  }
  if (
    selectedSymptoms.includes("rash") &&
    selectedSymptoms.includes("shortness-breath")
  ) {
    emergencyFlags.push("Rash with breathing difficulty may represent a severe allergic reaction.");
  }

  let risk = "Low";
  if (emergencyFlags.length || symptomWeight >= 9 || (age >= 65 && symptomWeight >= 6)) {
    risk = "High";
  } else if (symptomWeight >= 5 || selectedSymptoms.length >= 3) {
    risk = "Moderate";
  }

  const differentials = conditionCatalog
    .map((condition) => ({
      ...condition,
      confidence: scoreCondition(selectedSymptoms, condition),
    }))
    .filter((condition) => condition.confidence > 0)
    .sort((left, right) => right.confidence - left.confidence)
    .slice(0, 3);

  const medicationSuggestions = [];
  const safetyFlags = [];

  if (selectedSymptoms.includes("fever") || selectedSymptoms.includes("headache")) {
    medicationSuggestions.push("Acetaminophen for fever or headache support");
  }
  if (selectedSymptoms.includes("sore-throat") || selectedSymptoms.includes("cough")) {
    medicationSuggestions.push("Warm fluids, throat lozenges, and honey if age appropriate");
  }
  if (selectedSymptoms.includes("vomiting")) {
    medicationSuggestions.push("Oral rehydration fluids in small, frequent sips");
  }
  if (
    medicationSuggestions.length === 0 &&
    selectedSymptoms.length > 0
  ) {
    medicationSuggestions.push("Supportive rest, hydration, and symptom monitoring");
  }

  if (conditions.has("ulcer")) {
    safetyFlags.push("Avoid ibuprofen and other NSAIDs because of ulcer history.");
  }
  if (conditions.has("asthma") && selectedSymptoms.includes("shortness-breath")) {
    safetyFlags.push("Known asthma with breathing symptoms should be reviewed by a clinician promptly.");
  }
  if (conditions.has("pregnancy")) {
    safetyFlags.push("Pregnancy requires clinician review before taking new medications.");
  }
  if (allergies.some((entry) => entry.toLowerCase().includes("penicillin"))) {
    safetyFlags.push("Documented penicillin allergy noted for future prescription decisions.");
  }

  const recommendedTests = [];
  if (selectedSymptoms.includes("fever") && form.duration !== "Today") {
    recommendedTests.push("CBC to evaluate infection or inflammation");
  }
  if (selectedSymptoms.includes("sore-throat") && selectedSymptoms.includes("fever")) {
    recommendedTests.push("Rapid strep test if throat symptoms worsen");
  }
  if (selectedSymptoms.includes("cough") && selectedSymptoms.includes("shortness-breath")) {
    recommendedTests.push("Chest X-ray to assess lower respiratory involvement");
  }
  if (selectedSymptoms.includes("chest-pain")) {
    recommendedTests.push("ECG and clinician-directed cardiac evaluation");
  }
  if (selectedSymptoms.includes("vomiting")) {
    recommendedTests.push("Electrolyte panel if dehydration symptoms persist");
  }

  const careLevel =
    risk === "High" ? "emergency" : risk === "Moderate" ? "urgent" : "routine";
  const facilities = prioritizeFacilitiesForGender(facilityCatalog[careLevel], form.gender);

  let followUp = "Re-check symptoms in 72 hours or sooner if anything worsens.";
  if (risk === "Moderate") {
    followUp = "Arrange follow-up within 24 to 48 hours if symptoms are not improving.";
  }
  if (risk === "High") {
    followUp = "Seek immediate in-person care now. Do not rely on this demo for emergency treatment.";
  }

  const summary = differentials.length
    ? differentials[0].note
    : "Symptoms need clinician review because the pattern is not strongly matched.";

  return {
    age,
    allergies,
    careLevel,
    differentials,
    emergencyFlags,
    facilities,
    facilityOptions: buildFacilityOptions(facilities, form.location_query),
    followUp,
    medicationSuggestions,
    recommendedTests,
    risk,
    safetyFlags,
    summary,
  };
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [isRunning, setIsRunning] = useState(false);
  const [activeAgent, setActiveAgent] = useState(0);
  const [assessment, setAssessment] = useState(defaultAssessment);
  const [pendingAssessment, setPendingAssessment] = useState(null);
  const [requestError, setRequestError] = useState("");
  const [hasRunAnalysis, setHasRunAnalysis] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [selectionErrors, setSelectionErrors] = useState({
    symptoms: "",
    conditions: "",
  });

  useEffect(() => {
    if (!isRunning) {
      return undefined;
    }

    if (activeAgent >= agentSequence.length - 1) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setActiveAgent((current) => Math.min(current + 1, agentSequence.length - 1));
    }, AGENT_STEP_MS);

    return () => window.clearTimeout(timer);
  }, [activeAgent, form, isRunning]);

  useEffect(() => {
    if (!isRunning || !pendingAssessment) {
      return;
    }

    if (activeAgent >= agentSequence.length - 1) {
      setAssessment(pendingAssessment);
      setPendingAssessment(null);
      setActiveAgent(agentSequence.length);
      setIsRunning(false);
    }
  }, [activeAgent, isRunning, pendingAssessment]);

  const selectedSymptoms = useMemo(
    () => form.symptoms.map((symptomId) => formatLabel(symptomId)),
    [form.symptoms],
  );

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function toggleSymptom(symptomId) {
    setForm((current) => {
      const exists = current.symptoms.includes(symptomId);
      const nextSymptoms = exists
        ? current.symptoms.filter((item) => item !== symptomId)
        : [...current.symptoms, symptomId];
      setSelectionErrors((prev) => ({
        ...prev,
        symptoms: nextSymptoms.length ? "" : prev.symptoms,
      }));
      return {
        ...current,
        symptoms: nextSymptoms,
      };
    });
  }

  function toggleCondition(condition) {
    setForm((current) => {
      const exists = current.conditions.includes(condition);
      let nextConditions = current.conditions;

      if (condition === "none-reported") {
        nextConditions = exists ? [] : ["none-reported"];
      } else {
        nextConditions = exists
          ? current.conditions.filter((item) => item !== condition)
          : [...current.conditions.filter((item) => item !== "none-reported"), condition];
      }

      setSelectionErrors((prev) => ({
        ...prev,
        conditions: nextConditions.length ? "" : prev.conditions,
      }));
      return {
        ...current,
        conditions: nextConditions,
      };
    });
  }

  function runAnalysis(event) {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) {
      return;
    }

    const nextErrors = {
      symptoms: form.symptoms.length ? "" : "Select at least one symptom.",
      conditions: form.conditions.length ? "" : "Select at least one pre-existing condition or choose None reported.",
    };
    setSelectionErrors(nextErrors);
    if (nextErrors.symptoms || nextErrors.conditions) {
      return;
    }

    setRequestError("");
    setHasRunAnalysis(true);
    setIsSummaryOpen(false);
    setAssessment(loadingAssessment);
    setPendingAssessment(null);
    setActiveAgent(0);
    setIsRunning(true);
    const apiBaseUrl =
      import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

    fetch(`${apiBaseUrl}/api/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(form),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const data = await response.json();
        const rankedFacilities = prioritizeFacilitiesForGender(
          data.nearby_care || facilityCatalog.routine,
          form.gender,
        );
        const facilityOptions =
          data.nearby_care_options && data.nearby_care_options.length
            ? data.nearby_care_options.map((item) => ({
                label: item.label,
                googleMapsUrl: item.google_maps_url,
              }))
            : buildFacilityOptions(rankedFacilities, form.location_query);
        setPendingAssessment({
          risk: data.risk_level,
          summary: data.summary,
          differentials: data.differentials || [],
          medicationSuggestions: data.medication_support || [],
          safetyFlags: data.safety_flags || [],
          emergencyFlags: data.emergency_flags || [],
          recommendedTests: data.suggested_tests || [],
          facilities: rankedFacilities,
          facilityOptions,
          followUp: data.follow_up,
          agentOutputs: data.agent_outputs || defaultAssessment.agentOutputs,
          memoryContext: data.memory_context || [],
          agentStatus: data.agent_status || "ok",
        });
      })
      .catch((error) => {
        const fallback = buildAssessment(form);
        setPendingAssessment({
          risk: fallback.risk,
          summary: fallback.summary,
          differentials: (fallback.differentials || []).map((item) => ({
            condition: item.name,
            confidence: item.confidence,
            reason: item.note,
          })),
          medicationSuggestions: fallback.medicationSuggestions,
          safetyFlags: fallback.safetyFlags,
          emergencyFlags: fallback.emergencyFlags,
          recommendedTests: fallback.recommendedTests,
          facilities: fallback.facilities,
          facilityOptions: fallback.facilityOptions,
          followUp: fallback.followUp,
          agentOutputs: {
            test_recommendation_agent: fallback.recommendedTests.length
              ? `Recommended diagnostics: ${fallback.recommendedTests.join(", ")}`
              : "No immediate tests were suggested for the current symptom pattern.",
            nearby_care_agent: "Fallback facilities were used because the backend request failed.",
          },
          memoryContext: [],
          agentStatus: "frontend-fallback",
        });
        setRequestError(error.message);
      })
      .finally(() => {
        setActiveAgent((current) => current);
      });
  }

  const riskTone = {
    Low: "risk-low",
    Moderate: "risk-moderate",
    High: "risk-high",
  }[assessment.risk];

  const activeAgentName = agentSequence[Math.min(activeAgent, agentSequence.length - 1)];
  const summaryTitle = isRunning
    ? "Clinical summary pending"
    : assessment.summary;
  const summaryDescription = isRunning
    ? `${activeAgentName} is still working. The final clinical summary will appear after all agents finish.`
    : `Symptoms selected: ${selectedSymptoms.length ? selectedSymptoms.join(", ") : "none"}.`;

  return (
    <div className="page-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <main className="app-shell">
        <section className="hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Browser-based multi-agent care triage</p>
            <h1>MediFlow AI</h1>
            <p className="lead">
              A polished demo that simulates nine coordinated healthcare agents for
              symptom intake, risk escalation, medication safety signals, and follow-up planning.
            </p>
            <div className="hero-badges">
              {/* <span>9 agents</span>
              <span>Local decision logic</span>
              <span>Vercel-ready</span> */}
            </div>
          </div>
          <div className="hero-note">
            <p className="note-title">Important</p>
            <p>
              This is a demo for education and hackathon presentation. It is not a medical diagnosis
              tool and should never replace licensed clinical care.
            </p>
            <p>
              Output is prototype decision support only. For chest pain, breathing difficulty,
              confusion, severe allergy, or rapid worsening, seek emergency care immediately.
            </p>
          </div>
        </section>

        <section className="content-grid">
          <form className="panel intake-panel" onSubmit={runAnalysis}>
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Patient intake</p>
                <h2>Capture the visit snapshot</h2>
              </div>
            </div>

            <div className="field-grid">
              <label className="field">
                <span>Name</span>
                <input
                  value={form.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  placeholder="Taylor Morgan"
                  required
                />
              </label>
              <label className="field">
                <span>Age</span>
                <input
                  value={form.age}
                  onChange={(event) => updateField("age", event.target.value)}
                  inputMode="numeric"
                  placeholder="35"
                  min="0"
                  required
                />
              </label>
              <label className="field">
                <span>Gender</span>
                <select
                  value={form.gender}
                  onChange={(event) => updateField("gender", event.target.value)}
                  required
                >
                  <option value="" disabled>Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </label>
              <label className="field">
                <span>Symptom duration</span>
                <select
                  value={form.duration}
                  onChange={(event) => updateField("duration", event.target.value)}
                  required
                >
                  <option value="" disabled>Select symptom duration</option>
                  <option>Today</option>
                  <option>1-2 days</option>
                  <option>3-5 days</option>
                  <option>5+ days</option>
                </select>
              </label>
              <label className="field field-wide">
                <span>Allergies</span>
                <input
                  value={form.allergies}
                  onChange={(event) => updateField("allergies", event.target.value)}
                  placeholder="Penicillin, peanuts"
                />
              </label>
              <label className="field field-wide">
                <span>Location</span>
                <input
                  value={form.location_query}
                  onChange={(event) => updateField("location_query", event.target.value)}
                  placeholder="Area, City, State, Country"
                  required
                />
              </label>
            </div>

            <div className="subsection">
              <div className="subsection-header">
                <h3>Symptoms</h3>
                <p>Select all symptoms the patient reports today.</p>
              </div>
              <div className="chip-grid">
                {symptomCatalog.map((symptom) => {
                  const selected = form.symptoms.includes(symptom.id);
                  return (
                    <button
                      key={symptom.id}
                      type="button"
                      className={`chip ${selected ? "chip-selected" : ""}`}
                      onClick={() => toggleSymptom(symptom.id)}
                    >
                      {symptom.label}
                    </button>
                  );
                })}
              </div>
              {selectionErrors.symptoms ? (
                <p className="validation-note">{selectionErrors.symptoms}</p>
              ) : null}
            </div>

            <div className="subsection">
              <div className="subsection-header">
                <h3>Pre-existing conditions</h3>
                <p>Select all that apply, or choose None reported.</p>
              </div>
              <div className="checkbox-row">
                {["none-reported", "asthma", "diabetes", "hypertension", "pregnancy", "ulcer"].map((condition) => (
                  <label key={condition} className="checkbox-card">
                    <input
                      type="checkbox"
                      checked={form.conditions.includes(condition)}
                      onChange={() => toggleCondition(condition)}
                    />
                    <span>{condition === "none-reported" ? "None reported" : condition}</span>
                  </label>
                ))}
              </div>
              {selectionErrors.conditions ? (
                <p className="validation-note">{selectionErrors.conditions}</p>
              ) : null}
            </div>

            <label className="field">
              <span>Clinical notes</span>
              <textarea
                rows={4}
                value={form.notes}
                onChange={(event) => updateField("notes", event.target.value)}
                placeholder="Patient reports symptoms are worse at night, no home oxygen, appetite reduced."
              />
            </label>

            <div className="form-footer">
              <button className="primary-button" type="submit">
                Run care analysis
              </button>
            </div>
          </form>

          {hasRunAnalysis ? (
            <div className="results-column">
              <section className="panel orchestration-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">Agent orchestration</p>
                    <h2>Workflow status</h2>
                  </div>
                  <span className="status-pill">
                    {isRunning ? "Analyzing" : getSafeAgentStatusLabel(assessment.agentStatus)}
                  </span>
                </div>
                <div className="agent-list">
                  {agentSequence.map((agent, index) => {
                    const state =
                      activeAgent > index
                        ? "done"
                        : activeAgent === index && isRunning
                          ? "active"
                          : "idle";

                    return (
                      <div key={agent} className={`agent-row agent-${state}`}>
                        <span className="agent-index">{index + 1}</span>
                        <div>
                          <p>{agent}</p>
                          <small>
                            {state === "done"
                              ? "Completed"
                              : state === "active"
                                ? "Running now"
                                : "Queued"}
                          </small>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {!isRunning ? (
                <section className="panel summary-launch-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">Live assessment</p>
                      <h2>Clinical summary ready</h2>
                    </div>
                    <span className={`risk-badge ${riskTone}`}>{assessment.risk} risk</span>
                  </div>
                  <p className="summary-launch-copy">
                    The agent workflow has finished. Open the preview to review the full clinical summary.
                  </p>
                  <div className="form-footer">
                    <button
                      className="primary-button"
                      type="button"
                      onClick={() => setIsSummaryOpen(true)}
                    >
                      View clinical summary
                    </button>
                  </div>
                </section>
              ) : null}
            </div>
          ) : null}
        </section>
      </main>

      {isSummaryOpen ? (
        <div className="modal-backdrop" onClick={() => setIsSummaryOpen(false)}>
          <div
            className="modal-shell"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Clinical summary preview"
          >
            <div className="panel summary-panel modal-panel">
              <div className="panel-header">
                <div>
                  <p className="panel-kicker">Live assessment</p>
                  <h2>Clinical summary</h2>
                </div>
                <div className="modal-actions">
                  <span className={`risk-badge ${riskTone}`}>{assessment.risk} risk</span>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setIsSummaryOpen(false)}
                  >
                    Close
                  </button>
                </div>
              </div>

              <div className="summary-grid">
                {requestError ? (
                  <article className="card alert-card">
                    <p className="card-label">Backend status</p>
                    <p>
                      Live agent output was partially unavailable, so the application used its
                      built-in fallback logic for a safe response.
                    </p>
                    <p>Please review the summary as decision-support output only.</p>
                  </article>
                ) : null}
                <article className="card emphasis-card">
                  <p className="card-label">Lead interpretation</p>
                  <h3>{summaryTitle}</h3>
                  <p>{summaryDescription}</p>
                </article>

                <article className="card alert-card">
                  <p className="card-label">Escalation signals</p>
                  {assessment.emergencyFlags.length ? (
                    <ul>
                      {assessment.emergencyFlags.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No red-flag emergency pattern detected from the current symptom set.</p>
                  )}
                </article>

                <article className="card">
                  <p className="card-label">Top differentials</p>
                  {assessment.differentials.length ? (
                    <ul>
                      {assessment.differentials.map((item) => (
                        <li key={item.condition}>
                          <strong>{item.condition}</strong>
                          <span>{item.confidence}% confidence</span>
                          <span>{item.reason}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No strong pattern match yet. Consider in-person review.</p>
                  )}
                </article>

                <article className="card">
                  <p className="card-label">Safety guardrails</p>
                  {assessment.safetyFlags.length ? (
                    <ul>
                      {assessment.safetyFlags.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No extra medication cautions surfaced from the selected inputs.</p>
                  )}
                </article>

                <article className="card">
                  <p className="card-label">Suggested diagnostics</p>
                  {assessment.recommendedTests.length ? (
                    <ul>
                      {assessment.recommendedTests.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No tests suggested for the current low-signal symptom pattern.</p>
                  )}
                </article>

                <article className="card">
                  <p className="card-label">Test Recommendation Agent</p>
                  <p>{assessment.agentOutputs?.test_recommendation_agent}</p>
                </article>

                <article className="card">
                  <p className="card-label">Medication support</p>
                  <ul>
                    {assessment.medicationSuggestions.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>

                <article className="card">
                  <p className="card-label">Follow-up plan</p>
                  <p>{assessment.followUp}</p>
                </article>

                <article className="card">
                  <p className="card-label">Nearby care options</p>
                  <ul>
                    {assessment.facilityOptions.map((item) => (
                      <li key={item.label} className="facility-item">
                        <span className="facility-name">{item.label}</span>
                        <a
                          className="facility-link"
                          href={item.googleMapsUrl}
                          target="_blank"
                          rel="noreferrer"
                          aria-label={`Open ${item.label} in Google Maps`}
                          title="Open in Google Maps"
                        >
                          <GoogleMapsPinIcon />
                        </a>
                      </li>
                    ))}
                  </ul>
                </article>

                <article className="card">
                      <p className="card-label">Nearby Care Agent</p>
                      <p>{getSafeNearbyCareMessage(assessment.agentOutputs?.nearby_care_agent)}</p>
                    </article>

                <article className="card">
                  <p className="card-label">Chroma context</p>
                  {assessment.memoryContext.length ? (
                    <ul>
                      {assessment.memoryContext.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No prior case or guideline context returned yet.</p>
                  )}
                </article>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
