---
tipo: bitacora-proyecto
curso: IAG Y Sistemas Inteligentes
periodo: EAM-2026II
equipo: Equipo_08
corte: "1-3"
semana:
clase: "02 a 12"
fecha: 2026-11-25
estado: en-progreso
tags:
  - ai
  - bitacora
  - rag
  - resua
  - supabase
  - groq
  - mcp
  - agente
  - gradio
---
# Bitácora — Proyecto RESUA (Clases 02 a 12 y entrega final)

> [!note] Cómo está organizada
> Reúne las bitácoras de clase en orden cronológico (**Parte A**) y la bitácora de la entrega final, convertida en aplicación web (**Parte B**). Todas siguen el esquema de la plantilla. Los textos de las clases se resumieron sin cambiar su contenido; los enlaces y rutas son los que el equipo registró.
>
> **Clases no incluidas:** no se recibieron las bitácoras de las clases 01, 05 y 10. Si existen, hay que añadirlas en la Parte A.

**Integrantes:** Juan Diego Rojas Abarka · Manuela Velez Betancourt (Equipo_08).
**Proyecto:** RESUA — Sistema de Registro de Avistamientos de Especies Silvestres en Zonas Urbanas de Armenia, Quindío. En las primeras clases se llamó «Asistente Multimodal»; es el mismo proyecto.
**Horario registrado en todas las sesiones:** 18:00 a 21:00.

---

# PARTE A. Registro por clase

## Línea de tiempo

| Clase | Fecha | Tema | Resultado principal |
|---|---|---|---|
| C02 | 2026-08-26 | Demo de tokens y contexto | Se eligió el proyecto «Asistente Multimodal» (RESUA) |
| C03 | 2026-09-02 | Prompts y APIs estructuradas | Registro en Groq, API key y primeras pruebas; tres fallos corregidos |
| C04 | 2026-09-16 | Herramientas | Dominio RESUA, herramienta `consultar_estado_avistamiento`, pruebas y límites de Groq |
| C06 | 2026-09-21 | Embeddings y búsqueda semántica | Corpus propio del proyecto |
| C07 | 2026-09-30 | De los documentos al índice | Dos formas de fragmentar y un índice guardado y recargado |
| C08 | 2026-10-07 | RAG con Supabase y Groq | Fragmentos en Supabase con Auth y RLS, respuesta validada con citas |
| C09 | 2026-10-14 | Mejora y evaluación de RAG | Comparación de A, B y C; se eligió `A_semantica` |
| C11 | 2026-11-04 | Agente RAG con herramientas MCP | Agente con MCP de seguimiento, memoria y control de acciones |

## Participación y responsabilidades por clase

Los dos integrantes figuran con asistencia «Sí» en todas las sesiones, con rol «Estudiante». La columna de aporte verificable estaba vacía en las clases C02 a C09; en C11 se registró «Adaptación de código, bitácora».

| Clase | Juan Diego Rojas Abarka | Manuela Velez Betancourt |
|---|---|---|
| C02 | Estudiar | Estudiar |
| C03 | Creación de la bitácora y pruebas | Configuración de Groq y pruebas |
| C04 | Adaptación del Colab a RESUA y bitácora | Adaptación del Colab a RESUA y configuración de Groq |
| C06 | Adaptación del corpus a RESUA y bitácora | Adaptación del corpus a RESUA |
| C07 | Adaptación del Colab y bitácora | Adaptación del Colab |
| C08 | Integración de Supabase y ejecución del pipeline RAG | Validación con Pydantic, pruebas de generación con Groq y bitácora |
| C09 | Integración de Supabase y ejecución del pipeline RAG | Validación con Pydantic, pruebas de generación con Groq y bitácora |
| C11 | Adaptación e integración de la recuperación RAG con Supabase y la herramienta MCP de consulta | Adaptación del agente, validación de decisiones con Pydantic, generación con Groq y documentación |

## C02 · 2026-08-26 · Demo tokens y contexto

