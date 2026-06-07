import json
import re
from pathlib import Path

RAW = Path("data_security/raw")
OUT = Path("data_security/clean/security_corpus.jsonl")

OUT.parent.mkdir(parents=True, exist_ok=True)

EXTS = {
    ".md", ".txt", ".rst", ".json", ".yml", ".yaml",
    ".html", ".htm", ".py", ".sh", ".js", ".ts",
    ".go", ".java", ".c", ".cpp", ".h", ".cs"
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", "target", ".idea", ".vscode"
}

SKIP_WORDS = [
    "rockyou", "password", "passwd", "wordlist",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".bin", ".sqlite", ".db",
    ".pdf", ".mp4", ".mov", ".avi"
]

MAX_SIZE = 2_000_000
MIN_CHARS = 300
MAX_CHARS = 12000


def should_skip(path: Path) -> bool:
    lower = str(path).lower()

    if any(part in SKIP_DIRS for part in path.parts):
        return True

    if any(word in lower for word in SKIP_WORDS):
        return True

    if path.suffix.lower() not in EXTS:
        return True

    try:
        if path.stat().st_size > MAX_SIZE:
            return True
    except Exception:
        return True

    return False


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text.strip()


def split_chunks(text: str):
    text = clean_text(text)

    if len(text) <= MAX_CHARS:
        if len(text) >= MIN_CHARS:
            yield text
        return

    current = ""

    for part in text.split("\n\n"):
        if len(current) + len(part) + 2 <= MAX_CHARS:
            current += part + "\n\n"
        else:
            if len(current) >= MIN_CHARS:
                yield current.strip()
            current = part + "\n\n"

    if len(current) >= MIN_CHARS:
        yield current.strip()


def main():
    files = 0
    kept = 0
    skipped = 0

    with OUT.open("w", encoding="utf-8") as out:
        for path in RAW.rglob("*"):
            if not path.is_file():
                continue

            files += 1

            if should_skip(path):
                skipped += 1
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                skipped += 1
                continue

            if len(text.strip()) < MIN_CHARS:
                skipped += 1
                continue

            try:
                repo = path.relative_to(RAW).parts[0]
            except Exception:
                repo = "unknown"

            for chunk in split_chunks(text):
                record = {
                    "repo": repo,
                    "source": str(path),
                    "text": chunk
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                kept += 1

            if files % 10000 == 0:
                print(
                    f"files={files:,} docs={kept:,} skipped={skipped:,}",
                    flush=True
                )

    print("DONE")
    print(f"files scanned: {files:,}")
    print(f"docs written:  {kept:,}")
    print(f"skipped:       {skipped:,}")
    print(f"output:        {OUT}")


if __name__ == "__main__":
    main()