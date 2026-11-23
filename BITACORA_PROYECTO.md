# Bitácora del proyecto RESUA (cortes 1, 2 y 3)

*Sistema de Registro de Avistamientos de Especies Silvestres en Zonas Urbanas de Armenia, Quindío.*
IA Generativa y Sistemas Inteligentes · EAM 2026-II · Prof. Robert Garcia Rey.
Integrantes: **PENDIENTE: nombres del equipo**. Esta bitácora se redactó a partir de los notebooks `notebooks/Proyecto.ipynb` y
`notebooks/RESUA_Clase_11_Agente_RAG_MCP.ipynb` y de la carpeta `app/`. Cuando un dato no figura en las salidas guardadas de los
notebooks, se indica «no registrado» en lugar de suponerlo.

## 1. Problema y alcance
Ciudadanos reportan fauna silvestre urbana y necesitan saber qué datos aportar, cómo consultar el estado del reporte y qué
límites tiene la identificación de especies. Alcance, exclusiones y usuarios: ver `app/README.md` §1.

## 2. Arquitectura final
Gradio (`app.py`) → `sistema.py` (agente + RAG + cliente MCP) → Groq `openai/gpt-oss-20b`; Supabase para Auth, corpus vectorial
(`resua_fragmentos`) e historial (`resua_conversaciones`, `resua_mensajes`, con RLS). Diagrama y recorrido: `app/README.md` §2.

## 3. Corte 1 · Modelo, contratos y herramienta (notebook, celdas 1-38)
- **Tokens e inferencia.** Se tokenizaron una consulta y un registro de base de datos (13 y 24 tokens; el nombre «Castellana» se
  parte en varias piezas). Con temperaturas 0.2/0.7/1.2, la probabilidad de «zarigüeya» bajó de 97.1 % a 56.0 % mientras subían
  las alternativas (iguana 2.9 % → 31.2 %).
- **Modelo local.** Ollama con `gemma4:e2b` en Colab: `ollama ps` mostró **100 % CPU** (no GPU); las latencias fueron 137.3 s,
  80.7 s y 76.7 s para temperaturas 0.0/0.7/1.2 con ~262 tokens de entrada. Las tres respuestas fueron la misma llamada de herramienta
  `GetObservationsBySpecies` con `puma concolor`.
- **Contrato de salida con Pydantic y Groq.** Primera versión del esquema: categorías `avistamiento, consulta_fauna, emergencia_animal,
  general`. Cinco casos (normal, emergencia, ambiguo, malicioso, fuera de alcance). Resultado observado de la corrida con Groq:
  el caso malicioso terminó en `ERROR_TECNICO` en la traza de la celda 27, y la prueba negativa (`categoria: soporte`,
  `prioridad: urgente`) fue rechazada con `ERROR_FORMATO`, como se esperaba.
- **Reformulación (prompt v2 `resua_v2_herramienta`).** Se cambió el esquema a `avistamiento, identificacion, soporte, general`, se
  añadieron reglas de revisión humana y consultas de estado con código `AVS-0000`.
- **Herramienta.** `consultar_estado_avistamiento` sobre tres registros ficticios (`AVS-1001..1003`), argumentos validados con
  `^AVS-[0-9]{4}$` y comprobación de que el código aparezca en la entrada.

## 4. Corte 2 · Recuperación y RAG (celdas 39-64)
- Embeddings `paraphrase-multilingual-MiniLM-L12-v2` (384 dim, normalizados, coseno) y búsqueda semántica frente a búsqueda literal.
- Corpus: 2 documentos Markdown; comparación de dos estrategias de fragmentación (ventanas por tokens vs. párrafos); se usó
  **párrafos** (ver valor por defecto de `ESTRATEGIA`). Resultado en Supabase: **10 fragmentos** del corpus
  `soporte_didactico-731028551868` (salida de la Clase 11).
- Persistencia en `resua_fragmentos` con `owner_id`, metadatos de procedencia (`source`, `section`, `version`, `source_hash`) y revisión del modelo.
- Generación con contrato `RespuestaRAG` (estados `respondida/parcial/aclaracion/evidencia_insuficiente`) y validación de citas
  `[F1]`; cinco pruebas de comportamiento; comprobación de que otro cliente recupera los mismos fragmentos (Clase 8).

