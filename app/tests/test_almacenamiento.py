import pytest

from almacenamiento import Almacenamiento, Autenticador

URL, CLAVE = "https://x.supabase.co", "sb_publishable_x"


def entrar(almacen, fabrica, email):
    almacen.crear_usuario(email)
    s = Autenticador(URL, CLAVE, fabrica).iniciar_sesion(email, "clave123")
    return s, Almacenamiento(URL, CLAVE, s["access_token"], fabrica)


def test_guarda_y_recupera_preguntas_y_respuestas(almacen, fabrica):
    s, alm = entrar(almacen, fabrica, "a@x.co")
    c = alm.crear_conversacion("¿Cómo registro?")
    alm.guardar_mensaje(c, "usuario", "¿Cómo registro?")
    alm.guardar_mensaje(c, "asistente", "Indique ubicación [F1].", citas=["F1"])
    tok = Autenticador(URL, CLAVE, fabrica).iniciar_sesion("a@x.co", "clave123")["access_token"]
    msgs = Almacenamiento(URL, CLAVE, tok, fabrica).obtener_mensajes(c)  # otra solicitud / app reiniciada
    assert [m["rol"] for m in msgs] == ["usuario", "asistente"] and msgs[1]["citas"] == ["F1"]


def test_dos_conversaciones_de_una_misma_persona(almacen, fabrica):
    _, alm = entrar(almacen, fabrica, "a@x.co")
    c1, c2 = alm.crear_conversacion("uno"), alm.crear_conversacion("dos")
    alm.guardar_mensaje(c1, "usuario", "msg 1")
    alm.guardar_mensaje(c2, "usuario", "msg 2")
    assert c1 != c2 and len(alm.listar_conversaciones()) == 2
    assert [m["contenido"] for m in alm.obtener_mensajes(c1)] == ["msg 1"]
    assert [m["contenido"] for m in alm.obtener_mensajes(c2)] == ["msg 2"]


def test_otro_usuario_no_lee_ni_escribe_aunque_conozca_el_id(almacen, fabrica):
    _, a = entrar(almacen, fabrica, "a@x.co")
    _, b = entrar(almacen, fabrica, "b@x.co")
    c = a.crear_conversacion("privada")
    a.guardar_mensaje(c, "usuario", "secreto de A")
    with pytest.raises(PermissionError):
        b.obtener_mensajes(c)
    with pytest.raises(PermissionError):
        b.guardar_mensaje(c, "usuario", "intruso")
    assert b.listar_conversaciones() == []
    assert [m["contenido"] for m in a.obtener_mensajes(c)] == ["secreto de A"]


def test_token_invalido_y_id_malformado(almacen, fabrica):
    with pytest.raises(PermissionError):
        Almacenamiento(URL, CLAVE, "token-falso", fabrica)
    _, a = entrar(almacen, fabrica, "a@x.co")
    with pytest.raises(PermissionError):
        a.obtener_mensajes("1; drop table")


def test_no_anuncia_exito_si_el_guardado_falla(almacen, fabrica):
    _, a = entrar(almacen, fabrica, "a@x.co")
    c = a.crear_conversacion("x")
    almacen.fallar_insert_mensajes = True
    with pytest.raises(RuntimeError):
        a.guardar_mensaje(c, "usuario", "hola")


def test_validaciones_de_mensaje(almacen, fabrica):
    _, a = entrar(almacen, fabrica, "a@x.co")
    c = a.crear_conversacion("x")
    for rol, txt in [("sistema", "hola"), ("usuario", "   "), ("usuario", "x" * 9000)]:
        with pytest.raises(ValueError):
            a.guardar_mensaje(c, rol, txt)


def test_turnos_recientes_limita_a_cuatro(almacen, fabrica):
    _, a = entrar(almacen, fabrica, "a@x.co")
    c = a.crear_conversacion("x")
    for i in range(6):
        a.guardar_mensaje(c, "usuario", f"p{i}")
        a.guardar_mensaje(c, "asistente", f"r{i}")
    t = a.turnos_recientes(c, 4)
    assert len(t) == 4 and t[0]["usuario"] == "p2" and t[-1]["respuesta"] == "r5"


def test_login_incorrecto(almacen, fabrica):
    almacen.crear_usuario("a@x.co")
    with pytest.raises(PermissionError):
        Autenticador(URL, CLAVE, fabrica).iniciar_sesion("a@x.co", "mala")
