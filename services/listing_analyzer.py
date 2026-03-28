from typing import Dict, List, Optional

from services.local_analyzer import extract_tags_from_text, predict_category_from_text
from services.openai_listing import analyze_listing_text_openai, use_openai_for_listings


def analyze_listing_text(
    combined_or_description: str, *, local_text: Optional[str] = None
) -> Dict[str, object]:
    """
    OpenAI için genelde "Başlık: ...\\nAçıklama: ..." birleşik metin gönderilir.
    Yerel (keyword) analiz için ise sadece açıklama kullanılmalı; aksi halde
    "Başlık:/Açıklama:" önekleri anahtar kelime skorunu bozar ve güven 0 kalır.
    """
    text = (combined_or_description or "").strip()
    local_source = (local_text if local_text is not None else text).strip()

    if use_openai_for_listings():
        ai = analyze_listing_text_openai(text)
        if ai is not None:
            return ai

    predicted_category, confidence = predict_category_from_text(local_source)
    tags: List[str] = extract_tags_from_text(local_source, max_tags=5)

    return {
        "predicted_category": predicted_category,
        "confidence": confidence,
        "tags": tags,
        "short_summary": "",
        "suggested_title": "",
    }