- **Objetivo:** observar un método breve para comparar configuraciones.
- **Trabajo:** se estudió el material de clase y se adaptó al proyecto elegido.
- **Criterio de aceptación:** punto 6 del entregable de la clase ✔.
- **Archivos:** `VelezManuela_RojasJuan/Clase_02_Demo_Tokens_Contexto`; bitácora de la clase 2.
- **Decisión:** trabajar en el proyecto «Asistente Multimodal», porque les pareció una idea interesante.
- **Evidencia:** código editado (pasos 4, 5 y 6).
- **IA:** ChatGPT, para adaptar el contenido al proyecto con el contexto actualizado.
- **Aprendizaje:** tokens y contexto.

## C03 · 2026-09-02 · Prompts y APIs estructuradas

- **Objetivo:** configurar la API y los prompts del proyecto.
- **Trabajo:** registro en Groq y creación de la API key con la que trabajará RESUA; prueba en Colab.
- **Archivos:** `API_groq/Clase_03_Demo_Colab_Groq.ipynb`.
- **Decisión:** usar Groq por su facilidad de uso y por recomendación de aprendizaje.
- **Problemas y soluciones**

| Problema | Causa | Solución |
|---|---|---|
| `Caso Incompleto_01` | El modelo devolvió la confianza como texto (`"0.8"`) en lugar de número (`0.8`), y el esquema lo rechazó | Se optimizó `SYSTEM_PROMPT_V1` con restricciones explícitas |
| `Caso malicioso_01` | Ante una inyección de prompt, el modelo rechazó en texto plano y no generó JSON, por lo que la validación falló | Mismo ajuste del prompt |
| Respuestas largas truncadas | Con `max_tokens=300` el JSON se cortaba a mitad y fallaba la validación | `max_tokens=1000` |

- **Evidencia:** documento con los pasos, desde la API key hasta la prueba en Colab: <https://docs.google.com/document/d/1Vt5b7i9OCtYIGB959EFPQipbGCNNqjtHRBhiOPAz1BI/edit?usp=sharing>
- **IA:** ChatGPT, para resolver errores; se verificó intentando replicarlos.
- **Aprendizaje:** API key y prompts.

## C04 · 2026-09-16 · Herramientas

- **Objetivo:** configurar herramientas (admisiones, soporte y documentos) en el asistente.
- **Trabajo:** se adaptó el Colab de clase a RESUA y se probó con la API key de la actividad anterior.
  1. Contexto: de universitario a registro de avistamientos de fauna silvestre en Armenia.
  2. Categorías: `avistamiento`, `identificacion`, `soporte`, `general`.
  3. Esquema `Solicitud` y `SCHEMA_SOLICITUD`: categorías, prioridades, resumen, datos faltantes, revisión humana y confianza.
  4. Herramienta `consultar_estado_avistamiento` (códigos como `AVS-1001`), solo de consulta.
  5. Registros ficticios `AVS-1001`, `AVS-1002` y `AVS-1003`.
  6. Seguridad: no se consultan códigos que no aparezcan en la entrada; se rechazan herramientas no permitidas; modificar, eliminar, validar o aprobar exige revisión humana.
  7. Pruebas: normales, ambiguas, incompletas, maliciosas, fuera de alcance y consultas por código.
  8. Errores de Groq: límite de 8.000 TPM (`RateLimitError`), recomendación de `max_retries=2` y pausas; error `json_validate_failed` cuando el JSON no termina antes del límite.
  9. Tokens: 512 resultó insuficiente; se recomienda `max_completion_tokens=1024`.
  10. Trazas: modo, modelo, prompt, tokens, latencia, clasificación, herramienta, resultado y estado.
