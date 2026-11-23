# RESUA · aplicación web (Gradio)

## 1. Problema, usuarios y alcance
**Problema.** Quien observa fauna silvestre en zonas urbanas de Armenia no sabe qué datos aportar, cómo seguir su reporte ni
qué se puede afirmar sobre la especie. **Usuarios:** ciudadanos que reportan y personal que orienta el proceso.
**Alcance:** consulta documental con fuentes, consulta de estado de un avistamiento por código `AVS-0000` y rechazo de
acciones fuera de alcance. **Fuera de alcance:** modificar registros, aprobar identificaciones, asignar especies,
emergencias veterinarias (se remiten a revisión humana). Los registros del MCP son **ficticios, de demostración**.

## 2. Arquitectura y recorrido de una pregunta
```
Navegador ── Gradio (app.py) ──► almacenamiento.py ──► Supabase (Auth + tablas con RLS)
                │                      ▲
                └──► sistema.py ───────┘ (historial autorizado)
                        ├─ Groq (decide la siguiente acción, JSON validado con Pydantic)
                        ├─ buscar_documentos: embeddings + RPC resua_buscar_fragmentos (Supabase, A_semantica)
                        └─ consultar_estado_avistamiento: cliente MCP ► servidor_mcp.py (stdio o MCP_URL)
```
1. La persona inicia sesión (Supabase Auth). `gr.State` guarda **su** sesión; nada de usuario es global.
2. `app.py` valida la entrada, crea la conversación si es nueva y pide a `almacenamiento.py` los últimos 4 turnos.
3. `sistema.atender()` ejecuta el ciclo del agente (máx. 3 decisiones, 2 operaciones, 90 s): el modelo propone una acción,
   el programa la valida (citas, códigos AVS que aparezcan en la conversación, sin repetir operaciones) y la ejecuta.
4. Se guardan la pregunta y la respuesta (con citas y estado) y la interfaz muestra respuesta, fuentes y recorrido.

| Módulo | Responsabilidad |
|---|---|
| `app.py` | Interfaz, sesión por visitante, eventos. No contiene lógica del RAG. |
| `sistema.py` | Recuperación, agente, validaciones, cliente MCP. |
| `almacenamiento.py` | Auth + conversaciones/mensajes; comprueba propietario antes de leer/escribir. |
| `servidor_mcp.py` | MCP propio, una herramienta de **solo lectura**. |
| `config.py` | Lee y valida variables de entorno. |
| `supabase/esquema_conversaciones.sql` | Tablas, índices y políticas RLS. |

## 3. Corpus, embeddings y mejoras de recuperación
Corpus didáctico de 2 documentos (`registro_avistamientos.md`, `seguimiento_identificacion.md`), 10 fragmentos por
párrafos, ya cargados en la tabla `resua_fragmentos` (Clase 8). Embeddings:
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones, normalizados, similitud coseno, revisión
fijada. En la Clase 9 se compararon A (semántica), B (híbrida BM25+RRF) y C (híbrida + reranking); se eligió **A_semantica**
(M=10 candidatos, K=3 fragmentos al modelo). La app no recarga documentos: usa lo ya guardado. Para recuperarlo,
tome `corpus_id` y `configuracion_embeddings.revision` del JSON `RESUA_Evidencia_Evaluacion_RAG.json` de la Clase 9.

## 4. Requisitos
Python **3.11+** (probado en 3.13), cuenta de Supabase con el corpus ya cargado, clave de Groq.
`pip install -r requirements.txt` (versiones fijadas). `sentence-transformers` instala PyTorch: la primera ejecución descarga
el modelo (~470 MB).

## 5. Configuración de servicios
### Supabase
1. En el proyecto del RAG, ejecute `supabase/esquema_conversaciones.sql` en el *SQL Editor*. Crea `resua_conversaciones` y
   `resua_mensajes` (RLS activo) y una política que permite a usuarios autenticados **leer** `resua_fragmentos`
   (corpus público). Revise que la RPC `resua_buscar_fragmentos` sea `SECURITY INVOKER`; si es `DEFINER`, la política no es necesaria pero la RPC no aplicaría RLS.
2. *Authentication → Providers → Email* activo. Si exige confirmar correo, las cuentas nuevas deben confirmarse antes de entrar.
3. Use la **clave publicable** (`sb_publishable_…`). Nunca la `service_role`/secreta.

### Autenticación y RLS
Cada persona usa su propia cuenta de Supabase Auth. En cada solicitud la app valida el token con Supabase (`get_user`) y crea un
cliente nuevo con ese token, de modo que `auth.uid()` identifica a quien escribe. Políticas: `select` e `insert` solo si
`owner_id = auth.uid()`; un mensaje solo se inserta en una conversación propia; no hay `update` ni `delete`.

