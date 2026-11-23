"""Regresión: varias preguntas seguidas (cada una con su propio asyncio.run, como hace Gradio) deben funcionar
con el cliente real de Groq. Un AsyncGroq reutilizado entre bucles fallaba en la 2.ª llamada (APIConnectionError)."""
import asyncio
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import sistema as S
from conftest import ClienteRPC

DECISION = json.dumps({"accion": "aclarar", "consulta": "", "codigo_avistamiento": "", "especie": "",
                       "respuesta": "¿Puedes precisar tu pregunta?", "citas": []})


@pytest.fixture
def servidor_groq(monkeypatch):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"          # conexiones reutilizables, como la API real

        def do_POST(self):
            self.rfile.read(int(self.headers.get("content-length", 0)))
            cuerpo = json.dumps({"id": "x", "object": "chat.completion", "created": 1, "model": "m", "choices": [
                {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": DECISION}}]}).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("GROQ_BASE_URL", f"http://127.0.0.1:{srv.server_port}")
    yield
    srv.shutdown()


def test_preguntas_seguidas_con_el_cliente_real_de_groq(config, servidor_groq):
    s = S.Sistema(config, embeddings=object())           # sin cliente inyectado: usa AsyncGroq real
    for i in range(4):
        t = asyncio.run(s.atender(f"pregunta {i}", ClienteRPC([])))
        assert t["estado"] == "ACLARAR", t


def test_el_error_tecnico_queda_registrado_con_su_detalle(config, caplog):
    s = S.Sistema(config, embeddings=object(), groq=object())   # objeto sin API -> falla técnica
    with caplog.at_level(logging.ERROR, logger="resua"):
        t = asyncio.run(s.atender("hola", ClienteRPC([])))
    assert t["estado"] == "ERROR_TECNICO" and t["tipo_error"] == "AttributeError" and t["detalle_error"]
    assert any("ERROR_TECNICO" in r.message and r.exc_info for r in caplog.records)   # traza completa en el log


# --- tool_use_failed: el modelo intenta una llamada nativa en vez del JSON -------------------------
import httpx  # noqa: E402
import groq  # noqa: E402
from types import SimpleNamespace  # noqa: E402


def _error_tool_use_failed():
    cuerpo = {"error": {"message": "Tool choice is none, but model called a tool", "type": "invalid_request_error",
                        "code": "tool_use_failed",
                        "failed_generation": '{"name": "tool_mcp_consultar_estado_avistamiento", "arguments": {"codigo_avistamiento":"AVS-1001"}}'}}
    resp = httpx.Response(400, request=httpx.Request("POST", "http://x/chat"), json=cuerpo)
    return groq.BadRequestError("Error code: 400 - " + str(cuerpo), response=resp, body=cuerpo)


class GroqFalso:
    def __init__(self, fallos):
        self.fallos, self.llamadas = fallos, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kw):
        self.llamadas.append(kw["messages"][-1]["content"])
        if self.fallos:
            raise self.fallos.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=DECISION, refusal=None))],
                               usage=None)


def test_tool_use_failed_se_reintenta_una_vez_y_se_recupera(config):
    g = GroqFalso([_error_tool_use_failed()])
    t = asyncio.run(S.Sistema(config, embeddings=object(), groq=g).atender("hola", ClienteRPC([])))
    assert t["estado"] == "ACLARAR" and len(g.llamadas) == 2 and "no uses llamadas nativas" in g.llamadas[1]


def test_tool_use_failed_repetido_termina_en_error_tecnico_sin_ejecutar_la_generacion(config):
    g = GroqFalso([_error_tool_use_failed(), _error_tool_use_failed()])
    t = asyncio.run(S.Sistema(config, embeddings=object(), groq=g).atender("¿Estado de AVS-1001?", ClienteRPC([])))
    assert t["estado"] == "ERROR_TECNICO" and t["operaciones"] == 0 and len(g.llamadas) == 2


def test_otros_errores_no_se_reintentan(config):
    g = GroqFalso([RuntimeError("otra falla")])
    t = asyncio.run(S.Sistema(config, embeddings=object(), groq=g).atender("hola", ClienteRPC([])))
    assert t["estado"] == "ERROR_TECNICO" and len(g.llamadas) == 1


def test_el_contexto_no_expone_la_herramienta_con_forma_de_definicion(config):
    g = GroqFalso([])
    asyncio.run(S.Sistema(config, embeddings=object(), groq=g).atender("hola", ClienteRPC([])))
    assert '"capacidades"' in g.llamadas[0] and '"herramienta_mcp"' not in g.llamadas[0]