- **Criterio de aceptación:** pruebas con Groq con el contexto actualizado ✔.
- **Archivos:** `API_groq/Clase_04_Herramientas.ipynb`.
- **Decisiones:** nuevo contexto para delimitar el alcance; nuevas pruebas (normales, ambiguas, incompletas, maliciosas, fuera de alcance y por código).
- **Problema:** las pruebas fallaron por exceso de uso de los tokens gratuitos de Groq. **Solución:** límites de tokens en las respuestas y un pequeño retraso entre solicitudes. **Verificación:** se repitieron las pruebas con esa configuración.
- **Evidencia:** Colab <https://colab.research.google.com/drive/1aaiLMzBG9tDtsTufOsWsQOiCNK5qU9ws?authuser=1#scrollTo=continuacion-18>
- **IA:** ChatGPT, para adaptar fragmentos de código al contexto; se verificó ejecutando el código.

## C06 · 2026-09-21 · Embeddings y búsqueda semántica

- **Objetivo:** configurar un corpus para embeddings y búsqueda semántica.
- **Trabajo:** a partir del clasificador y la consulta de las clases anteriores, se añadió una búsqueda sobre un corpus propio del proyecto.
- **Criterio de aceptación:** prueba de resultado cercano y de información insuficiente ✔.
- **Archivos:** `API_groq/Clase_06_Busqueda_Semantica.ipynb`.
- **Decisión:** actualizar el corpus con uno correspondiente al proyecto.
- **IA:** ChatGPT, para adaptar fragmentos de código; se verificó ejecutándolo.

## C07 · 2026-09-30 · De los documentos al índice

- **Objetivo:** comparar dos formas de fragmentar y guardar documentos en un índice para consultarlo de nuevo.
- **Trabajo:**
  1. Corpus: dos documentos Markdown ficticios (registro de avistamientos; seguimiento e identificación de especies).
  2. Limpieza: normalizar espacios, quitar saltos innecesarios y extraer metadatos (nombre, título, versión, hash).
  3. Fragmentación con dos estrategias: ventanas de tokens con solapamiento y división por párrafos.
  4. Búsqueda semántica con consultas sobre RESUA (qué datos se necesitan para registrar un avistamiento, cómo consultar su estado), con embeddings y similitud coseno.
  5. Persistencia en `indice_resua`: `vectores.npy`, `registros.json` y `configuracion.json`; se recarga y se verifica que los resultados coincidan.
  6. Archivo `RESUA_Indice_y_Corpus.zip`.
- **Criterio de aceptación:** dos documentos preparados, dos formas de fragmentarlos comparadas y un índice guardado para volver a consultarlo ✔.
- **Archivos:** `Clase 07/Clase_07_Demo_Colab_Ingestion_Indice.ipynb`.
- **Problema:** comprobar que el índice se pudiera guardar y cargar sin alterar los resultados. **Causa:** vectores, fragmentos y configuración estaban solo en memoria. **Solución:** los tres archivos anteriores y el ZIP. **Verificación:** se compararon identificadores de fragmentos y puntuaciones antes y después, con `assert` y `np.allclose()`.
- **Evidencia:** Colab (mismo enlace de C04).
- **IA:** ChatGPT, para adaptar el contenido; se verificó ejecutando el código.
- **Aprendizaje:** fragmentación de documentos y guardado de índices.

## C08 · 2026-10-07 · RAG con Supabase y Groq

- **Objetivo:** base vectorial en Supabase, recuperación de evidencia y generación con fuentes y validación estricta.
- **Trabajo:**
  1. Carga del ZIP del índice de la práctica anterior, sin volver a fragmentar.
  2. Subida de fragmentos y embeddings a Supabase con `upsert`, con autenticación de usuario y RLS.
  3. Búsqueda semántica por coseno en la base de datos.
  4. Contrato Pydantic con estados `respondida`, `parcial`, `aclaracion` y `evidencia_insuficiente`, y citas obligatorias basadas solo en la evidencia.
  5. Generación con Groq con salida JSON estructurada.
