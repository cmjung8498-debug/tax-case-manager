import os
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
INBOX_DIR = BASE_DIR / "inbox"
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".amr"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp"}
DOC_EXTS = {".pdf", ".hwp", ".hwpx", ".doc", ".docx", ".xls", ".xlsx", ".txt"}

CASE_SUBDIRS = [
    "01_audio",
    "02_transcript",
    "03_documents",
    "04_extract",
    "05_missing",
    "06_reports",
    "07_tax_review",
]


def ensure_base_dirs():
    BASE_DIR.mkdir(exist_ok=True)
    INBOX_DIR.mkdir(exist_ok=True)
    CASES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)


def generate_case_id():
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"GT-{today}"

    existing = []
    if CASES_DIR.exists():
        existing = [
            p.name for p in CASES_DIR.iterdir()
            if p.is_dir() and p.name.startswith(prefix)
        ]

    nums = []
    for name in existing:
        try:
            nums.append(int(name.split("-")[-1]))
        except ValueError:
            pass

    next_num = max(nums) + 1 if nums else 1
    return f"{prefix}-{next_num:03d}"


def create_case_dirs(case_id):
    case_dir = CASES_DIR / case_id
    case_dir.mkdir(exist_ok=True)

    for subdir in CASE_SUBDIRS:
        (case_dir / subdir).mkdir(exist_ok=True)

    return case_dir


def classify_file(file_path):
    ext = file_path.suffix.lower()

    if ext in AUDIO_EXTS:
        return "01_audio"

    if ext in IMAGE_EXTS:
        return "03_documents"

    if ext in DOC_EXTS:
        return "03_documents"

    return "03_documents"


def safe_copy_to_case(file_path, target_dir):
    target_path = target_dir / file_path.name

    if not target_path.exists():
        shutil.copy2(file_path, target_path)
        return target_path

    stem = file_path.stem
    ext = file_path.suffix
    i = 1

    while True:
        new_name = f"{stem}_{i}{ext}"
        new_target = target_dir / new_name
        if not new_target.exists():
            shutil.copy2(file_path, new_target)
            return new_target
        i += 1


def write_case_meta(case_dir, case_id, copied_files):
    meta = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "kakao_manual_upload",
        "status": "01_RECEIVED",
        "real_estate_office": "",
        "manager_name": "",
        "client_name": "",
        "client_phone": "",
        "property_address": "",
        "sale_expected_date": "",
        "memo": "",
        "copied_files": copied_files,
        "next_action": "case_meta.json 기본정보 입력 후 음성 전사 단계 진행"
    }

    meta_path = case_dir / "case_meta.json"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta_path


def write_next_steps(case_dir, case_id, copied_files):
    audio_count = sum(1 for f in copied_files if f["category"] == "01_audio")
    doc_count = sum(1 for f in copied_files if f["category"] == "03_documents")

    content = f"""# {case_id} 진행 순서

## 현재 접수 상태

- 녹음파일 수: {audio_count}
- 증빙/문서 파일 수: {doc_count}

## 다음 진행 순서

1. `case_meta.json`에 부동산 사무실명, 담당자, 고객명, 연락처, 물건주소를 입력한다.
2. 녹음파일이 있으면 음성 전사 작업을 진행한다.
3. 전사 결과를 `02_transcript\\transcript.txt`에 저장한다.
4. 상담 내용에서 양도세 필수정보를 추출한다.
5. 누락자료 목록을 생성한다.
6. 부동산 사무실에 보완 요청할 내용을 정리한다.
7. 보완 완료 후 세무사용 검토 리포트를 생성한다.

## 우선 확인할 필수 정보

- 매도 예정 부동산 주소
- 취득일
- 취득가액
- 양도 예정일
- 양도 예정가액
- 현재 보유 주택 수
- 배우자 및 세대원 주택 보유 여부
- 실제 거주 여부 및 거주기간
- 상속/증여/분양권/입주권 여부
- 필요경비 증빙자료 보유 여부

## 주의

이 단계에서는 세무 판단을 확정하지 않는다.
현재 단계는 상담자료 접수 및 사건 정리 단계이다.
"""

    next_steps_path = case_dir / "next_steps.md"

    with open(next_steps_path, "w", encoding="utf-8") as f:
        f.write(content)

    return next_steps_path


def write_log(case_id, message):
    log_path = LOGS_DIR / "intake_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def main():
    ensure_base_dirs()

    files = [p for p in INBOX_DIR.iterdir() if p.is_file()]

    if not files:
        print("[STOP] inbox 폴더에 정리할 파일이 없습니다.")
        print(f"[INFO] 파일을 여기에 넣어주세요: {INBOX_DIR}")
        return

    case_id = generate_case_id()
    case_dir = create_case_dirs(case_id)

    copied_files = []

    for file_path in files:
        category = classify_file(file_path)
        target_dir = case_dir / category
        copied_path = safe_copy_to_case(file_path, target_dir)

        copied_files.append({
            "original_path": str(file_path),
            "saved_path": str(copied_path),
            "category": category,
            "filename": copied_path.name,
            "size_bytes": file_path.stat().st_size
        })

    meta_path = write_case_meta(case_dir, case_id, copied_files)
    next_steps_path = write_next_steps(case_dir, case_id, copied_files)

    write_log(case_id, f"received_files={len(copied_files)} case_dir={case_dir}")

    print("[SUCCESS] 카카오톡 수신 파일 정리 완료")
    print(f"[CASE_ID] {case_id}")
    print(f"[CASE_DIR] {case_dir}")
    print(f"[META] {meta_path}")
    print(f"[NEXT_STEPS] {next_steps_path}")
    print("")
    print("[COPIED_FILES]")
    for item in copied_files:
        print(f"- {item['category']} | {item['filename']}")
    print("")
    print("[NEXT]")
    print("1. case_meta.json에 고객/부동산 정보를 입력하세요.")
    print("2. 녹음파일이 있으면 다음 단계에서 transcribe_audio.py를 실행합니다.")
    print("3. 문서파일은 03_documents 폴더에서 확인하세요.")
    print("")
    print("[NOTE]")
    print("현재 버전은 inbox 파일을 복사만 하고 삭제하지 않습니다.")


if __name__ == "__main__":
    main()
