import pytest

from almacenamiento import Almacenamiento, Autenticador
from app import BIENVENIDA, Aplicacion

URL, CLAVE = "https://x.supabase.co", "sb_publishable_x"


class SistemaStub:
    async def atender(self, texto, cliente, historial=None):
        return {"entrada": texto, "estado": "RESPONDER", "respuesta": f"Respuesta a: {texto} [F1]",
                "citas": ["F1"], "operaciones": 1, "duracion_ms": 1.0, "uso_tokens": [],
                "eventos": [{"paso": 1, "etapa": "DECISION_VALIDADA", "accion": "responder"}],
                "fuentes": {"F1": {"texto": "frag", "fuente": {"source": "s.md", "section": "x", "version": "1"}}},
                "historial_recibido": historial}


def crear_app(config, almacen, fabrica):
    return Aplicacion(config, SistemaStub(), Autenticador(URL, CLAVE, fabrica),
                      lambda token: Almacenamiento(URL, CLAVE, token, fabrica))


def test_flujo_completo_guardar_cerrar_sesion_y_recuperar(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    app = crear_app(config, almacen, fabrica)
    sesion, *_ = app.entrar("a@x.co", "clave123")
    conv, chat, _, lista, fuentes, estado = app.enviar("¿Cómo registro?", sesion, None, BIENVENIDA)
    assert conv and chat[-1]["content"].startswith("Respuesta a") and "s.md" in fuentes
    app.salir()                                      # cierre de sesión
    app2 = crear_app(config, almacen, fabrica)       # "reinicio" de la aplicación
    sesion2, *_ = app2.entrar("a@x.co", "clave123")
    opciones = app2._opciones(app2._almacenamiento(sesion2["access_token"]))
    assert [o[1] for o in opciones] == [conv]
    c, chat2, fuentes2, msg = app2.abrir(sesion2, conv)
    assert [m["role"] for m in chat2] == ["user", "assistant"] and "s.md" in fuentes2 and "2 mensajes" in msg


def test_el_historial_llega_al_sistema_como_turnos(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    app = crear_app(config, almacen, fabrica)
    sesion, *_ = app.entrar("a@x.co", "clave123")
    conv, *_ = app.enviar("primera", sesion, None, [])
    visto = {}

    async def espia(texto, cliente, historial=None):
        visto["h"] = historial
        return await SistemaStub().atender(texto, cliente, historial)
    app.sistema.atender = espia
    app.enviar("segunda", sesion, conv, [])
    assert visto["h"] == [{"usuario": "primera", "respuesta": "Respuesta a: primera [F1]"}]


def test_aislamiento_entre_dos_usuarios_en_la_interfaz(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co"); almacen.crear_usuario("b@x.co")
    app = crear_app(config, almacen, fabrica)
    sa, *_ = app.entrar("a@x.co", "clave123")
    sb, *_ = app.entrar("b@x.co", "clave123")
    conv_a, *_ = app.enviar("pregunta privada de A", sa, None, [])
    # B conoce el identificador de A e intenta abrirlo y escribir en él
    _, chat, _, msg = app.abrir(sb, conv_a)
    assert chat == BIENVENIDA and "no encontrada" in msg.lower()
    r = app.enviar("intruso", sb, conv_a, [])
    assert "no encontrada" in r[-1].lower()
    assert [m["contenido"] for m in app._almacenamiento(sa["access_token"]).obtener_mensajes(conv_a)][0] == "pregunta privada de A"
    assert len(almacen.tablas["resua_mensajes"]) == 2     # nada de B se escribió


def test_acciones_sin_sesion_se_rechazan(config, almacen, fabrica):
    app = crear_app(config, almacen, fabrica)
    assert "Inicia sesión" in app.enviar("hola", None, None, [])[-1]
    assert "Inicia sesión" in app.nueva(None)[-1]


def test_login_con_datos_invalidos(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    app = crear_app(config, almacen, fabrica)
    assert app.entrar("no-es-correo", "x")[0] is None
    r = app.entrar("a@x.co", "mala")
    assert r[0] is None and "incorrectos" in r[-1]


def test_si_no_se_guarda_no_se_muestra_exito(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    app = crear_app(config, almacen, fabrica)
    sesion, *_ = app.entrar("a@x.co", "clave123")
    almacen.fallar_insert_mensajes = True
    conv, chat, caja, _, _, estado = app.enviar("hola", sesion, None, [])
    assert chat == [] and caja == "hola" and "No pudimos" in estado


def test_validacion_de_entrada(config, almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    app = crear_app(config, almacen, fabrica)
    sesion, *_ = app.entrar("a@x.co", "clave123")
    assert app.enviar("   ", sesion, None, [])[-1] == "Escribe una pregunta."
    assert "1200" in app.enviar("x" * 1201, sesion, None, [])[-1]


def test_la_interfaz_gradio_se_construye(config, almacen, fabrica):
    assert crear_app(config, almacen, fabrica).construir() is not None
