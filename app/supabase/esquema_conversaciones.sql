-- Historial de conversaciones de RESUA (ejecutar una vez en el SQL Editor de Supabase).

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

-- Corpus compartido: la app lo consulta con la identidad de cada usuario, por lo que los
-- usuarios autenticados necesitan LEER los fragmentos del corpus público de RESUA.
-- (Solo lectura. Revisa que la RPC resua_buscar_fragmentos sea SECURITY INVOKER.)
drop policy if exists resua_fragmentos_lectura_autenticados on public.resua_fragmentos;
create policy resua_fragmentos_lectura_autenticados on public.resua_fragmentos
  for select to authenticated using (true);
