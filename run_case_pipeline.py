import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

TRANSCRIBE_STEP = {
    "name": "transcribe_audio",
    "script": "transcribe_audio.py",
    "description": "음성파일 전사",
    "required": True,
}

STEPS = [
    {
        "name": "extract_tax_facts",
        "script": "extract_tax_facts.py",
        "description": "양도세 사실관계 추출",
        "required": True,
    },
    {
        "name": "legal_basis_manager",
        "script": "legal_basis_manager.py",
        "description": "법령 기준일 및 이력 DB 확인",
        "required": True,
    },
    {
        "name": "regulated_area_history_check",
        "script": "regulated_area_history_check.py",
        "description": "조정대상지역 이력 조회",
        "required": True,
    },
    {
        "name": "acquisition_price_review",
        "script": "acquisition_price_review.py",
        "description": "취득가액 불명확 및 대체 취득가액 검토",
        "required": True,
    },
    {
        "name": "multi_asset_split_review",
        "script": "multi_asset_split_review.py",
        "description": "재개발/재건축 및 다중 물건 분리 검토",
        "required": True,
    },
    {
        "name": "generate_tax_report",
        "script": "generate_tax_report.py",
        "description": "고객/부동산/세무사 리포트 생성",
        "required": True,
    },
    {
        "name": "convert_reports_to_docx",
        "script": "convert_reports_to_docx.py",
        "description": "리포트 DOCX 변환",
        "required": False,
    },
    {
        "name": "missing_request_message",
        "script": "missing_request_message.py",
        "description": "보완자료 카카오톡 요청문 생성",
        "required": False,
    },
    {
        "name": "attach_case_documents",
        "script": "attach_case_documents.py",
        "description": "세무사 송부용 첨부서류 분류",
        "required": False,
    },
    {
        "name": "export_case_bundle",
        "script": "export_case_bundle.py",
        "description": "세무사 전달용 ZIP 패키지 생성",
        "required": False,
    },
    {
        "name": "case_status_dashboard",
        "script": "case_status_dashboard.py",
        "description": "사건 상태 대시보드 갱신",
        "required": False,
    },
]


def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "pipeline_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def check_prerequisites(case_id, transcribe=False):
    case_dir = get_case_dir(case_id)
    transcript_path = case_dir / "02_transcript" / "transcript.txt"
    audio_dir = case_dir / "01_audio"
    input_json_path = case_dir / "00_input" / "case_input_form.json"

    checks = {
        "case_dir": case_dir.exists(),
        "transcript": transcript_path.exists(),
        "audio_dir": audio_dir.exists(),
        "input_json": input_json_path.exists(),
        "audio_count": 0,
    }

    if audio_dir.exists():
        checks["audio_count"] = sum(1 for p in audio_dir.iterdir() if p.is_file())

    if not transcribe and not checks["transcript"] and not checks["input_json"]:
        raise FileNotFoundError(
            f"transcript.txt 또는 case_input_form.json이 없습니다. 먼저 입력자료를 준비하세요."
        )

    if transcribe and checks["audio_count"] == 0:
        raise FileNotFoundError(
            f"--transcribe 옵션을 사용했지만 01_audio 폴더에 음성파일이 없습니다: {audio_dir}"
        )

    return checks


