"""Servidor MCP propio de RESUA: consulta de estado de un avistamiento (solo lectura).

Procedencia: adaptado del punto 4 del notebook de la Clase 11. Transporte por defecto: stdio
(el sistema lo lanza como subproceso). Para exponerlo de forma remota:
    python servidor_mcp.py --http      # streamable-http en 0.0.0.0:$MCP_PORT (por defecto 8000)

Los registros son FICTICIOS y sirven para demostrar la herramienta. No consultan la base
transaccional de RESUA y no hay operaciones de escritura.
"""
import os
import sys

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict, Field

mcp = MCPServer("Seguimiento de avistamientos RESUA")

AVISTAMIENTOS_DEMO = {
    "AVS-1001": {
        "tipo_registro": "avistamiento urbano",
        "estado": "pendiente_identificacion",
        "detalle": "El reporte está registrado y requiere revisión de la identificación.",
    },
    "AVS-1002": {
        "tipo_registro": "avistamiento urbano",
        "estado": "en_revision",
        "detalle": "La evidencia del reporte está en revisión.",
    },
    "AVS-1003": {
        "tipo_registro": "avistamiento urbano",
        "estado": "identificacion_completada",
        "detalle": "La revisión de identificación del ejemplo fue completada.",
    },
}

FUENTE = "avistamientos_ficticios_demo_RESUA"


class Argumentos(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    codigo_avistamiento: str = Field(pattern=r"^AVS-[0-9]{4}$")


class RegistroAvistamiento(BaseModel):
    tipo_registro: str
    estado: str
    detalle: str


class ResultadoEstado(BaseModel):
    codigo_avistamiento: str
    encontrada: bool
    registro: RegistroAvistamiento | None
    fuente: str


@mcp.tool()
def consultar_estado_avistamiento(codigo_avistamiento: str) -> ResultadoEstado:
    """Consulta el estado de un registro ficticio de avistamiento por código AVS-0000. Solo lectura."""
    codigo = Argumentos(codigo_avistamiento=codigo_avistamiento).codigo_avistamiento
    registro = AVISTAMIENTOS_DEMO.get(codigo)
    return ResultadoEstado(
        codigo_avistamiento=codigo,
        encontrada=registro is not None,
        registro=registro,
        fuente=FUENTE,
    )


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
    else:
        mcp.run(transport="stdio")