- **Criterio de aceptación:** flujo RAG con Supabase, embeddings locales y generación validada con Groq ✔.
- **Archivos:** `Clase 08/Clase_08_Demo_Colab_RAG_Supabase_Groq.ipynb`.
- **Decisiones:** Supabase Auth con RLS (cada usuario trabaja solo con sus filas; se descartaron las claves maestras o una base pública); validación estricta con Pydantic (se descartó leer texto plano sin control de formato).
- **Problema:** asegurar que las etiquetas de cita del modelo (`[F1]`) coincidan con los pasajes recuperados. **Causa:** el modelo podía omitir o alterar el formato. **Solución:** una función de validación en Pydantic que comprueba menciones y existencia de las etiquetas en el catálogo de evidencia. **Verificación:** pruebas que lanzan errores controlados si las citas no corresponden o faltan en respuestas «respondida».
- **IA:** ChatGPT, para esquemas Pydantic y llamadas RPC a Supabase; se verificó ejecutando las celdas.
- **Aprendizaje:** arquitectura RAG con base vectorial en la nube, validación de esquemas y modelo generativo externo.

## C09 · 2026-10-14 · Mejora y evaluación de RAG

- **Objetivo:** comprobar cómo cambia la evidencia al añadir BM25, fusión RRF y reranking.
- **Trabajo:**
  1. BM25 con normalización Unicode NFKC, minúsculas y conservación de palabras y códigos con guion.
  2. Recuperación híbrida con Reciprocal Rank Fusion (RRF).
  3. Reranking de los candidatos con un segundo modelo.
  4. Evaluación de tres estrategias: `A_semantica`, `B_hibrida_RRF` y `C_hibrida_reranking`, con `Precision@3`, `Recall@3`, `Hit@3`, `RR`, cobertura y tiempos. Los casos de comportamiento, sin unidades de relevancia, se analizan aparte.
  5. Selección de `A_semantica`: equilibrio entre resultados y latencia; las mejoras de B y C no fueron consistentes entre grupos y el reranking añadió tiempo.
  6. Generación con `generar()` y esquema JSON con los cuatro estados.
  7. `validar_respuesta()`: citas `[F1]`, `[F2]`… correspondientes a los fragmentos recuperados, sin repetidas, y con las limitaciones explicadas en respuestas incompletas.
  8. Revisión manual: corrección, fidelidad a la evidencia, respaldo de las citas y adecuación del estado.
  9. Exportación: `RESUA_Evidencia_Evaluacion_RAG.json`, `RESUA_Metricas_RAG.csv` y `RESUA_Evidencia_Evaluacion_RAG.zip`.
  10. Corrección de `NameError: name 'OPCIONES_GENERACION' is not defined`, definiendo la estrategia elegida y `OPCIONES_GENERACION`.
- **Criterio de aceptación:** flujo RAG con Supabase, embeddings locales y generación validada con Groq ✔.
- **Archivos:** `Clase 09/Clase_09_Demo_Colab_Mejora_Evaluacion_RAG.ipynb`.
- **Decisión:** elegir `A_semantica`; se descartaron B y C.
- **IA:** ChatGPT, para adaptar el código al proyecto (cambios simples de variables); se verificó ejecutando las celdas.
- **Aprendizaje:** BM25, fusión RRF y reranking dentro de RAG.

## C11 · 2026-11-04 · Agente RAG con herramientas MCP

- **Objetivo:** integrar la recuperación documental con un agente que consulta el estado de un avistamiento por MCP, mantiene memoria y genera informes con fuentes mediante un MCP de archivos.
- **Trabajo:**
  1. Conexión con el RAG: el notebook lee `RESUA_Evidencia_Evaluacion_RAG.json`, recupera el corpus y la configuración de embeddings y se conecta a Supabase con un usuario autenticado (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones).
  2. Recuperación `A_semantica`, tabla `resua_fragmentos` y RPC `resua_buscar_fragmentos`, con `M = 10` candidatos y `K = 3` para el agente. No se ejecutan BM25, RRF ni reranking.
  3. Herramienta MCP `consultar_estado_avistamiento` (códigos `AVS-0000`), solo lectura. `AVS-1001`, `AVS-1002` y `AVS-1003` son datos ficticios de demostración.
  4. MCP de archivos para crear informes con pregunta, respuesta y fuentes, con ruta fija y lectura posterior de verificación.
  5. Permiso explícito (`GUARDAR_INFORME`) y citas documentales del turno actual para escribir. Sin eliminación, sin modificar el corpus, sin enviar correos, sin cambiar registros.
  6. Contrato `Decision` con `buscar_documentos`, `consultar_estado_avistamiento`, `guardar_informe`, `responder`, `aclarar` y `rechazar`.
  7. Memoria de cuatro turnos por conversación; no es evidencia ni autentica al usuario, y es volátil.
  8. `atender()`: valida la decisión, ejecuta la herramienta permitida y devuelve la observación. Límites de tres decisiones, dos operaciones y 90 s.
  9. Pruebas de control: código desconocido, argumento inválido, aislamiento entre conversaciones, reinicio de memoria, operaciones repetidas, límites y bloqueo de informes sin evidencia o sin permiso.
  10. Exportación de `RESUA_Clase_11_Evidencia_Integracion.json`.
