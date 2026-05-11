from __future__ import annotations

import math
from typing import Any
from urllib.parse import quote_plus

import httpx

from backend.app.knowledge import FACILITY_CATALOG


OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]

WOMEN_CARE_KEYWORDS = (
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
)


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_miles * c


def _build_overpass_query(latitude: float, longitude: float, radius_meters: int) -> str:
    return f"""
    [out:json][timeout:12];
    (
      node["amenity"~"hospital|clinic|doctors"](around:{radius_meters},{latitude},{longitude});
      way["amenity"~"hospital|clinic|doctors"](around:{radius_meters},{latitude},{longitude});
      relation["amenity"~"hospital|clinic|doctors"](around:{radius_meters},{latitude},{longitude});
    );
    out center 10;
    """


def _facility_radius(care_level: str) -> int:
    if care_level == "emergency":
        return 7000
    if care_level == "urgent":
        return 4500
    return 3000


def build_google_maps_url(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def _is_women_focused_text(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in WOMEN_CARE_KEYWORDS)


def prioritize_facilities_for_gender(
    facilities: list[str],
    gender: str = "",
) -> list[str]:
    if gender.strip().lower() != "female":
        return facilities
    women_focused = [facility for facility in facilities if _is_women_focused_text(facility)]
    remaining = [facility for facility in facilities if not _is_women_focused_text(facility)]
    return women_focused + remaining


def build_nearby_care_options(
    facilities: list[str],
    location_query: str = "",
) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    location_suffix = f", {location_query.strip()}" if location_query.strip() else ""
    for facility in facilities:
        name = facility.split(" - ", 1)[0].strip()
        search_query = f"{name}{location_suffix}" if name else facility
        options.append(
            {
                "label": facility,
                "google_maps_url": build_google_maps_url(search_query),
            }
        )
    return options


async def _fetch_overpass_elements(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    care_level: str,
) -> tuple[list[dict[str, Any]], str]:
    base_radius = _facility_radius(care_level)
    radius_attempts = [base_radius, max(1500, base_radius // 2), 1200]
    last_error = "No facility results returned."

    for endpoint in OVERPASS_ENDPOINTS:
        for radius in radius_attempts:
            try:
                response = await client.post(
                    endpoint,
                    content=_build_overpass_query(latitude, longitude, radius),
                )
                response.raise_for_status()
                payload = response.json()
                elements: list[dict[str, Any]] = payload.get("elements", [])
                if elements:
                    return elements, (
                        f"Live nearby-care results came from {endpoint} within a {radius}m search radius."
                    )
                last_error = f"No facilities were returned from {endpoint} for radius {radius}m."
            except httpx.HTTPStatusError as exc:
                last_error = f"{endpoint} returned {exc.response.status_code}."
            except Exception as exc:  # pragma: no cover - network variability
                last_error = f"{endpoint} failed: {exc}"

    return [], last_error


async def discover_nearby_care(
    location_query: str,
    care_level: str,
    gender: str = "",
) -> tuple[list[str], str]:
    if not location_query.strip():
        return (
            prioritize_facilities_for_gender(FACILITY_CATALOG[care_level], gender),
            "No location provided, so fallback facilities were used.",
        )

    headers = {"User-Agent": "mediflow-ai/1.0 (care-discovery)"}
    async with httpx.AsyncClient(timeout=12.0, headers=headers) as client:
        geo_response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": location_query,
                "format": "jsonv2",
                "limit": 1,
            },
        )
        geo_response.raise_for_status()
        geocoded = geo_response.json()
        if not geocoded:
            return prioritize_facilities_for_gender(FACILITY_CATALOG[care_level], gender), (
                f'No geocoding result was found for "{location_query}", so fallback facilities were used.'
            )

        latitude = float(geocoded[0]["lat"])
        longitude = float(geocoded[0]["lon"])
        elements, source_note = await _fetch_overpass_elements(
            client,
            latitude,
            longitude,
            care_level,
        )

    facilities: list[tuple[int, float, str]] = []
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        element_lat = element.get("lat") or element.get("center", {}).get("lat")
        element_lon = element.get("lon") or element.get("center", {}).get("lon")
        if element_lat is None or element_lon is None:
            continue
        miles = _haversine_miles(latitude, longitude, float(element_lat), float(element_lon))
        amenity = tags.get("amenity", "facility")
        descriptor = " ".join(
            str(tags.get(key, ""))
            for key in ("name", "healthcare:speciality", "healthcare", "description", "operator")
            if tags.get(key)
        )
        gender_priority = 0 if gender.strip().lower() == "female" and _is_women_focused_text(descriptor) else 1
        facilities.append((gender_priority, miles, f"{name} - {miles:.1f} mi ({amenity})"))

    facilities.sort(key=lambda item: (item[0], item[1]))
    formatted = [item[2] for item in facilities[:5]]
    if formatted:
        return (
            formatted,
            f'Found {len(formatted)} live nearby care options near "{location_query}". {source_note}',
        )

    return prioritize_facilities_for_gender(FACILITY_CATALOG[care_level], gender), (
        f'Live nearby-care lookup could not return facilities near "{location_query}", so fallback facilities were used. {source_note}'
    )
