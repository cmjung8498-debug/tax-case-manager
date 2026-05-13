import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

HISTORY_PATH = DATA_DIR / "regulated_area_history.csv"
AUDIT_CSV_PATH = OUTPUT_DIR / "regulated_area_coverage_audit.csv"
AUDIT_MD_PATH = OUTPUT_DIR / "regulated_area_coverage_audit.md"

TARGET_REGIONS = [
    "서울특별시 강남구",
    "서울특별시 서초구",
    "서울특별시 송파구",
    "서울특별시 강동구",
    "서울특별시 마포구",
    "서울특별시 용산구",
    "서울특별시 성동구",
    "서울특별시 광진구",
    "서울특별시 영등포구",
    "서울특별시 양천구",
    "서울특별시 강서구",
    "서울특별시 노원구",
    "서울특별시 동작구",
    "서울특별시 종로구",
    "서울특별시 중구",

    "경기도 과천시",
    "경기도 성남시 분당구",
    "경기도 성남시 수정구",
    "경기도 성남시 중원구",
    "경기도 하남시",
    "경기도 광명시",
    "경기도 고양시",
    "경기도 남양주시",
    "경기도 화성시",
    "경기도 수원시",
    "경기도 용인시",
    "경기도 안양시",
    "경기도 의왕시",
    "경기도 구리시",
    "경기도 군포시",
    "경기도 부천시",
    "경기도 안산시",
    "경기도 시흥시",
    "경기도 김포시",
    "경기도 파주시",
    "경기도 동두천시",
    "경기도 양주시",
    "경기도 오산시",
    "경기도 평택시",

    "인천광역시 연수구",
    "인천광역시 남동구",
    "인천광역시 서구",
    "인천광역시 부평구",
    "인천광역시 계양구",
    "인천광역시 미추홀구",
    "인천광역시 중구",
    "인천광역시 동구",

    "부산광역시 해운대구",
    "부산광역시 수영구",
    "부산광역시 동래구",
    "부산광역시 남구",
    "부산광역시 연제구",

    "대구광역시 수성구",

    "대전광역시 유성구",
    "대전광역시 서구",
    "대전광역시 중구",
    "대전광역시 동구",
    "대전광역시 대덕구",

    "광주광역시 남구",
    "광주광역시 서구",
    "광주광역시 동구",
    "광주광역시 북구",
    "광주광역시 광산구",

    "울산광역시 남구",
    "울산광역시 중구",

    "세종특별자치시",

    "충청북도 청주시",
    "충청남도 천안시",
    "충청남도 공주시",
    "충청남도 논산시",
]


def write_log(message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "regulated_area_coverage_audit_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")


