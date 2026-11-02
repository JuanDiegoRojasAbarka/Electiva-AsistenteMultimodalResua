-- =========================================================
-- RESUA: configuración de la base de datos vectorial
-- Supabase + pgvector
-- Modelo de embeddings: paraphrase-multilingual-MiniLM-L12-v2
-- Dimensión de los embeddings: 384
-- =========================================================

-- 1. Habilitar la extensión para búsquedas vectoriales
CREATE EXTENSION IF NOT EXISTS vector
WITH SCHEMA extensions;


-- 2. Crear la tabla de fragmentos del corpus
CREATE TABLE IF NOT EXISTS public.resua_fragmentos (
    owner_id UUID NOT NULL,
    corpus_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    configuracion JSONB NOT NULL,
    embedding extensions.vector(384) NOT NULL,

    PRIMARY KEY (owner_id, corpus_id, chunk_id)
);


-- 3. Índice para filtrar por propietario y corpus
CREATE INDEX IF NOT EXISTS idx_resua_owner_corpus
ON public.resua_fragmentos (owner_id, corpus_id);


-- 4. Índice vectorial para similitud coseno
CREATE INDEX IF NOT EXISTS idx_resua_embedding_cosine
ON public.resua_fragmentos
USING hnsw (embedding extensions.vector_cosine_ops);


-- 5. Habilitar seguridad por filas (RLS)
ALTER TABLE public.resua_fragmentos
ENABLE ROW LEVEL SECURITY;


-- 6. Políticas de acceso para usuarios autenticados
-- Ejecutar estas políticas una sola vez.

CREATE POLICY "resua_select_own_fragments"
ON public.resua_fragmentos
FOR SELECT
TO authenticated
USING (owner_id = (SELECT auth.uid()));

CREATE POLICY "resua_insert_own_fragments"
ON public.resua_fragmentos
FOR INSERT
TO authenticated
WITH CHECK (owner_id = (SELECT auth.uid()));

CREATE POLICY "resua_update_own_fragments"
ON public.resua_fragmentos
FOR UPDATE
TO authenticated
USING (owner_id = (SELECT auth.uid()))
WITH CHECK (owner_id = (SELECT auth.uid()));

CREATE POLICY "resua_delete_own_fragments"
ON public.resua_fragmentos
FOR DELETE
TO authenticated
USING (owner_id = (SELECT auth.uid()));


-- 7. Función RPC para búsqueda semántica
CREATE OR REPLACE FUNCTION public.resua_buscar_fragmentos(
    query_embedding extensions.vector(384),
    p_corpus_id TEXT,
    p_modelo TEXT,
    p_revision TEXT,
    match_count INT
)
RETURNS TABLE (
    chunk_id TEXT,
    content TEXT,
    metadata JSONB,
    similitud DOUBLE PRECISION
)
LANGUAGE SQL
STABLE
SET search_path = public, extensions
AS $$
    SELECT
        f.chunk_id,
        f.content,
        f.metadata,
        1 - (f.embedding <=> query_embedding) AS similitud
    FROM public.resua_fragmentos AS f
    WHERE
        f.owner_id = auth.uid()
        AND f.corpus_id = p_corpus_id
        AND f.configuracion ->> 'modelo' = p_modelo
        AND f.configuracion ->> 'revision' = p_revision
    ORDER BY f.embedding <=> query_embedding
    LIMIT GREATEST(match_count, 1);
$$;


-- 8. Permitir el uso de la función a usuarios autenticados
GRANT EXECUTE ON FUNCTION public.resua_buscar_fragmentos(
    extensions.vector(384),
    TEXT,
    TEXT,
    TEXT,
    INT
) TO authenticated;