def run_script(script_name, args):
    script_path = BASE_DIR / script_name

    if not script_path.exists():
        return {
            "script": script_name,
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"script not found: {script_path}",
        }

    cmd = [sys.executable, str(script_path)] + args

    completed = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    return {
        "script": script_name,
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def should_skip_step(step_name, args):
    if step_name == "missing_request_message" and args.skip_missing:
        return True

    if step_name == "export_case_bundle" and args.skip_export:
        return True

    if step_name == "attach_case_documents" and not args.attach_source:
        return True

    return False


def build_step_args(step_name, case_id, args):
    if step_name == "case_status_dashboard":
        return ["--limit", str(args.dashboard_limit)]

    if step_name == "export_case_bundle":
        step_args = [case_id]
        if args.no_audio:
            step_args.append("--no-audio")
        return step_args

    if step_name == "attach_case_documents":
        return [case_id, "--source", args.attach_source]

    return [case_id]


def run_pipeline(case_id, args):
    results = []

    write_log(case_id, "pipeline_start")

    checks = check_prerequisites(case_id, transcribe=args.transcribe)
    write_log(case_id, f"prerequisites_ok transcript={checks['transcript']}")

    if args.transcribe:
        step = TRANSCRIBE_STEP
        print("")
        print(f"[STEP_START] {step['description']}")
        print(f"[SCRIPT] {step['script']}")

        result = run_script(step["script"], [case_id])
        result["name"] = step["name"]
        result["description"] = step["description"]
        result["required"] = step["required"]
        result["skipped"] = False
        results.append(result)

        if result["success"]:
            print(f"[STEP_PASS] {step['description']}")
            write_log(case_id, "step_pass name=transcribe_audio")
        else:
            print(f"[STEP_FAIL] {step['description']}")
            write_log(case_id, f"step_fail name=transcribe_audio returncode={result['returncode']}")
            return results, determine_verdict(results)

    for step in STEPS:
        step_name = step["name"]

        if should_skip_step(step_name, args):
            result = {
                "name": step_name,
                "description": step["description"],
                "required": step["required"],
                "skipped": True,
                "success": True,
                "returncode": 0,
                "stdout": "",
                "stderr": "",
            }
            results.append(result)
            write_log(case_id, f"step_skipped name={step_name}")
            continue

        print("")
        print(f"[STEP_START] {step['description']}")
        print(f"[SCRIPT] {step['script']}")

        step_args = build_step_args(step_name, case_id, args)
        result = run_script(step["script"], step_args)

        result["name"] = step_name
        result["description"] = step["description"]
        result["required"] = step["required"]
        result["skipped"] = False

        results.append(result)

        if result["success"]:
            print(f"[STEP_PASS] {step['description']}")
            write_log(case_id, f"step_pass name={step_name}")
        else:
            print(f"[STEP_FAIL] {step['description']}")
            print(f"[RETURN_CODE] {result['returncode']}")
            if result["stdout"].strip():
                print("[STDOUT]")
                print(result["stdout"])
            if result["stderr"].strip():
                print("[STDERR]")
                print(result["stderr"])

            write_log(
                case_id,
                f"step_fail name={step_name} returncode={result['returncode']} stderr={result['stderr'][:300]}"
            )

            if step["required"]:
                break

    verdict = determine_verdict(results)

    write_log(case_id, f"pipeline_end verdict={verdict}")

    return results, verdict


def determine_verdict(results):
    if not results:
        return "FAIL"

    required_failed = [
        r for r in results
        if r.get("required") and not r.get("success")
    ]

    any_failed = [
        r for r in results
        if not r.get("success")
    ]

    if required_failed:
        return "FAIL"

    if any_failed:
        return "PARTIAL"

    return "PASS"


def print_summary(case_id, results, verdict):
    print("")
    print("=" * 70)
    print("[PIPELINE SUMMARY]")
    print(f"[CASE_ID] {case_id}")
    print(f"[VERDICT] {verdict}")
    print("")

    for r in results:
        status = "SKIP" if r.get("skipped") else ("PASS" if r.get("success") else "FAIL")
        print(f"- {status:<5} | {r.get('description')} | {r.get('script', r.get('name'))}")

    print("")
    print("[OUTPUT CHECK]")
    case_dir = CASES_DIR / case_id

    expected_paths = [
        case_dir / "02_transcript" / "transcript.txt",
        case_dir / "02_transcript" / "transcript_meta.json",
        case_dir / "08_cost" / "api_usage.json",
        case_dir / "08_cost" / "api_usage_summary.md",
        case_dir / "04_extract" / "legal_basis_check.json",
        case_dir / "04_extract" / "tax_facts.json",
        case_dir / "04_extract" / "acquisition_price_review.json",
        case_dir / "05_missing" / "acquisition_price_missing_items.md",
        case_dir / "06_reports" / "01_customer_summary.md",
        case_dir / "06_reports" / "02_office_check_report.md",
        case_dir / "06_reports" / "03_tax_accountant_review.md",
        case_dir / "05_missing" / "kakao_request_message.txt",
        BASE_DIR / "exports" / f"{case_id}.zip",
        BASE_DIR / "outputs" / "case_status_dashboard.csv",
        BASE_DIR / "outputs" / "case_status_dashboard.md",
    ]

    for path in expected_paths:
        yn = "Y" if path.exists() else "N"
        print(f"- {yn} | {path}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 사건 처리 통합 실행기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    parser.add_argument("--transcribe", action="store_true", help="전사 단계 포함 실행")
    parser.add_argument("--no-audio", action="store_true", help="export ZIP에서 녹음파일 제외")
    parser.add_argument("--skip-export", action="store_true", help="export_case_bundle.py 단계 생략")
    parser.add_argument("--skip-missing", action="store_true", help="missing_request_message.py 단계 생략")
    parser.add_argument("--dashboard-limit", type=int, default=20, help="대시보드 콘솔 표시 사건 수")
    parser.add_argument("--attach-source", help="첨부서류 분류 시 원본 폴더 경로")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        print("[START] TaxCaseManager 사건 처리 통합 실행")
        print(f"[CASE_ID] {case_id}")
        print(f"[NO_AUDIO] {args.no_audio}")
        print(f"[SKIP_EXPORT] {args.skip_export}")
        print(f"[SKIP_MISSING] {args.skip_missing}")

        results, verdict = run_pipeline(case_id, args)
        print_summary(case_id, results, verdict)

    except Exception as e:
        write_log(case_id, f"PIPELINE_ERROR {type(e).__name__}: {e}")
        print("[FAIL] 파이프라인 실행 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