def load_history():
    if not HISTORY_PATH.exists():
        raise FileNotFoundError(f"regulated_area_history.csv 없음: {HISTORY_PATH}")

    with open(HISTORY_PATH, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def classify_region(region_name, rows):
    matched = [r for r in rows if (r.get("region_name") or "").strip() == region_name]

    if not matched:
        partial_candidates = [
            r for r in rows
            if region_name in (r.get("note") or "")
            or region_name in (r.get("region_name") or "")
        ]

        if partial_candidates:
            return "PARTIAL_ONLY", partial_candidates, "일부 지역 지정으로 PARTIAL 처리", False

        return "MISSING", [], "지역 이력 행 없음", True

    has_active = any((r.get("status") or "").strip() == "ACTIVE" for r in matched)
    has_released = any((r.get("status") or "").strip() == "RELEASED" for r in matched)
    has_official = any((r.get("confidence") or "").strip() == "A_OFFICIAL" for r in matched)
    has_source = any((r.get("source_url") or "").strip() for r in matched)
    has_notice = any((r.get("notice_no") or "").strip() for r in matched)
    has_partial = any((r.get("status") or "").strip() == "PARTIAL" or (r.get("confidence") or "").strip() == "B_PARTIAL" for r in matched)

    if has_partial and not has_active:
        return "PARTIAL_ONLY", matched, "일부 지역 지정으로 PARTIAL 처리", False

    if not has_official or not has_source or not has_notice:
        return "NO_OFFICIAL_SOURCE", matched, "공식 source_url 부족", True

    if not has_active and not has_released:
        return "NEEDS_REVIEW", matched, "상태 이상", True

    return "OK", matched, "공식 이력 행 존재", False


def summarize_rows(rows):
    if not rows:
        return {
            "row_count": 0,
            "active_count": 0,
            "released_count": 0,
            "partial_count": 0,
            "official_count": 0,
            "notice_nos": "",
            "date_ranges": "",
        }

    active_count = sum(1 for r in rows if r.get("status") == "ACTIVE")
    released_count = sum(1 for r in rows if r.get("status") == "RELEASED")
    partial_count = sum(1 for r in rows if r.get("status") == "PARTIAL" or r.get("confidence") == "B_PARTIAL")
    official_count = sum(1 for r in rows if r.get("confidence") == "A_OFFICIAL")

    notice_nos = sorted({r.get("notice_no", "") for r in rows if r.get("notice_no", "")})
    date_ranges = []
    for r in rows:
        date_ranges.append(f"{r.get('start_date','')[:10]}~{r.get('end_date','')[:10]}({r.get('status','')})")

    return {
        "row_count": len(rows),
        "active_count": active_count,
        "released_count": released_count,
        "partial_count": partial_count,
        "official_count": official_count,
        "notice_nos": "; ".join(notice_nos),
        "date_ranges": "; ".join(date_ranges),
    }


def run_audit():
    rows = load_history()
    results = []

    for region_name in TARGET_REGIONS:
        verdict, matched, reason, needs_manual_review = classify_region(region_name, rows)
        summary = summarize_rows(matched)

        results.append({
            "region_name": region_name,
            "verdict": verdict,
            "row_count": summary["row_count"],
            "active_count": summary["active_count"],
            "released_count": summary["released_count"],
            "partial_count": summary["partial_count"],
            "official_count": summary["official_count"],
            "needs_manual_review": needs_manual_review,
            "reason": reason,
            "notice_nos": summary["notice_nos"],
            "date_ranges": summary["date_ranges"]
        })

    return results


def write_csv(results):
    OUTPUT_DIR.mkdir(exist_ok=True)

    fieldnames = [
        "region_name",
        "verdict",
        "row_count",
        "active_count",
        "released_count",
        "partial_count",
        "official_count",
        "needs_manual_review",
        "reason",
        "notice_nos",
        "date_ranges",
    ]

    with open(AUDIT_CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return AUDIT_CSV_PATH


def write_md(results):
    OUTPUT_DIR.mkdir(exist_ok=True)

    total = len(results)
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    lines = []
    lines.append("# 전국 조정대상지역 커버리지 감사 결과")
    lines.append("")
    lines.append("## 전체 커버리지 요약")
    lines.append("")
    lines.append(f"- 감사 대상 전체: {total}")
    lines.append(f"- OK: {counts.get('OK', 0)}")
    lines.append(f"- PARTIAL_ONLY: {counts.get('PARTIAL_ONLY', 0)}")
    lines.append(f"- MISSING: {counts.get('MISSING', 0)}")
    lines.append(f"- NO_OFFICIAL_SOURCE: {counts.get('NO_OFFICIAL_SOURCE', 0)}")
    lines.append(f"- NEEDS_REVIEW: {counts.get('NEEDS_REVIEW', 0)}")
    lines.append("")
    lines.append("## 실사용 가능성 판정")
    lines.append("")
    lines.append("- OK + PARTIAL_ONLY는 사전진단 참고 가능")
    lines.append("- MISSING은 자동 판정 불가")
    lines.append("- NO_OFFICIAL_SOURCE는 공식 근거 보강 필요")
    lines.append("- NEEDS_REVIEW는 수동 검토 필요")
    lines.append("")
    lines.append("## 상세 결과")
    lines.append("")
    lines.append("| 지역 | 판정 | 사유 | 수동검토 | 행수 | ACTIVE | RELEASED | PARTIAL | A_OFFICIAL | 공고 | 기간 |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---|---|")

    for r in results:
        lines.append(
            f"| {r['region_name']} | {r['verdict']} | {r['reason']} | {r['needs_manual_review']} | {r['row_count']} "
            f"| {r['active_count']} | {r['released_count']} | {r['partial_count']} "
            f"| {r['official_count']} | {r['notice_nos']} | {r['date_ranges']} |"
        )

    lines.append("")
    lines.append("## 판정 기준")
    lines.append("")
    lines.append("- OK: 이력 행과 공식 근거가 존재")
    lines.append("- MISSING: 해당 지역 이력 행 없음")
    lines.append("- PARTIAL_ONLY: 일부 지역 또는 택지지구만 존재")
    lines.append("- NO_OFFICIAL_SOURCE: 공식 공고번호/source_url 근거 부족")
    lines.append("- NEEDS_REVIEW: 기간 또는 상태값 확인 필요")
    lines.append("")
    lines.append("주의: 본 감사 결과는 DB 커버리지 확인용이며, 세무 판단 확정 자료가 아닙니다.")

    with open(AUDIT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return AUDIT_MD_PATH


def main():
    try:
        results = run_audit()
        csv_path = write_csv(results)
        md_path = write_md(results)

        counts = {}
        for r in results:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

        print("[SUCCESS] 조정대상지역 커버리지 감사 완료")
        print(f"[CSV] {csv_path}")
        print(f"[MD] {md_path}")
        for key in sorted(counts):
            print(f"[{key}] {counts[key]}")

        write_log(f"audit_success total={len(results)} counts={counts}")

    except Exception as e:
        write_log(f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 조정대상지역 커버리지 감사 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
