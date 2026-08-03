/* ==========================================================================
   Сборка одного самодостаточного файла из index.html и папки assets.
   Запуск: node build.js
   Результат: dist/aistenok.html — фрагмент со встроенными стилями и скриптами,
   без обёртки <html>/<head>/<body>. Именно его публикуем как ссылку.
   ========================================================================== */
const fs = require('fs');
const path = require('path');

const root = __dirname;
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');

const html = read('index.html');
const css = read('assets/css/styles.css');
const data = read('assets/js/data.js');
const app = read('assets/js/app.js');

const between = (source, startTag, endTag) => {
  const start = source.indexOf(startTag);
  const end = source.indexOf(endTag);
  if (start === -1 || end === -1) throw new Error('Не найден фрагмент ' + startTag);
  return source.slice(start + startTag.length, end);
};

const title = between(html, '<title>', '</title>');

/* Тело страницы без ссылок на внешние файлы — они встраиваются ниже */
const body = between(html, '<body>', '</body>')
  .replace(/<script src="[^"]*"><\/script>\s*/g, '')
  .trim();

const out = `<title>${title}</title>
<style>
${css}
</style>
${body}
<script>
${data}
${app}
</script>
`;

fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
fs.writeFileSync(path.join(root, 'dist/aistenok.html'), out, 'utf8');
console.log('dist/aistenok.html — ' + (out.length / 1024).toFixed(1) + ' КБ');
