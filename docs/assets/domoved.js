/* ───────────────────────────────────────────────────────────
   Домовед · автозаполнение страниц данными из data.js

   На странице достаточно написать:
     <span data-dm="account.number"></span>
     <span data-dm="balance.total" data-fmt="money"></span>
     <span data-dm="balance.collection" data-fmt="percent"></span>

   Форматы: text (по умолчанию), money, percent, date, area, tariff.
   Если значение не заполнено — подставляется прочерк, элемент
   получает класс .empty, а страница показывает счётчик пропусков
   в элементе с id="fillState" (если он есть).
   ─────────────────────────────────────────────────────────── */

(function () {
  var D = window.DOMOVED || {};
  var missing = [];

  function get(path) {
    return path.split('.').reduce(function (acc, key) {
      return acc == null ? undefined : acc[key];
    }, D);
  }

  function isEmpty(v) {
    return v === null || v === undefined || v === '' ||
           (Array.isArray(v) && v.length === 0);
  }

  var MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

  function money(v) {
    var n = Number(v);
    if (!isFinite(n)) return null;
    var whole = Math.floor(Math.abs(n));
    var cents = Math.round((Math.abs(n) - whole) * 100);
    var s = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    if (cents) s += ',' + String(cents).padStart(2, '0');
    return (n < 0 ? '−' : '') + s + ' ₽';
  }

  function dateLong(v) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(v));
    if (!m) return String(v);
    return Number(m[3]) + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1];
  }

  function dateShort(v) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(v));
    return m ? m[3] + '.' + m[2] + '.' + m[1] : String(v);
  }

  function format(v, fmt) {
    switch (fmt) {
      case 'money':   return money(v);
      case 'percent': return String(v).replace('.', ',') + ' %';
      case 'date':    return dateLong(v);
      case 'dateShort': return dateShort(v);
      case 'area':    return String(v).replace('.', ',') + ' м²';
      case 'tariff':  return String(v).replace('.', ',') + ' ₽/м² в месяц';
      default:        return String(v);
    }
  }

  /* ── подстановка значений ─────────────────────────────── */
  document.querySelectorAll('[data-dm]').forEach(function (el) {
    var path = el.getAttribute('data-dm');
    var val = get(path);

    if (isEmpty(val)) {
      el.textContent = el.getAttribute('data-empty') || '—';
      el.classList.add('empty');
      if (missing.indexOf(path) === -1) missing.push(path);
      return;
    }
    el.textContent = format(val, el.getAttribute('data-fmt'));
    el.classList.remove('empty');
  });

  /* ── полоса собираемости ──────────────────────────────── */
  document.querySelectorAll('[data-meter]').forEach(function (el) {
    var val = Number(get(el.getAttribute('data-meter')));
    var bar = el.querySelector('span');
    if (!bar) return;
    bar.style.width = isFinite(val) ? Math.max(0, Math.min(100, val)) + '%' : '0%';
  });

  /* ── кнопки «написать в Telegram» ─────────────────────── */
  var tg = (D.contacts && D.contacts.telegram || '').trim().replace(/^@/, '');
  document.querySelectorAll('[data-tg-text]').forEach(function (el) {
    if (!tg) {
      el.setAttribute('aria-disabled', 'true');
      el.removeAttribute('href');
      var hint = document.getElementById(el.getAttribute('data-tg-hint') || '');
      if (hint) hint.textContent = 'Контакт для заявок ещё не указан в data.js';
      return;
    }
    var text = el.getAttribute('data-tg-text');
    el.setAttribute('href', 'https://t.me/' + tg + '?text=' + encodeURIComponent(text));
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener');
  });

  /* ── дата актуальности и счётчик пропусков ────────────── */
  /* Если страница уже написала свой текст в #fillState — не трогаем его. */
  var state = document.getElementById('fillState');
  if (state && !state.textContent.trim()) {
    var parts = [];
    if (D.updated) parts.push('Данные на ' + dateLong(D.updated));
    if (missing.length) parts.push(missing.length + ' показателей ещё не заполнено');
    state.textContent = parts.join(' · ') || 'Данные ещё не заполнены';
    var dot = state.parentElement && state.parentElement.querySelector('.dot');
    if (dot && (missing.length || !D.updated)) dot.classList.add('stale');
  }

  /* ── списки работ и планов ────────────────────────────── */
  document.querySelectorAll('[data-list]').forEach(function (el) {
    var rows = get(el.getAttribute('data-list'));
    var body = el.querySelector('tbody');
    var blank = el.querySelector('[data-blank]');
    if (!body) return;

    if (isEmpty(rows)) {
      el.querySelector('table').hidden = true;
      if (blank) blank.hidden = false;
      return;
    }
    if (blank) blank.hidden = true;
    el.querySelector('table').hidden = false;

    body.innerHTML = '';
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      var c1 = document.createElement('td');
      c1.textContent = r.name || '—';
      var c2 = document.createElement('td');
      c2.textContent = r.date ? dateShort(r.date) : (r.term || '—');
      var c3 = document.createElement('td');
      c3.className = 'num';
      c3.textContent = r.amount == null ? '—' : money(r.amount);
      tr.append(c1, c2, c3);
      body.appendChild(tr);
    });
  });

  /* ── печать ───────────────────────────────────────────── */
  document.querySelectorAll('[data-print]').forEach(function (el) {
    el.addEventListener('click', function () { window.print(); });
  });

  /* ── копирование ──────────────────────────────────────── */
  document.querySelectorAll('[data-copy]').forEach(function (el) {
    el.addEventListener('click', function () {
      var value = get(el.getAttribute('data-copy')) || el.getAttribute('data-copy-raw') || '';
      var note = document.getElementById(el.getAttribute('data-copy-note') || '');
      var done = function () {
        if (!note) return;
        var prev = note.textContent;
        note.textContent = 'Скопировано';
        setTimeout(function () { note.textContent = prev; }, 2500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(String(value)).then(done, function () {
          if (note) note.textContent = String(value);
        });
      } else if (note) {
        note.textContent = String(value);
      }
    });
  });
})();
