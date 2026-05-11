SYMPTOM_LABELS = {
    "fever": "Fever",
    "cough": "Cough",
    "sore-throat": "Sore throat",
    "shortness-breath": "Shortness of breath",
    "chest-pain": "Chest pain",
    "headache": "Headache",
    "vomiting": "Vomiting",
    "abdominal-pain": "Abdominal pain",
    "dizziness": "Dizziness",
    "fatigue": "Fatigue",
    "rash": "Rash",
    "confusion": "Confusion",
}

CONDITION_PROTOCOLS = [
    {
        "id": "uri",
        "title": "Upper respiratory viral syndrome",
        "content": "Fever, cough, sore throat, and fatigue often fit a viral upper respiratory illness. Supportive care, hydration, and reassessment within 48 to 72 hours are typical unless red flags emerge.",
    },
    {
        "id": "flu",
        "title": "Influenza-like illness",
        "content": "Fever with cough, headache, and fatigue can align with an influenza-like presentation. Watch hydration status, worsening breathing symptoms, and prolonged fever.",
    },
    {
        "id": "pneumonia",
        "title": "Lower respiratory infection concern",
        "content": "Fever plus cough and shortness of breath raise concern for pneumonia or another lower respiratory issue. Chest pain further increases the need for timely in-person evaluation.",
    },
    {
        "id": "gastro",
        "title": "Gastroenteritis and dehydration",
        "content": "Vomiting, abdominal pain, dizziness, and fatigue can indicate gastroenteritis with dehydration risk. Oral rehydration and electrolyte assessment become more important if symptoms persist.",
    },
    {
        "id": "allergy",
        "title": "Allergic reaction escalation",
        "content": "Rash with breathing difficulty or dizziness can indicate a serious allergic response. Escalate urgently if breathing, swelling, or confusion are involved.",
    },
    {
        "id": "cardio",
        "title": "Cardiopulmonary warning pattern",
        "content": "Chest pain, shortness of breath, confusion, or severe dizziness should be treated as high-risk symptoms requiring urgent or emergency assessment.",
    },
]

FACILITY_CATALOG = {
    "emergency": [
        "CityCare Emergency Center - 1.8 mi",
        "Mercy General Hospital - 3.2 mi",
        "Riverside Trauma Unit - 4.9 mi",
    ],
    "urgent": [
        "Northside Urgent Care - 1.1 mi",
        "QuickVisit Clinic - 2.4 mi",
        "WellSpring Family Care - 2.9 mi",
    ],
    "routine": [
        "Greenfield Primary Care - 0.9 mi",
        "Harbor Family Medicine - 2.0 mi",
        "Downtown Community Clinic - 2.7 mi",
    ],
}
