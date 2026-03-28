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
    cat = str(raw.get("predicted_category") or "Diğer").strip()
    if cat not in CATEGORIES:
        cat = "Diğer"
    raw_conf = raw.get("confidence", 0)
    try:
        if isinstance(raw_conf, float):
            conf = int(round(raw_conf))
        else:
            conf = int(raw_conf)
    except (TypeError, ValueError):
        conf = 0
    conf = max(0, min(100, conf))
    tags_raw = raw.get("tags") or []
    if not isinstance(tags_raw, list):
        tags_raw = []
    tags: List[str] = []
    for t in tags_raw:
        s = str(t).strip()
        if s and s not in tags:
            tags.append(s)
        if len(tags) >= 3:
            break
    summary = str(raw.get("short_summary") or raw.get("summary") or "").strip()
    if len(summary) > 400:
        summary = summary[:400]
    suggested_title = str(
        raw.get("suggested_title") or raw.get("title_suggestion") or ""
    ).strip()
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
        'JSON şeması: {"predicted_category": string, "confidence": integer 0-100, '
        '"tags": string array en fazla 3 kısa etiket, '
        '"short_summary": string tek cümle özet en fazla 200 karakter, '
        '"suggested_title": string kısa ilan başlığı önerisi en fazla 80 karakter '
        "(başlık zaten doluysa onu iyileştirerek veya açıklamadan üret)}.\n"
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
        return _normalize_analyze(raw)
    except (json.JSONDecodeError, APIError, KeyError, IndexError, TypeError) as exc:
        _logger.warning("OpenAI ilan analizi başarısız: %s", exc)
        return None
    except Exception as exc:
        _logger.warning("OpenAI ilan analizi beklenmeyen hata: %s", exc)
        return None


def _normalize_improve(raw: Dict[str, Any], original: str) -> Dict[str, str | List[str]]:
    improved = str(raw.get("improved_description") or "").strip()
    if not improved:
        improved = original
    cat = str(raw.get("suggested_category") or "Diğer").strip()
    if cat not in CATEGORIES:
        cat = "Diğer"
    tags_raw = raw.get("tags") or []
    if not isinstance(tags_raw, list):
        tags_raw = []
    tags: List[str] = []
    for t in tags_raw:
        s = str(t).strip()
        if s and s not in tags:
            tags.append(s)
        if len(tags) >= 3:
            break
    summary = str(raw.get("short_summary") or raw.get("summary") or "").strip()
    if len(summary) > 400:
        summary = summary[:400]
    suggested_title = str(
        raw.get("suggested_title") or raw.get("title_suggestion") or ""
    ).strip()
    if len(suggested_title) > 120:
        suggested_title = suggested_title[:120]
    return {
        "improved_description": improved,
        "suggested_category": cat,
        "tags": tags,
        "short_summary": summary,
        "suggested_title": suggested_title,
    }


def improve_listing_description_openai(description: str) -> Optional[Dict[str, str | List[str]]]:
    original = (description or "").strip()
    if not original:
        return None

    system = (
        "Sen atık ilanı açıklamalarını Türkçe, net ve profesyonel hale getiriyorsun. "
        "Yanıt yalnızca geçerli bir JSON nesnesi."
    )
    user = (
        f"Geçerli kategoriler (tam eşleşme): {_categories_csv()}.\n"
        'JSON şeması: {"improved_description": string tam metin, '
        '"suggested_category": string, "tags": string array en fazla 3, '
        '"short_summary": string tek cümle özet en fazla 200 karakter, '
        '"suggested_title": string kısa ilan başlığı en fazla 80 karakter}.\n'
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
            temperature=0.4,
        )
        content = (resp.choices[0].message.content or "").strip()
        raw = json.loads(content)
        if not isinstance(raw, dict):
            return None
        return _normalize_improve(raw, original)
    except (json.JSONDecodeError, APIError, KeyError, IndexError, TypeError) as exc:
        _logger.warning("OpenAI açıklama iyileştirme başarısız: %s", exc)
        return None
    except Exception as exc:
        _logger.warning("OpenAI açıklama iyileştirme beklenmeyen hata: %s", exc)
        return None
