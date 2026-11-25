"""Interfaz Gradio de RESUA. Presenta el chat, gestiona la sesión de cada visitante y delega la lógica
en sistema.py y el historial en almacenamiento.py.

Ejecución local:  python app.py   (lee app/.env)
"""
import asyncio
import base64
import json
import logging
import os
import re
import time

import gradio as gr

from almacenamiento import Almacenamiento, Autenticador
from config import Config, cargar_config
from sistema import Sistema, formatear_fuentes

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BIENVENIDA = [{"role": "assistant", "content":
               "Hola, soy el asistente de RESUA. Pregúntame cómo registrar un avistamiento, cómo consultar su "
               "estado o dame un código **AVS-0000** para consultarlo."}]


def _exp_jwt(token: str) -> float:
    try:
        carga = token.split(".")[1]
        carga += "=" * (-len(carga) % 4)
        return float(json.loads(base64.urlsafe_b64decode(carga))["exp"])
    except Exception:
        return 0.0


class Aplicacion:
    def __init__(self, config: Config, sistema: Sistema, autenticador: Autenticador | None = None,
                 fabrica_almacenamiento=None):
        self.cfg, self.sistema = config, sistema
        self.auth = autenticador or Autenticador(config.supabase_url, config.supabase_key)
        self._almacenamiento = fabrica_almacenamiento or (
            lambda token: Almacenamiento(config.supabase_url, config.supabase_key, token))

    # -- sesión -----------------------------------------------------------
    def _vigente(self, sesion: dict | None) -> dict:
        if not sesion:
            raise PermissionError("Inicia sesión para continuar.")
        if _exp_jwt(sesion["access_token"]) - time.time() < 60:
            sesion = self.auth.renovar(sesion["refresh_token"])
        return sesion

    def _opciones(self, alm: Almacenamiento) -> list[tuple[str, str]]:
        return [(f"{c['titulo']}  ·  {str(c['creada_en'])[:16].replace('T', ' ')}", c["id"])
                for c in alm.listar_conversaciones()]

    @staticmethod
    def _mensajes_ui(msgs: list[dict]) -> list[dict]:
        return [{"role": "user" if m["rol"] == "usuario" else "assistant", "content": m["contenido"]} for m in msgs]

    # -- eventos ----------------------------------------------------------
    def entrar(self, email, password, registrarse):
        """Salidas: sesion, acceso, panel, lista, conv, chat, fuentes, quien, estado."""
        def fallo(msg):
            return (None, gr.update(visible=True), gr.update(visible=False), gr.update(choices=[], value=None),
                    None, BIENVENIDA, "", "", msg)
        if not EMAIL_RE.fullmatch((email or "").strip()) or not password:
            return fallo("Escribe un correo válido y una contraseña.")
        try:
            if registrarse:
                sesion = self.auth.registrar(email, password)
                if sesion is None:
                    return fallo("Cuenta creada. Confirma tu correo y luego inicia sesión.")
            else:
                sesion = self.auth.iniciar_sesion(email, password)
            opciones = self._opciones(self._almacenamiento(sesion["access_token"]))
        except (PermissionError, ValueError) as e:
            return fallo(str(e))
        except Exception:
            return fallo("No pudimos conectar con Supabase. Intenta de nuevo.")
        return (sesion, gr.update(visible=False), gr.update(visible=True), gr.update(choices=opciones, value=None),
                None, BIENVENIDA, "", f"Sesión: {sesion['email']}", "Sesión iniciada.")

    def salir(self):
        return (None, gr.update(visible=True), gr.update(visible=False), gr.update(choices=[], value=None),
                None, BIENVENIDA, "", "", "Sesión cerrada.")

    def nueva(self, sesion):
        try:
            alm = self._almacenamiento(self._vigente(sesion)["access_token"])
        except PermissionError as e:
            return gr.update(), None, BIENVENIDA, "", str(e)
        return gr.update(choices=self._opciones(alm), value=None), None, BIENVENIDA, "", "Conversación nueva: escribe tu primera pregunta."

    def abrir(self, sesion, conv_id):
        if not conv_id:
            return None, BIENVENIDA, "", ""
        try:
            sesion = self._vigente(sesion)
            msgs = self._almacenamiento(sesion["access_token"]).obtener_mensajes(conv_id)
        except PermissionError as e:
            return None, BIENVENIDA, "", str(e)
        except Exception:
            return None, BIENVENIDA, "", "No pudimos recuperar la conversación."
        ultimo = next((m for m in reversed(msgs) if m["rol"] == "asistente" and m["citas"]), None)
        fuentes = (ultimo or {}).get("metadata", {}).get("fuentes_md", "")
        return conv_id, self._mensajes_ui(msgs) or BIENVENIDA, fuentes, f"Conversación recuperada ({len(msgs)} mensajes)."

    def enviar(self, texto, sesion, conv_id, chat):
        chat = list(chat or [])
        if chat == BIENVENIDA:
            chat = []
        texto = (texto or "").strip()
        if not texto:
            return conv_id, chat, "", gr.update(), "", "Escribe una pregunta."
        if len(texto) > 1200:
            return conv_id, chat, texto, gr.update(), "", "La pregunta supera los 1200 caracteres."
        try:
            sesion = self._vigente(sesion)
            alm = self._almacenamiento(sesion["access_token"])
            nueva = conv_id is None
            if nueva:
                conv_id = alm.crear_conversacion(texto[:60])
            turnos = alm.turnos_recientes(conv_id)
            alm.guardar_mensaje(conv_id, "usuario", texto)
            traza = asyncio.run(self.sistema.atender(texto, alm.cliente, turnos))
            fuentes_md = formatear_fuentes(traza)
            alm.guardar_mensaje(conv_id, "asistente", traza["respuesta"], citas=traza["citas"],
                                metadata={"estado": traza["estado"], "operaciones": traza["operaciones"],
                                          "duracion_ms": traza["duracion_ms"], "fuentes_md": fuentes_md})
        except PermissionError as e:
            return conv_id, chat, texto, gr.update(), "", str(e)
        except Exception:
            return conv_id, chat, texto, gr.update(), "", "No pudimos guardar o procesar el mensaje. Intenta de nuevo."
        chat += [{"role": "user", "content": texto}, {"role": "assistant", "content": traza["respuesta"]}]
        info = {"estado": traza["estado"], "recorrido": traza["eventos"],
                "operaciones": traza["operaciones"], "duracion_ms": traza["duracion_ms"]}
        if traza.get("tipo_error"):
            info["tipo_error"] = traza["tipo_error"]
            if os.environ.get("RESUA_DEBUG") == "1":   # el detalle puede contener datos internos: solo en depuración
                info["detalle_error"] = traza.get("detalle_error")
                info["ultima_decision"] = traza.get("ultima_decision")
        detalle = json.dumps(info, ensure_ascii=False, indent=2)
        lista = gr.update(choices=self._opciones(alm), value=conv_id) if nueva else gr.update()
        panel_fuentes = (fuentes_md + "\n\n" if fuentes_md else "") + "```json\n" + detalle + "\n```"
        return conv_id, chat, "", lista, panel_fuentes, f"Estado: {traza['estado']}"

    # -- interfaz ---------------------------------------------------------
    def construir(self) -> gr.Blocks:
        with gr.Blocks(title="RESUA · Asistente de avistamientos") as demo:
            gr.Markdown("# RESUA · Asistente de avistamientos\nRegistro de especies silvestres en zonas urbanas de Armenia, Quindío.")
            sesion, conv = gr.State(None), gr.State(None)
            estado = gr.Markdown("")
            with gr.Group(visible=True) as acceso:
                email = gr.Textbox(label="Correo")
                password = gr.Textbox(label="Contraseña", type="password")
                with gr.Row():
                    b_in, b_reg = gr.Button("Iniciar sesión", variant="primary"), gr.Button("Crear cuenta")
            with gr.Row(visible=False) as panel:
                with gr.Column(scale=1):
                    quien = gr.Markdown("")
                    b_nueva, b_salir = gr.Button("Nueva conversación"), gr.Button("Cerrar sesión")
                    lista = gr.Dropdown(label="Mis conversaciones", choices=[], interactive=True)
                with gr.Column(scale=3):
                    chat = gr.Chatbot(value=BIENVENIDA, label="Chat", height=420)
                    caja = gr.Textbox(label="Tu pregunta", placeholder="¿Qué información necesito para registrar un avistamiento?")
                    b_env = gr.Button("Enviar", variant="primary")
                    with gr.Accordion("Fuentes y recorrido", open=False):
                        fuentes = gr.Markdown("")
            salida_entrar = [sesion, acceso, panel, lista, conv, chat, fuentes, quien, estado]
            b_in.click(lambda e, p: self.entrar(e, p, False), [email, password], salida_entrar)
            b_reg.click(lambda e, p: self.entrar(e, p, True), [email, password], salida_entrar)
            b_salir.click(self.salir, None, salida_entrar)
            b_nueva.click(self.nueva, [sesion], [lista, conv, chat, fuentes, estado])
            lista.input(self.abrir, [sesion, lista], [conv, chat, fuentes, estado])
            ev = [caja, sesion, conv, chat]
            sal = [conv, chat, caja, lista, fuentes, estado]
            b_env.click(self.enviar, ev, sal)
            caja.submit(self.enviar, ev, sal)
        return demo


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = cargar_config()
    sistema = Sistema(cfg)
    demo = Aplicacion(cfg, sistema).construir()
    # El puerto se abre ANTES de cargar el modelo: Render busca un puerto abierto y, si la descarga
    # del modelo tarda, declara "No open ports detected".
    demo.queue(default_concurrency_limit=4).launch(
        server_name=cfg.host, server_port=cfg.port, prevent_thread_lock=True)
    sistema.precalentar()                      # el modelo de embeddings se descarga aquí, una sola vez
    asyncio.run(sistema.descubrir_mcp())       # falla al arrancar si el MCP no está disponible
    logging.getLogger("resua").info("RESUA lista en %s:%s", cfg.host, cfg.port)
    demo.block_thread()

if __name__ == "__main__":
    main()