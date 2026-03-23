import re
import unicodedata
from typing import Iterable, List, Sequence


_TURKISH_LOWER_MAP = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "i": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)

_STOPWORDS = {
    "ve",
    "veya",
    "ile",
    "icin",
    "için",
    "bir",
    "olarak",
    "gibi",
    "olan",
    "hakkinda",
    "hakkında",
    "daha",
    "sadece",
    "yalnizca",
    "yalnızca",
    "tumu",
    "tüm",
    "kendi",
    "tarih",
    "tarihi",
    "adet",
    "kg",
    "ton",
    "litre",
    "l",
    "adet",
    "parca",
    "parça",
}


def normalize_text_tr(text: str | None) -> str:
    """
    Türkçe metni basitçe normalize eder (küçük harf, Türkçe karakter düzeltme, noktalama temizliği).
    Yerel ve ücretsiz benzerlik/keyword mantığı için yeterli olacak şekilde tasarlanmıştır.
    """
    if not text:
        return ""

    text = str(text).strip()
    # "İ" (noktalı büyük i) lower() sonrası "i̇" (i + combining dot) oluşturabiliyor.
    # Bunu önlemek için özel olarak düzeltelim.
    text = text.replace("İ", "i")

    text = text.lower()
    text = text.translate(_TURKISH_LOWER_MAP)

    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_tr(text: str | None) -> List[str]:
    norm = normalize_text_tr(text)
    if not norm:
        return []
    tokens = [t for t in norm.split() if t and t not in _STOPWORDS]
    return tokens


def jaccard_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    inter = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(inter) / len(union) if union else 0.0


def unique_ordered(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

