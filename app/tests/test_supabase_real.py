"""Pruebas contra el Supabase REAL (RLS incluido). Se omiten si faltan las variables.

Requieren: SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, y dos cuentas de PRUEBA ya confirmadas en Auth:
  TEST_EMAIL_A / TEST_PASSWORD_A y TEST_EMAIL_B / TEST_PASSWORD_B.
Ejecutar:  python -m pytest tests/test_supabase_real.py -v
"""
import os

import pytest

from almacenamiento import Almacenamiento, Autenticador

V = ["SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "TEST_EMAIL_A", "TEST_PASSWORD_A", "TEST_EMAIL_B", "TEST_PASSWORD_B"]
pytestmark = pytest.mark.skipif(any(not os.environ.get(v) for v in V), reason="Faltan variables de Supabase real")


@pytest.fixture(scope="module")
def usuarios():
    url, clave = os.environ["SUPABASE_URL"], os.environ["SUPABASE_PUBLISHABLE_KEY"]
    aut = Autenticador(url, clave)
    sa = aut.iniciar_sesion(os.environ["TEST_EMAIL_A"], os.environ["TEST_PASSWORD_A"])
    sb = aut.iniciar_sesion(os.environ["TEST_EMAIL_B"], os.environ["TEST_PASSWORD_B"])
    return (Almacenamiento(url, clave, sa["access_token"]), Almacenamiento(url, clave, sb["access_token"]),
            url, clave, sa)


def test_persistencia_y_recuperacion(usuarios):
    a, _, url, clave, sa = usuarios
    c = a.crear_conversacion("prueba RLS")
    a.guardar_mensaje(c, "usuario", "pregunta de prueba")
    a.guardar_mensaje(c, "asistente", "respuesta de prueba")
    nuevo = Autenticador(url, clave).iniciar_sesion(os.environ["TEST_EMAIL_A"], os.environ["TEST_PASSWORD_A"])
    msgs = Almacenamiento(url, clave, nuevo["access_token"]).obtener_mensajes(c)
    assert [m["contenido"] for m in msgs] == ["pregunta de prueba", "respuesta de prueba"]


def test_rls_bloquea_a_otro_usuario_saltandose_la_comprobacion_de_la_app(usuarios):
    """Consulta directa con el cliente de B (sin pasar por _verificar_propietario): RLS debe devolver vacío
    y rechazar la inserción."""
    a, b, *_ = usuarios
    c = a.crear_conversacion("solo de A")
    a.guardar_mensaje(c, "usuario", "secreto de A")
    leidos = b.cliente.table("resua_mensajes").select("id").eq("conversacion_id", c).execute().data
    assert leidos == []
    conv = b.cliente.table("resua_conversaciones").select("id").eq("id", c).execute().data
    assert conv == []
    with pytest.raises(Exception):
        b.cliente.table("resua_mensajes").insert({"conversacion_id": c, "owner_id": b.user_id, "rol": "usuario",
                                                  "contenido": "intruso"}).execute()
    with pytest.raises(Exception):  # tampoco puede suplantar el propietario
        b.cliente.table("resua_mensajes").insert({"conversacion_id": c, "owner_id": a.user_id, "rol": "usuario",
                                                  "contenido": "suplantación"}).execute()
