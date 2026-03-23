import os
from typing import Dict, List

from services.local_analyzer import extract_tags_from_text, predict_category_from_text


def analyze_listing_text(description: str) -> Dict[str, object]:
    """
    İleride Hugging Face gibi farklı provider'lara bağlanabilmesi için tek giriş noktası.
    Şu an sadece lokal ve ücretsiz keyword mantığı kullanıyoruz.
    """
    _provider = os.environ.get("LISTING_ANALYZER_PROVIDER", "local").lower().strip()

    # Ücretli/harici servis kullanmıyoruz; HF opsiyonunu mimari olarak bırakıyoruz.
    # Provider değişirse bile şu an lokal döndürür.
    _ = _provider

    predicted_category, confidence = predict_category_from_text(description)
    tags: List[str] = extract_tags_from_text(description, max_tags=5)

    return {
        "predicted_category": predicted_category,
        "confidence": confidence,
        "tags": tags,
    }

