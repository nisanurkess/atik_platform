from typing import List, TypedDict

from services.local_analyzer import extract_tags_from_text, predict_category_from_text
from services.openai_listing import improve_listing_description_openai, use_openai_for_listings


class ImproveResult(TypedDict):
    improved_description: str
    suggested_category: str
    tags: List[str]
    short_summary: str


def improve_listing_description(text: str) -> ImproveResult:
    """
    Açıklama iyileştirme: OpenAI açıksa gerçek API; değilse veya hata olursa yerel öneri (mock metin).
    """

    original = (text or "").strip()
    if not original:
        return {
            "improved_description": "",
            "suggested_category": "Diğer",
            "tags": [],
            "short_summary": "",
        }

    if use_openai_for_listings():
        oa = improve_listing_description_openai(original)
        if oa is not None:
            return {
                "improved_description": str(oa["improved_description"]),
                "suggested_category": str(oa["suggested_category"]),
                "tags": list(oa["tags"]),
                "short_summary": str(oa.get("short_summary", "")),
            }

    predicted_category, _conf = predict_category_from_text(original)
    tags = extract_tags_from_text(original, max_tags=5)
    suggested_category = predicted_category or "Diğer"

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
        "short_summary": "",
    }