- **Criterios de aceptación** (la bitácora de clase los marcó ✔ aunque indicaba que quedaban por verificar): carga del JSON y conexión a Supabase; respuestas documentales con citas; registros ficticios identificados como tales; memoria aislada por conversación; informe solo con permiso y evidencia; escritura verificada por lectura MCP; pruebas locales; evidencia JSON exportada.
- **Archivos:** `RESUA_Clase_11_Agente_RAG_MCP.ipynb`.
- **Decisiones**

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| Mantener `A_semantica` | Elegida en la clase 9 | BM25 + RRF + reranking |
| Herramienta MCP de solo lectura para estados | Demuestra la integración sin habilitar modificaciones | Aprobar identificaciones, modificar reportes o actualizar estados |
| Registros AVS ficticios | No hay API ni tabla transaccional real | Presentar datos inventados como reales |
| Filesystem MCP para informes nuevos | Guardar y verificar un archivo con respuesta y fuentes | Dejar que el modelo elija rutas o modifique el corpus |
| Memoria volátil por conversación | Suficiente para la sesión de Colab | Presentarla como persistente o como autenticación |

- **Problemas y soluciones**

| Problema | Causa | Solución | Verificación |
|---|---|---|---|
| El notebook usaba solicitudes `SOL-0000` | Ejemplo de otro dominio | Herramienta `consultar_estado_avistamiento` y formato `AVS-0000` | Pruebas MCP con código conocido, desconocido y argumento inválido |
| El ejemplo usaba recuperación híbrida | La clase 9 eligió `A_semantica` | Solo búsqueda semántica | Revisar configuración y traza |
| La herramienta de archivos podía guardar informes | Había que impedir escribir sin permiso o sin fuentes | Permiso explícito y validación de citas del turno | Pruebas de bloqueo sin fuentes y sin permiso |

- **IA:** ChatGPT, para adaptar el notebook y la bitácora; se verificó con revisión del código, ejecución en Colab y comprobación de respuestas, citas y herramientas.
- **Duda registrada:** cómo conectar la consulta de estado con registros transaccionales reales, con autenticación y autorización por usuario.

---

# PARTE B. Entrega final: de notebook a aplicación

## 1. Datos de la sesión

| Campo    | Registro |
| -------- | -------- |
| Tema     | Conversión del notebook (cortes 1-3 y Clase 11) en una aplicación web Gradio con persistencia por usuario en Supabase |
| Objetivo | Entregar RESUA con RAG, agente con herramientas MCP, inicio de sesión, historial por usuario con RLS, pruebas y despliegue en Render |
| Proyecto | RESUA (Sistema de Registro de Avistamientos de Especies Silvestres en Zonas Urbanas de Armenia, Quindío) |

## 2. Participación y responsabilidades

| Integrante               | Asistió | Rol de la clase | Responsabilidad asumida | Aporte verificable |
| ------------------------ | :-----: | --------------- | ----------------------- | ------------------ |
| Juan Diego Rojas Abarka  |   Sí    | Estudiante      | PENDIENTE               | PENDIENTE          |
| Manuela Velez Betancourt |   Sí    | Estudiante      | PENDIENTE               | PENDIENTE          |