## 5. Corte 3 · Evaluación, agente y MCP (celdas 65-77 y Clase 11)
- **Evaluación (Clase 9).** Ocho casos anotados (R1-R3, S1-S2, I1, C1-C2), métricas Precision@3, Recall@3, Hit@3, MRR y cobertura
  para A (semántica), B (BM25 + RRF, c=60) y C (B + reranker `mmarco-mMiniLMv2`). Decisión registrada: **A_semantica**, «por su menor
  latencia y resultados competitivos; las mejoras de B y C no fueron consistentes entre grupos». Las tablas numéricas no quedaron en las
  salidas guardadas del notebook; el JSON de evidencia de la Clase 9 las contiene. La reserva no se abrió.
- **Agente y MCP (Clase 11).** Decisión JSON validada, máximo 3 decisiones y 2 operaciones, 90 s, memoria de 4 turnos, MCP de
  seguimiento por stdio (protocolo `2026-07-28` en la salida) y MCP de archivos. Observado: la corrida del punto 7 terminó
  en `INFORME_NO_GENERADO` (el modelo respondió sin buscar y el control lo detuvo; 0 operaciones, 790 ms), y las comprobaciones
  locales del punto 8 dieron `MCP_real: correcto`, informe sin fuentes/permiso `bloqueado`, código desconocido «no encontrado, sin
  error técnico», argumento inválido `rechazado`. La salida guardada no muestra una ejecución exitosa del informe.

## 6. Corte final · De notebook a aplicación (esta entrega)
### Decisiones técnicas
| # | Decisión | Motivo |
|---|---|---|
| D1 | Conservar A_semantica y el agente de la Clase 11 | Decisión basada en evaluación; no se rehízo el experimento |
| D2 | Historial en `resua_conversaciones` / `resua_mensajes`, separado del corpus | Guardar fragmentos no guarda el chat |
| D3 | Un cliente de Supabase **nuevo por solicitud** con el token del usuario | Evita compartir un cliente autenticado mutable |
| D4 | Comprobar propietario en la app **y** en RLS | Defensa en profundidad |
| D5 | **Retirar** el MCP de archivos y la acción `guardar_informe` | Exigía Node en Render y una escritura en disco efímero del servidor; la persistencia pedida es Supabase. El MCP propio de lectura cubre el requisito |
| D6 | Política de lectura de `resua_fragmentos` para autenticados | Con RLS por `owner_id`, otros usuarios no verían el corpus público |
| D7 | `CORPUS_ID` y `EMBEDDINGS_REVISION` por entorno | Antes llegaban por el JSON subido a Colab |
| D9 | Segunda herramienta MCP `buscar_avistamientos_por_especie` (solo lectura) y campo `especie_reportada` en los registros ficticios | Solicitud del equipo: buscar avistamientos por especie, no solo por código. Se amplía el contrato de decisión con el campo `especie`; no se añade ninguna escritura |

### Cambios al extraer el código
`userdata`, `files.upload`, `display`, parámetros `#@param` → `config.py`/funciones; `MEMORIA` (dict volátil) → Supabase;
modelo de embeddings y cliente Groq se crean una vez; validación fragmento a fragmento contra una copia local (`por_id`) se
reemplazó por validación de forma y procedencia en cada consulta (la copia local exigía leer el corpus del propietario).

### Errores corregidos durante la construcción
1. `autocomplete` no existe en `gr.Textbox` de Gradio 6.32 → retirado (la prueba de construcción de la interfaz lo detectó).
2. Las salidas de los eventos de login tenían forma distinta según el caso → se unificó a 9 salidas en el orden de los componentes.
3. `postgrest.auth(token)` no modifica las cabeceras de la sesión HTTP en supabase-py 2.32 → el token se inyecta con
   `ClientOptions(headers={"Authorization": ...})` al crear el cliente (verificado inspeccionando las cabeceras).
4. El entorno de trabajo se reinició y eliminó directorios vacíos; se recrearon y se volvieron a ejecutar las pruebas.
5. **Carpeta `app/supabase/` con el mismo nombre que la librería `supabase`**: si la librería no estaba instalada en el Python
   usado, Python importaba la carpeta y fallaba con `cannot import name 'ClientOptions' … (unknown location)`. Se renombró a `app/sql/`.