### Tablas
`resua_conversaciones(id uuid, owner_id, titulo, creada_en)` · `resua_mensajes(id, conversacion_id, owner_id, rol, contenido, citas jsonb, metadata jsonb, creado_en)`.
**Recuperación del historial:** el desplegable «Mis conversaciones» lista las del usuario; al elegir una se leen sus mensajes
y las últimas fuentes. El historial completo se conserva; al modelo solo se envían los últimos 4 turnos.

### MCP
Por defecto `servidor_mcp.py` se lanza como subproceso (stdio), versión de `mcp==2.3.0`, herramienta única
`consultar_estado_avistamiento` (lectura, datos ficticios), sin credenciales. Para un MCP remoto: `python servidor_mcp.py --http`
en otro servicio y `MCP_URL=https://…/mcp`. Esta versión **no** incluye el MCP de archivos de la Clase 11 (escritura de informes):
requería Node en el servidor y una escritura sensible; ver decisión D5 en la bitácora.

## 6. Ejecución desde un clon limpio
PowerShell (Windows):
```powershell
git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r app/requirements-dev.txt
Copy-Item app/.env.ejemplo app/.env
# Completar app/.env (ver sección 5) antes de iniciar
cd app
..\.venv\Scripts\python.exe app.py
```
Linux/macOS: `python3 -m venv .venv && .venv/bin/pip install -r app/requirements-dev.txt && cp app/.env.ejemplo app/.env && cd app && ../.venv/bin/python app.py`.
Abra http://127.0.0.1:7860. Antes de hacer `git add`, compruebe con `git status` que `.env` no aparezca.

## 7. Pruebas
```bash
cd app && python -m pytest -v
```
- **39 pruebas automáticas** (sin red ni claves): historial por usuario, aislamiento entre dos usuarios aun conociendo el
  identificador, dos conversaciones de una persona, recuperación tras «reinicio», validaciones del agente, acción no permitida,
  falla técnica controlada, código desconocido, MCP real por stdio, configuración y construcción de la interfaz.
  Resultado guardado en `../evidencias/resultados_pruebas_automaticas.txt`.
- `tests/test_supabase_real.py` verifica **RLS en el Supabase real** con dos cuentas de prueba
  (`TEST_EMAIL_A/B`, `TEST_PASSWORD_A/B`). Se omite si faltan; **debe ejecutarse antes de entregar** (ver sección 10).
- Las pruebas del modelo (pregunta con fuentes, sin evidencia, entrada incompleta, etc.) se hacen desde la interfaz con los
  servicios reales y se registran en `../evidencias/` (tabla en la bitácora).

## 8. Despliegue en Render
Web Service conectado al repositorio · **Root Directory:** `app` · **Build Command:** `pip install -r requirements.txt` ·
**Start Command:** `python app.py` · variable `PYTHON_VERSION=3.12.7` (o la que use). Variables y secretos en *Environment*:
las de `.env.ejemplo` salvo `GRADIO_SERVER_NAME=0.0.0.0` (el puerto lo fija Render en `PORT`). No se necesita disco
persistente: corpus e historiales viven en Supabase (SQLite no se usa). Tras desplegar, compruebe recuperar una conversación
desde la URL pública y después de reiniciar el servicio. **URL:** PENDIENTE.

## 9. Problemas frecuentes
- `SUPABASE_URL debe ser…` / `EMBEDDINGS_REVISION debe ser…`: revise `.env` (config.py valida al arrancar).
- «La búsqueda no devolvió candidatos»: falta la política de lectura de `resua_fragmentos`, `CORPUS_ID` o revisión incorrectos.
- `ERROR_TECNICO` en el recorrido: cuota de Groq, red o modelo; no significa que falten documentos.
- Arranque lento o `Out of memory` en Render: PyTorch + modelo necesitan RAM; use una instancia con ≥2 GB.
- Cuenta nueva no entra: confirmar el correo si el proyecto lo exige.

## 10. Limitaciones y pendientes
- Corpus muy pequeño (10 fragmentos): la calidad de recuperación no se generaliza.
- Registros AVS ficticios; una versión productiva debe consultar la fuente transaccional con control de acceso.
- Las citas válidas solo prueban correspondencia con la evidencia, no fidelidad: requieren revisión humana.
- **Sin verificar en este repositorio:** ejecución contra Supabase/Groq reales, RLS real, despliegue en Render e instalación desde
  un clon limpio (solo se probó con dobles de prueba y un entorno virtual nuevo). Registre su resultado en `evidencias/`.
- Sin límite de intentos de login propio (lo gestiona Supabase Auth); sin recuperación de contraseña en la interfaz.
