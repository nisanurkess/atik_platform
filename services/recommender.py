import difflib
from typing import Any, Dict, List, Sequence, Tuple

from utils.text_analysis import jaccard_similarity, normalize_text_tr, tokenize_tr


def _description_similarity(text_a: str, text_b: str) -> float:
    """
    Ücretsiz, lokal ve deterministik bir benzerlik yaklaşımı.
    Token overlap + difflib SequenceMatcher karışımı kullanır.
    """
    norm_a = normalize_text_tr(text_a)
    norm_b = normalize_text_tr(text_b)
    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0

    tokens_a = tokenize_tr(norm_a)
    tokens_b = tokenize_tr(norm_b)
    token_sim = jaccard_similarity(tokens_a, tokens_b)

    ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
    # Token overlap, hızlı; string benzerliği daha yumuşak yakalar.
    return 0.6 * token_sim + 0.4 * ratio


def _shared_tags(tags_a: Sequence[str], tags_b: Sequence[str]) -> List[str]:
    set_a = set(tags_a or [])
    set_b = set(tags_b or [])
    shared = sorted(set_a.intersection(set_b))
    return shared


def _tags_jaccard(tags_a: Sequence[str], tags_b: Sequence[str]) -> float:
    set_a = set(tags_a or [])
    set_b = set(tags_b or [])
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    inter = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(inter) / len(union) if union else 0.0


def compute_uyum_skoru(selected: Any, candidate: Any) -> Dict[str, Any]:
    """
    selected ve candidate için uyum skoru üretir.
    Ağırlıklar: kategori + şehir + etiket + açıklama benzerliği.
    """
    cat_match = 1.0 if getattr(selected, "category", None) == getattr(candidate, "category", None) else 0.0
    city_match = 1.0 if (getattr(selected, "city", None) or "").strip().lower() == (getattr(candidate, "city", None) or "").strip().lower() else 0.0

    selected_tags = getattr(selected, "tags_list", []) or []
    candidate_tags = getattr(candidate, "tags_list", []) or []

    ortak_tags = _shared_tags(selected_tags, candidate_tags)
    tags_sim = _tags_jaccard(selected_tags, candidate_tags)
    text_sim = _description_similarity(getattr(selected, "description", ""), getattr(candidate, "description", ""))

    uyum = 0.35 * cat_match + 0.2 * city_match + 0.25 * tags_sim + 0.2 * text_sim
    uyum_skoru = int(round(uyum * 100))
    uyum_skoru = max(0, min(100, uyum_skoru))

    return {
        "uyum_skoru": uyum_skoru,
        "ortak_etiketler": ortak_tags,
    }


def recommend_similar_listings(selected_listing: Any, candidate_listings: List[Any], limit: int = 4) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for cand in candidate_listings:
        if getattr(cand, "id", None) == getattr(selected_listing, "id", None):
            continue
        payload = compute_uyum_skoru(selected_listing, cand)
        results.append({"listing": cand, **payload})

    # Uyum skoru aynıysa daha yeni ilanlar öne gelsin.
    results.sort(key=lambda x: (-x["uyum_skoru"], -(x["listing"].created_at.timestamp() if getattr(x["listing"], "created_at", None) else 0)))
    return results[:limit]