6. **Cliente `AsyncGroq` reutilizado entre preguntas**: Gradio ejecuta cada mensaje en un `asyncio.run()` nuevo y el cliente quedaba
   ligado al primer bucle; con el servidor local de pruebas, la 1.ª llamada funcionó y la 2.ª falló (`APIConnectionError`), lo que en
   la interfaz aparecía como `ERROR_TECNICO`. Ahora se crea y cierra un cliente por llamada (prueba de regresión
   `test_preguntas_seguidas_con_el_cliente_real_de_groq`). Además `ERROR_TECNICO` registra la traza completa en la consola.
7. **`tool_use_failed` de Groq** (observado en la ejecución local del equipo, consulta «¿Cuál es el estado del avistamiento AVS-1001?»):
   el modelo respondió con una llamada nativa `tool_mcp_consultar_estado_avistamiento` en lugar del JSON del contrato y Groq devolvió
   HTTP 400. Causa probable: el contexto incluía el catálogo MCP con nombre y esquema, que se parece a la definición de una herramienta.
   Cambios: el contexto describe las capacidades en prosa («acción del contrato, no es una herramienta nativa»), el prompt prohíbe
   function calling nativo y la app reintenta **una vez** con un recordatorio de formato (la generación fallida nunca se ejecuta).
   Cuatro pruebas lo cubren con un cliente simulado; **no se verificó con el modelo real**, y como el comportamiento del modelo es
   probabilístico, el reintento reduce pero no garantiza la ausencia del fallo.
8. **`REPETICION_SIN_AVANCE` en todas las consultas de estado AVS** (observado por el equipo): el recorrido mostraba paso 1 con la
   operación MCP ejecutada y `RESULTADO_RECIBIDO`, y en el paso 2 el modelo volvía a proponer la misma operación; el control aborta
   ante cualquier repetición, por lo que nunca se llegaba a responder. Causas: el prompt no decía qué hacer tras recibir un resultado
   y el control era demasiado estricto con una sola repetición. Cambios: (a) el prompt y el contexto indican «ya tienes el resultado
   (etiquetas T1…), responde y cítalo»; (b) la primera repetición no se re-ejecuta, se avisa al modelo (evento `REPETICION_EVITADA`) y
   se le da otra decisión; una segunda repetición detiene el recorrido. Pruebas nuevas con modelo simulado; **no verificado con
   el modelo real**: pendiente repetir la consulta AVS-1001/1002/1003/9999 desde la interfaz.
9. **`ERROR_VALIDACION` en la consulta AVS-1001** (observado por el equipo): `recorrido` vacío y `detalle_error` «La respuesta está vacía
   o excede el límite», es decir, la primera decisión del modelo fue `responder`/`aclarar`/`rechazar` con `respuesta` vacía y el
   validador abortó el turno sin diagnóstico. Cambios: (a) el prompt dice que esas acciones exigen texto y que una pregunta de estado
   con código AVS debe usar `consultar_estado_avistamiento`; (b) mensajes de validación específicos; (c) **una corrección por turno**:
   se devuelve el motivo al modelo y la nueva decisión pasa por la misma validación (una segunda decisión inválida termina en
   `ERROR_VALIDACION`); (d) la decisión inválida se registra en la consola y, con `RESUA_DEBUG=1`, se muestra como `ultima_decision`.
   Probado con modelo simulado; **no verificado con el modelo real**.

## 7. Pruebas y resultados
**Automáticas (ejecutadas):** `evidencias/resultados_pruebas_automaticas.txt` → **69 aprobadas, 2 omitidas** (las 2 omitidas son las de
Supabase real, por falta de credenciales en este entorno).

