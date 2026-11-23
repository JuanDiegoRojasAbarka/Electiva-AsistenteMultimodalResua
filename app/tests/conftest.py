import itertools
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config  # noqa: E402

REV = "a" * 40


class Almacen:
    """Base de datos en memoria compartida por todos los clientes falsos. NO emula RLS:
    por eso las pruebas ejercitan la comprobación de propietario de almacenamiento.py."""

    def __init__(self):
        self.tablas = {"resua_conversaciones": [], "resua_mensajes": []}
        self.tokens = {}          # token -> user_id
        self.cuentas = {}         # email -> (password, user_id)
        self.ids = itertools.count(1)
        self.fallar_insert_mensajes = False

    def crear_usuario(self, email, password="clave123"):
        uid = str(uuid.uuid4())
        self.cuentas[email] = (password, uid)
        return uid


class Consulta:
    def __init__(self, almacen, tabla):
        self.a, self.t, self.filtros, self._orden, self._lim, self._ins = almacen, tabla, [], None, None, None

    def select(self, *_a, **_k): return self
    def eq(self, c, v): self.filtros.append((c, v)); return self
    def order(self, c, desc=False): self._orden = (c, desc); return self
    def limit(self, n): self._lim = n; return self
    def insert(self, fila): self._ins = dict(fila); return self

    def execute(self):
        filas = self.a.tablas[self.t]
        if self._ins is not None:
            if self.t == "resua_mensajes" and self.a.fallar_insert_mensajes:
                return SimpleNamespace(data=[])
            fila = self._ins
            fila["id"] = str(uuid.uuid4()) if self.t == "resua_conversaciones" else next(self.a.ids)
            fila.setdefault("creada_en", f"2026-11-23T10:{len(filas):02d}:00")
            fila.setdefault("creado_en", f"2026-11-23T10:{len(filas):02d}:00")
            filas.append(fila)
            return SimpleNamespace(data=[dict(fila)])
        res = [dict(f) for f in filas if all(f.get(c) == v for c, v in self.filtros)]
        if self._orden:
            res.sort(key=lambda f: f[self._orden[0]], reverse=self._orden[1])
        return SimpleNamespace(data=res[: self._lim] if self._lim else res)


class ClienteFalso:
    def __init__(self, almacen, token=None):
        self.a, self.token = almacen, token
        self.auth = SimpleNamespace(get_user=self._get_user, sign_in_with_password=self._login,
                                    sign_up=self._signup, refresh_session=self._refresh)

    def table(self, nombre): return Consulta(self.a, nombre)

    def _sesion(self, email, uid):
        tok = f"tok-{uuid.uuid4()}"
        self.a.tokens[tok] = uid
        return SimpleNamespace(user=SimpleNamespace(id=uid, email=email),
                               session=SimpleNamespace(access_token=tok, refresh_token=f"ref-{uid}"))

    def _login(self, cred):
        cuenta = self.a.cuentas.get(cred["email"])
        if not cuenta or cuenta[0] != cred["password"]:
            raise Exception("invalid")
        return self._sesion(cred["email"], cuenta[1])

    def _signup(self, cred):
        uid = self.a.crear_usuario(cred["email"], cred["password"])
        return self._sesion(cred["email"], uid)

    def _refresh(self, refresh):
        uid = refresh.removeprefix("ref-")
        email = next(e for e, (_, u) in self.a.cuentas.items() if u == uid)
        return self._sesion(email, uid)

    def _get_user(self, token):
        if token not in self.a.tokens:
            raise Exception("jwt")
        return SimpleNamespace(user=SimpleNamespace(id=self.a.tokens[token]))


@pytest.fixture
def almacen():
    return Almacen()


@pytest.fixture
def fabrica(almacen):
    return lambda url, clave, token=None: ClienteFalso(almacen, token)


@pytest.fixture
def config():
    return Config(supabase_url="https://x.supabase.co", supabase_key="sb_publishable_x", groq_api_key="g",
                  groq_model="m", corpus_id="soporte_didactico-1", embeddings_revision=REV,
                  mcp_url="", host="127.0.0.1", port=7860)


class EmbeddingsFalso:
    max_seq_length = 128
    tokenizer = SimpleNamespace(encode=lambda t, truncation=False: t.split())

    def encode(self, texto, normalize_embeddings=True):
        return SimpleNamespace(tolist=lambda: [0.0] * 384)


FRAGMENTO = {"chunk_id": "registro_avistamientos-0",
             "content": "Para registrar un avistamiento indique ubicación, fecha, hora y descripción.",
             "metadata": {"source": "registro_avistamientos.md", "section": "Registrar un avistamiento",
                          "version": "1.0-didactica", "source_hash": "h"}, "similitud": 0.71}


class ClienteRPC:
    def __init__(self, filas=None, error=None):
        self.filas, self.error, self.llamadas = filas, error, []

    def rpc(self, nombre, params):
        self.llamadas.append((nombre, params))

        def ejecutar():
            if self.error:
                raise self.error
            return SimpleNamespace(data=self.filas)
        return SimpleNamespace(execute=ejecutar)
