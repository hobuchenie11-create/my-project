-- ═══════════════════════════════════════════════════════════════
-- «Копилка класса» — схема базы для Supabase
--
-- Как применить:
--   1. supabase.com → New project (бесплатный тариф)
--   2. в проекте: SQL Editor → New query → вставить весь этот файл → Run
--   3. Project Settings → API: скопировать Project URL и ключ anon public
--   4. в приложении: ⚙ → «Общая база» → вставить URL и ключ → «Создать класс»
--
-- Модель доступа. Ключ anon public по определению открыт всем, поэтому саму
-- таблицу закрываем полностью и работаем только через функции ниже.
-- Секретов два вида, и разница между ними — не в интерфейсе, а здесь, в базе:
--
--   • код класса      — только чтение. Его знают все родители.
--   • пароль админа   — чтение и запись. Их может быть несколько (казначеи).
--
-- Запись разрешена ТОЛЬКО по паролю админа: даже если родитель откроет
-- приложение в режиме казначея, сервер его правку не примет.
-- ═══════════════════════════════════════════════════════════════

-- В Supabase расширение pgcrypto установлено в схему extensions, а не в public.
-- Без этой строки функция digest не находится, и вся схема не создаётся
-- («function digest(text, unknown) does not exist»). Несуществующие схемы
-- в search_path просто игнорируются, поэтому строка безопасна и на обычном
-- Postgres, где pgcrypto лежит в public.
set search_path = public, extensions;

create extension if not exists pgcrypto;

-- Одна строка = один класс. Всё состояние хранится единым JSON-документом:
-- список учеников, сборы, отметки об оплате, траты. Для класса на 24 человека
-- это десятки килобайт — отдельные таблицы тут только усложнили бы слияние
-- одновременных правок.
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

-- Таблица закрыта наглухо: ни select, ни insert, ни update напрямую.
alter table public.classes enable row level security;
revoke all on public.classes from anon, authenticated;

-- ── Токен установки ────────────────────────────────────────────
-- Ключ anon public открыт всем, поэтому без этого токена посторонний мог бы
-- насоздавать классов в вашем проекте. ЗАМЕНИТЕ строку ниже на свою, прежде
-- чем выполнять файл, и запомните её — она понадобится один раз, при создании
-- класса в приложении.
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

-- Токен берётся отсюда при каждом выполнении файла: если запустить схему
-- повторно с другой строкой, подействует новая. (С «do nothing» повторный
-- запуск молча оставлял бы прежний токен — и появлялась бы необъяснимая
-- ошибка «неверный токен установки».)
insert into public.app_config (create_token_hash)
values (public.sha('ЗАМЕНИТЕ-ЭТУ-СТРОКУ-НА-СВОЮ'))
on conflict (only_row) do update set create_token_hash = excluded.create_token_hash;

-- ── Проверка доступа и защита от перебора ──────────────────────
-- Два принципиальных момента, оба выяснились на испытаниях:
--
--  1. Функция НЕ бросает исключение при неверном секрете, а возвращает ok=false.
--     Иначе Postgres откатил бы транзакцию вместе со счётчиком попыток,
--     и защита от перебора не работала бы вовсе.
--
--  2. Верный секрет проверяется ДО блокировки и счётчик не трогает. Поэтому,
--     во-первых, приложения родителей и казначеев, опрашивающие базу каждые
--     7 секунд, не обнуляют счётчик подбирающему; во-вторых, посторонний
--     не может пятью неверными попытками закрыть вход всему классу —
--     блокировка касается только тех, кто предъявляет неверный секрет.
--
-- Пять неверных попыток за 15 минут — и неверные секреты перестают
-- приниматься ещё на 15 минут.
create or replace function public.auth_check(p_id uuid, p_secret text)
returns table (role text, reason text)
language plpgsql security definer set search_path = public, extensions as $$
declare c classes%rowtype;
begin
  select * into c from classes where id = p_id;
  if not found then
    return query select null::text, 'класс не найден'; return;
  end if;

  -- верный секрет действует всегда
  if sha(p_secret) = any(c.admin_hashes) then
    return query select 'admin'::text, null::text; return;
  end if;
  if c.code_hash = sha(p_secret) then
    return query select 'parent'::text, null::text; return;
  end if;

  -- дальше только неверные секреты
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

-- ── Создать класс ──────────────────────────────────────────────
-- Требует токен установки: без него посторонний с вашим ключом мог бы
-- насоздавать классов в проекте.
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

-- ── Прочитать класс ────────────────────────────────────────────
-- Подходит и код класса, и пароль казначея. Вместе с данными возвращается
-- роль — по ней приложение понимает, показывать ли кнопки редактирования.
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

-- ── Узнать версию, не выкачивая состояние ──────────────────────
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

-- ── Сохранить класс — только казначей ──────────────────────────
-- Оптимистическая блокировка: запись проходит, только если версия на сервере
-- не изменилась с момента чтения. Иначе ok=true, но version=null — клиент
-- перечитает свежее состояние, наложит на него свои правки и повторит.
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

-- ── Сменить код класса — только казначей ───────────────────────
-- Нужно, если ссылка ушла не туда или кто-то покинул класс: старый код
-- сразу перестаёт работать, родители вводят новый.
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

-- ── Второй казначей ────────────────────────────────────────────
-- Свой пароль у каждого — значит, можно отозвать доступ одному, не трогая
-- другого.
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

-- Убирает все пароли казначеев, кроме предъявленного: так отзывается доступ
-- у второго администратора, если он больше не ведёт сборы.
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

-- Вызывать функции можно без регистрации, но только зная id класса и секрет.
grant execute on function public.class_create(jsonb, text, text, text)  to anon, authenticated;
grant execute on function public.class_get(uuid, text)                  to anon, authenticated;
grant execute on function public.class_version(uuid, text)              to anon, authenticated;
grant execute on function public.class_save(uuid, text, jsonb, integer) to anon, authenticated;
grant execute on function public.class_set_code(uuid, text, text)       to anon, authenticated;
grant execute on function public.class_admin_add(uuid, text, text)      to anon, authenticated;
grant execute on function public.class_admin_reset_others(uuid, text)   to anon, authenticated;
-- auth_check и sha — вспомогательные, наружу не отдаём
revoke execute on function public.auth_check(uuid, text) from anon, authenticated;
revoke execute on function public.sha(text)             from anon, authenticated;

-- ── Обновить кэш API ───────────────────────────────────────────
-- Supabase держит список функций в кэше. Без этой строки только что
-- созданные функции могут какое-то время отвечать «404 не найдено».
notify pgrst, 'reload schema';

comment on table public.classes is
  'Классы приложения «Копилка класса». Одна строка — один класс, всё состояние в state. Доступ только через функции class_*: код класса даёт чтение, пароль казначея — запись.';

-- ── Полезно при разборе неполадок ──────────────────────────────
-- Выполнить в SQL Editor по отдельности, когда что-то не сходится.
--
-- Проверить, тот ли токен установки:
--   select create_token_hash = public.sha('ваша-строка') as токен_верный
--     from public.app_config;
--
-- Сменить токен, не выполняя файл целиком:
--   update public.app_config set create_token_hash = public.sha('новая-строка');
--
-- Снять блокировку перебора досрочно (для всех классов):
--   update public.classes set fails = 0, fail_window = null, locked_until = null;
--
-- Посмотреть заведённые классы (сами данные не показываются):
--   select id, version, updated_at, array_length(admin_hashes,1) as казначеев
--     from public.classes order by created_at;
