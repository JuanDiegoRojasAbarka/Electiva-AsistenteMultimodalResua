# RESUA - Sistema de Registro de Avistamientos de Especies Silvestres

Manuela Velez Betancourt - Juan Diego Rojas Abarka

## Descripción

RESUA es un sistema orientado al registro y seguimiento de avistamientos de especies silvestres en zonas urbanas de Armenia, Quindío.

El proyecto incorpora un sistema de recuperación aumentada por generación (RAG) que permite consultar información documental relacionada con el registro de avistamientos, la evidencia disponible y el seguimiento de reportes.

## Tecnologías utilizadas

- Python
- Google Colab
- Supabase
- PostgreSQL y extensión pgvector
- Sentence Transformers
- Groq
- Pandas y NumPy
- BM25 para recuperación léxica
- Pydantic para validación de respuestas

## Modelo de embeddings

- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Dimensión: 384

## Modelo generativo

- Proveedor: Groq
- Modelo: `openai/gpt-oss-20b`

## Recuperación de información

Se evaluaron tres estrategias:

1. Búsqueda semántica.
2. Búsqueda híbrida mediante BM25 y Reciprocal Rank Fusion (RRF).
3. Búsqueda híbrida con reranking.

La estrategia seleccionada para el sistema fue la búsqueda semántica (`A_semantica`), considerando el equilibrio entre calidad de recuperación y tiempo de ejecución observado durante las pruebas.

## Configuración e instalación

1. Clonar el repositorio.
2. Instalar las dependencias:

   `pip install -r requirements.txt`

3. Crear un proyecto en Supabase.
4. Ejecutar el script `database/resua_vector_db.sql` en el SQL Editor de Supabase, revisando previamente si ya existen las tablas, índices y políticas.
5. Configurar las credenciales de Supabase y Groq mediante variables de entorno o los secretos de Google Colab.
6. Abrir y ejecutar el notebook ubicado en `notebooks/`.

## Estructura del repositorio

- `database/`: configuración SQL de la base de datos vectorial.
- `notebooks/`: implementación y evaluación del sistema RAG.
- `requirements.txt`: dependencias de Python.
- `.env.example`: plantilla de variables de entorno.

## Seguridad

No se deben publicar claves de Supabase, claves de Groq ni credenciales de acceso en el repositorio.

## Estado del proyecto

Proyecto académico en desarrollo.
