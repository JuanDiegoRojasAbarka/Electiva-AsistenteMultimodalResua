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


def test_host_por_defecto_en_render(monkeypatch):
    """Render define PORT; sin GRADIO_SERVER_NAME la app debe escuchar en 0.0.0.0, no en 127.0.0.1."""
    entorno(monkeypatch)
    monkeypatch.delenv("GRADIO_SERVER_NAME", raising=False)
    monkeypatch.setenv("PORT", "10000")
    cfg = cargar_config()
    assert cfg.host == "0.0.0.0" and cfg.port == 10000
