/* ==========================================================================
   Сборка самодостаточных файлов из разметки и папки assets.
   Запуск: node build.js

   Собираются две страницы — витрина магазина и журнал заказов. Для каждой
   получается обычная веб-страница (её можно переслать или открыть двойным
   кликом) и фрагмент без обёртки <html>/<body> — в таком виде страницу
   принимает публикация по ссылке.
   ========================================================================== */
const fs = require('fs');
const path = require('path');

const root = __dirname;
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const write = (p, content) => {
  fs.mkdirSync(path.join(root, path.dirname(p)), { recursive: true });
  fs.writeFileSync(path.join(root, p), content, 'utf8');
};

const between = (source, startTag, endTag) => {
  const start = source.indexOf(startTag);
  const end = source.indexOf(endTag);
  if (start === -1 || end === -1) throw new Error('Не найден фрагмент ' + startTag + ' в исходной разметке');
  return source.slice(start + startTag.length, end);
};

/* Собирает одну страницу: встраивает стили и скрипты внутрь разметки */
function bundle({ html, css, js, description }) {
  const source = read(html);
  const title = between(source, '<title>', '</title>');

  /* Тело страницы: всё между открывающим <body ...> и </body>,
     без ссылок на внешние файлы — они встраиваются ниже */
  const bodyOpen = source.indexOf('<body');
  const bodyEnd = source.indexOf('</body>');
  if (bodyOpen === -1 || bodyEnd === -1) throw new Error('В ' + html + ' не найден тег <body>');

  const bodyTag = source.slice(bodyOpen, source.indexOf('>', bodyOpen) + 1);
  const bodyClass = (bodyTag.match(/class="([^"]*)"/) || [])[1] || '';

  const body = source
    .slice(source.indexOf('>', bodyOpen) + 1, bodyEnd)
    .replace(/<script src="[^"]*"><\/script>\s*/g, '')
    .trim();

  const inlined = `<style>
${css.map(read).join('\n')}
</style>
${body}
<script>
${js.map(read).join('\n')}
</script>`;

  return {
    title,
    fragment: `<title>${title}</title>\n${inlined}\n`,
    page: `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<meta name="description" content="${description}">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex, nofollow">
</head>
<body${bodyClass ? ' class="' + bodyClass + '"' : ''}>
${inlined}
</body>
</html>
`,
  };
}

/* ── Витрина магазина ──────────────────────────────────────────────────── */
const shop = bundle({
  html: 'index.html',
  css: ['assets/css/styles.css'],
  js: ['assets/js/data.js', 'assets/js/app.js'],
  description: 'Комплекты на выписку из роддома, ползунки и распашонки, чепчики, комбинезоны и боди для новорождённых.',
});

/* Адрес опубликованного сайта. В отдельных файлах относительные ссылки между
   страницами не работают, поэтому подставляем полные адреса. */
const SITE_URL = 'https://hobuchenie11-create.github.io/my-project/';

const shopPage = shop.page.replace(/href="orders\/"/g, 'href="' + SITE_URL + 'orders/"');

write('dist/alisa.html', shop.fragment.replace(/href="orders\/"/g, 'href="' + SITE_URL + 'orders/"'));
write('dist/alisa-sait.html', shopPage);

/* Копия в demo/ попадает в репозиторий, в отличие от dist/,
   поэтому ссылка для клиента всегда указывает на свежую сборку. */
write('demo/index.html', shopPage);

/* ── Журнал заказов ────────────────────────────────────────────────────── */
const orders = bundle({
  html: 'orders/index.html',
  css: ['assets/css/styles.css', 'assets/css/orders.css'],
  js: ['assets/js/data.js', 'assets/js/orders-data.js', 'assets/js/orders.js'],
  description: 'Демонстрация: как владелец магазина видит заказы с сайта — список, статусы, поиск и выгрузка в таблицу.',
});

/* Ссылки «вернуться на сайт» ведут на ../ — в одиночном файле это ломается,
   поэтому подставляем полный адрес витрины. */
const ordersPage = orders.page.replace(/href="\.\.\/"/g, 'href="' + SITE_URL + '"');

write('dist/alisa-zhurnal-zakazov.html', ordersPage);

console.log('Витрина магазина:');
console.log('  dist/alisa-sait.html            — страница, ' + (shop.page.length / 1024).toFixed(1) + ' КБ');
console.log('  dist/alisa.html                 — фрагмент для публикации, ' + (shop.fragment.length / 1024).toFixed(1) + ' КБ');
console.log('  demo/index.html                 — копия для ссылки в репозитории');
console.log('Журнал заказов:');
console.log('  dist/alisa-zhurnal-zakazov.html — страница, ' + (ordersPage.length / 1024).toFixed(1) + ' КБ');
console.log('  orders/index.html               — публикуется по ссылке /orders/');
