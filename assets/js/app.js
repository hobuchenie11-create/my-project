/* ==========================================================================
   Алиса — логика прототипа
   Каталог с фильтрами, карточка товара, избранное, корзина, оформление заказа.
   Состояние корзины и избранного переживает перезагрузку (localStorage).
   ========================================================================== */
(function () {
  'use strict';

  /* ── Утилиты ────────────────────────────────────────────────────────── */
  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const money = (n) => new Intl.NumberFormat('ru-RU').format(Math.round(n)) + ' ₽';

  /* Склонение: plural(3, 'товар', 'товара', 'товаров') → 'товара' */
  const plural = (n, one, few, many) => {
    const a = Math.abs(n) % 100;
    const b = a % 10;
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
        const raw = localStorage.getItem('alisa:' + key);
        return raw ? JSON.parse(raw) : fallback;
      } catch (e) { return fallback; }
    },
    write(key, value) {
      try { localStorage.setItem('alisa:' + key, JSON.stringify(value)); } catch (e) { /* приватный режим */ }
    },
  };

  /* ── Иллюстрации товаров ────────────────────────────────────────────────
     Вместо фотографий — рисованные силуэты вещей. Когда появятся снимки
     товаров, art(...) заменяется на <img src="...">, разметка не меняется. */
  const ART = {
    envelope: (t) => `
      <rect x="20" y="26" width="80" height="74" rx="16" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <path d="M20 42 L60 68 L100 42" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".65"/>
      <path d="M44 26 Q60 44 76 26" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".5"/>
      <circle cx="60" cy="70" r="7" fill="none" stroke="var(--accent)" stroke-width="2"/>
      <path d="M53 70 Q44 62 42 72 Q46 78 53 70Z M67 70 Q76 62 78 72 Q74 78 67 70Z" fill="var(--accent)" opacity=".55"/>`,
    set: (t) => `
      <rect x="16" y="56" width="88" height="44" rx="10" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <rect x="26" y="38" width="68" height="30" rx="9" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <rect x="38" y="22" width="44" height="26" rx="8" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <path d="M28 78 H92" stroke="var(--accent)" stroke-width="2" opacity=".5"/>
      <path d="M36 52 H84" stroke="var(--accent)" stroke-width="2" opacity=".4"/>
      <circle cx="60" cy="34" r="3.5" fill="var(--accent)" opacity=".6"/>`,
    pants: (t) => `
      <path d="M36 26 H84 L88 50 L82 100 H64 L60 66 L56 100 H38 L32 50 Z"
            fill="${t}" stroke="var(--line-strong)" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M34 38 H86" stroke="var(--accent)" stroke-width="3" opacity=".55"/>
      <path d="M60 52 V66" stroke="var(--accent)" stroke-width="1.5" opacity=".4"/>
      <circle cx="47" cy="94" r="3" fill="var(--accent)" opacity=".45"/>
      <circle cx="73" cy="94" r="3" fill="var(--accent)" opacity=".45"/>`,
    shirt: (t) => `
      <path d="M32 34 L48 26 Q60 36 72 26 L88 34 L97 54 L83 60 L81 96 Q60 101 39 96 L37 60 L23 54 Z"
            fill="${t}" stroke="var(--line-strong)" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M48 26 L60 60 L72 26" fill="none" stroke="var(--accent)" stroke-width="1.6" opacity=".5"/>
      <path d="M60 60 V94" stroke="var(--accent)" stroke-width="1.4" opacity=".35"/>
      <circle cx="60" cy="70" r="2.6" fill="var(--accent)" opacity=".55"/>
      <circle cx="60" cy="82" r="2.6" fill="var(--accent)" opacity=".55"/>`,
    bonnet: (t) => `
      <path d="M28 66 Q28 26 60 26 Q92 26 92 66 Z" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <path d="M22 66 H98 Q98 76 88 76 H32 Q22 76 22 66Z" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <path d="M34 76 Q30 92 40 100" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".6"/>
      <path d="M86 76 Q90 92 80 100" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".6"/>
      <path d="M40 60 Q60 44 80 60" fill="none" stroke="var(--accent)" stroke-width="1.6" opacity=".45"/>`,
    romper: (t) => `
      <path d="M34 32 L48 24 Q60 34 72 24 L86 32 L95 50 L82 55 L82 62 L78 100 H64 L61 72 L58 100 H44 L38 62 L38 55 L25 50 Z"
            fill="${t}" stroke="var(--line-strong)" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M60 34 V72" stroke="var(--accent)" stroke-width="1.6" opacity=".5"/>
      <circle cx="60" cy="44" r="2.4" fill="var(--accent)" opacity=".6"/>
      <circle cx="60" cy="56" r="2.4" fill="var(--accent)" opacity=".6"/>
      <path d="M44 96 H58 M64 96 H78" stroke="var(--accent)" stroke-width="2" opacity=".45"/>`,
    bodysuit: (t) => `
      <path d="M34 32 L48 25 Q60 34 72 25 L86 32 L95 50 L82 55 L81 74 Q60 94 39 74 L38 55 L25 50 Z"
            fill="${t}" stroke="var(--line-strong)" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M48 25 Q60 40 72 25" fill="none" stroke="var(--accent)" stroke-width="1.6" opacity=".5"/>
      <path d="M46 80 H74" stroke="var(--accent)" stroke-width="2" opacity=".5"/>
      <circle cx="53" cy="80" r="2.4" fill="var(--accent)"/>
      <circle cx="60" cy="82" r="2.4" fill="var(--accent)"/>
      <circle cx="67" cy="80" r="2.4" fill="var(--accent)"/>`,
    all: (t) => `
      <rect x="20" y="20" width="36" height="36" rx="9" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <rect x="64" y="20" width="36" height="36" rx="9" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <rect x="20" y="64" width="36" height="36" rx="9" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>
      <rect x="64" y="64" width="36" height="36" rx="9" fill="${t}" stroke="var(--line-strong)" stroke-width="1.5"/>`,
  };

  const art = (kind, tone) => {
    const draw = ART[kind] || ART.set;
    return `<svg viewBox="0 0 120 120" role="img" aria-hidden="true" focusable="false">${draw(tone || 'var(--surface)')}</svg>`;
  };

  /* ── Иконки интерфейса ──────────────────────────────────────────────── */
  const ICON = {
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    heart:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M12 20s-7-4.6-7-9.4A4.1 4.1 0 0 1 12 8a4.1 4.1 0 0 1 7 2.6C19 15.4 12 20 12 20Z"/></svg>',
    cart:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h2l2.2 10.2a2 2 0 0 0 2 1.6h7.2a2 2 0 0 0 2-1.5L21 8H7"/><circle cx="10.5" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/></svg>',
    plus:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 6v12M6 12h12"/></svg>',
    close:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    star:   '<svg viewBox="0 0 24 24"><path d="m12 3.6 2.5 5.2 5.7.8-4.1 4 1 5.7-5.1-2.7-5.1 2.7 1-5.7-4.1-4 5.7-.8Z"/></svg>',
    check:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7"/></svg>',
    home:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1Z"/></svg>',
    grid:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/></svg>',
    leaf:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M20 4c-8 0-14 3.6-14 10a5 5 0 0 0 5 5c6 0 9-6.4 9-15Z"/><path d="M8 20c1.5-4 4-6.5 7.5-8.5"/></svg>',
    truck:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M3 7h11v9H3zM14 10h3.5l2.5 3v3h-6z"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></svg>',
    swap:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13l-3-3M20 16H7l3 3"/></svg>',
    ruler:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><rect x="2.5" y="8" width="19" height="8" rx="2"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/></svg>',
    sun:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/></svg>',
    moon:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4 8.2 8.2 0 1 0 20 14.5Z"/></svg>',
  };

  /* ── Состояние ──────────────────────────────────────────────────────── */
  const state = {
    cat: 'all',
    season: 'all',
    size: 'all',
    query: '',
    sort: 'popular',
    cart: store.read('cart', []),          // [{ id, size, color, qty }]
    favs: store.read('favs', []),          // [id]
    promo: null,                           // { code, discount, title }
    checkoutStep: 1,
    order: {
      name: '', phone: '', email: '',
      city: '', address: '',
      delivery: 'courier', payment: 'card',
      comment: '', gift: false, callback: true,
    },
  };

  const productById = (id) => PRODUCTS.find((p) => p.id === id);

  /* ── Корзина ────────────────────────────────────────────────────────── */
  const cartKey = (item) => item.id + '|' + item.size + '|' + item.color;

  function addToCart(id, size, color, qty) {
    const p = productById(id);
    if (!p) return;
    const line = {
      id,
      size: size || p.sizes[0],
      color: color || p.colors[0],
      qty: qty || 1,
    };
    const found = state.cart.find((c) => cartKey(c) === cartKey(line));
    if (found) found.qty += line.qty;
    else state.cart.push(line);
    persistCart();
    toast(`«${p.name}» — в корзине`);
  }

  function setQty(key, delta) {
    const line = state.cart.find((c) => cartKey(c) === key);
    if (!line) return;
    line.qty += delta;
    if (line.qty < 1) state.cart = state.cart.filter((c) => cartKey(c) !== key);
    persistCart();
  }

  function removeLine(key) {
    state.cart = state.cart.filter((c) => cartKey(c) !== key);
    persistCart();
    toast('Товар убран из корзины');
  }

  function persistCart() {
    store.write('cart', state.cart);
    renderCart();
    renderCounters();
  }

  const cartCount = () => state.cart.reduce((s, c) => s + c.qty, 0);
  const cartSubtotal = () => state.cart.reduce((s, c) => {
    const p = productById(c.id);
    return p ? s + p.price * c.qty : s;
  }, 0);

  function deliveryPrice() {
    const method = DELIVERY.find((d) => d.id === state.order.delivery) || DELIVERY[0];
    if (method.id === 'courier' && cartSubtotal() - discountValue() >= BRAND.freeFrom) return 0;
    return method.price;
  }

  const discountValue = () => (state.promo ? Math.round(cartSubtotal() * state.promo.discount) : 0);
  const giftPrice = () => (state.order.gift ? 350 : 0);
  const orderTotal = () => cartSubtotal() - discountValue() + deliveryPrice() + giftPrice();

  /* ── Избранное ──────────────────────────────────────────────────────── */
  function toggleFav(id) {
    const i = state.favs.indexOf(id);
    if (i === -1) { state.favs.push(id); toast('Добавлено в избранное'); }
    else { state.favs.splice(i, 1); toast('Убрано из избранного'); }
    store.write('favs', state.favs);
    renderCatalog();
    renderCounters();
  }

  /* ── Уведомления ────────────────────────────────────────────────────── */
  let toastTimer = null;
  function toast(text) {
    const box = $('#toasts');
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = text;
    box.innerHTML = '';           /* показываем только последнее сообщение */
    box.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { box.innerHTML = ''; }, 2600);
  }

  /* ── Шапка: бренд ───────────────────────────────────────────────────── */
  function renderBrand() {
    /* Логотип-заглушка. Когда придёт готовый файл — положить его в
       assets/img/logo.svg и указать путь в BRAND.logo (data.js). */
    const mark = BRAND.logo
      ? `<img class="brand__logo" src="${esc(BRAND.logo)}" alt="${esc(BRAND.name)}">`
      : `<svg class="brand__mark" viewBox="0 0 40 40" aria-hidden="true">
           <circle cx="20" cy="20" r="19" fill="var(--accent-wash)" stroke="var(--accent)" stroke-width="1.2"/>
           <text x="20" y="20" text-anchor="middle" dominant-baseline="central"
                 font-family="Georgia, serif" font-size="19" fill="var(--accent-deep)"
                 >${esc(BRAND.name.charAt(0))}</text>
         </svg>`;

    $$('[data-brand-mark]').forEach((el) => { el.innerHTML = mark; });
    $$('[data-brand-name]').forEach((el) => { el.textContent = BRAND.name; });
    $$('[data-brand-tag]').forEach((el) => { el.textContent = BRAND.tagline; });
    $$('[data-brand-phone]').forEach((el) => { el.textContent = BRAND.phone; el.href = 'tel:' + BRAND.phoneHref; });
    $$('[data-brand-email]').forEach((el) => { el.textContent = BRAND.email; el.href = 'mailto:' + BRAND.email; });
    $$('[data-brand-address]').forEach((el) => { el.textContent = BRAND.address; });
    $$('[data-brand-hours]').forEach((el) => { el.textContent = BRAND.hours; });
    $$('[data-free-from]').forEach((el) => { el.textContent = money(BRAND.freeFrom); });
    $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
  }

  /* ── Категории ──────────────────────────────────────────────────────── */
  function renderCategoryTiles() {
    const counts = {};
    PRODUCTS.forEach((p) => { counts[p.cat] = (counts[p.cat] || 0) + 1; });

    $('#catTiles').innerHTML = CATEGORIES.filter((c) => c.id !== 'all').map((c) => `
      <button class="cat-tile" type="button" data-cat-tile="${c.id}">
        ${art(c.icon, 'var(--surface-2)')}
        <b>${esc(c.title)}</b>
        <span class="num">${counts[c.id] || 0} ${plural(counts[c.id] || 0, 'модель', 'модели', 'моделей')}</span>
      </button>`).join('');
  }

  function renderFilterChips() {
    $('#catChips').innerHTML = CATEGORIES.map((c) => `
      <button class="chip${state.cat === c.id ? ' is-active' : ''}" type="button" data-cat="${c.id}">${esc(c.title)}</button>
    `).join('');

    $('#seasonChips').innerHTML = [{ id: 'all', title: 'Любой' }].concat(SEASONS).map((s) => `
      <button class="chip chip--sm${state.season === s.id ? ' is-active' : ''}" type="button" data-season="${s.id}">${esc(s.title)}</button>
    `).join('');

    $('#sizeChips').innerHTML = [{ id: 'all' }].concat(SIZES).map((s) => `
      <button class="chip chip--sm${state.size === s.id ? ' is-active' : ''}" type="button" data-size="${s.id}">${s.id === 'all' ? 'Любой' : esc(s.id)}</button>
    `).join('');
  }

  /* ── Каталог ────────────────────────────────────────────────────────── */
  function visibleProducts() {
    const q = state.query.trim().toLowerCase();
    let list = PRODUCTS.filter((p) => {
      if (state.cat !== 'all' && p.cat !== state.cat) return false;
      if (state.season !== 'all' && p.season !== state.season && p.season !== 'vsesezon') return false;
      if (state.size !== 'all' && !p.sizes.includes(state.size)) return false;
      if (q) {
        const hay = (p.name + ' ' + p.desc + ' ' + p.material + ' ' + p.colors.join(' ')).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    const sorters = {
      popular:  (a, b) => (b.reviews * b.rating) - (a.reviews * a.rating),
      cheap:    (a, b) => a.price - b.price,
      expensive:(a, b) => b.price - a.price,
      rating:   (a, b) => b.rating - a.rating,
    };
    return list.sort(sorters[state.sort] || sorters.popular);
  }

  function flagFor(p) {
    if (p.oldPrice) {
      const off = Math.round((1 - p.price / p.oldPrice) * 100);
      return `<span class="flag flag--sale">−${off}%</span>`;
    }
    return '';
  }

  function renderCatalog() {
    const list = visibleProducts();
    const grid = $('#grid');

    $('#resultsCount').textContent =
      list.length + ' ' + plural(list.length, 'товар', 'товара', 'товаров');

    if (!list.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <strong>Ничего не нашлось</strong>
          Попробуйте убрать часть фильтров или поискать по другому слову.
          <div style="margin-top:16px"><button class="btn btn--ghost" type="button" data-reset-filters>Сбросить фильтры</button></div>
        </div>`;
      return;
    }

    const seasonTitle = (id) => (SEASONS.find((s) => s.id === id) || {}).title || '';

    grid.innerHTML = list.map((p) => `
      <article class="card">
        <button class="card__art" type="button" data-open="${p.id}" aria-label="Открыть карточку: ${esc(p.name)}">
          ${art(p.art, p.tone)}
        </button>
        <div class="card__flags">
          ${p.badge ? `<span class="flag flag--${p.badge === 'Хит' ? 'hit' : 'new'}">${esc(p.badge)}</span>` : ''}
          ${flagFor(p)}
        </div>
        <button class="fav-btn${state.favs.includes(p.id) ? ' is-on' : ''}" type="button" data-fav="${p.id}"
                aria-label="${state.favs.includes(p.id) ? 'Убрать из избранного' : 'В избранное'}">${ICON.heart}</button>

        <div class="card__body">
          <div class="card__meta">
            <span>${esc(seasonTitle(p.season))}</span>
            <i class="dot"></i>
            <span class="rating">${ICON.star}<span class="num">${p.rating.toFixed(1)}</span></span>
          </div>
          <button class="card__title" type="button" data-open="${p.id}">${esc(p.name)}</button>
          <div class="sizes-row">${p.sizes.map((s) => `<span class="size-tag num">${esc(s)}</span>`).join('')}</div>
          <div class="card__foot">
            <span class="price">
              <b class="num">${money(p.price)}</b>
              ${p.oldPrice ? `<s class="num">${money(p.oldPrice)}</s>` : ''}
            </span>
            <button class="add-btn" type="button" data-add="${p.id}" aria-label="Добавить в корзину">${ICON.plus}</button>
          </div>
        </div>
      </article>`).join('');
  }

  /* ── Карточка товара ────────────────────────────────────────────────── */
  let pdpSelection = { id: null, size: null, color: null };

  function openProduct(id) {
    const p = productById(id);
    if (!p) return;
    pdpSelection = { id: p.id, size: p.sizes[0], color: p.colors[0] };
    $('#productTitle').textContent = (CATEGORIES.find((c) => c.id === p.cat) || {}).title || 'Товар';

    $('#productBody').innerHTML = `
      <div class="pdp">
        <div>
          <div class="pdp__art">${art(p.art, p.tone)}</div>
        </div>
        <div>
          <h3>${esc(p.name)}</h3>
          <div class="rating">${ICON.star}<span class="num">${p.rating.toFixed(1)}</span>
            <span style="color:var(--muted)">· ${p.reviews} ${plural(p.reviews, 'отзыв', 'отзыва', 'отзывов')}</span></div>

          <div class="pdp__price">
            <b class="num">${money(p.price)}</b>
            ${p.oldPrice ? `<s class="num">${money(p.oldPrice)}</s>` : ''}
          </div>

          <p class="pdp__desc">${esc(p.desc)}</p>

          <div class="pdp__block" style="margin-top:18px">
            <b>Размер</b>
            <div class="sizes-row" id="pdpSizes">
              ${p.sizes.map((s, i) => `<button class="chip chip--sm${i === 0 ? ' is-active' : ''}" type="button" data-pdp-size="${esc(s)}">${esc(s)}</button>`).join('')}
            </div>
            <p class="hint" style="font-size:12.5px;color:var(--muted);margin-top:7px">
              Размер — это рост ребёнка в сантиметрах.
              <button class="link-danger" type="button" data-open-sizes style="color:var(--accent-deep)">Таблица размеров</button>
            </p>
          </div>

          <div class="pdp__block">
            <b>Цвет</b>
            <div class="sizes-row" id="pdpColors">
              ${p.colors.map((c, i) => `<button class="chip chip--sm${i === 0 ? ' is-active' : ''}" type="button" data-pdp-color="${esc(c)}">${esc(c)}</button>`).join('')}
            </div>
          </div>

          ${p.includes.length ? `
          <div class="pdp__block">
            <b>Состав комплекта</b>
            <ul class="includes">${p.includes.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>
          </div>` : ''}

          <div class="pdp__block">
            <b>Характеристики</b>
            <dl class="spec">
              <dt>Ткань</dt><dd>${esc(p.material)}</dd>
              <dt>Состав</dt><dd>${esc(p.composition)}</dd>
              <dt>Уход</dt><dd>${esc(p.care)}</dd>
              <dt>Сезон</dt><dd>${esc((SEASONS.find((s) => s.id === p.season) || {}).title || '')}</dd>
            </dl>
          </div>

          <div class="pdp__actions">
            <button class="btn btn--primary btn--lg" type="button" data-pdp-add>${ICON.cart} В корзину</button>
            <button class="btn btn--ghost btn--lg" type="button" data-fav="${p.id}">${ICON.heart} В избранное</button>
          </div>
        </div>
      </div>`;

    openLayer('#productModal');
  }

  /* ── Корзина: отрисовка ─────────────────────────────────────────────── */
  function renderCart() {
    const body = $('#cartBody');
    const foot = $('#cartFoot');

    if (!state.cart.length) {
      body.innerHTML = `
        <div class="empty-state" style="border:none;padding:48px 8px">
          <strong>Корзина пуста</strong>
          Загляните в каталог — там комплекты на выписку, боди и слипы.
          <div style="margin-top:18px"><button class="btn btn--primary" type="button" data-close-layers data-goto="#catalog">В каталог</button></div>
        </div>`;
      foot.innerHTML = '';
      return;
    }

    body.innerHTML = state.cart.map((c) => {
      const p = productById(c.id);
      if (!p) return '';
      const key = cartKey(c);
      return `
        <div class="cart-line">
          <div class="cart-line__art">${art(p.art, p.tone)}</div>
          <div class="cart-line__info">
            <b>${esc(p.name)}</b>
            <span>Размер ${esc(c.size)} · ${esc(c.color)}</span>
            <div class="cart-line__ctrl">
              <span class="qty">
                <button type="button" data-qty-minus="${esc(key)}" aria-label="Уменьшить количество">−</button>
                <span class="num">${c.qty}</span>
                <button type="button" data-qty-plus="${esc(key)}" aria-label="Увеличить количество">+</button>
              </span>
              <b class="num">${money(p.price * c.qty)}</b>
            </div>
            <button class="link-danger" type="button" data-remove="${esc(key)}">Убрать</button>
          </div>
        </div>`;
    }).join('');

    const left = BRAND.freeFrom - (cartSubtotal() - discountValue());
    const pct = Math.min(100, Math.round(((cartSubtotal() - discountValue()) / BRAND.freeFrom) * 100));

    foot.innerHTML = `
      ${left > 0 ? `
        <div class="free-bar">
          До бесплатной доставки по городу — <b class="num">${money(left)}</b>
          <div class="free-bar__track"><div class="free-bar__fill" style="width:${pct}%"></div></div>
        </div>` : `
        <div class="free-bar">Доставка по городу — бесплатно ✓</div>`}

      <div style="margin:14px 0 12px">
        <div class="promo-row">
          <input class="field" id="promoInput" type="text" placeholder="Промокод" value="${state.promo ? esc(state.promo.code) : ''}" autocomplete="off">
          <button class="btn btn--ghost" type="button" data-apply-promo>Применить</button>
        </div>
        <p class="promo-note${state.promo ? ' is-ok' : ''}" id="promoNote">${state.promo ? 'Промокод применён: ' + esc(state.promo.title) : 'Попробуйте МАЛЫШ10'}</p>
      </div>

      <div class="sum-row"><span>Товары, ${cartCount()} ${plural(cartCount(), 'шт.', 'шт.', 'шт.')}</span><b class="num">${money(cartSubtotal())}</b></div>
      ${state.promo ? `<div class="sum-row is-discount"><span>Скидка</span><b class="num">−${money(discountValue())}</b></div>` : ''}
      <div class="sum-row is-total"><span>Итого</span><b class="num">${money(cartSubtotal() - discountValue())}</b></div>

      <button class="btn btn--primary btn--block btn--lg" type="button" data-checkout style="margin-top:14px">Оформить заказ</button>
      <p style="font-size:12px;color:var(--muted);text-align:center;margin-top:10px">Доставка рассчитывается на следующем шаге</p>`;
  }

  function renderCounters() {
    const c = cartCount();
    $$('[data-cart-count]').forEach((el) => {
      el.textContent = c;
      el.classList.toggle('is-on', c > 0);
    });
    const f = state.favs.length;
    $$('[data-fav-count]').forEach((el) => {
      el.textContent = f;
      el.classList.toggle('is-on', f > 0);
    });
  }

  /* ── Оформление заказа ──────────────────────────────────────────────── */
  function openCheckout() {
    if (!state.cart.length) { toast('Сначала добавьте товары в корзину'); return; }
    state.checkoutStep = 1;
    closeLayer('#cartDrawer');
    renderCheckout();
    openLayer('#checkoutModal');
  }

  function renderSteps() {
    const titles = ['Контакты', 'Доставка и оплата', 'Подтверждение'];
    $('#checkoutSteps').innerHTML = titles.map((t, i) => {
      const n = i + 1;
      const cls = state.checkoutStep === n ? ' is-active' : (state.checkoutStep > n ? ' is-done' : '');
      return `<div class="step${cls}"><i class="step__num">${state.checkoutStep > n ? '✓' : n}</i><span>${t}</span></div>` +
             (n < 3 ? '<i class="step__line"></i>' : '');
    }).join('');
  }

  function renderCheckout() {
    renderSteps();
    const o = state.order;
    const body = $('#checkoutBody');
    const foot = $('#checkoutFoot');

    if (state.checkoutStep === 1) {
      body.innerHTML = `
        <div class="form-grid">
          <div class="form-field is-wide" data-field="name">
            <label for="f-name">Имя и фамилия</label>
            <input class="field" id="f-name" type="text" value="${esc(o.name)}" placeholder="Анна Смирнова" autocomplete="name">
            <span class="err">Укажите, как к вам обращаться</span>
          </div>
          <div class="form-field" data-field="phone">
            <label for="f-phone">Телефон</label>
            <input class="field" id="f-phone" type="tel" value="${esc(o.phone)}" placeholder="+7 900 123-45-67" autocomplete="tel" inputmode="tel">
            <span class="err">Введите номер из 11 цифр</span>
          </div>
          <div class="form-field" data-field="email">
            <label for="f-email">Электронная почта</label>
            <input class="field" id="f-email" type="email" value="${esc(o.email)}" placeholder="anna@mail.ru" autocomplete="email">
            <span class="err">Проверьте адрес — на него придёт чек</span>
          </div>
          <div class="form-field is-wide">
            <label class="check">
              <input type="checkbox" id="f-callback" ${o.callback ? 'checked' : ''}>
              <span>Позвонить для подтверждения заказа. Если снимете галочку — напишем в мессенджер.</span>
            </label>
          </div>
        </div>`;
      foot.innerHTML = `
        <div class="total">К оплате<b class="num">${money(orderTotal())}</b></div>
        <button class="btn btn--primary btn--lg" type="button" data-step-next>Далее — доставка</button>`;
    }

    if (state.checkoutStep === 2) {
      body.innerHTML = `
        <div class="form-grid" style="margin-bottom:20px">
          <div class="form-field" data-field="city">
            <label for="f-city">Город</label>
            <input class="field" id="f-city" type="text" value="${esc(o.city)}" placeholder="Москва" autocomplete="address-level2">
            <span class="err">Укажите город доставки</span>
          </div>
          <div class="form-field" data-field="address">
            <label for="f-address">Адрес или пункт выдачи</label>
            <input class="field" id="f-address" type="text" value="${esc(o.address)}" placeholder="ул. Ленина, 10, кв. 5" autocomplete="street-address">
            <span class="err">Укажите адрес — курьеру нужно знать, куда ехать</span>
          </div>
        </div>

        <p class="eyebrow" style="margin-bottom:10px">Способ доставки</p>
        <div class="opt-list" style="margin-bottom:22px">
          ${DELIVERY.map((d) => {
            const free = d.id === 'courier' && (cartSubtotal() - discountValue()) >= BRAND.freeFrom;
            const price = d.price === 0 || free ? 'Бесплатно' : money(d.price);
            return `
            <label class="opt${o.delivery === d.id ? ' is-active' : ''}" data-delivery="${d.id}">
              <input type="radio" name="delivery" value="${d.id}" ${o.delivery === d.id ? 'checked' : ''}>
              <i class="opt__dot"></i>
              <span class="opt__text"><b>${esc(d.title)}</b><span>${esc(d.eta)} · ${esc(d.note)}</span></span>
              <span class="opt__price num">${price}</span>
            </label>`;
          }).join('')}
        </div>

        <p class="eyebrow" style="margin-bottom:10px">Оплата</p>
        <div class="opt-list" style="margin-bottom:22px">
          ${PAYMENT.map((m) => `
            <label class="opt${o.payment === m.id ? ' is-active' : ''}" data-payment="${m.id}">
              <input type="radio" name="payment" value="${m.id}" ${o.payment === m.id ? 'checked' : ''}>
              <i class="opt__dot"></i>
              <span class="opt__text"><b>${esc(m.title)}</b><span>${esc(m.note)}</span></span>
            </label>`).join('')}
        </div>

        <div class="form-field is-wide" style="margin-bottom:14px">
          <label for="f-comment">Комментарий к заказу</label>
          <textarea class="field" id="f-comment" placeholder="Например: домофон не работает, позвоните за час">${esc(o.comment)}</textarea>
        </div>

        <label class="check">
          <input type="checkbox" id="f-gift" ${o.gift ? 'checked' : ''}>
          <span>Подарочная упаковка и открытка с подписью — <b>350 ₽</b>. Пригодится, если заказ едет прямо в роддом.</span>
        </label>`;
      foot.innerHTML = `
        <div class="total">К оплате<b class="num">${money(orderTotal())}</b></div>
        <div style="display:flex;gap:10px">
          <button class="btn btn--ghost btn--lg" type="button" data-step-back>Назад</button>
          <button class="btn btn--primary btn--lg" type="button" data-step-next>Далее — проверка</button>
        </div>`;
    }

    if (state.checkoutStep === 3) {
      const d = DELIVERY.find((x) => x.id === o.delivery);
      const m = PAYMENT.find((x) => x.id === o.payment);
      body.innerHTML = `
        <p class="eyebrow" style="margin-bottom:10px">Состав заказа</p>
        <div class="order-summary" style="margin-bottom:18px">
          ${state.cart.map((c) => {
            const p = productById(c.id);
            return `<div class="sum-row"><span>${esc(p.name)} · ${esc(c.size)} · ${esc(c.color)} · ${c.qty} шт.</span><b class="num">${money(p.price * c.qty)}</b></div>`;
          }).join('')}
        </div>

        <p class="eyebrow" style="margin-bottom:10px">Получатель</p>
        <div class="order-summary" style="margin-bottom:18px">
          <div class="sum-row"><span>Имя</span><b>${esc(o.name)}</b></div>
          <div class="sum-row"><span>Телефон</span><b class="num">${esc(o.phone)}</b></div>
          <div class="sum-row"><span>Почта</span><b>${esc(o.email)}</b></div>
          <div class="sum-row"><span>Адрес</span><b>${esc(o.city)}, ${esc(o.address)}</b></div>
          <div class="sum-row"><span>Доставка</span><b>${esc(d.title)}, ${esc(d.eta)}</b></div>
          <div class="sum-row"><span>Оплата</span><b>${esc(m.title)}</b></div>
          ${o.comment ? `<div class="sum-row"><span>Комментарий</span><b>${esc(o.comment)}</b></div>` : ''}
        </div>

        <p class="eyebrow" style="margin-bottom:10px">К оплате</p>
        <div class="order-summary">
          <div class="sum-row"><span>Товары</span><b class="num">${money(cartSubtotal())}</b></div>
          ${state.promo ? `<div class="sum-row is-discount"><span>Скидка (${esc(state.promo.code)})</span><b class="num">−${money(discountValue())}</b></div>` : ''}
          <div class="sum-row"><span>Доставка</span><b class="num">${deliveryPrice() === 0 ? 'Бесплатно' : money(deliveryPrice())}</b></div>
          ${o.gift ? `<div class="sum-row"><span>Подарочная упаковка</span><b class="num">${money(giftPrice())}</b></div>` : ''}
          <div class="sum-row is-total"><span>Итого</span><b class="num">${money(orderTotal())}</b></div>
        </div>

        <p style="font-size:12.5px;color:var(--muted);margin-top:14px">
          Нажимая «Подтвердить заказ», вы соглашаетесь с условиями обработки персональных данных.
          Это прототип — оплата не проводится.
        </p>`;
      foot.innerHTML = `
        <div class="total">К оплате<b class="num">${money(orderTotal())}</b></div>
        <div style="display:flex;gap:10px">
          <button class="btn btn--ghost btn--lg" type="button" data-step-back>Назад</button>
          <button class="btn btn--primary btn--lg" type="button" data-submit-order>Подтвердить заказ</button>
        </div>`;
    }
  }

  /* Собирает значения полей текущего шага в state.order */
  function collectStep() {
    const o = state.order;
    if (state.checkoutStep === 1) {
      o.name = ($('#f-name') || {}).value || '';
      o.phone = ($('#f-phone') || {}).value || '';
      o.email = ($('#f-email') || {}).value || '';
      o.callback = !!($('#f-callback') || {}).checked;
    }
    if (state.checkoutStep === 2) {
      o.city = ($('#f-city') || {}).value || '';
      o.address = ($('#f-address') || {}).value || '';
      o.comment = ($('#f-comment') || {}).value || '';
      o.gift = !!($('#f-gift') || {}).checked;
    }
  }

  function markError(fieldName, hasError) {
    const el = $(`[data-field="${fieldName}"]`);
    if (el) el.classList.toggle('has-error', hasError);
    return !hasError;
  }

  function validateStep() {
    const o = state.order;
    let ok = true;

    if (state.checkoutStep === 1) {
      ok = markError('name', o.name.trim().length < 2) && ok;
      ok = markError('phone', o.phone.replace(/\D/g, '').length !== 11) && ok;
      ok = markError('email', !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(o.email.trim())) && ok;
    }
    if (state.checkoutStep === 2) {
      ok = markError('city', o.city.trim().length < 2) && ok;
      /* Для самовывоза адрес не нужен — пункт выдачи один */
      const needAddress = o.delivery !== 'pickup';
      ok = markError('address', needAddress && o.address.trim().length < 4) && ok;
    }
    if (!ok) toast('Проверьте отмеченные поля');
    return ok;
  }

  function submitOrder() {
    const number = 'АЛ-' + String(Date.now()).slice(-6);
    const o = state.order;
    const d = DELIVERY.find((x) => x.id === o.delivery);

    const orders = store.read('orders', []);
    orders.push({
      number, date: new Date().toISOString(),
      items: state.cart.slice(), total: orderTotal(), order: Object.assign({}, o),
    });
    store.write('orders', orders);

    $('#checkoutSteps').innerHTML = '';
    $('#checkoutBody').innerHTML = `
      <div class="success">
        <div class="success__mark">${ICON.check}</div>
        <h3>Заказ принят</h3>
        <p>Мы отправили подтверждение на <b>${esc(o.email)}</b>${o.callback ? ' и скоро позвоним по номеру ' + esc(o.phone) : ''}.</p>
        <span class="order-id num">${number}</span>
        <p>${esc(d.title)} — ${esc(d.eta)}. Сумма к оплате <b class="num">${money(orderTotal())}</b>.</p>
        <p style="margin-top:14px;font-size:13px;color:var(--muted)">Это прототип: платёж не проводится, заказ сохранён только в этом браузере.</p>
      </div>`;
    $('#checkoutFoot').innerHTML = `
      <div class="total">Номер заказа<b class="num">${number}</b></div>
      <button class="btn btn--primary btn--lg" type="button" data-close-layers>Хорошо</button>`;

    state.cart = [];
    state.promo = null;
    persistCart();
  }

  /* ── Слои: оверлей, шторка, модалки ─────────────────────────────────── */
  let lastFocused = null;

  function openLayer(sel) {
    lastFocused = document.activeElement;
    $('#overlay').classList.add('is-open');
    $(sel).classList.add('is-open');
    document.body.style.overflow = 'hidden';
    const focusTarget = $(sel).querySelector('button, input, [tabindex]');
    if (focusTarget) setTimeout(() => focusTarget.focus(), 60);
  }

  function closeLayer(sel) {
    $(sel).classList.remove('is-open');
    if (!$$('.drawer.is-open, .modal.is-open').length) {
      $('#overlay').classList.remove('is-open');
      document.body.style.overflow = '';
      if (lastFocused) lastFocused.focus();
    }
  }

  function closeAllLayers() {
    $$('.drawer.is-open, .modal.is-open').forEach((el) => el.classList.remove('is-open'));
    $('#overlay').classList.remove('is-open');
    document.body.style.overflow = '';
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

  /* ── Статический контент ────────────────────────────────────────────── */
  function renderStatic() {
    const sizeRows = SIZES.map((s) => `
      <tr>
        <td class="num">${esc(s.id)}</td>
        <td class="num">${esc(s.height)}</td>
        <td class="num">${esc(s.weight)}</td>
        <td>${esc(s.age)}</td>
      </tr>`).join('');
    $('#sizeRows').innerHTML = sizeRows;
    $('#sizeRowsModal').innerHTML = sizeRows;

    $('#reviewGrid').innerHTML = REVIEWS.map((r) => `
      <article class="review">
        <div class="rating">${ICON.star.repeat(r.rating)}</div>
        <p>${esc(r.text)}</p>
        <footer>
          <span class="avatar">${esc(r.name.charAt(0))}</span>
          <span><b>${esc(r.name)}</b><span>${esc(r.city)}</span></span>
        </footer>
      </article>`).join('');

    $('#faqList').innerHTML = FAQ.map((f, i) => `
      <details class="faq"${i === 0 ? ' open' : ''}>
        <summary>${esc(f.q)}</summary>
        <p>${esc(f.a)}</p>
      </details>`).join('');

    $('#deliveryList').innerHTML = DELIVERY.map((d) => `
      <li><span style="font-size:14px;color:var(--ink-soft)">${esc(d.title)} — ${d.price === 0 ? 'бесплатно' : money(d.price)}, ${esc(d.eta)}</span></li>
    `).join('');

    $('#footerCats').innerHTML = CATEGORIES.filter((c) => c.id !== 'all').map((c) => `
      <li><a href="#catalog" data-cat-link="${c.id}">${esc(c.title)}</a></li>`).join('');
  }

  /* ── События ────────────────────────────────────────────────────────── */
  function bind() {
    /* Делегирование кликов по всему документу */
    document.addEventListener('click', (e) => {
      const t = e.target;
      const hit = (attr) => { const el = t.closest('[' + attr + ']'); return el ? el.getAttribute(attr) : null; };

      /* Фильтры */
      const cat = hit('data-cat');
      if (cat !== null) { state.cat = cat; renderFilterChips(); renderCatalog(); return; }

      const catTile = hit('data-cat-tile');
      if (catTile !== null) {
        state.cat = catTile; renderFilterChips(); renderCatalog();
        $('#catalog').scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }

      const catLink = hit('data-cat-link');
      if (catLink !== null) {
        e.preventDefault();
        state.cat = catLink; renderFilterChips(); renderCatalog();
        $('#catalog').scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }

      const season = hit('data-season');
      if (season !== null) { state.season = season; renderFilterChips(); renderCatalog(); return; }

      const size = hit('data-size');
      if (size !== null) { state.size = size; renderFilterChips(); renderCatalog(); return; }

      if (t.closest('[data-reset-filters]')) {
        state.cat = 'all'; state.season = 'all'; state.size = 'all'; state.query = '';
        $('#searchInput').value = '';
        renderFilterChips(); renderCatalog();
        return;
      }

      /* Товары */
      const open = hit('data-open');
      if (open !== null) { openProduct(open); return; }

      const add = hit('data-add');
      if (add !== null) { addToCart(add); return; }

      const fav = hit('data-fav');
      if (fav !== null) { toggleFav(fav); return; }

      /* Карточка товара */
      const pdpSize = hit('data-pdp-size');
      if (pdpSize !== null) {
        pdpSelection.size = pdpSize;
        $$('#pdpSizes .chip').forEach((c) => c.classList.toggle('is-active', c.getAttribute('data-pdp-size') === pdpSize));
        return;
      }
      const pdpColor = hit('data-pdp-color');
      if (pdpColor !== null) {
        pdpSelection.color = pdpColor;
        $$('#pdpColors .chip').forEach((c) => c.classList.toggle('is-active', c.getAttribute('data-pdp-color') === pdpColor));
        return;
      }
      if (t.closest('[data-pdp-add]')) {
        addToCart(pdpSelection.id, pdpSelection.size, pdpSelection.color);
        closeLayer('#productModal');
        openLayer('#cartDrawer');
        return;
      }

      /* Корзина */
      const qMinus = hit('data-qty-minus');
      if (qMinus !== null) { setQty(qMinus, -1); return; }
      const qPlus = hit('data-qty-plus');
      if (qPlus !== null) { setQty(qPlus, 1); return; }
      const rm = hit('data-remove');
      if (rm !== null) { removeLine(rm); return; }

      if (t.closest('[data-apply-promo]')) {
        const code = ($('#promoInput').value || '').trim().toUpperCase();
        const found = PROMOS[code];
        if (found) {
          state.promo = { code, discount: found.discount, title: found.title };
          renderCart();
          toast('Промокод применён: ' + found.title);
        } else {
          state.promo = null;
          const note = $('#promoNote');
          note.className = 'promo-note is-err';
          note.textContent = code ? 'Такого промокода нет. Проверьте раскладку клавиатуры.' : 'Введите промокод';
        }
        return;
      }

      /* Открытие слоёв */
      if (t.closest('[data-open-cart]')) { renderCart(); openLayer('#cartDrawer'); return; }
      if (t.closest('[data-open-sizes]')) { openLayer('#sizesModal'); return; }
      if (t.closest('[data-checkout]')) { openCheckout(); return; }

      if (t.closest('[data-open-favs]')) {
        if (!state.favs.length) { toast('В избранном пока пусто'); return; }
        state.cat = 'all'; state.season = 'all'; state.size = 'all';
        state.query = '';
        $('#searchInput').value = '';
        renderFilterChips();
        /* Показываем только избранное, подменяя выборку на один рендер */
        const grid = $('#grid');
        const favProducts = PRODUCTS.filter((p) => state.favs.includes(p.id));
        $('#resultsCount').textContent = 'Избранное: ' + favProducts.length + ' ' + plural(favProducts.length, 'товар', 'товара', 'товаров');
        renderCatalogFrom(favProducts);
        $('#catalog').scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }

      /* Шаги оформления */
      if (t.closest('[data-step-next]')) {
        collectStep();
        if (!validateStep()) return;
        state.checkoutStep += 1;
        renderCheckout();
        $('#checkoutBody').scrollTop = 0;
        return;
      }
      if (t.closest('[data-step-back]')) {
        collectStep();
        state.checkoutStep -= 1;
        renderCheckout();
        return;
      }
      if (t.closest('[data-submit-order]')) { submitOrder(); return; }

      /* Выбор доставки и оплаты */
      const delivery = hit('data-delivery');
      if (delivery !== null) {
        collectStep();
        state.order.delivery = delivery;
        renderCheckout();
        return;
      }
      const payment = hit('data-payment');
      if (payment !== null) {
        collectStep();
        state.order.payment = payment;
        renderCheckout();
        return;
      }

      /* Закрытие */
      const closeSel = hit('data-close');
      if (closeSel !== null) { closeLayer(closeSel); return; }
      if (t.closest('[data-close-layers]')) {
        const goto = t.closest('[data-close-layers]').getAttribute('data-goto');
        closeAllLayers();
        if (goto) $(goto).scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      if (t.id === 'overlay') { closeAllLayers(); return; }

      /* Тема */
      if (t.closest('[data-theme-toggle]')) {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
          (!document.documentElement.getAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        applyTheme(isDark ? 'light' : 'dark');
        return;
      }
    });

    /* Подарочная упаковка пересчитывает сумму сразу */
    document.addEventListener('change', (e) => {
      if (e.target.id === 'f-gift') {
        state.order.gift = e.target.checked;
        renderCheckout();
      }
    });

    /* Поиск */
    $('#searchInput').addEventListener('input', (e) => {
      state.query = e.target.value;
      renderCatalog();
    });

    $('#sortSelect').addEventListener('change', (e) => {
      state.sort = e.target.value;
      renderCatalog();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeAllLayers();
    });
  }

  /* Отрисовка произвольного списка (используется для избранного) */
  function renderCatalogFrom(list) {
    const grid = $('#grid');
    if (!list.length) {
      grid.innerHTML = `<div class="empty-state"><strong>Пусто</strong>Здесь появятся отмеченные сердечком товары.</div>`;
      return;
    }
    const seasonTitle = (id) => (SEASONS.find((s) => s.id === id) || {}).title || '';
    grid.innerHTML = list.map((p) => `
      <article class="card">
        <button class="card__art" type="button" data-open="${p.id}" aria-label="Открыть карточку: ${esc(p.name)}">${art(p.art, p.tone)}</button>
        <div class="card__flags">${p.badge ? `<span class="flag flag--${p.badge === 'Хит' ? 'hit' : 'new'}">${esc(p.badge)}</span>` : ''}${flagFor(p)}</div>
        <button class="fav-btn is-on" type="button" data-fav="${p.id}" aria-label="Убрать из избранного">${ICON.heart}</button>
        <div class="card__body">
          <div class="card__meta"><span>${esc(seasonTitle(p.season))}</span><i class="dot"></i>
            <span class="rating">${ICON.star}<span class="num">${p.rating.toFixed(1)}</span></span></div>
          <button class="card__title" type="button" data-open="${p.id}">${esc(p.name)}</button>
          <div class="sizes-row">${p.sizes.map((s) => `<span class="size-tag num">${esc(s)}</span>`).join('')}</div>
          <div class="card__foot">
            <span class="price"><b class="num">${money(p.price)}</b>${p.oldPrice ? `<s class="num">${money(p.oldPrice)}</s>` : ''}</span>
            <button class="add-btn" type="button" data-add="${p.id}" aria-label="Добавить в корзину">${ICON.plus}</button>
          </div>
        </div>
      </article>`).join('');
  }

  /* ── Старт ──────────────────────────────────────────────────────────── */
  function init() {
    /* Иконки в статичной разметке */
    $$('[data-icon]').forEach((el) => {
      const name = el.getAttribute('data-icon');
      if (ICON[name]) el.innerHTML = ICON[name] + el.innerHTML;
    });

    applyTheme(store.read('theme', null));
    renderBrand();
    renderStatic();
    renderCategoryTiles();
    renderFilterChips();
    renderCatalog();
    renderCart();
    renderCounters();
    bind();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
