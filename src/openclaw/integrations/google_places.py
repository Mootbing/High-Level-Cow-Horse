"""Google Places API (New) client — competitor discovery."""

from __future__ import annotations

import math

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

PLACES_BASE = "https://places.googleapis.com/v1"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.types",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.primaryType",
    "places.primaryTypeDisplayName",
])


async def search_nearby_competitors(
    query: str,
    latitude: float,
    longitude: float,
    radius_m: float = 5000.0,
    max_results: int = 20,
) -> list[dict]:
    """Search for businesses near a location using Text Search (New).

    Returns list of place dicts with normalized fields.
    """
    url = f"{PLACES_BASE}/places:searchText"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
        "Content-Type": "application/json",
    }
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_m,
            }
        },
        "maxResultCount": max_results,
        "languageCode": "en",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(
                "places_search_error",
                status=response.status_code,
                body=response.text[:500],
            )
            response.raise_for_status()
        data = response.json()

    places: list[dict] = []
    for place in data.get("places", []):
        loc = place.get("location", {})
        places.append({
            "place_id": place.get("id", ""),
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "rating": place.get("rating"),
            "review_count": place.get("userRatingCount", 0),
            "price_level": place.get("priceLevel"),
            "types": place.get("types", []),
            "primary_type": place.get("primaryType", ""),
            "primary_type_display": (
                place.get("primaryTypeDisplayName", {}).get("text", "")
            ),
            "website": place.get("websiteUri"),
            "google_maps_url": place.get("googleMapsUri"),
        })

    logger.info("places_search_complete", query=query[:80], results=len(places))
    return places


async def get_place_details(place_id: str) -> dict:
    """Get detailed info for a single place."""
    detail_mask = ",".join([
        "id",
        "displayName",
        "formattedAddress",
        "location",
        "rating",
        "userRatingCount",
        "priceLevel",
        "types",
        "websiteUri",
        "googleMapsUri",
        "currentOpeningHours",
        "reviews",
        "primaryType",
        "primaryTypeDisplayName",
    ])
    url = f"{PLACES_BASE}/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": detail_mask,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(
                "place_details_error",
                status=response.status_code,
                body=response.text[:500],
            )
            response.raise_for_status()
        return response.json()


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float,
) -> float:
    """Calculate distance in meters between two lat/lng points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Canonical price level enum → numeric for comparison
PRICE_LEVEL_MAP: dict[str, int] = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


def score_relevance(
    place: dict,
    prospect_lat: float,
    prospect_lng: float,
    prospect_types: list[str],
    prospect_price_level: str | None,
    radius_m: float = 5000.0,
) -> float:
    """Score how relevant a competitor is (0.0–1.0).

    Weights:
      - type_match:    0.40  — overlap in business types
      - proximity:     0.25  — closer = more relevant
      - price_match:   0.20  — same price tier
      - review_volume: 0.15  — similar scale (penalise large chains)
    """
    # --- Type match ---
    place_types = set(place.get("types", []))
    prospect_type_set = set(prospect_types)
    type_overlap = len(place_types & prospect_type_set)
    type_match = min(type_overlap / max(len(prospect_type_set), 1), 1.0)

    # --- Proximity ---
    plat = place.get("latitude")
    plng = place.get("longitude")
    if plat is not None and plng is not None:
        dist = haversine_distance(prospect_lat, prospect_lng, plat, plng)
        proximity = max(0.0, 1.0 - dist / radius_m)
    else:
        proximity = 0.5

    # --- Price match ---
    pp = PRICE_LEVEL_MAP.get(prospect_price_level or "", 2)
    cp = PRICE_LEVEL_MAP.get(place.get("price_level") or "", 2)
    price_diff = abs(pp - cp)
    price_match = max(0.0, 1.0 - price_diff * 0.5)

    # --- Review volume ---
    review_count = place.get("review_count", 0)
    if review_count > 5000:
        review_score = 0.3  # Likely a chain
    elif review_count > 1000:
        review_score = 0.6
    elif review_count > 50:
        review_score = 1.0  # Sweet spot
    elif review_count > 10:
        review_score = 0.8
    else:
        review_score = 0.5  # Very new / low-traffic

    relevance = (
        type_match * 0.40
        + proximity * 0.25
        + price_match * 0.20
        + review_score * 0.15
    )
    return round(relevance, 3)