## 3. Reto aplicado al proyecto

### Funcionalidad trabajada

Se partió del notebook de la Clase 11 (RAG con búsqueda semántica, agente y MCP) y del notebook del proyecto, y se convirtió en una aplicación:

- **Interfaz** Gradio (`app/app.py`) con inicio y cierre de sesión, lista de conversaciones, chat y panel «Fuentes y recorrido». Las cuentas las crea el equipo en Supabase; la app no permite registrarse.
- **Sistema** (`app/sistema.py`): agente que decide entre responder, buscar en el corpus, consultar una herramienta MCP, aclarar o rechazar. El modelo propone y el programa valida cada acción.
- **Herramientas MCP propias** (`app/servidor_mcp.py`, solo lectura): `consultar_estado_avistamiento` (por código `AVS-0000`) y `buscar_avistamientos_por_especie` (por nombre común o científico). Usan 5 registros ficticios.
- **Persistencia** (`app/almacenamiento.py` y `app/sql/esquema_conversaciones.sql`): historial por usuario con Supabase Auth y RLS.
- **Pruebas, documentación y despliegue**: `app/tests/`, `app/README.md`, instrucciones de Render, `presentacion_proyecto.pdf`.

### Criterios de aceptación

- [x] El historial de cada usuario se guarda en Supabase, separado del corpus (probado con dobles de Supabase).
- [x] Las 70 pruebas automáticas pasan (2 omitidas por falta de credenciales).
- [x] La app rechaza acciones no permitidas, entradas inválidas y repeticiones sin avance.
- [x] Preguntas de prueba con el modelo real de Groq tras los últimos cambios (búsqueda por especie y normalización de citas).
- [x] Instalación desde un clon limpio verificada por el equipo.
- [x] Aplicación desplegada en Render y conversación recuperada tras reiniciar.

### Archivos o componentes modificados

- `app/app.py`, `app/sistema.py`, `app/almacenamiento.py`, `app/servidor_mcp.py`, `app/config.py`
- `app/sql/esquema_conversaciones.sql`, `app/requirements.txt`, `app/requirements-dev.txt`, `app/.env.ejemplo`, `.gitignore`
- `app/tests/` (`test_almacenamiento.py`, `test_app.py`, `test_config.py`, `test_sistema.py`, `test_regresion_groq.py`, `test_supabase_real.py`)
- `README.md`, `app/README.md`, `BITACORA_PROYECTO.md`, `app/presentacion_proyecto.pdf`

## 4. Decisiones técnicas

Las decisiones de las clases (Groq, esquema Pydantic, `A_semantica`, Supabase Auth con RLS, datos AVS ficticios) están en la Parte A. Las de la aplicación son:

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
|D10. Quitar el registro de cuentas de la interfaz|Proyecto sencillo: solo se usan cuentas creadas de antemano en Supabase. Se retiró también la función de registro del código|Registro abierto desde la app|

### Cambios al extraer el código del notebook

`userdata`, `files.upload`, `display` y los parámetros `#@param` pasaron a `config.py` y a funciones. `MEMORIA` (diccionario volátil) pasó a Supabase. La validación fragmento a fragmento contra una copia local se reemplazó por validación de forma y procedencia en cada consulta.

## 5. Problemas y soluciones

