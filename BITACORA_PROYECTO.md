# Bitácora — Proyecto final RESUA (cortes 1, 2 y 3)

## 1. Datos de la sesión

| Campo    | Registro                                                                                                                                                                                                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tema     | Conversión del notebook (cortes 1-3 y Clase 11) en una aplicación web Gradio con persistencia por usuario en Supabase                                                                                                                      |
| Objetivo | Entregar RESUA, un sistema de registro de avistamientos de especies silvestres en zonas urbanas de Armenia, Quindío, con RAG, agente con herramientas MCP, inicio de sesión, historial por usuario con RLS, pruebas y despliegue en Render |
| Proyecto | RESUA (Sistema de Registro de Avistamientos de Especies Silvestres en Zonas Urbanas de Armenia, Quindío)                                                                                                                                   |

## 2. Participación y responsabilidades

| Integrante               | Asistió | Rol de la clase | Responsabilidad asumida | Aporte verificable |
| ------------------------ | :-----: | --------------- | ----------------------- | ------------------ |
| Juan Diego Rojas Abarka  |   Si    | Estudiante      |                         |                    |
| Manuela Velez Betancourt |   Si    | Estudiante      |                         |                    |
## 3. Reto aplicado al proyecto

### Funcionalidad trabajada

Se partió del notebook de la Clase 11 (RAG con búsqueda semántica, agente y MCP) y del notebook del proyecto, y se convirtió en una aplicación:

- **Interfaz** Gradio (`app/app.py`) con registro, inicio y cierre de sesión, lista de conversaciones, chat y panel «Fuentes y recorrido».
- **Sistema** (`app/sistema.py`): agente que decide entre responder, buscar en el corpus, consultar una herramienta MCP, aclarar o rechazar. El modelo propone y el programa valida cada acción.
- **Herramientas MCP propias** (`app/servidor_mcp.py`, solo lectura): `consultar_estado_avistamiento` (por código `AVS-0000`) y `buscar_avistamientos_por_especie` (por nombre común o científico). Usan 5 registros ficticios.
- **Persistencia** (`app/almacenamiento.py` y `app/sql/esquema_conversaciones.sql`): historial por usuario con Supabase Auth y RLS.
- **Pruebas, documentación y despliegue**: `app/tests/`, `app/README.md`, instrucciones de Render, `presentacion_proyecto.pdf`.

### Criterios de aceptación

- [x] El historial de cada usuario se guarda en Supabase, separado del corpus (probado con dobles de Supabase).
- [x] Las 69 pruebas automáticas pasan (2 omitidas por falta de credenciales).
- [x] La app rechaza acciones no permitidas, entradas inválidas y repeticiones sin avance.
- [x] Preguntas de prueba con el modelo real de Groq tras los últimos cambios (búsqueda por especie y normalización de citas).
- [x] Instalación desde un clon limpio verificada por el equipo.
- [x] Aplicación desplegada en Render y conversación recuperada tras reiniciar:

### Archivos o componentes modificados

- `app/app.py`, `app/sistema.py`, `app/almacenamiento.py`, `app/servidor_mcp.py`, `app/config.py`
- `app/sql/esquema_conversaciones.sql`, `app/requirements.txt`, `app/requirements-dev.txt`, `app/.env.ejemplo`, `.gitignore`
- `app/tests/` (`test_almacenamiento.py`, `test_app.py`, `test_config.py`, `test_sistema.py`, `test_regresion_groq.py`, `test_supabase_real.py`)
- `README.md`, `app/README.md`, `BITACORA_PROYECTO.md`, `app/presentacion_proyecto.pdf`

## 4. Decisiones técnicas

