/* ==========================================================================
   Сборка одного самодостаточного файла из index.html и папки assets.
   Запуск: node build.js
   Результат — два файла со встроенными стилями и скриптами:
     dist/alisa-sait.html — обычная веб-страница. Её можно отправить клиенту,
                               открыть двойным кликом или выложить на хостинг.
     dist/alisa.html      — тот же сайт без обёртки <html>/<body>,
                               в таком виде его принимает публикация по ссылке.
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

const inlined = `<style>
${css}
</style>
${body}
<script>
${data}
${app}
</script>`;

/* Фрагмент для публикации по ссылке */
const fragment = `<title>${title}</title>\n${inlined}\n`;

/* Полноценная страница для отправки клиенту и любого хостинга */
const page = `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<meta name="description" content="Комплекты на выписку из роддома, ползунки и распашонки, чепчики, комбинезоны и боди для новорождённых.">
<meta name="color-scheme" content="light dark">
</head>
<body>
${inlined}
</body>
</html>
`;

fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
fs.writeFileSync(path.join(root, 'dist/alisa.html'), fragment, 'utf8');
fs.writeFileSync(path.join(root, 'dist/alisa-sait.html'), page, 'utf8');
console.log('dist/alisa-sait.html — страница, ' + (page.length / 1024).toFixed(1) + ' КБ');
console.log('dist/alisa.html      — фрагмент для публикации, ' + (fragment.length / 1024).toFixed(1) + ' КБ');
