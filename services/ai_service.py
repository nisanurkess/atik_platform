import os
from typing import Dict, List, TypedDict

from services.listing_analyzer import analyze_listing_text


class ImproveResult(TypedDict):
    improved_description: str
    suggested_category: str
    tags: List[str]


def improve_listing_description(text: str) -> ImproveResult:
    """
    AI iyileştirme servisi (mock).

    Not:
    - Şu an gerçek bir dış API çağırmıyoruz.
    - İleride `OPENAI_API_KEY` varsa burada OpenAI/benzeri bir provider'a geçmek kolay olacak.
    """

    original = (text or "").strip()
    if not original:
        return {
            "improved_description": "",
            "suggested_category": "Diğer",
            "tags": [],
        }

    # Placeholder: gelecekte gerçek API entegrasyonu buraya gelecek.
    # openai_key = os.environ.get("OPENAI_API_KEY")
    _ = os.environ.get("OPENAI_API_KEY")

    analysis = analyze_listing_text(original)
    suggested_category = analysis.get("predicted_category") or "Diğer"
    tags = analysis.get("tags") or []

    # Basit, daha profesyonel görünümlü mock metin üretimi.
    improved = original
    if not improved.endswith("."):
        improved += "."

    improved_description = (
        f"Bu ilan, atık türünü ve kullanım amacını daha anlaşılır bir şekilde açıklar: {improved} "
        "Malzeme uygunluğu ve teslimat düzeni için detaylar metinde bilgilendirme amaçlı verilmiştir."
    )

    return {
        "improved_description": improved_description,
        "suggested_category": suggested_category,
        "tags": tags,
    }