| Caso exigido | Cobertura | Estado |
|---|---|---|
| Pregunta del corpus con fuentes | `test_pregunta_del_corpus_con_fuentes` (modelo simulado) | Automática ✔ · **con Groq real: PENDIENTE** |
| Sin evidencia | `test_sin_evidencia_pide_aclaracion_sin_inventar` | Automática ✔ · real: PENDIENTE |
| Entrada incompleta | `test_entrada_incompleta_sin_codigo...`, `test_entrada_invalida` | Automática ✔ · real: PENDIENTE |
| Herramienta pertinente (MCP) | `test_herramienta_mcp_real_por_stdio` (servidor MCP real) | Automática ✔ |
| Acción no permitida | `test_accion_no_permitida_se_rechaza`, `test_la_accion_guardar_informe_ya_no_existe` | Automática ✔ |
| Falla técnica controlada | `test_falla_tecnica_controlada_en_la_busqueda` | Automática ✔ |
| Guardado de preguntas/respuestas | `test_guarda_y_recupera...` | Automática ✔ · Supabase real: PENDIENTE |
| Dos usuarios | `test_otro_usuario_no_lee_ni_escribe...`, `test_aislamiento_entre_dos_usuarios_en_la_interfaz` | Automática ✔ · **RLS real: PENDIENTE** (`test_supabase_real.py`) |
| Dos conversaciones de una persona | `test_dos_conversaciones_de_una_misma_persona` | Automática ✔ |
| Recuperar tras cerrar sesión y reiniciar | `test_flujo_completo_guardar_cerrar_sesion_y_recuperar` (nueva instancia de la app) | Automática ✔ · en URL desplegada: PENDIENTE |
| Clon limpio / variables / URL desplegada | — | **PENDIENTE** |

Observado vs. esperado para las filas PENDIENTE: complete aquí la columna «observado» tras ejecutarlas.
Limitación de las automáticas: usan dobles de Supabase que **no emulan RLS**; por eso `test_supabase_real.py` es obligatorio.

## 8. Limitaciones
Ver `app/README.md` §10.

## 9. Aportes del equipo
| Integrante | Componente | Archivos |
|---|---|---|
| PENDIENTE | PENDIENTE | PENDIENTE |

## 10. Evidencias ↔ archivos
| Evidencia | Archivo |
|---|---|
| Cortes 1-3 | `notebooks/Proyecto.ipynb` |
| Agente + MCP (Clase 11) | `notebooks/RESUA_Clase_11_Agente_RAG_MCP.ipynb` |
| Pruebas automáticas | `evidencias/resultados_pruebas_automaticas.txt` |
| Esquema SQL y RLS | `app/sql/esquema_conversaciones.sql` |
| Código de la aplicación | `app/*.py` |
10. **Formato de citas del agente** (observado en la consola con el modelo real, consulta AVS-1001): la consulta MCP se ejecutó y el
    modelo redactó el estado correcto, pero devolvió `citas: ["[T1]"]` (con corchetes) y no incluyó `[T1]` en el texto; la validación
    falló en los pasos 2 y 3 y el turno terminó en `ERROR_VALIDACION`. Causa: el prompt del agente (heredado de la Clase 11) decía
    «cítalas como [T1] y anótalas en citas», ambiguo; el prompt del RAG (Clase 8) sí tenía reglas explícitas. Cambios: reglas de
    citación explícitas en el prompt, mensaje de corrección con ejemplo y `normalizar_decision`, que **solo repara la forma** (quita
    corchetes de `citas`; añade al texto una etiqueta declarada y existente que falte). **Decisión D8 y su límite:** la normalización no
    verifica que el texto se apoye de verdad en esa fuente, igual que la validación de citas en general (solo comprueba correspondencia);
    una etiqueta inexistente sigue bloqueada. Probado con el caso observado y con modelo simulado; no verificado todavía con el modelo real.
11. **Búsqueda por especie (cambio solicitado).** Se asignó especie reportada y nombre científico a los registros ficticios (AVS-1001 y
    AVS-1004 pelícano pardo; 1002 zarigüeya; 1003 iguana verde; 1005 búho chico) y se añadió la herramienta con validación de entrada
    (3-60 letras; rechaza `<script>`, números y cadenas largas), búsqueda sin tildes ni plural, y salida con `total`/`mostrados`. El
    sistema valida la forma del resultado MCP. La especie se presenta como **reportada, no confirmada** salvo `identificacion_completada`.
    Probado con el servidor MCP real por stdio y modelo simulado; **pendiente probar con el modelo real** desde la interfaz.
