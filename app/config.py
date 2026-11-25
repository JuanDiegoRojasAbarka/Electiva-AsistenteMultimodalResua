"""Configuración leída desde variables de entorno (.env en local; panel del alojamiento en Render)."""
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

try:  # en producción las variables ya vienen del entorno
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass

MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass(frozen=True)
class Config:
    supabase_url: str
    supabase_key: str
    groq_api_key: str
    groq_model: str
    corpus_id: str
    embeddings_revision: str
    mcp_url: str
    host: str
    port: int


def cargar_config(requerir_groq: bool = True) -> Config:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    clave = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or not re.fullmatch(r"[a-z0-9-]+\.supabase\.co", host):
        raise ValueError("SUPABASE_URL debe ser la Project URL HTTPS de Supabase.")
    if not clave.startswith("sb_publishable_"):
        raise ValueError("SUPABASE_PUBLISHABLE_KEY debe ser la clave publicable, nunca una administrativa.")
    groq = os.environ.get("GROQ_API_KEY", "")
    if requerir_groq and not groq:
        raise ValueError("Falta GROQ_API_KEY.")
    corpus = os.environ.get("CORPUS_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", corpus):
        raise ValueError("CORPUS_ID no es válido (ver evidencia JSON de la Clase 9).")
    rev = os.environ.get("EMBEDDINGS_REVISION", "")
    if not re.fullmatch(r"[0-9a-f]{40}", rev):
        raise ValueError("EMBEDDINGS_REVISION debe ser el hash de 40 caracteres de configuracion_embeddings.revision.")
    return Config(
        supabase_url=url,
        supabase_key=clave,
        groq_api_key=groq,
        groq_model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
        corpus_id=corpus,
        embeddings_revision=rev,
        mcp_url=os.environ.get("MCP_URL", "").strip(),
        host=os.environ.get("GRADIO_SERVER_NAME") or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"),
        port=int(os.environ.get("PORT", "7860")),
    )