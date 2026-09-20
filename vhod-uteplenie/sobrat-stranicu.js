// Собирает публичную страницу для GitHub Pages из исходника raschet-otdelki-vhoda.html.
//
// Исходник написан в формате Claude Artifact: без <!doctype>, <html>, <head> и <body> —
// эту обвязку artifact подставляет сам. Для обычного сайта её нужно дописать.
// Здесь один источник правды: правим только исходник, потом запускаем
//
//     node vhod-uteplenie/sobrat-stranicu.js
//
// и файл vhod/index.html пересобирается.

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SRC = path.join(__dirname, "raschet-otdelki-vhoda.html");
const OUT_DIR = path.join(ROOT, "vhod");
const OUT = path.join(OUT_DIR, "index.html");

const URL = "https://hobuchenie11-create.github.io/my-project/vhod/";
const TITLE = "Утепление входной ниши";
const DESC =
  "Чертёж, площади и сравнение трёх вариантов отделки двух стен у входной двери: " +
  "фасадная плитка, панели под кирпич, сайдинг. Считает стоимость по вашим ценам.";

const body = fs.readFileSync(SRC, "utf8");

const head = `<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="${DESC}">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Вход частного дома">
<meta property="og:url" content="${URL}">
<meta property="og:title" content="${TITLE}">
<meta property="og:description" content="${DESC}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="${TITLE}">
<meta name="twitter:description" content="${DESC}">
<style>
  :root {
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  body { margin: 0; font: 14px system-ui, -apple-system, "Segoe UI", sans-serif; background: #fafafa; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
`;

const foot = `
</body>
</html>
`;

fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT, head + body + foot, "utf8");

const kb = (fs.statSync(OUT).size / 1024).toFixed(1);
console.log("Собрано: " + path.relative(ROOT, OUT) + " (" + kb + " КБ)");
console.log("Адрес после публикации: " + URL);
