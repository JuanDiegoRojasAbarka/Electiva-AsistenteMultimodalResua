"""Servidor MCP propio de RESUA: consulta de avistamientos (solo lectura).

Herramientas:
  - consultar_estado_avistamiento(codigo_avistamiento)  -> estado de un registro por código AVS-0000
  - buscar_avistamientos_por_especie(especie)           -> avistamientos cuya especie reportada coincide

Procedencia: adaptado del punto 4 del notebook de la Clase 11. Transporte por defecto: stdio
(el sistema lo lanza como subproceso). Para exponerlo de forma remota:
    python servidor_mcp.py --http      # streamable-http en 0.0.0.0:$MCP_PORT (por defecto 8000)

Los registros son FICTICIOS y sirven para demostrar las herramientas. No consultan la base
transaccional de RESUA y no hay operaciones de escritura. La especie es la REPORTADA por quien
observó; solo se considera confirmada cuando el estado es identificacion_completada.
"""
import os
import re
import sys
import unicodedata

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict, Field

mcp = MCPServer("Seguimiento de avistamientos RESUA")

AVISTAMIENTOS_DEMO = {
    "AVS-1001": {"tipo_registro": "avistamiento urbano", "estado": "pendiente_identificacion",
                 "detalle": "El reporte está registrado y requiere revisión de la identificación.",
                 "especie_reportada": "pelícano pardo", "nombre_cientifico": "Pelecanus occidentalis"},
    "AVS-1002": {"tipo_registro": "avistamiento urbano", "estado": "en_revision",
                 "detalle": "La evidencia del reporte está en revisión.",
                 "especie_reportada": "zarigüeya", "nombre_cientifico": "Didelphis marsupialis"},
    "AVS-1003": {"tipo_registro": "avistamiento urbano", "estado": "identificacion_completada",
                 "detalle": "La revisión de identificación del ejemplo fue completada.",
                 "especie_reportada": "iguana verde", "nombre_cientifico": "Iguana iguana"},
    "AVS-1004": {"tipo_registro": "avistamiento urbano", "estado": "en_revision",
                 "detalle": "La evidencia del reporte está en revisión.",
                 "especie_reportada": "pelícano pardo", "nombre_cientifico": "Pelecanus occidentalis"},
    "AVS-1005": {"tipo_registro": "avistamiento urbano", "estado": "pendiente_identificacion",
                 "detalle": "El reporte está registrado y requiere revisión de la identificación.",
                 "especie_reportada": "búho chico", "nombre_cientifico": "Megascops choliba"},
}

FUENTE = "avistamientos_ficticios_demo_RESUA"
MAX_RESULTADOS = 10


def _norm(texto: str) -> str:
    """Minúsculas, sin tildes ni signos: 'Pelícano' -> 'pelicano'."""
    sin = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sin.lower()).strip()


def _raiz(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") else token   # pelicanos -> pelicano


def coincide(especie_consultada: str, registro: dict) -> bool:
    """Cada palabra de la consulta (sin plural) debe ser prefijo de alguna palabra del nombre común o científico."""
    palabras = (_norm(registro["especie_reportada"]) + " " + _norm(registro["nombre_cientifico"])).split()
    tokens = [_raiz(t) for t in _norm(especie_consultada).split()]
    return bool(tokens) and all(any(p.startswith(t) for p in palabras) for t in tokens)


class Argumentos(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    codigo_avistamiento: str = Field(pattern=r"^AVS-[0-9]{4}$")


class ArgumentosEspecie(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    especie: str = Field(min_length=3, max_length=60, pattern=r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'-]*$")


class RegistroAvistamiento(BaseModel):
    tipo_registro: str
    estado: str
    detalle: str
    especie_reportada: str
    nombre_cientifico: str


class ResultadoEstado(BaseModel):
    codigo_avistamiento: str
    encontrada: bool
    registro: RegistroAvistamiento | None
    fuente: str


class ItemAvistamiento(BaseModel):
    codigo_avistamiento: str
    especie_reportada: str
    nombre_cientifico: str
    estado: str
    especie_confirmada: bool
    detalle: str


class ResultadoBusquedaEspecie(BaseModel):
    especie_consultada: str
    total: int
    mostrados: int
    avistamientos: list[ItemAvistamiento]
    fuente: str


@mcp.tool()
def consultar_estado_avistamiento(codigo_avistamiento: str) -> ResultadoEstado:
    """Consulta el estado de un registro ficticio de avistamiento por código AVS-0000. Solo lectura."""
    codigo = Argumentos(codigo_avistamiento=codigo_avistamiento).codigo_avistamiento
    registro = AVISTAMIENTOS_DEMO.get(codigo)
    return ResultadoEstado(codigo_avistamiento=codigo, encontrada=registro is not None,
                           registro=registro, fuente=FUENTE)


@mcp.tool()
def buscar_avistamientos_por_especie(especie: str) -> ResultadoBusquedaEspecie:
    """Lista los avistamientos ficticios cuya especie reportada coincide con el nombre común o científico
    (sin distinguir tildes ni plural; p. ej. 'pelícanos'). Solo lectura. La especie es la reportada, no confirmada,
    salvo que el estado sea identificacion_completada."""
    consulta = ArgumentosEspecie(especie=especie).especie.strip()
    hallados = [(c, r) for c, r in sorted(AVISTAMIENTOS_DEMO.items()) if coincide(consulta, r)]
    items = [ItemAvistamiento(codigo_avistamiento=c, especie_reportada=r["especie_reportada"],
                              nombre_cientifico=r["nombre_cientifico"], estado=r["estado"],
                              especie_confirmada=r["estado"] == "identificacion_completada", detalle=r["detalle"])
             for c, r in hallados[:MAX_RESULTADOS]]
    return ResultadoBusquedaEspecie(especie_consultada=consulta, total=len(hallados), mostrados=len(items),
                                    avistamientos=items, fuente=FUENTE)


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
    else:
        mcp.run(transport="stdio")
