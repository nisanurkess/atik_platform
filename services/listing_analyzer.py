from typing import Dict, List

from services.local_analyzer import extract_tags_from_text, predict_category_from_text
from services.openai_listing import analyze_listing_text_openai, use_openai_for_listings


def analyze_listing_text(description: str) -> Dict[str, object]:
    """
    Tek giriş noktası: OPENAI_API_KEY + LISTING_ANALYZER_PROVIDER (auto/openai) ise OpenAI;
    aksi halde veya API başarısızsa yerel anahtar kelime analizi.
    """
    text = (description or "").strip()

    if use_openai_for_listings():
        ai = analyze_listing_text_openai(text)
        if ai is not None:
            return ai

    predicted_category, confidence = predict_category_from_text(text)
    tags: List[str] = extract_tags_from_text(text, max_tags=5)

    return {
        "predicted_category": predicted_category,
        "confidence": confidence,
        "tags": tags,
        "short_summary": "",
    }

