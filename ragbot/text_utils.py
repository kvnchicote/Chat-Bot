"""Validación determinista de citas extraídas del PDF."""
import re
import unicodedata


def normalized(text: str) -> str:
    # Conserva las letras pero elimina diferencias de saltos de línea y espacios.
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', ' ', text).strip()


def exact_quote_in_source(quote: str, source: str) -> bool:
    if not isinstance(quote, str) or not quote.strip():
        return False
    return normalized(quote) in normalized(source)


def clean_question(question: str) -> str:
    return question.strip()[:1000]
