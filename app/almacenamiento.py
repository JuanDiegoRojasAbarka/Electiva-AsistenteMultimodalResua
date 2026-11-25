"""Historial de conversaciones por usuario en Supabase.

Reglas de diseño:
- La identidad sale de Supabase Auth: el access token se valida en el servidor de Supabase (get_user).
- Cada solicitud usa un cliente NUEVO con el token del usuario en la cabecera Authorization,
  de modo que RLS evalúa auth.uid(). No se comparte ningún cliente autenticado entre usuarios.
- Antes de leer o escribir mensajes, cada método comprueba que la conversación pertenece al usuario
  (defensa en profundidad; la política RLS es la segunda barrera).
"""
import re
from typing import Any, Callable

from supabase import ClientOptions, create_client

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
MAX_CONTENIDO = 8000


def _cliente(url: str, clave: str, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return create_client(url, clave, options=ClientOptions(
        persist_session=False, auto_refresh_token=False, headers=headers))


class Autenticador:
    """Operaciones de Supabase Auth con un cliente anónimo nuevo en cada llamada."""

    def __init__(self, url: str, clave: str, fabrica: Callable[..., Any] = _cliente):
        self._url, self._clave, self._fabrica = url, clave, fabrica

    def _sesion(self, r) -> dict:
        if r.user is None or r.session is None:
            raise PermissionError("Supabase no devolvió una sesión válida.")
        return {"access_token": r.session.access_token, "refresh_token": r.session.refresh_token,
                "user_id": r.user.id, "email": r.user.email}

    def iniciar_sesion(self, email: str, password: str) -> dict:
        try:
            r = self._fabrica(self._url, self._clave).auth.sign_in_with_password(
                {"email": email.strip(), "password": password})
        except Exception:
            raise PermissionError("Correo o contraseña incorrectos, o correo sin confirmar.") from None
        return self._sesion(r)

    def renovar(self, refresh_token: str) -> dict:
        try:
            r = self._fabrica(self._url, self._clave).auth.refresh_session(refresh_token)
        except Exception:
            raise PermissionError("La sesión expiró. Inicia sesión de nuevo.") from None
        return self._sesion(r)

    def validar_token(self, token: str) -> str:
        """Pregunta a Supabase quién es el dueño del token. Devuelve su user_id."""
        try:
            r = self._fabrica(self._url, self._clave).auth.get_user(token)
        except Exception:
            raise PermissionError("Token inválido o vencido.") from None
        if r is None or r.user is None:
            raise PermissionError("Token inválido o vencido.")
        return r.user.id


class Almacenamiento:
    """Acceso al historial de UN usuario autenticado (se crea por solicitud)."""

    def __init__(self, url: str, clave: str, token: str, fabrica: Callable[..., Any] = _cliente):
        self.user_id = Autenticador(url, clave, fabrica).validar_token(token)
        self.cliente = fabrica(url, clave, token)

    # -- conversaciones -------------------------------------------------
    def crear_conversacion(self, titulo: str = "Nueva conversación") -> str:
        fila = {"owner_id": self.user_id, "titulo": (titulo.strip() or "Nueva conversación")[:80]}
        datos = self.cliente.table("resua_conversaciones").insert(fila).execute().data
        if not datos or datos[0].get("owner_id") != self.user_id:
            raise RuntimeError("No se pudo crear la conversación.")
        return datos[0]["id"]

    def listar_conversaciones(self) -> list[dict]:
        return (self.cliente.table("resua_conversaciones").select("id,titulo,creada_en")
                .eq("owner_id", self.user_id).order("creada_en", desc=True).limit(100).execute().data)

    def _verificar_propietario(self, conversacion_id: str) -> None:
        if not isinstance(conversacion_id, str) or not UUID_RE.fullmatch(conversacion_id):
            raise PermissionError("Conversación no válida.")
        datos = (self.cliente.table("resua_conversaciones").select("id")
                 .eq("id", conversacion_id).eq("owner_id", self.user_id).limit(1).execute().data)
        if not datos:  # no existe o es de otra persona: mismo mensaje para no revelar cuál
            raise PermissionError("Conversación no encontrada para este usuario.")

    # -- mensajes -------------------------------------------------------
    def obtener_mensajes(self, conversacion_id: str, limite: int = 200) -> list[dict]:
        self._verificar_propietario(conversacion_id)
        return (self.cliente.table("resua_mensajes").select("id,rol,contenido,citas,metadata,creado_en")
                .eq("conversacion_id", conversacion_id).eq("owner_id", self.user_id)
                .order("id").limit(limite).execute().data)

    def guardar_mensaje(self, conversacion_id: str, rol: str, contenido: str,
                        citas: list | None = None, metadata: dict | None = None) -> int:
        self._verificar_propietario(conversacion_id)
        if rol not in ("usuario", "asistente"):
            raise ValueError("Rol no válido.")
        if not isinstance(contenido, str) or not contenido.strip() or len(contenido) > MAX_CONTENIDO:
            raise ValueError("Contenido vacío o demasiado largo.")
        fila = {"conversacion_id": conversacion_id, "owner_id": self.user_id, "rol": rol,
                "contenido": contenido, "citas": citas or [], "metadata": metadata or {}}
        datos = self.cliente.table("resua_mensajes").insert(fila).execute().data
        if not datos:
            raise RuntimeError("El mensaje no se guardó.")  # nunca anunciar éxito sin confirmación
        return datos[0]["id"]

    def turnos_recientes(self, conversacion_id: str, max_turnos: int = 4) -> list[dict]:
        """Convierte los últimos mensajes en turnos {usuario, respuesta} para el contexto del modelo."""
        msgs = self.obtener_mensajes(conversacion_id)
        turnos, pendiente = [], None
        for m in msgs:
            if m["rol"] == "usuario":
                pendiente = m["contenido"]
            elif pendiente is not None:
                turnos.append({"usuario": pendiente, "respuesta": m["contenido"]})
                pendiente = None
        return turnos[-max_turnos:]
