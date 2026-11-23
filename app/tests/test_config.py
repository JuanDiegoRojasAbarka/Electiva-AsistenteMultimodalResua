import pytest

from config import cargar_config


def entorno(mp, **kw):
    base = {"SUPABASE_URL": "https://abc.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_k",
            "GROQ_API_KEY": "g", "CORPUS_ID": "soporte_didactico-1", "EMBEDDINGS_REVISION": "b" * 40}
    base.update(kw)
    for k, v in base.items():
        mp.setenv(k, v)


def test_config_valida(monkeypatch):
    entorno(monkeypatch)
    assert cargar_config().port == 7860


@pytest.mark.parametrize("campo,valor", [("SUPABASE_URL", "http://abc.supabase.co"),
                                         ("SUPABASE_URL", "https://evil.example.com"),
                                         ("SUPABASE_PUBLISHABLE_KEY", "sb_secret_x"),
                                         ("CORPUS_ID", "../x"), ("EMBEDDINGS_REVISION", "abc")])
def test_config_rechaza_valores_invalidos(monkeypatch, campo, valor):
    entorno(monkeypatch, **{campo: valor})
    with pytest.raises(ValueError):
        cargar_config()
