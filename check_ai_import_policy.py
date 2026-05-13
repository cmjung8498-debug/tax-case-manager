from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")

ALLOWED_FILES = {
    "transcribe_audio.py",
    "ai_call_guard.py",
    "ai_extract_tax_facts.py",
    "ai_tax_law_rag.py",
    "check_ai_import_policy.py",
}

BLOCK_PATTERNS = [
    "from openai import",
    "import openai",
    "OpenAI(",
]


def main():
    violations = []

    for path in BASE_DIR.glob("*.py"):
        if path.name in ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")

        for pattern in BLOCK_PATTERNS:
            if pattern in text:
                violations.append((path.name, pattern))

    if violations:
        print("[FAIL] 허용되지 않은 AI 직접 호출 가능성이 발견되었습니다.")
        for filename, pattern in violations:
            print(f"- {filename}: {pattern}")
        raise SystemExit(1)

    print("[PASS] AI import policy OK")


if __name__ == "__main__":
    main()
