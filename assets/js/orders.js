/* ==========================================================================
   Алиса — журнал заказов (демонстрация)
   Показывает, как владелец магазина видит заказы: список, статусы, поиск,
   карточка заказа и выгрузка в таблицу. Данные демонстрационные, изменения
   статусов сохраняются в браузере, чтобы показ выглядел живым.
   ========================================================================== */
(function () {
  'use strict';

  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const money = (n) => new Intl.NumberFormat('ru-RU').format(Math.round(n)) + ' ₽';

  const plural = (n, one, few, many) => {
    const a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b > 1 && b < 5) return few;
    if (b === 1) return one;
    return many;
  };

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));

  const store = {
    read(key, fallback) {
      try {
        const raw = localStorage.getItem('alisa-orders:' + key);
        return raw ? JSON.parse(raw) : fallback;
      } catch (e) { return fallback; }
    },
    write(key, value) {
      try { localStorage.setItem('alisa-orders:' + key, JSON.stringify(value)); } catch (e) { /* приватный режим */ }
    },
  };

  const ICON = {
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    close:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    down:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12m0 0 4-4m-4 4-4-4M4 20h16"/></svg>',
    sun:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/></svg>',
    moon:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4 8.2 8.2 0 1 0 20 14.5Z"/></svg>',
  };

  /* ── Состояние ──────────────────────────────────────────────────────── */
  const state = {
    query: '',
    status: 'all',
    period: 'all',
    selected: null,
    /* Изменённые статусы: { 'АЛ-000412': 'work' } */
    changed: store.read('changed', {}),
  };

  /* ── Заказы ─────────────────────────────────────────────────────────── */
  const productById = (id) => PRODUCTS.find((p) => p.id === id);
  const statusById = (id) => ORDER_STATUSES.find((s) => s.id === id) || ORDER_STATUSES[0];

  function orderStatus(order) {
    return state.changed[order.number] || order.status;
  }

  function orderDate(order) {
    return new Date(Date.now() - order.hoursAgo * 3600 * 1000);
  }

  function orderSum(order) {
    const goods = order.items.reduce((s, i) => {
      const p = productById(i.id);
      return p ? s + p.price * i.qty : s;
    }, 0);
    const promo = order.promo && PROMOS[order.promo] ? Math.round(goods * PROMOS[order.promo].discount) : 0;
    const method = DELIVERY.find((d) => d.id === order.delivery) || DELIVERY[0];
    let ship = method.price;
    if (method.id === 'courier' && goods - promo >= BRAND.freeFrom) ship = 0;
    return { goods, promo, ship, gift: order.gift ? 350 : 0, total: goods - promo + ship + (order.gift ? 350 : 0) };
  }

  const fmtDate = (d) => d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' });
  const fmtTime = (d) => d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

  function fmtAgo(hours) {
    if (hours < 1) return 'только что';
    if (hours < 24) return hours + ' ' + plural(hours, 'час', 'часа', 'часов') + ' назад';
    const days = Math.round(hours / 24);
    return days + ' ' + plural(days, 'день', 'дня', 'дней') + ' назад';
  }

  const itemsSummary = (order) => order.items.map((i) => {
    const p = productById(i.id);
    return (p ? p.name : i.id) + ' · ' + i.size + ' · ' + i.qty + ' шт.';
  }).join('; ');

  /* ── Фильтрация ─────────────────────────────────────────────────────── */
  function visibleOrders() {
    const q = state.query.trim().toLowerCase();
    return DEMO_ORDERS.filter((o) => {
      if (state.status !== 'all' && orderStatus(o) !== state.status) return false;
      if (state.period === 'today' && o.hoursAgo > 24) return false;
      if (state.period === 'week' && o.hoursAgo > 24 * 7) return false;
      if (q) {
        const hay = (o.number + ' ' + o.customer.name + ' ' + o.customer.phone + ' ' +
                     o.customer.city + ' ' + itemsSummary(o)).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  /* ── Показатели ─────────────────────────────────────────────────────── */
  function renderStats() {
    const isNew = DEMO_ORDERS.filter((o) => orderStatus(o) === 'new');
    const inWork = DEMO_ORDERS.filter((o) => ['work', 'shipped'].includes(orderStatus(o)));
    const done = DEMO_ORDERS.filter((o) => orderStatus(o) === 'done');
    const revenue = done.reduce((s, o) => s + orderSum(o).total, 0);
    const avg = done.length ? revenue / done.length : 0;

    $('#stats').innerHTML = `
      <div class="stat${isNew.length ? ' stat--attention' : ''}">
        <div class="stat__label">Новые заказы</div>
        <div class="stat__value num">${isNew.length}</div>
        <div class="stat__note">${isNew.length ? 'Ждут подтверждения' : 'Всё обработано'}</div>
      </div>
      <div class="stat">
        <div class="stat__label">В работе</div>
        <div class="stat__value num">${inWork.length}</div>
        <div class="stat__note">Собираются и в пути</div>
      </div>
      <div class="stat">
        <div class="stat__label">Выполнено</div>
        <div class="stat__value num">${done.length}</div>
        <div class="stat__note">За последнюю неделю</div>
      </div>
      <div class="stat">
        <div class="stat__label">Выручка</div>
        <div class="stat__value num">${money(revenue)}</div>
        <div class="stat__note">Средний чек ${money(avg)}</div>
      </div>`;
  }

  /* ── Таблица ────────────────────────────────────────────────────────── */
  function renderTable() {
    const list = visibleOrders();
    const wrap = $('#ordersWrap');

    $('#resultsLine').textContent =
      list.length + ' ' + plural(list.length, 'заказ', 'заказа', 'заказов') +
      (list.length !== DEMO_ORDERS.length ? ' из ' + DEMO_ORDERS.length : '');

    if (!list.length) {
      wrap.innerHTML = `
        <div class="empty-orders">
          <strong>Ничего не найдено</strong>
          Попробуйте изменить фильтр или очистить поиск.
        </div>`;
      return;
    }

    wrap.innerHTML = `
      <table class="orders">
        <thead>
          <tr>
            <th>Заказ</th>
            <th>Покупатель</th>
            <th>Состав</th>
            <th>Доставка</th>
            <th style="text-align:right">Сумма</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          ${list.map((o) => {
            const st = statusById(orderStatus(o));
            const d = orderDate(o);
            const sum = orderSum(o);
            const dm = DELIVERY.find((x) => x.id === o.delivery) || DELIVERY[0];
            return `
            <tr data-order="${esc(o.number)}"${state.selected === o.number ? ' class="is-selected"' : ''}>
              <td>
                <div class="o-num num">${esc(o.number)}</div>
                <div class="o-date num">${fmtDate(d)}, ${fmtTime(d)}</div>
              </td>
              <td>
                <div class="o-name">${esc(o.customer.name)}</div>
                <div class="o-sub num">${esc(o.customer.phone)}</div>
              </td>
              <td class="o-items">
                ${esc(o.items.map((i) => (productById(i.id) || {}).name || i.id).join(', '))}
                ${o.gift ? '<span class="gift-mark">· подарочная упаковка</span>' : ''}
              </td>
              <td>
                <div>${esc(dm.title)}</div>
                <div class="o-sub">${esc(o.customer.city)}</div>
              </td>
              <td class="o-sum num">${money(sum.total)}</td>
              <td><span class="pill pill--${st.tone}">${esc(st.title)}</span></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>`;
  }

  /* ── Фильтры ────────────────────────────────────────────────────────── */
  function renderFilters() {
    const counts = {};
    DEMO_ORDERS.forEach((o) => { const s = orderStatus(o); counts[s] = (counts[s] || 0) + 1; });

    $('#statusChips').innerHTML =
      [{ id: 'all', title: 'Все' }].concat(ORDER_STATUSES).map((s) => {
        const n = s.id === 'all' ? DEMO_ORDERS.length : (counts[s.id] || 0);
        return `<button class="chip chip--sm${state.status === s.id ? ' is-active' : ''}" type="button"
                  data-status="${s.id}">${esc(s.title)} <span class="num">${n}</span></button>`;
      }).join('');
  }

  /* ── Карточка заказа ────────────────────────────────────────────────── */
  function openOrder(number) {
    const o = DEMO_ORDERS.find((x) => x.number === number);
    if (!o) return;
    state.selected = number;

    const st = orderStatus(o);
    const sum = orderSum(o);
    const d = orderDate(o);
    const dm = DELIVERY.find((x) => x.id === o.delivery) || DELIVERY[0];
    const pm = PAYMENT.find((x) => x.id === o.payment) || PAYMENT[0];

    /* Шкала статусов: отменённый заказ показываем отдельной строкой */
    const flow = ['new', 'work', 'shipped', 'done'];
    const currentIdx = flow.indexOf(st);
    const track = st === 'cancel'
      ? `<div class="track__step is-current"><i class="track__dot"></i>
           <div class="track__body"><b>Отменён</b><span>${esc(o.comment || 'Покупатель отказался от заказа')}</span></div>
         </div>`
      : flow.map((s, i) => {
          const info = statusById(s);
          const cls = i < currentIdx ? ' is-done' : (i === currentIdx ? ' is-current' : '');
          return `<div class="track__step${cls}"><i class="track__dot"></i>
                    <div class="track__body"><b>${esc(info.title)}</b><span>${esc(info.hint)}</span></div>
                  </div>`;
        }).join('');

    $('#orderTitle').textContent = o.number;

    $('#orderBody').innerHTML = `
      <div class="od__section">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
          <span class="pill pill--${statusById(st).tone}">${esc(statusById(st).title)}</span>
          <span class="o-date num">${fmtDate(d)}, ${fmtTime(d)} · ${fmtAgo(o.hoursAgo)}</span>
        </div>
      </div>

      <div class="od__section">
        <div class="od__label">Покупатель</div>
        <div class="od__row"><span>Имя</span><b>${esc(o.customer.name)}</b></div>
        <div class="od__row"><span>Телефон</span><b class="num">${esc(o.customer.phone)}</b></div>
        <div class="od__row"><span>Почта</span><b>${esc(o.customer.email)}</b></div>
        <div class="od__row"><span>Город</span><b>${esc(o.customer.city)}</b></div>
        <div class="od__row"><span>Адрес</span><b>${esc(o.customer.address)}</b></div>
        <div class="od__contact">
          <a class="btn btn--ghost" href="tel:${esc(o.customer.phone.replace(/[^\d+]/g, ''))}">Позвонить</a>
          <a class="btn btn--ghost" href="https://wa.me/${esc(o.customer.phone.replace(/\D/g, ''))}" target="_blank" rel="noopener">Написать</a>
        </div>
      </div>

      <div class="od__section">
        <div class="od__label">Состав заказа</div>
        ${o.items.map((i) => {
          const p = productById(i.id) || {};
          return `<div class="od__item">
                    <div>${esc(p.name || i.id)}<span>Размер ${esc(i.size)} · ${esc(i.color)} · ${i.qty} шт.</span></div>
                    <b class="num">${money((p.price || 0) * i.qty)}</b>
                  </div>`;
        }).join('')}
      </div>

      ${o.comment ? `
      <div class="od__section">
        <div class="od__label">Комментарий покупателя</div>
        <div class="od__comment">${esc(o.comment)}</div>
      </div>` : ''}

      <div class="od__section">
        <div class="od__label">Доставка и оплата</div>
        <div class="od__row"><span>Способ</span><b>${esc(dm.title)}</b></div>
        <div class="od__row"><span>Срок</span><b>${esc(dm.eta)}</b></div>
        <div class="od__row"><span>Оплата</span><b>${esc(pm.title)}</b></div>
        ${o.gift ? '<div class="od__row"><span>Упаковка</span><b>Подарочная + открытка</b></div>' : ''}
      </div>

      <div class="od__section">
        <div class="od__label">К оплате</div>
        <div class="od__row"><span>Товары</span><b class="num">${money(sum.goods)}</b></div>
        ${sum.promo ? `<div class="od__row"><span>Промокод ${esc(o.promo)}</span><b class="num">−${money(sum.promo)}</b></div>` : ''}
        <div class="od__row"><span>Доставка</span><b class="num">${sum.ship ? money(sum.ship) : 'Бесплатно'}</b></div>
        ${sum.gift ? `<div class="od__row"><span>Упаковка</span><b class="num">${money(sum.gift)}</b></div>` : ''}
        <div class="od__row" style="border-top:1px solid var(--line);margin-top:8px;padding-top:10px">
          <span style="color:var(--ink);font-weight:700">Итого</span>
          <b class="num" style="font-size:17px">${money(sum.total)}</b>
        </div>
      </div>

      <div class="od__section">
        <div class="od__label">Что происходит с заказом</div>
        <div class="track">${track}</div>
      </div>`;

    /* Кнопки смены статуса — следующий шаг и отмена */
    const nextMap = { new: 'work', work: 'shipped', shipped: 'done' };
    const next = nextMap[st];
    $('#orderFoot').innerHTML = `
      <div class="od__actions">
        ${next ? `<button class="btn btn--primary" type="button" data-set-status="${next}">
                    Перевести в «${esc(statusById(next).title)}»</button>` : ''}
        ${st !== 'cancel' && st !== 'done'
          ? '<button class="btn btn--ghost" type="button" data-set-status="cancel">Отменить заказ</button>' : ''}
        ${st === 'done' || st === 'cancel'
          ? '<button class="btn btn--ghost" type="button" data-set-status="new">Вернуть в новые</button>' : ''}
      </div>`;

    $('#overlay').classList.add('is-open');
    $('#orderDrawer').classList.add('is-open');
    document.body.style.overflow = 'hidden';
    renderTable();
  }

  function closeOrder() {
    $('#orderDrawer').classList.remove('is-open');
    $('#overlay').classList.remove('is-open');
    document.body.style.overflow = '';
    state.selected = null;
    renderTable();
  }

  function setStatus(number, status) {
    state.changed[number] = status;
    store.write('changed', state.changed);
    renderStats();
    renderFilters();
    openOrder(number);
    toast('Статус заказа ' + number + ' — «' + statusById(status).title + '»');
  }

  /* ── Выгрузка в таблицу ─────────────────────────────────────────────── */
  function exportCsv() {
    const rows = [[
      'Номер', 'Дата', 'Статус', 'Покупатель', 'Телефон', 'Почта',
      'Город', 'Адрес', 'Состав', 'Доставка', 'Оплата', 'Сумма, ₽', 'Комментарий',
    ]];

    visibleOrders().forEach((o) => {
      const d = orderDate(o);
      const dm = DELIVERY.find((x) => x.id === o.delivery) || DELIVERY[0];
      const pm = PAYMENT.find((x) => x.id === o.payment) || PAYMENT[0];
      rows.push([
        o.number,
        fmtDate(d) + ' ' + fmtTime(d),
        statusById(orderStatus(o)).title,
        o.customer.name, o.customer.phone, o.customer.email,
        o.customer.city, o.customer.address,
        itemsSummary(o),
        dm.title, pm.title,
        orderSum(o).total,
        o.comment || '',
      ]);
    });

    /* Точка с запятой и BOM — чтобы русский Excel открыл файл без плясок */
    const csv = rows.map((r) => r.map((cell) => {
      const v = String(cell).replace(/"/g, '""');
      return /[";\n]/.test(v) ? '"' + v + '"' : v;
    }).join(';')).join('\r\n');

    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'zakazy-alisa-' + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);

    toast('Файл выгружен — откроется в Excel или Google Таблицах');
  }

  /* ── Уведомления ────────────────────────────────────────────────────── */
  let toastTimer = null;
  function toast(text) {
    const box = $('#toasts');
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = text;
    box.innerHTML = '';
    box.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { box.innerHTML = ''; }, 2800);
  }

  /* ── Пример сообщения в мессенджере ─────────────────────────────────── */
  function renderChat() {
    const o = DEMO_ORDERS[0];
    const sum = orderSum(o);
    const dm = DELIVERY.find((x) => x.id === o.delivery) || DELIVERY[0];
    const pm = PAYMENT.find((x) => x.id === o.payment) || PAYMENT[0];

    $('#chatBubble').innerHTML = `
      <b>🛍 Новый заказ ${esc(o.number)}</b>
      <hr>
      ${o.items.map((i) => {
        const p = productById(i.id) || {};
        return `• ${esc(p.name || i.id)}<br>&nbsp;&nbsp;&nbsp;размер ${esc(i.size)}, ${esc(i.color)}, ${i.qty} шт.`;
      }).join('<br>')}
      <hr>
      <b>${esc(o.customer.name)}</b><br>
      ${esc(o.customer.phone)}<br>
      ${esc(o.customer.city)}, ${esc(o.customer.address)}
      <hr>
      ${esc(dm.title)} · ${esc(pm.title)}${o.gift ? '<br>🎁 Подарочная упаковка' : ''}<br>
      <b>Итого: ${money(sum.total)}</b>
      ${o.comment ? '<hr>💬 ' + esc(o.comment) : ''}`;

    $('#chatTime').textContent = fmtTime(new Date());
  }

  /* ── Тема ───────────────────────────────────────────────────────────── */
  function applyTheme(theme) {
    if (theme) document.documentElement.setAttribute('data-theme', theme);
    else document.documentElement.removeAttribute('data-theme');
    store.write('theme', theme);
    const dark = theme === 'dark' ||
      (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
    $$('[data-theme-toggle]').forEach((el) => {
      el.innerHTML = dark ? ICON.sun : ICON.moon;
      el.setAttribute('aria-label', dark ? 'Светлая тема' : 'Тёмная тема');
    });
  }

  /* ── События ────────────────────────────────────────────────────────── */
  function bind() {
    document.addEventListener('click', (e) => {
      const t = e.target;
      const hit = (attr) => { const el = t.closest('[' + attr + ']'); return el ? el.getAttribute(attr) : null; };

      const status = hit('data-status');
      if (status !== null) { state.status = status; renderFilters(); renderTable(); return; }

      const row = hit('data-order');
      if (row !== null) { openOrder(row); return; }

      const setSt = hit('data-set-status');
      if (setSt !== null) { setStatus(state.selected, setSt); return; }

      if (t.closest('[data-close-order]') || t.id === 'overlay') { closeOrder(); return; }
      if (t.closest('[data-export]')) { exportCsv(); return; }

      if (t.closest('[data-reset]')) {
        state.query = ''; state.status = 'all'; state.period = 'all';
        $('#searchInput').value = '';
        $('#periodSelect').value = 'all';
        renderFilters(); renderTable();
        return;
      }

      if (t.closest('[data-theme-toggle]')) {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
          (!document.documentElement.getAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        applyTheme(isDark ? 'light' : 'dark');
        return;
      }
    });

    $('#searchInput').addEventListener('input', (e) => { state.query = e.target.value; renderTable(); });
    $('#periodSelect').addEventListener('change', (e) => { state.period = e.target.value; renderTable(); });

    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeOrder(); });
  }

  /* ── Старт ──────────────────────────────────────────────────────────── */
  function init() {
    $$('[data-icon]').forEach((el) => {
      const name = el.getAttribute('data-icon');
      if (ICON[name]) el.innerHTML = ICON[name] + el.innerHTML;
    });

    applyTheme(store.read('theme', null));
    $$('[data-brand-name]').forEach((el) => { el.textContent = BRAND.name; });
    $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });

    renderChat();
    renderStats();
    renderFilters();
    renderTable();
    bind();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
