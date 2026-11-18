"""Configuración común sin exponer secretos."""
from pathlib import Path
import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):
        return False  # python-dotenv se instala mediante requirements.txt

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DB_DIR = ROOT / 'chroma_db'
PDF_DIR = ROOT / 'documentos'
COLLECTION_NAME = 'pdf_documento_activo'
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
NO_ANSWER = 'No encuentro esa información de forma explícita en el PDF proporcionado.'


def env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def require_secret(key: str) -> str:
    value = os.getenv(key, '').strip()
    if not value or value.startswith('PEGAR_'):
        raise RuntimeError(f'Falta configurar {key} en el archivo .env')
    return value
