"""Data-grounded tools used by the CityWheels agent."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "data" / "policies"
BOOKINGS_FILE = ROOT / "data" / "bookings.json"
CURRENT_TIME = datetime.fromisoformat("2026-06-10T09:00:00+02:00")
STOP_WORDS = {
    "a", "an", "and", "are", "at", "can", "do", "does", "for", "from",
    "get", "how", "i", "in", "is", "it", "me", "my", "of", "on", "or",
    "the", "there", "to", "we", "what", "when", "where", "which", "you",
}
SYNONYMS = {"located": "entrance", "location": "entrance", "address": "entrance"}


def _tokens(text: str) -> set[str]:
    tokens = {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS}
    normalized = {_normalize_token(word) for word in tokens}
    return normalized | {SYNONYMS[word] for word in tokens if word in SYNONYMS}


def _normalize_token(word: str) -> str:
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _policy_sections() -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        heading = path.stem
        body: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                if body:
                    sections.append({"file": path.name, "section": heading, "text": "\n".join(body).strip()})
                heading = line.lstrip("# ").strip()
                body = []
            else:
                body.append(line)
        if body:
            sections.append({"file": path.name, "section": heading, "text": "\n".join(body).strip()})
    return sections


def search_policies(question: str, limit: int = 4) -> dict[str, Any]:
    """Return the most relevant policy sections for a customer question."""
    query_tokens = _tokens(question)
    if not query_tokens:
        return {"found": False, "matches": []}

    scored: list[dict[str, Any]] = []
    for section in _policy_sections():
        section_tokens = _tokens(f"{section['section']} {section['text']}")
        score = len(query_tokens & section_tokens)
        if score:
            scored.append({**section, "score": score})

    scored.sort(key=lambda item: (-item["score"], item["file"], item["section"]))
    matches = scored[:limit]
    return {"found": bool(matches), "matches": matches}


def _load_bookings() -> list[dict[str, Any]]:
    with BOOKINGS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def get_booking(booking_id: str) -> dict[str, Any]:
    """Return a booking or a structured not-found result."""
    normalized_id = booking_id.strip().upper()
    for booking in _load_bookings():
        if booking["id"].upper() == normalized_id:
            return {"found": True, "booking": booking}
    return {"found": False, "booking_id": normalized_id, "message": "Booking not found."}


def calculate_refund(booking_id: str) -> dict[str, Any]:
    """Calculate an eligible cancellation refund using the fixed assignment date."""
    result = get_booking(booking_id)
    if not result["found"]:
        return {
            "found": False,
            "booking_id": result["booking_id"],
            "eligible": False,
            "total_refund_eur": 0.0,
            "message": result["message"],
        }

    booking = result["booking"]
    base = {
        "found": True,
        "booking_id": booking["id"],
        "eligible": booking["status"] == "confirmed",
        "rental_refund_eur": 0.0,
        "deposit_refund_eur": 0.0,
        "booking_fee_refund_eur": 0.0,
        "total_refund_eur": 0.0,
        "refund_method": "card" if booking["paid_with"] == "card" else "new voucher",
    }
    if booking["status"] != "confirmed":
        base["message"] = f"A booking with status '{booking['status']}' cannot be cancelled; no refund is due."
        return base

    starts_at = datetime.fromisoformat(booking["start"])
    hours_until_start = (starts_at - CURRENT_TIME).total_seconds() / 3600
    if hours_until_start >= 48:
        rental_percentage = 1.0
    elif hours_until_start >= 24:
        rental_percentage = 0.5
    else:
        rental_percentage = 0.0

    rental_refund = round(booking["rental_price_eur"] * rental_percentage, 2)
    deposit_refund = round(booking["deposit_eur"], 2)
    base.update(
        rental_refund_eur=rental_refund,
        deposit_refund_eur=deposit_refund,
        booking_fee_refund_eur=0.0,
        total_refund_eur=round(rental_refund + deposit_refund, 2),
        rental_refund_percentage=int(rental_percentage * 100),
        hours_until_start=round(hours_until_start, 2),
        message=(
            "The booking fee is not refunded. "
            + ("Card refunds are returned to the same card within 5 working days." if booking["paid_with"] == "card" else "The rental and deposit are returned as a voucher, not as money.")
        ),
    )
    return base