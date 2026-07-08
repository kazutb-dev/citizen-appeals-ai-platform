"""Языковая поддержка AI-генерации (kk / ru / en).

Определяет язык интерфейса из cookie ``medhub_lang`` (устанавливается фронтендом
через i18next) либо из заголовка ``Accept-Language`` и формирует директиву для
локального LLM, чтобы официальные ответы и сводки генерировались на выбранном
языке. Для уже сохранённых обращений язык можно определить по тексту
(``detect_language``) — гражданину отвечают на языке его обращения.
"""
from fastapi import Request

SUPPORTED = ("kk", "ru", "en")
DEFAULT_LANGUAGE = "ru"
LANGUAGE_COOKIE = "medhub_lang"

_LANGUAGE_NAMES = {
    "kk": "казахском языке (қазақ тілінде)",
    "ru": "русском языке",
    "en": "английском языке (English)",
}

# Специфические буквы казахской кириллицы (отсутствуют в русском алфавите).
_KK_CHARS = set("әғқңөұүһі")


def normalize(lang: str | None) -> str:
    """Приводит произвольную языковую метку к поддерживаемому коду (kk/ru/en)."""
    if not lang:
        return DEFAULT_LANGUAGE
    code = lang.strip().lower().replace("_", "-")[:2]
    return code if code in SUPPORTED else DEFAULT_LANGUAGE


def resolve_language(request: Request | None) -> str:
    """Язык интерфейса из cookie или заголовка Accept-Language."""
    if request is None:
        return DEFAULT_LANGUAGE
    cookie = request.cookies.get(LANGUAGE_COOKIE)
    if cookie:
        return normalize(cookie)
    header = request.headers.get("accept-language", "")
    if header:
        return normalize(header.split(",")[0])
    return DEFAULT_LANGUAGE


def detect_language(text: str | None) -> str:
    """Эвристическое определение языка текста обращения (kk/ru/en)."""
    if not text:
        return DEFAULT_LANGUAGE
    sample = text.lower()
    if any(ch in _KK_CHARS for ch in sample):
        return "kk"
    cyrillic = sum(1 for ch in sample if "а" <= ch <= "я" or ch == "ё")
    latin = sum(1 for ch in sample if "a" <= ch <= "z")
    letters = cyrillic + latin
    if letters and latin / letters > 0.6:
        return "en"
    return "ru"


def language_name(lang: str) -> str:
    return _LANGUAGE_NAMES.get(normalize(lang), _LANGUAGE_NAMES[DEFAULT_LANGUAGE])


def language_directive(lang: str) -> str:
    """Строгая инструкция для LLM: на каком языке формировать вывод."""
    return (
        f"ВАЖНО: составь весь ответ строго на {language_name(lang)}. "
        "Не смешивай языки и используй естественные для носителя формулировки."
    )
