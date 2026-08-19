"""База знаний Домоведа: памятки для жителей и поиск ответов.

Тексты памяток лежат в файлах `content/faq/*.md` — править их в редакторе
удобнее, чем в переписке с ботом, а история правок остаётся в git. При старте
бот загружает файлы в базу: оттуда быстрее искать и видно, чего не хватает.

Поиск нарочно простой и предсказуемый: житель пишет вопрос своими словами,
бот ищет совпадения по ключевым словам и заголовку. Не нашёл — честно
говорит «не знаю» и записывает вопрос в журнал `faq_gaps`, чтобы председатель
раз в неделю посмотрел, о чём спрашивают, и дописал памятку.
"""
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from bot.config import config
from database import repository
from database.models import FAQ_CATEGORIES

FAQ_DIR = config.base_dir / "content" / "faq"
IMAGES_DIR = FAQ_DIR / "images"

# Слова короче трёх букв в поиске бесполезны: «на», «до», «не»
MIN_WORD = 3

# Служебные слова вопроса — они есть в любом вопросе и ничего не отличают
STOP_WORDS = {"как", "где", "что", "когда", "почему", "зачем", "кто", "куда",
              "можно", "нужно", "надо", "подскажите", "скажите", "помогите",
              "пожалуйста", "добрый", "день", "вечер", "утро", "здравствуйте",
              "быть", "если", "для", "это", "мне", "нам", "они", "меня"}


@dataclass
class Memo:
    """Памятка, готовая к отправке жителю."""
    code: str
    title: str
    category: str
    body: str
    image: str = ""

    @property
    def image_path(self) -> Path | None:
        path = IMAGES_DIR / self.image if self.image else None
        return path if path and path.exists() else None

    def text(self) -> str:
        return f"<b>{self.title}</b>\n\n{self.body}"


# ---------------------------------------------------------------------------
# Загрузка из файлов
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_memo_file(path: Path) -> dict:
    """Разбирает файл памятки: заголовок в «---» и текст под ним."""
    raw = path.read_text(encoding="utf-8")
    header, body = {}, raw

    match = _HEADER_RE.match(raw)
    if match:
        body = raw[match.end():]
        for line in match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                header[key.strip().lower()] = value.strip()

    return {
        "code": path.stem,
        "title": header.get("title") or path.stem,
        "category": header.get("category", "other"),
        "keywords": header.get("keywords", ""),
        "image": header.get("image", ""),
        "sort_order": int(header.get("order") or 0),
        "body": body.strip(),
    }


def load_memos(conn: sqlite3.Connection, directory: Path | None = None) -> int:
    """Перечитывает памятки из файлов. Возвращает число загруженных."""
    directory = directory or FAQ_DIR
    if not directory.exists():
        return 0

    loaded = 0
    codes = []
    for path in sorted(directory.glob("*.md")):
        if path.stem.lower() == "readme":
            continue
        memo = parse_memo_file(path)
        repository.upsert_memo(conn, **memo)
        codes.append(memo["code"])
        loaded += 1

    # Файл удалили — памятка уходит из меню, но остаётся в базе
    repository.deactivate_missing_memos(conn, codes)
    return loaded


# ---------------------------------------------------------------------------
# Поиск и выдача
# ---------------------------------------------------------------------------

def _words(text: str) -> set[str]:
    lowered = re.sub(r"[^а-яёa-z0-9]+", " ", text.lower())
    return {w for w in lowered.split() if len(w) >= MIN_WORD} - STOP_WORDS


def _score(question: set[str], memo: sqlite3.Row) -> int:
    """Насколько памятка подходит вопросу. 0 — не подходит."""
    keywords = _words(memo["keywords"])
    title = _words(memo["title"])
    score = 0
    for word in question:
        # Совпадение по началу слова: «оплат» ловит «оплата», «оплатить»
        if any(k.startswith(word) or word.startswith(k) for k in keywords):
            score += 3
        if any(t.startswith(word) or word.startswith(t) for t in title):
            score += 2
    return score


def search(conn: sqlite3.Connection, question: str,
           limit: int = 3) -> list[Memo]:
    """Памятки, подходящие вопросу, — самая близкая первой."""
    words = _words(question)
    if not words:
        return []

    scored = []
    for row in repository.active_memos(conn):
        score = _score(words, row)
        if score:
            scored.append((score, row))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["sort_order"]))
    return [_memo(row) for _, row in scored[:limit]]


def by_code(conn: sqlite3.Connection, code: str) -> Memo | None:
    row = repository.get_memo(conn, code)
    return _memo(row) if row else None


def by_category(conn: sqlite3.Connection, category: str) -> list[Memo]:
    return [_memo(row) for row in repository.active_memos(conn, category)]


def categories(conn: sqlite3.Connection) -> list[str]:
    """Разделы, в которых есть хотя бы одна памятка — в порядке справочника."""
    present = set(repository.memo_categories(conn))
    known = [code for code in FAQ_CATEGORIES if code in present]
    return known + sorted(present - set(known))


def _memo(row: sqlite3.Row) -> Memo:
    return Memo(code=row["code"], title=row["title"], category=row["category"],
                body=row["body"], image=row["image"])


# ---------------------------------------------------------------------------
# Журнал вопросов без ответа
# ---------------------------------------------------------------------------

def remember_gap(conn: sqlite3.Connection, tg_id: int | None,
                 apartment: str, question: str) -> None:
    repository.add_faq_gap(conn, tg_id, apartment, question.strip()[:500])


def gaps_text(conn: sqlite3.Connection, limit: int = 20) -> str:
    """Сводка для председателя: о чём спрашивали, а ответа нет."""
    rows = repository.faq_gaps(conn, limit=limit)
    if not rows:
        return ("❓ Вопросов без ответа нет.\n\n"
                "Сюда попадают вопросы жителей, на которые Домовед не нашёл "
                "памятку. По ним удобно понимать, чего не хватает в базе.")

    lines = [f"❓ <b>Вопросы без ответа ({len(rows)})</b>", ""]
    for row in rows:
        who = f"кв. {row['apartment']}" if row["apartment"] else "житель"
        lines.append(f"• {row['question']}")
        lines.append(f"  <i>{who}, {row['created_at'][:16]}</i>")
    lines.append("")
    lines.append("Чтобы ответить — добавьте памятку в content/faq/ "
                 "и перезапустите бота.")
    return "\n".join(lines)


NOT_FOUND = (
    "Не нашёл ответа на этот вопрос — пока такой памятки нет.\n\n"
    "Я передал вопрос председателю: ответ появится в разделе «❓ Памятки». "
    "Если вопрос срочный, напишите председателю напрямую."
)
