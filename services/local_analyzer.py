from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from utils.text_analysis import normalize_text_tr


@dataclass(frozen=True)
class CategoryRule:
    keyword: str
    weight: int


@dataclass(frozen=True)
class TagRule:
    label: str
    keywords: List[Tuple[str, int]]


CATEGORY_RULES: Dict[str, List[CategoryRule]] = {
    "Plastik": [
        CategoryRule("pet", 35),
        CategoryRule("plastik", 20),
        CategoryRule("granul", 15),
        CategoryRule("granül", 15),
        CategoryRule("sise", 12),
        CategoryRule("şişe", 12),  # normalization sonrası genelde "sise" olur; korunması için
        CategoryRule("polietilen", 12),
        CategoryRule("film", 8),
        CategoryRule("ambalaj", 6),
    ],
    "Metal": [
        CategoryRule("metal", 18),
        CategoryRule("celik", 20),
        CategoryRule("aluminyum", 18),
        CategoryRule("alum", 12),
        CategoryRule("hurda", 15),
        CategoryRule("sac", 10),
        CategoryRule("krom", 6),
    ],
    "Kağıt": [
        CategoryRule("kagit", 20),
        CategoryRule("karton", 18),
        CategoryRule("kutu", 10),
        CategoryRule("ambalaj", 8),
    ],
    "Cam": [
        CategoryRule("cam", 25),
        CategoryRule("kirik cam", 30),
        CategoryRule("sise", 10),
        CategoryRule("kavanoz", 12),
    ],
    "Organik": [
        CategoryRule("organik", 22),
        CategoryRule("gida", 18),
        CategoryRule("kompost", 20),
        CategoryRule("biyolojik", 8),
    ],
    "Tekstil": [
        CategoryRule("tekstil", 22),
        CategoryRule("kumas", 20),
        CategoryRule("iplik", 15),
        CategoryRule("elyaf", 15),
        CategoryRule("kuma s", 10),  # normalization sonrası boşluklar değişebilir
    ],
    "Elektronik": [
        CategoryRule("elektronik", 25),
        CategoryRule("devre", 20),
        CategoryRule("baskili devre", 25),
        CategoryRule("pcb", 25),
        CategoryRule("kart", 12),
        CategoryRule("kablo", 12),
        CategoryRule("elektronik kart", 20),
    ],
    "Kimyasal": [
        CategoryRule("kimyasal", 25),
        CategoryRule("solvent", 28),
        CategoryRule("asid", 18),
        CategoryRule("asit", 18),
        CategoryRule("baz", 10),
        CategoryRule("temizlik", 10),
        CategoryRule("kimyasal temizlik", 20),
        CategoryRule("sivi", 6),
    ],
}


def _score_keywords(rules: List[CategoryRule], normalized_text: str) -> int:
    score = 0
    for rule in rules:
        if rule.keyword in normalized_text:
            score += rule.weight
    return score


def predict_category_from_text(description: str) -> tuple[str, int]:
    normalized = normalize_text_tr(description)
    if not normalized:
        return "Diğer", 0

    scores: Dict[str, int] = {}
    for category, rules in CATEGORY_RULES.items():
        scores[category] = _score_keywords(rules, normalized)

    best_category = max(scores.keys(), key=lambda c: scores[c])
    best_score = scores[best_category]
    if best_score <= 0:
        return "Diğer", 0

    second_score = 0
    for c, s in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]:
        if c != best_category:
            second_score = s
            break

    confidence = int(round(100 * best_score / (best_score + second_score + 1)))
    confidence = max(0, min(100, confidence))
    return best_category, confidence


TAG_RULES: List[TagRule] = [
    TagRule("PET", [("pet", 30), ("sise", 12)]),
    TagRule("kırık cam", [("kirik cam", 35), ("cam", 15), ("kavanoz", 10)]),
    TagRule("alüminyum", [("aluminyum", 35), ("alum", 15)]),
    TagRule("hurda metal", [("hurda", 18), ("metal", 12), ("celik", 12), ("sac", 10)]),
    TagRule("tekstil parçası", [("tekstil", 18), ("kumas", 16), ("iplik", 10), ("elyaf", 10)]),
    TagRule("granül", [("granul", 20)]),
    TagRule("kablo", [("kablo", 25)]),
    TagRule("organik atık", [("organik", 20), ("gida", 12), ("kompost", 20)]),
    TagRule("karton", [("karton", 22)]),
    TagRule("solvent", [("solvent", 30), ("kimyasal", 10)]),
]


def extract_tags_from_text(description: str, max_tags: int = 5) -> List[str]:
    normalized = normalize_text_tr(description)
    if not normalized:
        return []

    tag_scores: Dict[str, int] = {}
    for rule in TAG_RULES:
        score = 0
        for kw, w in rule.keywords:
            if kw in normalized:
                score += w
        if score > 0:
            tag_scores[rule.label] = score

    # Skora göre azalan, etiket adina göre artan deterministik sıralama
    sorted_labels = sorted(tag_scores.items(), key=lambda kv: (-kv[1], kv[0]))
    labels = [label for label, _ in sorted_labels]

    # Basit temizleme: aynı/benzer etiketler birbirini tamamen kapsıyorsa ele
    cleaned: List[str] = []
    for lab in labels:
        if lab in cleaned:
            continue
        cleaned.append(lab)
        if len(cleaned) >= max_tags:
            break
    return cleaned

