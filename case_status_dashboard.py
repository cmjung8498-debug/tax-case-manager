import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
OUTPUTS_DIR = BASE_DIR / "outputs"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"


STATUS_LABELS = {
    "01_RECEIVED": "접수완료",
    "02_TRANSCRIBED": "전사완료",
    "03_EXTRACTED": "사실관계추출",
    "04_REPORTED": "리포트생성",
    "05_MISSING_REQUESTED": "보완요청",
    "06_EXPORTED": "세무사전달패키지",
}


def write_log(message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "dashboard_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")


def read_json_if_exists(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def file_exists_text(path):
    return "Y" if path.exists() else "N"


def count_files(path):
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_file())


def get_last_modified(case_dir):
    latest = case_dir.stat().st_mtime

    for p in case_dir.rglob("*"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except Exception:
            pass

    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")


def build_case_row(case_dir):
    case_id = case_dir.name

    meta = read_json_if_exists(case_dir / "case_meta.json")
    tax_data = read_json_if_exists(case_dir / "04_extract" / "tax_facts.json")

    facts = tax_data.get("facts", {})
    missing_items = tax_data.get("missing_items", [])

    status = meta.get("status", "UNKNOWN")
    case_type = tax_data.get("case_type") or meta.get("case_type", "")
    risk_level = tax_data.get("risk_level") or meta.get("risk_level", "")

    export_zip = EXPORTS_DIR / f"{case_id}.zip"

    row = {
        "case_id": case_id,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "case_type": case_type,
        "risk_level": risk_level,
        "missing_count": len(missing_items),
        "real_estate_office": meta.get("real_estate_office", ""),
        "manager_name": meta.get("manager_name", ""),
        "client_name": meta.get("client_name", ""),
        "client_phone": meta.get("client_phone", ""),
        "property_address": facts.get("property_address") or meta.get("property_address", ""),
        "audio_count": count_files(case_dir / "01_audio"),
        "document_count": count_files(case_dir / "03_documents"),
        "has_transcript": file_exists_text(case_dir / "02_transcript" / "transcript.txt"),
        "has_tax_facts": file_exists_text(case_dir / "04_extract" / "tax_facts.json"),
        "has_customer_report": file_exists_text(case_dir / "06_reports" / "01_customer_summary.md"),
        "has_tax_report": file_exists_text(case_dir / "06_reports" / "03_tax_accountant_review.md"),
        "has_kakao_request": file_exists_text(case_dir / "05_missing" / "kakao_request_message.txt"),
        "has_export_zip": file_exists_text(export_zip),
        "export_zip": str(export_zip) if export_zip.exists() else "",
        "next_action": meta.get("next_action", ""),
        "created_at": meta.get("created_at", ""),
        "last_modified": get_last_modified(case_dir),
    }

    return row


def scan_cases():
    if not CASES_DIR.exists():
        return []

    case_dirs = [p for p in CASES_DIR.iterdir() if p.is_dir()]
    rows = []

    for case_dir in sorted(case_dirs, key=lambda p: p.stat().st_mtime, reverse=True):
        rows.append(build_case_row(case_dir))

    return rows


def write_csv(rows):
    OUTPUTS_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUTS_DIR / "case_status_dashboard.csv"

    fieldnames = [
        "case_id",
        "status",
        "status_label",
        "case_type",
        "risk_level",
        "missing_count",
        "real_estate_office",
        "manager_name",
        "client_name",
        "client_phone",
        "property_address",
        "audio_count",
        "document_count",
        "has_transcript",
        "has_tax_facts",
        "has_customer_report",
        "has_tax_report",
        "has_kakao_request",
        "has_export_zip",
        "export_zip",
        "next_action",
        "created_at",
        "last_modified",
    ]

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return csv_path


def write_markdown(rows):
    OUTPUTS_DIR.mkdir(exist_ok=True)
    md_path = OUTPUTS_DIR / "case_status_dashboard.md"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("# TaxCaseManager 사건 상태 대시보드")
    lines.append("")
    lines.append(f"- 생성일시: {now}")
    lines.append(f"- 전체 사건 수: {len(rows)}")
    lines.append("")

    status_counts = {}
    risk_counts = {}

    for row in rows:
        status_counts[row["status_label"]] = status_counts.get(row["status_label"], 0) + 1
        risk = row["risk_level"] or "미확정"
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    lines.append("## 1. 상태별 건수")
    lines.append("")
    if status_counts:
        for key, value in status_counts.items():
            lines.append(f"- {key}: {value}건")
    else:
        lines.append("- 사건 없음")
    lines.append("")

    lines.append("## 2. 위험등급별 건수")
    lines.append("")
    if risk_counts:
        for key, value in risk_counts.items():
            lines.append(f"- {key}: {value}건")
    else:
        lines.append("- 사건 없음")
    lines.append("")

    lines.append("## 3. 사건 목록")
    lines.append("")
    lines.append("| 사건번호 | 상태 | 유형 | 위험 | 누락 | 고객 | 물건 | ZIP | 다음 조치 |")
    lines.append("|---|---|---|---|---:|---|---|---|---|")

    for row in rows:
        lines.append(
            f"| {row['case_id']} "
            f"| {row['status_label']} "
            f"| {row['case_type'] or '미확정'} "
            f"| {row['risk_level'] or '미확정'} "
            f"| {row['missing_count']} "
            f"| {row['client_name'] or '미입력'} "
            f"| {row['property_address'] or '미확인'} "
            f"| {row['has_export_zip']} "
            f"| {row['next_action'] or ''} |"
        )

    lines.append("")
    lines.append("## 4. 관리 주의사항")
    lines.append("")
    lines.append("- `05_MISSING_REQUESTED` 상태 사건은 고객 보완자료 수신 여부를 확인한다.")
    lines.append("- `06_EXPORTED` 상태 사건은 세무사 전달 여부와 회신 여부를 별도 기록한다.")
    lines.append("- 위험등급 ORANGE/RED 사건은 세무사 검토 전 단정 안내를 금지한다.")
    lines.append("- ZIP 파일에는 개인정보와 재산정보가 포함될 수 있으므로 전달 수신자를 반드시 확인한다.")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return md_path


def print_console_table(rows, limit):
    print("[DASHBOARD] TaxCaseManager 사건 상태")
    print(f"[TOTAL] {len(rows)}")
    print("")

    if not rows:
        print("[INFO] 등록된 사건이 없습니다.")
        return

    header = f"{'CASE_ID':<18} {'STATUS':<14} {'RISK':<8} {'MISS':<5} {'ZIP':<4} {'CLIENT':<10} {'TYPE'}"
    print(header)
    print("-" * len(header))

    for row in rows[:limit]:
        case_id = row["case_id"][:18]
        status = row["status_label"][:14]
        risk = (row["risk_level"] or "미확정")[:8]
        miss = str(row["missing_count"])
        zip_yn = row["has_export_zip"]
        client = (row["client_name"] or "미입력")[:10]
        case_type = (row["case_type"] or "미확정")[:30]

        print(f"{case_id:<18} {status:<14} {risk:<8} {miss:<5} {zip_yn:<4} {client:<10} {case_type}")


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 사건 상태 대시보드")
    parser.add_argument("--limit", type=int, default=20, help="콘솔에 표시할 최대 사건 수")
    args = parser.parse_args()

    try:
        rows = scan_cases()

        csv_path = write_csv(rows)
        md_path = write_markdown(rows)

        print_console_table(rows, args.limit)

        print("")
        print("[SUCCESS] 사건 상태 대시보드 생성 완료")
        print(f"[CSV] {csv_path}")
        print(f"[MD] {md_path}")

        write_log(f"dashboard_created cases={len(rows)} csv={csv_path} md={md_path}")

    except Exception as e:
        write_log(f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 사건 상태 대시보드 생성 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
