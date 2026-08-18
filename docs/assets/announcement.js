/* ───────────────────────────────────────────────────────────
   Домовед · отрисовка ежемесячного объявления по спецсчёту
   на canvas — тот же макет, что и в tools/announcement.py.

   ВАЖНО: при изменении макета правьте оба файла, иначе картинка
   с сайта и картинка от бота начнут отличаться.
   ─────────────────────────────────────────────────────────── */

window.DomovedAnnouncement = (function () {
  var W = 1180, H_BASE = 810, H_SPENT = 946, PAD = 56;

  var C = {
    head:  '#0E766D',
    sub:   '#6DACB5',
    page:  '#B7C5C6',
    tile:  '#9EC3BB',
    grey:  '#C6C5CB',
    ink:   '#0B4D47',
    inkSoft: '#175C55',
    subInk: '#07332F',
    white: '#FFFFFF'
  };

  var MONTHS = ['ЯНВАРЬ', 'ФЕВРАЛЬ', 'МАРТ', 'АПРЕЛЬ', 'МАЙ', 'ИЮНЬ',
                'ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ'];

  var FACE = '"Segoe UI", system-ui, -apple-system, Arial, sans-serif';

  function money(v) {
    if (v === null || v === undefined || v === '') return '—';
    var n = Number(v);
    if (!isFinite(n)) return '—';
    var whole = Math.floor(Math.abs(n));
    var cents = Math.round((Math.abs(n) - whole) * 100);
    var s = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (n < 0 ? '−' : '') + s + ',' + String(cents).padStart(2, '0') + ' ₽';
  }

  function periodTitle(period) {
    var p = String(period).split('-');
    return 'за ' + MONTHS[Number(p[1]) - 1] + ' ' + p[0] + ' г';
  }

  function dateRu(value) {
    var p = String(value).split('-');
    return p[2] + '.' + p[1] + '.' + p[0];
  }

  /* monthName("2026-06")        → "Июнь 2026"
     monthName("2026-06", true)  → "июнь 2026" — для середины фразы */
  function monthName(period, lower) {
    var p = String(period).split('-');
    var m = MONTHS[Number(p[1]) - 1].toLowerCase();
    return (lower ? m : m.charAt(0).toUpperCase() + m.slice(1)) + ' ' + p[0];
  }

  function centered(ctx, text, size, weight, color, cx, y) {
    ctx.font = weight + ' ' + size + 'px ' + FACE;
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(text, cx, y);
  }

  function hasSpent(m) {
    return m.spent !== null && m.spent !== undefined && m.spent !== '';
  }

  /* Рисует объявление в переданный <canvas>. m — запись месяца.
     Плашка «израсходовано» появляется только если у месяца задан spent. */
  function draw(canvas, m, address) {
    var H = hasSpent(m) ? H_SPENT : H_BASE;
    var scale = window.devicePixelRatio > 1 ? 2 : 1;
    canvas.width = W * scale;
    canvas.height = H * scale;
    var ctx = canvas.getContext('2d');
    ctx.setTransform(scale, 0, 0, scale, 0, 0);

    var cx = W / 2;

    ctx.fillStyle = C.page;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = C.head;
    ctx.fillRect(0, 0, W, 92);
    centered(ctx, 'ВЗНОСЫ НА КАПИТАЛЬНЫЙ РЕМОНТ', 46, '700', C.white, cx, 22);

    ctx.fillStyle = C.sub;
    ctx.fillRect(0, 92, W, 53);
    centered(ctx, 'Спецсчёт МКД ' + address + ' · ежемесячная информация для собственников',
             23, '700', C.subInk, cx, 105);

    ctx.fillStyle = C.tile;
    ctx.fillRect(PAD, 190, W - PAD * 2, 98);
    centered(ctx, periodTitle(m.period), 50, '700', C.ink, cx, 210);

    var top = 326;
    ctx.fillStyle = C.grey;
    ctx.fillRect(PAD, top, W - PAD * 2, 174);

    var leftCx = PAD + (cx - PAD) / 2;
    var rightCx = cx + (W - PAD - cx) / 2;

    centered(ctx, 'ОПЛАЧЕНО СОБСТВЕННИКАМИ', 27, '700', C.inkSoft, leftCx, top + 24);
    centered(ctx, 'ЗА ЭТОТ МЕСЯЦ', 27, '700', C.inkSoft, leftCx, top + 58);
    centered(ctx, money(m.paid), 44, '700', C.ink, leftCx, top + 106);

    centered(ctx, 'НАЧИСЛЕНО ПРОЦЕНТОВ', 27, '700', C.inkSoft, rightCx, top + 24);
    centered(ctx, 'ПО СПЕЦСЧЁТУ', 27, '700', C.inkSoft, rightCx, top + 58);
    centered(ctx, money(m.interest), 44, '700', C.ink, rightCx, top + 106);

    var restTop = 542;
    if (hasSpent(m)) {
      ctx.fillStyle = C.grey;
      ctx.fillRect(PAD, 522, W - PAD * 2, 140);
      centered(ctx, 'ИЗРАСХОДОВАНО НА РАБОТЫ', 27, '700', C.inkSoft, cx, 544);
      centered(ctx, money(m.spent), 44, '700', C.ink, cx, 576);
      if (m.spentNote) centered(ctx, m.spentNote, 22, '400', C.inkSoft, cx, 628);
      restTop = 690;
    }

    ctx.fillStyle = C.tile;
    ctx.fillRect(PAD, restTop, W - PAD * 2, 206);
    centered(ctx, 'ОСТАТОК ОБЩЕЙ СУММЫ НА СЧЁТЕ на ' + dateRu(m.balanceDate),
             29, '700', C.ink, cx, restTop + 34);
    centered(ctx, money(m.balance), 60, '700', C.ink, cx, restTop + 100);
  }

  function fileName(m) {
    return 'kapremont-' + String(m.period).replace('-', '-') + '.png';
  }

  return {
    draw: draw,
    money: money,
    monthName: monthName,
    dateRu: dateRu,
    fileName: fileName,
    hasSpent: hasSpent,
    width: W
  };
})();
