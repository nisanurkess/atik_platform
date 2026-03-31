"""Kayıt / giriş için ortak normalizasyon (e-posta eşleşmesi ve şifre tutarlılığı)."""

from __future__ import annotations

import unicodedata


def normalize_email(value: str) -> str:
    """
    E-postayı tek biçime getirir: boşluk temizliği, Unicode birleştirme, casefold.
    Böylece tarayıcı / klavye farkından kaynaklı 'aynı adres ama eşleşmiyor' sorunları azalır.
    """
    s = unicodedata.normalize("NFKC", (value or "").strip())
    return s.casefold()


def normalize_password_input(value: str) -> str:
    """
    Şifrede baş/son boşlukları kaldırır (kopyala-yapıştır hataları).
    Kayıt ve giriş aynı kuralı kullanmalı; aksi halde giriş başarısız olur.
    """
    return (value or "").strip()
