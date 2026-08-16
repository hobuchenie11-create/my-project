-- KOPILKA KLASSA: minimal schema. Zamenite stroku TOKEN-ZDES na svoyu.
-- Polnaya versiya s poyasneniyami: supabase-schema.sql

set search_path = public, extensions;

create extension if not exists pgcrypto;

create table if not exists public.classes (
  id           uuid primary key default gen_random_uuid(),
  state        jsonb       not null,
  version      integer     not null default 1,
  code_hash    text        not null,          -- код класса (родители, чтение)
  admin_hashes text[]      not null,          -- пароли казначеев (чтение и запись)
  fails        integer     not null default 0, -- неверных попыток в текущем окне
  fail_window  timestamptz,                    -- начало окна подсчёта попыток
  locked_until timestamptz,                    -- до этого времени неверные попытки не принимаются
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

alter table public.classes enable row level security;
revoke all on public.classes from anon, authenticated;

create table if not exists public.app_config (
  only_row         boolean primary key default true check (only_row),
  create_token_hash text not null
);
alter table public.app_config enable row level security;
revoke all on public.app_config from anon, authenticated;

create or replace function public.sha(t text)
returns text language sql immutable
set search_path = public, extensions as $$
  select encode(digest(coalesce(t,''), 'sha256'), 'hex')
$$;

insert into public.app_config (create_token_hash)
values (public.sha('TOKEN-ZDES'))
on conflict (only_row) do update set create_token_hash = excluded.create_token_hash;

create or replace function public.auth_check(p_id uuid, p_secret text)
returns table (role text, reason text)
language plpgsql security definer set search_path = public, extensions as $$
declare c classes%rowtype;
begin
  select * into c from classes where id = p_id;
  if not found then
    return query select null::text, 'класс не найден'; return;
  end if;

  if sha(p_secret) = any(c.admin_hashes) then
    return query select 'admin'::text, null::text; return;
  end if;
  if c.code_hash = sha(p_secret) then
    return query select 'parent'::text, null::text; return;
  end if;

  if c.locked_until is not null and c.locked_until > now() then
    return query select null::text,
      format('слишком много неверных попыток, попробуйте через %s мин',
             greatest(1, ceil(extract(epoch from (c.locked_until - now())) / 60))::int);
    return;
  end if;

  if c.fail_window is null or now() - c.fail_window > interval '15 minutes' then
    update classes set fails = 1, fail_window = now(), locked_until = null
     where id = p_id;
  else
    update classes
       set fails = fails + 1,
           locked_until = case when fails + 1 >= 5 then now() + interval '15 minutes'
                               else locked_until end
     where id = p_id;
  end if;

  return query select null::text, 'неверный код доступа'; return;
end $$;

create or replace function public.class_create(
  p_state jsonb, p_code text, p_admin text, p_token text
) returns table (ok boolean, reason text, id uuid)
language plpgsql security definer set search_path = public, extensions as $$
declare v_id uuid;
begin
  if not exists (select 1 from app_config where create_token_hash = sha(p_token)) then
    return query select false, 'неверный токен установки', null::uuid; return;
  end if;
  if length(coalesce(p_code,'')) < 6 then
    return query select false, 'код класса — не короче 6 символов', null::uuid; return;
  end if;
  if length(coalesce(p_admin,'')) < 8 then
    return query select false, 'пароль казначея — не короче 8 символов', null::uuid; return;
  end if;
  if p_code = p_admin then
    return query select false, 'код класса и пароль казначея должны отличаться', null::uuid; return;
  end if;
  insert into classes (state, code_hash, admin_hashes)
  values (p_state, sha(p_code), array[sha(p_admin)])
  returning classes.id into v_id;
  return query select true, null::text, v_id;
end $$;

create or replace function public.class_get(p_id uuid, p_secret text)
returns table (ok boolean, reason text, state jsonb, version integer, role text)
language plpgsql security definer set search_path = public, extensions as $$
declare a record;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is null then
    return query select false, a.reason, null::jsonb, null::integer, null::text; return;
  end if;
  return query
    select true, null::text, c.state, c.version, a.role from classes c where c.id = p_id;
end $$;

create or replace function public.class_version(p_id uuid, p_secret text)
returns table (ok boolean, reason text, version integer)
language plpgsql security definer set search_path = public, extensions as $$
declare a record;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is null then
    return query select false, a.reason, null::integer; return;
  end if;
  return query select true, null::text, c.version from classes c where c.id = p_id;
end $$;

create or replace function public.class_save(
  p_id uuid, p_secret text, p_state jsonb, p_version integer
) returns table (ok boolean, reason text, version integer)
language plpgsql security definer set search_path = public, extensions as $$
declare a record; v_new integer;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is null then
    return query select false, a.reason, null::integer; return;
  end if;
  if a.role <> 'admin' then
    return query select false, 'запись доступна только казначею', null::integer; return;
  end if;
  update classes
     set state = p_state, version = classes.version + 1, updated_at = now()
   where id = p_id and classes.version = p_version
  returning classes.version into v_new;
  return query select true, null::text, v_new;   -- version=null → нужен повтор
end $$;

create or replace function public.class_set_code(
  p_id uuid, p_secret text, p_new_code text
) returns table (ok boolean, reason text)
language plpgsql security definer set search_path = public, extensions as $$
declare a record;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is distinct from 'admin' then
    return query select false, coalesce(a.reason, 'сменить код может только казначей'); return;
  end if;
  if length(coalesce(p_new_code,'')) < 6 then
    return query select false, 'код класса — не короче 6 символов'; return;
  end if;
  if exists (select 1 from classes c
              where c.id = p_id and sha(p_new_code) = any(c.admin_hashes)) then
    return query select false, 'код класса не должен совпадать с паролем казначея'; return;
  end if;
  update classes set code_hash = sha(p_new_code) where id = p_id;
  return query select true, null::text;
end $$;

create or replace function public.class_admin_add(
  p_id uuid, p_secret text, p_new_admin text
) returns table (ok boolean, reason text, admins integer)
language plpgsql security definer set search_path = public, extensions as $$
declare a record; n integer;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is distinct from 'admin' then
    return query select false, coalesce(a.reason, 'доступно только казначею'), null::integer; return;
  end if;
  if length(coalesce(p_new_admin,'')) < 8 then
    return query select false, 'пароль — не короче 8 символов', null::integer; return;
  end if;
  if exists (select 1 from classes c where c.id = p_id and c.code_hash = sha(p_new_admin)) then
    return query select false, 'пароль не должен совпадать с кодом класса', null::integer; return;
  end if;
  update classes
     set admin_hashes = (select array_agg(distinct h)
                           from unnest(admin_hashes || sha(p_new_admin)) h)
   where id = p_id
  returning array_length(admin_hashes, 1) into n;
  return query select true, null::text, n;
end $$;

create or replace function public.class_admin_reset_others(
  p_id uuid, p_secret text
) returns table (ok boolean, reason text)
language plpgsql security definer set search_path = public, extensions as $$
declare a record;
begin
  select * into a from auth_check(p_id, p_secret);
  if a.role is distinct from 'admin' then
    return query select false, coalesce(a.reason, 'доступно только казначею'); return;
  end if;
  update classes set admin_hashes = array[sha(p_secret)] where id = p_id;
  return query select true, null::text;
end $$;

grant execute on function public.class_create(jsonb, text, text, text)  to anon, authenticated;
grant execute on function public.class_get(uuid, text)                  to anon, authenticated;
grant execute on function public.class_version(uuid, text)              to anon, authenticated;
grant execute on function public.class_save(uuid, text, jsonb, integer) to anon, authenticated;
grant execute on function public.class_set_code(uuid, text, text)       to anon, authenticated;
grant execute on function public.class_admin_add(uuid, text, text)      to anon, authenticated;
grant execute on function public.class_admin_reset_others(uuid, text)   to anon, authenticated;
revoke execute on function public.auth_check(uuid, text) from anon, authenticated;
revoke execute on function public.sha(text)             from anon, authenticated;

notify pgrst, 'reload schema';

comment on table public.classes is
  'Классы приложения «Копилка класса». Одна строка — один класс, всё состояние в state. Доступ только через функции class_*: код класса даёт чтение, пароль казначея — запись.';
