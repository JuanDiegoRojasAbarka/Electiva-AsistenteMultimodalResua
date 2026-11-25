-- Historial de conversaciones de RESUA (ejecutar una vez en el SQL Editor de Supabase).
-- No modifica resua_fragmentos ni sus embeddings.

create table if not exists public.resua_conversaciones (
  id         uuid primary key default gen_random_uuid(),
  owner_id   uuid not null default auth.uid() references auth.users(id) on delete cascade,
  titulo     text not null default 'Nueva conversación' check (char_length(titulo) <= 80),
  creada_en  timestamptz not null default now()
);

create table if not exists public.resua_mensajes (
  id              bigint generated always as identity primary key,
  conversacion_id uuid   not null references public.resua_conversaciones(id) on delete cascade,
  owner_id        uuid   not null default auth.uid() references auth.users(id) on delete cascade,
  rol             text   not null check (rol in ('usuario','asistente')),
  contenido       text   not null check (char_length(contenido) between 1 and 8000),
  citas           jsonb  not null default '[]'::jsonb,
  metadata        jsonb  not null default '{}'::jsonb,
  creado_en       timestamptz not null default now()
);

create index if not exists resua_conv_owner_idx on public.resua_conversaciones (owner_id, creada_en desc);
create index if not exists resua_msg_conv_idx   on public.resua_mensajes (conversacion_id, id);

alter table public.resua_conversaciones enable row level security;
alter table public.resua_mensajes       enable row level security;

drop policy if exists conv_select on public.resua_conversaciones;
drop policy if exists conv_insert on public.resua_conversaciones;
create policy conv_select on public.resua_conversaciones for select to authenticated
  using (owner_id = (select auth.uid()));
create policy conv_insert on public.resua_conversaciones for insert to authenticated
  with check (owner_id = (select auth.uid()));

drop policy if exists msg_select on public.resua_mensajes;
drop policy if exists msg_insert on public.resua_mensajes;
create policy msg_select on public.resua_mensajes for select to authenticated
  using (owner_id = (select auth.uid()));
-- Solo se inserta en conversaciones propias y con el propio owner_id.
create policy msg_insert on public.resua_mensajes for insert to authenticated
  with check (
    owner_id = (select auth.uid())
    and exists (select 1 from public.resua_conversaciones c
                where c.id = conversacion_id and c.owner_id = (select auth.uid()))
  );
-- Sin políticas de update/delete: el historial es de solo lectura/inserción desde la app.

-- Tabla del corpus (creada en el notebook; se documenta aquí para poder reconstruir el esquema).
-- Si ya existe en tu proyecto, "if not exists" no la modifica.
create extension if not exists vector with schema extensions;

create table if not exists public.resua_fragmentos (
  owner_id      uuid  not null references auth.users(id) on delete cascade,
  corpus_id     text  not null,
  chunk_id      text  not null,
  content       text  not null,
  metadata      jsonb not null default '{}'::jsonb,   -- source, section, version, source_hash
  configuracion jsonb not null default '{}'::jsonb,   -- claves 'modelo' y 'revision' (las filtra la RPC)
  embedding     extensions.vector(384) not null,      -- paraphrase-multilingual-MiniLM-L12-v2
  primary key (owner_id, corpus_id, chunk_id)
);

alter table public.resua_fragmentos enable row level security;

-- Corpus compartido: la app lo consulta con la identidad de cada usuario, por lo que los
-- usuarios autenticados necesitan LEER los fragmentos del corpus público de RESUA.
-- (Solo lectura. Revisa que la RPC resua_buscar_fragmentos sea SECURITY INVOKER.)
drop policy if exists resua_fragmentos_lectura_autenticados on public.resua_fragmentos;
create policy resua_fragmentos_lectura_autenticados on public.resua_fragmentos
  for select to authenticated using (true);

-- Búsqueda semántica A_semantica (coseno). SECURITY INVOKER: respeta RLS con la identidad del usuario.
-- El cuerpo es el de tu Supabase; la firma (parámetros y retorno) se dedujo del uso en sistema.py.
create or replace function public.resua_buscar_fragmentos(
  query_embedding extensions.vector(384),
  p_corpus_id     text,
  p_modelo        text,
  p_revision      text,
  match_count     int default 10
)
returns table (chunk_id text, content text, metadata jsonb, similitud float)
language sql
stable
security invoker
set search_path = ''
as $$
    select
        f.chunk_id,
        f.content,
        f.metadata,
        (1 - (f.embedding operator(extensions.<=>) query_embedding))::float
            as similitud
    from public.resua_fragmentos as f
    where f.corpus_id = p_corpus_id
      and f.configuracion->>'modelo' = p_modelo
      and f.configuracion->>'revision' = p_revision
    order by f.embedding operator(extensions.<=>) query_embedding
    limit least(greatest(match_count, 1), 10);
$$;
