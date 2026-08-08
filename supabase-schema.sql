-- ═══════════════════════════════════════════════════════════════
-- «Копилка класса» — схема базы для Supabase
--
-- Как применить:
--   1. supabase.com → New project (бесплатный тариф)
--   2. в проекте: SQL Editor → New query → вставить весь этот файл → Run
--   3. Project Settings → API: скопировать Project URL и ключ anon public
--   4. в приложении: ⚙ → «Общая база» → вставить URL и ключ → «Создать класс»
--
-- Модель доступа: ключ anon public по определению открыт всем, кто откроет
-- ссылку, поэтому саму таблицу закрываем полностью и работаем только через
-- функции ниже. Каждая функция требует id класса И код класса — без них
-- ни прочитать, ни записать нельзя, и перечислить чужие классы тоже нельзя.
-- ═══════════════════════════════════════════════════════════════

create extension if not exists pgcrypto;

-- Одна строка = один класс. Всё состояние хранится единым JSON-документом:
-- список учеников, сборы, отметки об оплате, траты. Для класса на 24 человека
-- это десятки килобайт — отдельные таблицы тут только усложнили бы слияние
-- одновременных правок.
create table if not exists public.classes (
  id          uuid primary key default gen_random_uuid(),
  state       jsonb       not null,
  version     integer     not null default 1,
  code_hash   text        not null,   -- код класса, для родителей
  admin_hash  text        not null,   -- пароль казначея
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Таблица закрыта наглухо: ни select, ни insert, ни update напрямую.
alter table public.classes enable row level security;
revoke all on public.classes from anon, authenticated;

create or replace function public.sha(t text)
returns text language sql immutable as $$
  select encode(digest(coalesce(t,''), 'sha256'), 'hex')
$$;

-- ── Создать класс ──────────────────────────────────────────────
-- Возвращает id — его получает казначей и раздаёт в ссылке.
create or replace function public.class_create(
  p_state jsonb, p_code text, p_admin text
) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_id uuid;
begin
  if length(coalesce(p_code,'')) < 4 then
    raise exception 'код класса слишком короткий';
  end if;
  if length(coalesce(p_admin,'')) < 4 then
    raise exception 'пароль казначея слишком короткий';
  end if;
  insert into classes (state, code_hash, admin_hash)
  values (p_state, sha(p_code), sha(p_admin))
  returning id into v_id;
  return v_id;
end $$;

-- ── Прочитать класс ────────────────────────────────────────────
-- Нужны и id, и код. Неверный код — ошибка, а не пустой результат,
-- чтобы приложение могло отличить опечатку от удалённого класса.
create or replace function public.class_get(p_id uuid, p_code text)
returns table (state jsonb, version integer, updated_at timestamptz)
language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from classes c where c.id = p_id) then
    raise exception 'класс не найден';
  end if;
  if not exists (select 1 from classes c where c.id = p_id and c.code_hash = sha(p_code)) then
    raise exception 'неверный код класса';
  end if;
  return query
    select c.state, c.version, c.updated_at from classes c where c.id = p_id;
end $$;

-- ── Сохранить класс ────────────────────────────────────────────
-- Оптимистическая блокировка: запись проходит, только если версия на сервере
-- не изменилась с момента чтения. Иначе возвращается null — клиент перечитает
-- свежее состояние, наложит на него свои правки и повторит.
create or replace function public.class_save(
  p_id uuid, p_code text, p_state jsonb, p_version integer
) returns integer
language plpgsql security definer set search_path = public as $$
declare v_new integer;
begin
  if not exists (select 1 from classes c where c.id = p_id and c.code_hash = sha(p_code)) then
    raise exception 'неверный код класса';
  end if;
  update classes
     set state = p_state, version = version + 1, updated_at = now()
   where id = p_id and version = p_version
  returning version into v_new;
  return v_new;   -- null = кто-то опередил, нужен повтор
end $$;

-- ── Проверить пароль казначея ──────────────────────────────────
create or replace function public.class_is_admin(
  p_id uuid, p_code text, p_admin text
) returns boolean
language plpgsql security definer set search_path = public as $$
begin
  return exists (
    select 1 from classes c
     where c.id = p_id and c.code_hash = sha(p_code) and c.admin_hash = sha(p_admin)
  );
end $$;

-- ── Узнать версию, не выкачивая состояние ──────────────────────
-- Приложение опрашивает её раз в несколько секунд: если версия та же,
-- качать состояние целиком не нужно.
create or replace function public.class_version(p_id uuid, p_code text)
returns integer
language plpgsql security definer set search_path = public as $$
declare v integer;
begin
  select c.version into v from classes c
   where c.id = p_id and c.code_hash = sha(p_code);
  if v is null then raise exception 'неверный код класса'; end if;
  return v;
end $$;

-- Вызывать функции можно без регистрации, но только зная id и код класса.
grant execute on function public.class_create(jsonb, text, text) to anon, authenticated;
grant execute on function public.class_get(uuid, text)            to anon, authenticated;
grant execute on function public.class_save(uuid, text, jsonb, integer) to anon, authenticated;
grant execute on function public.class_is_admin(uuid, text, text) to anon, authenticated;
grant execute on function public.class_version(uuid, text)        to anon, authenticated;

comment on table public.classes is
  'Классы приложения «Копилка класса». Одна строка — один класс, всё состояние в state. Доступ только через функции class_*.';