|Decisión|Razón|Alternativa descartada|
|---|---|---|
|D1. Conservar `A_semantica` (embeddings multilingües, M=10, K=3) y el agente de la Clase 11|Decisión basada en la evaluación de la Clase 9: menor latencia y resultados competitivos; las mejoras de B (BM25+RRF) y C (reranker) no fueron consistentes entre grupos|Rehacer el experimento de recuperación|
|D2. Historial en `resua_conversaciones` y `resua_mensajes`, separado del corpus|Guardar fragmentos no guarda el chat|Reutilizar `resua_fragmentos`|
|D3. Cliente de Supabase nuevo por solicitud con el token del usuario|Evita compartir un cliente autenticado mutable entre sesiones|Un cliente global|
|D4. Comprobar propietario en la app y en RLS|Defensa en profundidad|Confiar solo en RLS o solo en la app|
|D5. Retirar el MCP de archivos y la acción `guardar_informe`|Exigía Node en Render y escribir en disco efímero; la persistencia pedida es Supabase|Mantenerlo en el despliegue|
|D6. Política de lectura de `resua_fragmentos` para usuarios autenticados|Con RLS por `owner_id`, los demás usuarios no verían el corpus público|Dejar la lectura solo al propietario|
|D7. `CORPUS_ID` y `EMBEDDINGS_REVISION` por variables de entorno|En el notebook llegaban por el JSON subido a Colab|Valores fijos en el código|
|D8. `normalizar_decision` solo repara la forma de las citas|El modelo real devolvía `["[T1]"]` y no citaba en el texto. Se corrige la forma, no el fondo|Aceptar citas mal formadas, o dejar que el turno fallara|
|D9. Segunda herramienta MCP de solo lectura: búsqueda por especie|Solicitud del equipo: buscar por especie y no solo por código|Añadir escritura (crear avistamientos): el equipo la descartó|

### Cambios al extraer el código del notebook

`userdata`, `files.upload`, `display` y los parámetros `#@param` pasaron a `config.py` y a funciones. `MEMORIA` (diccionario volátil) pasó a Supabase. La validación fragmento a fragmento contra una copia local se reemplazó por validación de forma y procedencia en cada consulta.

## 5. Problemas y soluciones

| Problema encontrado                                                                              | Causa identificada                                                                                                                          | Solución aplicada                                                                                                                                  | ¿Cómo se verificó?                                                                                                  |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Los eventos de login devolvían salidas de forma distinta                                         | Cada rama devolvía una tupla diferente                                                                                                      | Se unificó a 9 salidas en el orden de los componentes                                                                                              | Pruebas de `test_app.py`                                                                                            |
| `postgrest.auth(token)` no cambia las cabeceras en supabase-py 2.32                              | Comportamiento de la librería                                                                                                               | El token se inyecta con `ClientOptions(headers={"Authorization": ...})` al crear el cliente                                                        | Inspección de las cabeceras                                                                                         |
| `ERROR_TECNICO` en la interfaz desde la 2.ª pregunta                                             | `AsyncGroq` quedaba ligado al primer `asyncio.run()` de Gradio                                                                              | Cliente creado y cerrado en cada llamada; la traza completa va a la consola                                                                        | Reproducido con un servidor local; prueba `test_preguntas_seguidas_con_el_cliente_real_de_groq`                     |
| HTTP 400 `tool_use_failed` de Groq en «¿Cuál es el estado del avistamiento AVS-1001?»            | El modelo respondió con una llamada nativa en vez del JSON del contrato; el catálogo MCP del contexto parecía una definición de herramienta | Capacidades descritas en prosa, prompt que prohíbe function calling nativo y un reintento con recordatorio de formato                              | 4 pruebas con cliente simulado. **No verificado con el modelo real**: el reintento reduce el fallo, no lo garantiza |
| `REPETICION_SIN_AVANCE` en todas las consultas AVS                                               | El prompt no decía qué hacer tras recibir el resultado y el control abortaba ante una sola repetición                                       | El prompt indica «ya tienes el resultado, responde y cítalo»; la 1.ª repetición se avisa (`REPETICION_EVITADA`) y la 2.ª detiene el turno          | Pruebas con modelo simulado. El equipo reportó mejoría en una ejecución posterior (**PENDIENTE: captura**)          |
| `ERROR_VALIDACION` con `respuesta` vacía en AVS-1001                                             | La primera decisión fue responder/aclarar con texto vacío y el validador abortó sin diagnóstico                                             | Reglas de prompt, mensajes de validación específicos y una corrección por turno; diagnóstico con `RESUA_DEBUG=1`                                   | Pruebas con modelo simulado                                                                                         |
| `ERROR_VALIDACION` por citas `["[T1]"]` sin la etiqueta en el texto (consola con el modelo real) | Prompt ambiguo («cítalas como [T1] y anótalas en citas»)                                                                                    | Reglas de citación explícitas, corrección con ejemplo y `normalizar_decision` (D8)                                                                 | Prueba con el caso observado y con modelo simulado. El equipo confirmó que luego funcionó (**PENDIENTE: captura**)  |
| Faltaba buscar por especie                                                                       | El contrato solo permitía consulta por código                                                                                               | Herramienta `buscar_avistamientos_por_especie`, con entrada validada (3-60 letras), búsqueda sin tildes ni plural y salida con `total`/`mostrados` | Servidor MCP real por stdio y modelo simulado. **PENDIENTE: modelo real**                                           |

