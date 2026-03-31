"""
OpenAI ile ilan metni analizi ve açıklama iyileştirme.
API anahtarı yalnızca ortam değişkeninden okunur; asla sabitlenmez.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import APIError, OpenAI

from services.categories import CATEGORIES

_logger = logging.getLogger(__name__)


def _unwrap_nested_json(raw: Any) -> Dict[str, Any]:
    """Model bazen {'result': {...}} gibi tek anahtarlı sarıcı döndürür."""
    if not isinstance(raw, dict):
        return {}
    if len(raw) != 1:
        return raw
    sole_key = str(next(iter(raw.keys()))).lower().replace(" ", "_")
    sole_val = raw[next(iter(raw.keys()))]
    if isinstance(sole_val, dict) and sole_key in (
        "data",
        "result",
        "response",
        "output",
        "json",
        "ilan",
        "listing",
        "analysis",
    ):
        return sole_val
    return raw


def _get_str(raw: Dict[str, Any], *names: str) -> str:
    """Önce tam anahtar, sonra büyük/küçük harf duyarsız eşleşme."""
    for n in names:
        if n in raw:
            v = raw[n]
            if v is not None and str(v).strip():
                return str(v).strip()
    key_map = {str(k).lower(): k for k in raw}
    for n in names:
        ln = n.lower()
        if ln in key_map:
            v = raw[key_map[ln]]
            if v is not None and str(v).strip():
                return str(v).strip()
    return ""


def _derive_summary_title_from_body(body: str) -> tuple[str, str]:
    """Model özet/başlık göndermezse metinden kısa yedek üret (ekran boş kalmasın)."""
    text = (body or "").strip()
    if "Açıklama:" in text:
        text = text.split("Açıklama:", 1)[-1].strip()
    if not text:
        return "", ""
    first_sentence = text.split(".")[0].strip()
    if len(first_sentence) > 220:
        first_sentence = first_sentence[:217].rstrip() + "…"
    summary = first_sentence if first_sentence else text[:220]
    line = text.split("\n")[0].strip()
    title = (line[:80] if line else text[:80]).strip()
    return summary, title


def _api_key() -> str:
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if key == "your_api_key_here":
        return ""
    return key


def use_openai_for_listings() -> bool:
    """
    LISTING_ANALYZER_PROVIDER:
      - local: her zaman yerel (keyword) analiz
      - openai: anahtar varsa OpenAI, yoksa veya hata olursa üst katman yerel'e döner
      - auto (varsayılan): geçerli OPENAI_API_KEY varsa OpenAI, yoksa yerel
    """
    if not _api_key():
        return False
    provider = (os.environ.get("LISTING_ANALYZER_PROVIDER") or "auto").lower().strip()
    if provider == "local":
        return False
    return provider in ("openai", "auto", "")


def _client() -> OpenAI:
    return OpenAI(api_key=_api_key())


def _categories_csv() -> str:
    return ", ".join(CATEGORIES)


def _normalize_analyze(raw: Dict[str, Any]) -> Dict[str, object]:
    cat = _get_str(raw, "predicted_category", "category", "suggested_category", "kategori") or "Diğer"
    if cat not in CATEGORIES:
        cat = "Diğer"
    raw_conf = raw.get("confidence", raw.get("Confidence", 0))
    try:
        if isinstance(raw_conf, float):
            conf = int(round(raw_conf))
        else:
            conf = int(raw_conf)
    except (TypeError, ValueError):
        conf = 0
    conf = max(0, min(100, conf))
    tags_raw = raw.get("tags") or raw.get("etiketler") or []
    if not isinstance(tags_raw, list):
        tags_raw = []
    tags: List[str] = []
    for t in tags_raw:
        s = str(t).strip()
        if s and s not in tags:
            tags.append(s)
        if len(tags) >= 3:
            break
    summary = _get_str(
        raw,
        "short_summary",
        "summary",
        "shortSummary",
        "kisa_ozet",
        "kısa_ozet",
        "ozet",
        "özet",
        "brief_summary",
    )
    if len(summary) > 400:
        summary = summary[:400]
    suggested_title = _get_str(
        raw,
        "suggested_title",
        "title_suggestion",
        "suggestedTitle",
        "titleSuggestion",
        "baslik_onerisi",
        "baslik",
        "önerilen_baslik",
        "ilan_basligi",
        "title",
    )
    if len(suggested_title) > 120:
        suggested_title = suggested_title[:120]

    # Model bazen güven göndermez veya 0 döner; ön yüz "öneri yok" sanmasın
    if conf <= 0 and (tags or summary or suggested_title or cat != "Diğer"):
        conf = 72

    return {
        "predicted_category": cat,
        "confidence": conf,
        "tags": tags,
        "short_summary": summary,
        "suggested_title": suggested_title,
    }


def analyze_listing_text_openai(combined_text: str) -> Optional[Dict[str, object]]:
    """
    combined_text: genelde "Başlık: ...\\nAçıklama: ..." veya sadece açıklama.
    Başarısızlıkta None döner (çağıran yerel analize düşer).
    """
    text = (combined_text or "").strip()
    if not text:
        return None

    system = (
        "Sen Türkiye'deki atık ve geri dönüşüm ilanları için sınıflandırıcısın. "
        "Yanıtın yalnızca geçerli bir JSON nesnesi olmalı, başka metin veya markdown yok."
    )
    user = (
        f"Geçerli kategoriler (tam eşleşme): {_categories_csv()}.\n"
        "Aşağıdaki JSON anahtarlarını TAM OLARAK bu İngilizce isimlerle döndür: "
        "predicted_category, confidence, tags, short_summary, suggested_title. "
        "short_summary ve suggested_title boş bırakma; mutlaka anlamlı Türkçe doldur.\n"
        'Örnek şema: {"predicted_category": string, "confidence": integer 0-100, '
        '"tags": string array en fazla 3, '
        '"short_summary": string tek cümle max 200 karakter, '
        '"suggested_title": string max 80 karakter}.\n'
        "Metin:\n"
        f"{text}"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = (resp.choices[0].message.content or "").strip()
        raw = json.loads(content)
        if not isinstance(raw, dict):
            return None
        raw = _unwrap_nested_json(raw)
        out = _normalize_analyze(raw)
        if not str(out.get("short_summary") or "").strip():
            out["short_summary"], _ = _derive_summary_title_from_body(text)
        if not str(out.get("suggested_title") or "").strip():
            _, t = _derive_summary_title_from_body(text)
            out["suggested_title"] = t
        return out
    except (json.JSONDecodeError, APIError, KeyError, IndexError, TypeError) as exc:
        _logger.warning("OpenAI ilan analizi başarısız: %s", exc)
        return None
    except Exception as exc:
        _logger.warning("OpenAI ilan analizi beklenmeyen hata: %s", exc)
        return None


def _normalize_improve(raw: Dict[str, Any], original: str) -> Dict[str, str | List[str]]:
    improved = _get_str(
        raw,
        "improved_description",
        "improvedDescription",
        "improved_text",
        "improvedText",
        "new_description",
        "description_improved",
    )
    if not improved:
        improved = original
    cat = _get_str(raw, "suggested_category", "suggestedCategory", "category", "kategori") or "Diğer"
    if cat not in CATEGORIES:
        cat = "Diğer"
    tags_raw = raw.get("tags") or raw.get("etiketler") or []
    if not isinstance(tags_raw, list):
        tags_raw = []
    tags: List[str] = []
    for t in tags_raw:
        s = str(t).strip()
        if s and s not in tags:
            tags.append(s)
        if len(tags) >= 3:
            break
    summary = _get_str(
        raw,
        "short_summary",
        "summary",
        "shortSummary",
        "kisa_ozet",
        "kısa_ozet",
        "ozet",
        "özet",
    )
    if len(summary) > 400:
        summary = summary[:400]
    suggested_title = _get_str(
        raw,
        "suggested_title",
        "title_suggestion",
        "suggestedTitle",
        "baslik_onerisi",
        "baslik",
        "title",
    )
    if len(suggested_title) > 120:
        suggested_title = suggested_title[:120]
    out: Dict[str, str | List[str]] = {
        "improved_description": improved,
        "suggested_category": cat,
        "tags": tags,
        "short_summary": summary,
        "suggested_title": suggested_title,
    }
    if not out["short_summary"]:
        out["short_summary"], _ = _derive_summary_title_from_body(improved)
    if not out["suggested_title"]:
        _, t = _derive_summary_title_from_body(improved)
        out["suggested_title"] = t
    return out


def improve_listing_description_openai(description: str) -> Optional[Dict[str, str | List[str]]]:
    original = (description or "").strip()
    if not original:
        return None

    system = (
        "Sen atık ilanı açıklamalarını Türkçe, doğal ve profesyonel hale getiriyorsun. "
        "Kalıp cümlelerden kaçın; gerçek bir ilan metni gibi yaz. "
        "Yanıt yalnızca geçerli bir JSON nesnesi olmalı."
    )
    user = (
        f"Geçerli kategoriler (tam eşleşme): {_categories_csv()}.\n"
        "Şu İngilizce anahtar isimlerini AYNEN kullan: improved_description, "
        "suggested_category, tags, short_summary, suggested_title. "
        "short_summary ve suggested_title boş olamaz.\n"
        'Şema: {"improved_description": string, "suggested_category": string, '
        '"tags": string array en fazla 3, "short_summary": string max 200 karakter, '
        '"suggested_title": string max 80 karakter}.\n'
        "Aşağıdaki açıklamayı iyileştir; uydurma miktar veya yasal iddia ekleme.\n"
        f"Açıklama:\n{original}"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.55,
        )
        content = (resp.choices[0].message.content or "").strip()
        raw = json.loads(content)
        if not isinstance(raw, dict):
            return None
        raw = _unwrap_nested_json(raw)
        return _normalize_improve(raw, original)
    except (json.JSONDecodeError, APIError, KeyError, IndexError, TypeError) as exc:
        _logger.warning("OpenAI açıklama iyileştirme başarısız: %s", exc)
        return None
    except Exception as exc:
        _logger.warning("OpenAI açıklama iyileştirme beklenmeyen hata: %s", exc)
        return None