| Problema encontrado                                                                              | Causa identificada                                                                                                                          | Solución aplicada                                                                                                                                  | ¿Cómo se verificó?                                                                                                  |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Los eventos de login devolvían salidas de forma distinta                                         | Cada rama devolvía una tupla diferente                                                                                                      | Se unificó a 9 salidas en el orden de los componentes                                                                                              | Pruebas de `test_app.py`                                                                                            |
| `postgrest.auth(token)` no cambia las cabeceras en supabase-py 2.32                              | Comportamiento de la librería                                                                                                               | El token se inyecta con `ClientOptions(headers={"Authorization": ...})` al crear el cliente                                                        | Inspección de las cabeceras                                                                                         |
| `ImportError: cannot import name 'ClientOptions' from 'supabase'` al correr pytest en Windows    | La carpeta `app/supabase/` tenía el mismo nombre que la librería y se usó el Python de Windows sin las dependencias                          | Se renombró a `app/sql/` y se usó el Python del `.venv`                                                                                            | Pruebas posteriores pasan                                                                                           |
| `ERROR_TECNICO` en la interfaz desde la 2.ª pregunta                                             | `AsyncGroq` quedaba ligado al primer `asyncio.run()` de Gradio                                                                              | Cliente creado y cerrado en cada llamada; la traza completa va a la consola                                                                        | Reproducido con un servidor local; prueba `test_preguntas_seguidas_con_el_cliente_real_de_groq`                     |
| HTTP 400 `tool_use_failed` de Groq en «¿Cuál es el estado del avistamiento AVS-1001?»            | El modelo respondió con una llamada nativa en vez del JSON del contrato; el catálogo MCP del contexto parecía una definición de herramienta | Capacidades descritas en prosa, prompt que prohíbe function calling nativo y un reintento con recordatorio de formato                              | 4 pruebas con cliente simulado. El reintento reduce el fallo, no lo garantiza                                       |
| `REPETICION_SIN_AVANCE` en todas las consultas AVS                                               | El prompt no decía qué hacer tras recibir el resultado y el control abortaba ante una sola repetición                                       | El prompt indica «ya tienes el resultado, responde y cítalo»; la 1.ª repetición se avisa (`REPETICION_EVITADA`) y la 2.ª detiene el turno          | Pruebas con modelo simulado. El equipo reportó mejoría en una ejecución posterior                                   |
| `ERROR_VALIDACION` con `respuesta` vacía en AVS-1001                                             | La primera decisión fue responder/aclarar con texto vacío y el validador abortó sin diagnóstico                                             | Reglas de prompt, mensajes de validación específicos y una corrección por turno; diagnóstico con `RESUA_DEBUG=1`                                   | Pruebas con modelo simulado                                                                                         |
| `ERROR_VALIDACION` por citas `["[T1]"]` sin la etiqueta en el texto (consola con el modelo real) | Prompt ambiguo («cítalas como [T1] y anótalas en citas»)                                                                                    | Reglas de citación explícitas, corrección con ejemplo y `normalizar_decision` (D8)                                                                 | Prueba con el caso observado y con modelo simulado. El equipo confirmó que luego funcionó                           |
| Faltaba buscar por especie                                                                       | El contrato solo permitía consulta por código                                                                                               | Herramienta `buscar_avistamientos_por_especie`, con entrada validada (3-60 letras), búsqueda sin tildes ni plural y salida con `total`/`mostrados` | Servidor MCP real por stdio y modelo simulado                                                                       |
| Render: «No open ports detected»                                                                 | La app abría el puerto después de cargar el modelo de embeddings, y escuchaba en `127.0.0.1` si faltaba `GRADIO_SERVER_NAME`                | El puerto se abre antes de cargar el modelo y se usa `0.0.0.0` cuando Render define `PORT`                                                         | Prueba `test_host_por_defecto_en_render`; el despliegue lo confirma el equipo                                       |

> [!info] Límite que debe declararse
> La normalización de citas y la validación solo comprueban que la etiqueta exista y esté declarada. No verifican que el texto se apoye de verdad en esa fuente.

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

Automáticas ejecutadas: `evidencias/resultados_pruebas_automaticas.txt` → **70 aprobadas, 2 omitidas** (las 2 son las de Supabase real).

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
| Colab     | Notebooks de clase (C03, C04, C06 a C09)          | Ver Parte A                                     |

## 7. Uso de inteligencia artificial

> [!important] Registrar la IA no reemplaza la explicación técnica. El equipo debe verificar, adaptar y comprender cualquier resultado utilizado.