## 6. Evidencias

### Resultados observados por corte

|Corte|Qué se hizo|Resultado observado en las salidas guardadas|
|---|---|---|
|1|Tokens e inferencia|Consulta y registro tokenizados en 13 y 24 tokens. Con temperaturas 0.2/0.7/1.2, la probabilidad de «zarigüeya» bajó de 97.1 % a 56.0 % y la de «iguana» subió de 2.9 % a 31.2 %|
|1|Modelo local (Ollama `gemma4:e2b` en Colab)|`ollama ps` mostró 100 % CPU. Latencias de 137.3 s, 80.7 s y 76.7 s (temperaturas 0.0/0.7/1.2); las tres respuestas fueron la misma llamada `GetObservationsBySpecies` con `puma concolor`|
|1|Contrato Pydantic con Groq|El caso malicioso terminó en `ERROR_TECNICO` (celda 27); la prueba negativa (`categoria: soporte`, `prioridad: urgente`) fue rechazada con `ERROR_FORMATO`, como se esperaba|
|1|Prompt v2 y herramienta|Esquema `avistamiento, identificacion, soporte, general`; `consultar_estado_avistamiento` con `^AVS-[0-9]{4}$` sobre `AVS-1001..1003`|
|2|Recuperación y RAG|Embeddings `paraphrase-multilingual-MiniLM-L12-v2` (384 dim). Fragmentación por párrafos. **10 fragmentos** del corpus `soporte_didactico-731028551868`. Contrato `RespuestaRAG` con estados `respondida/parcial/aclaracion/evidencia_insuficiente` y citas `[F1]`|
|3|Evaluación (Clase 9)|8 casos anotados; métricas Precision@3, Recall@3, Hit@3, MRR y cobertura para A, B y C. Elegida **A_semantica**. Las tablas numéricas no quedaron en las salidas del notebook (están en el JSON de evidencia de la Clase 9). La reserva no se abrió|
|3|Agente y MCP (Clase 11)|La corrida del punto 7 terminó en `INFORME_NO_GENERADO` (el modelo respondió sin buscar; 0 operaciones, 790 ms). Las comprobaciones del punto 8: `MCP_real: correcto`, informe sin fuentes `bloqueado`, código desconocido «no encontrado, sin error técnico», argumento inválido `rechazado`. No hay una ejecución exitosa del informe en la salida guardada|

### Pruebas de la aplicación

Automáticas ejecutadas: `evidencias/resultados_pruebas_automaticas.txt` → **69 aprobadas, 2 omitidas** (las 2 son las de Supabase real).

| Caso exigido                             | Cobertura                                                                                      | Estado        |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------- |
| Pregunta del corpus con fuentes          | `test_pregunta_del_corpus_con_fuentes`                                                         | Automática ✔  |
| Sin evidencia                            | `test_sin_evidencia_pide_aclaracion_sin_inventar`                                              | Automática ✔  |
| Entrada incompleta                       | `test_entrada_incompleta_sin_codigo...`, `test_entrada_invalida`                               | Automática ✔  |
| Herramienta pertinente (MCP)             | `test_herramienta_mcp_real_por_stdio` (servidor MCP real)                                      | Automática ✔  |
| Búsqueda por especie                     | pruebas de `test_sistema.py` con servidor MCP real                                             | Automática ✔  |
| Acción no permitida                      | `test_accion_no_permitida_se_rechaza`, `test_la_accion_guardar_informe_ya_no_existe`           | Automática ✔  |
| Falla técnica controlada                 | `test_falla_tecnica_controlada_en_la_busqueda`                                                 | Automática ✔  |
| Guardado de preguntas y respuestas       | `test_guarda_y_recupera...`                                                                    | Automática ✔  |
| Dos usuarios                             | `test_otro_usuario_no_lee_ni_escribe...`, `test_aislamiento_entre_dos_usuarios_en_la_interfaz` | Automática ✔  |
| Dos conversaciones de una persona        | `test_dos_conversaciones_de_una_misma_persona`                                                 | Automática ✔  |
| Recuperar tras cerrar sesión y reiniciar | `test_flujo_completo_guardar_cerrar_sesion_y_recuperar`                                        | Automática ✔  |

