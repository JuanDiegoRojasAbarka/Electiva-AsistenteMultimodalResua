---
tipo: bitacora-clase
curso: IAG Y Sistemas Inteligentes
periodo: EAM-2026II
equipo: Equipo_08
corte: 1
semana: "5"
clase: "08"
fecha: 2026-10-14
estado: en-progreso
tags:
  - ai
  - bitacora
  - rag
  - supabase
  - groq
---

# Bitácora — Clase [C08_2026-10-14_RAG_Supabase_Groq]

## 1. Datos de la sesión

| Campo    | Registro                                                                           |
| -------- | ---------------------------------------------------------------------------------- |
| Tema     | [Mejora de evaluacion RAG]                                                         |
| Objetivo | [Comprobar como cambia la evidencia cuando se añade BM25, fusion RFF y reranking.] |
| Proyecto | [Asistente Multimodal]                                                             |
| Inicio   | [18:00]                                                                            |
| Cierre   | [21:00]                                                                            |

## 2. Participación y responsabilidades

| Integrante                 | Asistió | Rol de la clase | Responsabilidad asumida                                               | Aporte verificable |
| -------------------------- | :-----: | --------------- | --------------------------------------------------------------------- | ------------------ |
| [Juan Diego Rojas Abarka]  |   Sí    | [Estudiante]    | [Integración de Supabase y ejecución de pipeline RAG]                 | []                 |
| [Manuela Velez Betancourt] |   Sí    | [Estudiante]    | [Validación con Pydantic y pruebas de generación con Groq - Bitácora] | []                 |

## 3. Reto aplicado al proyecto

### Funcionalidad trabajada

1. Tokenización y búsqueda BM25: adaptamos el procesamiento léxico para normalizar los textos con Unicode NFKC, convertirlos a minúsculas y conservar palabras y códigos con guion. Se utiliza para buscar coincidencias textuales en los fragmentos de RESUA.

2. Recuperación híbrida con RRF: adaptamos la fusión de los resultados de búsqueda semántica y BM25 mediante Reciprocal Rank Fusion (RRF), combinando sus posiciones en lugar de comparar directamente sus puntuaciones.

3. Reranking: incorporamos la reorganización de los fragmentos candidatos para evaluar si un segundo modelo mejora la relevancia de los resultados recuperados.

4. Evaluación de estrategias: comparamos tres alternativas:
	- `A_semantica`: búsqueda semántica.
	- `B_hibrida_RRF`: búsqueda semántica combinada con BM25 mediante RRF.
	- `C_hibrida_reranking`: búsqueda híbrida seguida de reranking.
		Utilizamos `Precision@3`, `Recall@3`, `Hit@3`, `RR`, cobertura y tiempos de ejecución. Los casos de comportamiento sin unidades de relevancia se deben analizar por separado.

5. Selección de estrategia: elegimos `A_semantica` porque ofreció un equilibrio adecuado entre resultados y latencia. Las mejoras de B y C no fueron consistentes en todos los grupos y el reranking añadió tiempo de procesamiento.

6. Generación RAG con Groq: adaptamos la función `generar()` para responder preguntas sobre el registro de avistamientos, la evidencia disponible y el seguimiento de reportes. La respuesta utiliza un esquema JSON estructurado con los estados `respondida`, `parcial`, `aclaracion` y `evidencia_insuficiente`.

7. Validación de respuestas y citas: conservamos `validar_respuesta()` para comprobar que las citas `[F1]`, `[F2]`, etc., correspondan a los fragmentos recuperados, que no haya citas repetidas y que las respuestas incompletas o insuficientes expliquen sus limitaciones.

8. Revisión manual: adaptamos la revisión de respuestas para evaluar cuatro criterios: corrección, fidelidad a la evidencia, respaldo de las citas y adecuación del estado asignado.

9. Pruebas y exportación: conservamos las pruebas sintéticas de RRF y métricas, y adaptamos la exportación de los resultados a tres archivos:
	- `RESUA_Evidencia_Evaluacion_RAG.json`
	- `RESUA_Metricas_RAG.csv`    
	- `RESUA_Evidencia_Evaluacion_RAG.zip`

10. Corrección de variables: solucionamos el error `NameError: name 'OPCIONES_GENERACION' is not defined`, definiendo la estrategia de generación elegida como `A_semantica` y configurando `OPCIONES_GENERACION` para que refleje esa selección.

### Criterios de aceptación

- [x] [Implementación exitosa del flujo RAG conectando Supabase, embeddings locales y generación validada con Groq.]

### Archivos o componentes modificados

- `[VelezManuela_RojasJuan/Clase 09/Clase_09_Demo_Colab_Mejora_Evaluacion_RAG.ipynb]`: [Cuaberno Colab con el flujo completo de RAG
- `[VelezManuela_RojasJuan/Clase 09/Bitácora - Clase - C09_2026-10-14_Demo_Colab_Rag_Supabase_Groq.md]`: [Bitácora de la sesión realizada]

## 4. Decisiones técnicas

| Decisión                                       | Razón                                                                                                                                                                                                      | Alternativa descartada                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| [Seleccion de estrategia]                      | [elegimos `A_semantica` porque ofreció un equilibrio adecuado entre resultados y latencia. Las mejoras de B y C no fueron consistentes en todos los grupos y el reranking añadió tiempo de procesamiento.] | [B y C]                                         |


## 5. Problemas y soluciones

| Problema encontrado | Causa identificada | Solución aplicada | ¿Cómo se verificó? |
| ------------------- | ------------------ | ----------------- | ------------------ |
| []                  | []                 | []                | []                 |

## 6. Evidencias

| Tipo   | Descripción                                              | Enlace o ruta                                     |
| ------ | -------------------------------------------------------- | ------------------------------------------------- |
| Collab | [Cuaderno de Colab ejecutado con la integración de RAG.] | [Clase_09_Demo_Colab_Mejora_Evaluacion_RAG.ipynb] |

## 7. Uso de inteligencia artificial

> [!important] Registrar la IA no reemplaza la explicación técnica. El equipo debe verificar, adaptar y comprender cualquier resultado utilizado.

| Herramienta | Objetivo o pregunta                                           | Qué se utilizó                 | Cómo se verificó                                                          | Qué se modificó                                                                         |
| ----------- | ------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [Chatgpt]   | [Soporte en la adaptacion de codigo a nuestro proyecto RESUA] | [Cambios simples de variables] | [Se verificó mediante la ejecución exitosa de las celdas en Google Colab] | [Se adaptaron los parámetros y nombres de tablas al contexto específico de la práctica] |

## 8. Defensa técnica y retroalimentación

| Campo                     | Registro |
| ------------------------- | -------- |
| Integrante que defendió   | []       |
| Pregunta recibida         | []       |
| Respuesta resumida        | []       |
| Retroalimentación docente | []       |
| Mejora acordada           | []       |

## 9. Aprendizajes

- **Concepto comprendido:** [BM25, fusión RRF y reranking dentro de RAG]
- **Algo que aún genera duda:** []
- **Qué haríamos diferente:** []

## 10. Revisión antes de entregar

- [x] Todos los integrantes registraron un aporte verificable.
- [x] Los enlaces y rutas de evidencia funcionan.
- [x] Los criterios de aceptación están actualizados.
- [x] El uso de IA fue declarado y verificado.
- [x] El equipo puede explicar las decisiones registradas.