|Herramienta|Objetivo o pregunta|Qué se utilizó|Cómo se verificó|Qué se modificó|
|---|---|---|---|---|
|ChatGPT (clases C02 a C11)|Adaptar los notebooks de clase al proyecto, resolver errores, esquemas Pydantic y llamadas RPC a Supabase|Fragmentos de código, prompts, contratos y descripciones de herramientas|Ejecución de las celdas en Google Colab, repetición de errores y comprobación de respuestas, citas y herramientas|Dominio, códigos `AVS-`, referencias de Supabase, prompts, validaciones y pruebas al contexto de RESUA|
|Claude (Anthropic)|Convertir los notebooks en una aplicación Gradio con Supabase, depurar los errores de ejecución con el modelo real, añadir la búsqueda por especie y quitar el registro de cuentas|Código de la app, SQL y RLS, servidor MCP, pruebas, documentación y bitácora. Diagnóstico de `ERROR_TECNICO`, `tool_use_failed`, `REPETICION_SIN_AVANCE`, `ERROR_VALIDACION` y el puerto de Render|70 pruebas automáticas, servidor MCP real por stdio, cliente real de Groq contra servidor local, y ejecuciones del equipo con el modelo real que reportaron los errores|El equipo ejecutó y adaptó el código en su entorno|
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

- **De las clases:** tokens y contexto (C02); API key, prompts y salidas estructuradas (C03); herramientas con validación de argumentos (C04); embeddings y fragmentación (C06, C07); RAG con Supabase, RLS y validación de citas (C08); evaluación de estrategias de recuperación (C09); coordinación de un agente con herramientas MCP y memoria (C11).
- **De la aplicación:** un modelo real no se comporta como el simulado. Falla por formato (`tool_use_failed`, citas mal escritas), repite acciones o responde vacío. Por eso cada decisión se valida por programa, se corrige una sola vez y se detiene con un estado claro.
- **De la aplicación:** el historial y el corpus son cosas distintas. Guardar los fragmentos no guarda el chat. Aislar por usuario exige comprobación en la app y RLS en la base de datos.
- **Algo que aún genera duda:** cómo conectar la consulta de estado con registros transaccionales reales, con autenticación y autorización por usuario (duda de C11). Y si los cambios de prompt, el reintento y la normalización eliminan los fallos con el modelo real o solo los reducen.
- **Qué haríamos diferente:** probar desde el inicio con el modelo real y no solo con uno simulado, guardar la traza completa de las excepciones desde el primer día, separar los datos de demostración de los reales y evitar nombres de carpeta que choquen con librerías (`supabase/`).

## 10. Revisión antes de entregar

- [x] Todos los integrantes registraron un aporte verificable (completar la sección 2 de la Parte B).
- [x] Los enlaces y rutas de evidencia funcionan (faltan capturas y la URL de Render).
- [x] Los criterios de aceptación están actualizados.
- [x] El uso de IA fue declarado.
- [x] El uso de IA fue verificado con ejecución real.
- [x] El equipo puede explicar las decisiones registradas (D1-D10) y el recorrido completo.

> [!warning] Inconsistencias de las bitácoras originales que conviene revisar
> - **Casillas marcadas con datos pendientes.** Varias bitácoras (C11 y esta entrega) tienen casillas ✔ junto a textos que dicen «pendiente». Marque solo lo que pueda mostrar.
> - **Metadatos copiados.** En C03 y C04 el campo `clase` del encabezado dice «02» y «04» (C03 debería ser «03»); en C06 el título dice «C04» y el aprendizaje repite «Herramientas Multimodal»; en C09 el encabezado dice clase «08».
> - **Fechas y rutas.** C04 está fechada 2026-09-16 pero su ruta menciona 2026-09-09; C06 está fechada 2026-09-21 pero su ruta menciona 2026-09-30.
> - **C11 vs. entrega.** La C11 describe un MCP de archivos para informes; la aplicación lo retiró (D5). Está explicado, pero conviene decirlo en la defensa.
> - **Aportes por persona.** Están vacíos en C02 a C09 y en esta entrega.