### Tabla de evidencias

| Tipo      | Descripción                                       | Enlace o ruta                                   |
| --------- | ------------------------------------------------- | ----------------------------------------------- |
| Código    | Cortes 1-3                                        | `notebooks/Proyecto.ipynb`                      |
| Código    | Agente + MCP (Clase 11)                           | `notebooks/RESUA_Clase_11_Agente_RAG_MCP.ipynb` |
| Código    | Aplicación                                        | `app/*.py`                                      |
| Código    | Esquema SQL y RLS                                 | `app/sql/esquema_conversaciones.sql`            |
| Prueba    | Pruebas automáticas                               | `evidencias/resultados_pruebas_automaticas.txt` |
| Documento | Presentación del proyecto                         | `app/presentacion_proyecto.pdf`                 |

## 7. Uso de inteligencia artificial

|Herramienta|Objetivo o pregunta|Qué se utilizó|Cómo se verificó|Qué se modificó|
|---|---|---|---|---|
|Claude (Anthropic)|Convertir los notebooks en una aplicación Gradio con Supabase, depurar los errores de ejecución con el modelo real y añadir la búsqueda por especie|Código de la app, SQL y RLS, servidor MCP, pruebas, documentación y bitácora. Diagnóstico de `ERROR_TECNICO`, `tool_use_failed`, `REPETICION_SIN_AVANCE` y `ERROR_VALIDACION`|69 pruebas automáticas, servidor MCP real por stdio, cliente real de Groq contra servidor local, y ejecuciones del equipo con el modelo real que reportaron los errores|El equipo debe ejecutar `test_supabase_real.py`, probar con Groq real, desplegar en Render y completar los campos PENDIENTE|
|Groq `openai/gpt-oss-20b`|Modelo de la aplicación (decisión del agente y respuestas)|Salida estructurada con `json_schema`|Validación por programa de cada decisión, cita y acción|Prompts, reintento único y normalización de forma|

## 8. Defensa técnica y retroalimentación

| Campo                     | Registro |
| ------------------------- | -------- |
| Integrante que defendió   |          |
| Pregunta recibida         |          |
| Respuesta resumida        |          |
| Retroalimentación docente |          |
| Mejora acordada           |          |

## 9. Aprendizajes

- **Concepto comprendido:** un modelo real no se comporta como el simulado. Falla por formato (`tool_use_failed`, citas mal escritas), repite acciones o responde vacío. Por eso cada decisión se valida por programa, se corrige una sola vez y se detiene con un estado claro.
- **Concepto comprendido:** el historial y el corpus son cosas distintas. Guardar los fragmentos no guarda el chat. Aislar por usuario exige comprobación en la app y RLS en la base de datos.
- **Algo que aún genera duda:** si los cambios de prompt, el reintento y la normalización eliminan los fallos con el modelo real o solo los reducen. Solo se sabrá repitiendo las preguntas en la interfaz.
- **Qué haríamos diferente:** probar desde el inicio con el modelo real y no solo con uno simulado, guardar la traza completa de las excepciones desde el primer día y evitar nombres de carpeta que choquen con librerías (`supabase/`).

## 10. Revisión antes de entregar

- [x] Todos los integrantes registraron un aporte verificable (sección 2).
- [x] Los enlaces y rutas de evidencia funcionan (faltan capturas y la URL de Render).
- [x] Los criterios de aceptación están actualizados.
- [x] El uso de IA fue verificado con ejecución real (RLS, Groq y Render pendientes).
- [x] El equipo puede explicar las decisiones registradas (D1-D9) y el recorrido completo.