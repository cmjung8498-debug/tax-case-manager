import json
import subprocess
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
TEMPLATES_FORMS_DIR = BASE_DIR / "templates" / "client_forms"
EXPORTS_DIR = BASE_DIR / "exports"


DEMO_CASE_ID = "DEMO-20260511-001"


CASE_SUBDIRS = [
    "00_input",
    "00_input_forms",
    "01_audio",
    "02_transcript",
    "03_documents",
    "04_extract",
    "05_missing",
    "06_reports",
    "07_tax_review",
    "08_cost",
]


def ensure_case_dirs(case_id):
    case_dir = CASES_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    for subdir in CASE_SUBDIRS:
        (case_dir / subdir).mkdir(exist_ok=True)

    return case_dir


def build_demo_input(case_id):
    return {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_method": "demo_case_template",
        "client": {
            "client_name": "홍길동",
            "client_phone": "010-0000-0000",
            "real_estate_office": "데모부동산",
            "manager_name": "김중개",
            "consult_purpose": "양도세 사전진단"
        },
        "property": {
            "property_address": "서울 강남구 테스트아파트",
            "property_type": "아파트",
            "land_area": "",
            "building_area": "84㎡",
            "ownership_type": "단독소유",
            "ownership_share": "100%",
            "co_owners": "",
            "acquisition_method": "매매",
            "acquired_date": "2020년 5월 10일",
            "registration_date": "2020년 5월 15일",
            "actual_payment_date": "2020년 5월 10일",
            "acquired_price": "7억",
            "sale_expected_date": "2026년 8월 30일",
            "sale_balance_date": "2026년 8월 30일",
            "sale_expected_price": "13억",
            "sale_status": "매도 예정"
        },
        "household": {
            "current_house_count": "1",
            "spouse_house_count": "",
            "household_member_house_count": "",
            "spouse_same_household": "unknown",
            "spouse_house_owned": "unknown",
            "household_member_house_owned": "unknown",
            "presale_right_owned": "no",
            "occupancy_right_owned": "no",
            "inherited_house_owned": "no",
            "co_inherited_house_owned": "no",
            "officetel_owned": "unknown",
            "rural_house_owned": "no",
            "long_term_rental_house_owned": "no"
        },
        "residence": {
            "lived_in": "yes",
            "first_move_in_date": "2020년 6월 1일",
            "final_move_out_date": "2023년 1월 31일",
            "residence_period": "2년 6개월",
            "currently_living": "no",
            "resident_registration_available": "yes",
            "utility_evidence_available": "unknown",
            "lease_contract_available": "unknown"
        },
        "acquisition_price": {
            "purchase_contract_available": "unknown",
            "purchase_contract_type": "확인 필요",
            "bank_transfer_records_available": "unknown",
            "acquisition_tax_records_available": "yes",
            "acquisition_tax_base_visible": "unknown",
            "registry_acquisition_date_confirmable": "yes",
            "acquisition_price_unclear": "no",
            "old_acquisition": "no",
            "standard_market_price_needed": "unknown",
            "land_grade_data_needed": "no",
            "comparable_sale_review_needed": "unknown",
            "appraisal_value_review_needed": "unknown",
            "conversion_acquisition_value_review_needed": "unknown",
            "deemed_acquisition_date_review_needed": "no"
        },
        "expenses": {
            "expense_evidence_items": ["취득세", "중개수수료"]
        },
        "exception_flags": {
            "temporary_two_house_possible": "no",
            "inherited_or_gifted": "no",
            "inherited_acquisition": "no",
            "gifted_acquisition": "no",
            "burdened_gift": "no",
            "redevelopment_reconstruction": "no",
            "member_occupancy_right_conversion": "no",
            "joint_ownership": "no",
            "partial_share_transfer": "no",
            "family_transaction": "no",
            "special_relation_transaction": "no",
            "rental_business_history": "no",
            "non_business_land_possible": "no",
            "mixed_use_house": "no",
            "contract_already_signed": "no",
            "balance_date_imminent": "no",
            "tax_filing_deadline_imminent": "no",
            "prior_tax_consultation": "no",
            "tax_office_inquiry_history": "no"
        },
        "required_documents": {
            "registry_document": "yes",
            "purchase_contract": "unknown",
            "sale_contract": "unknown",
            "acquisition_tax_receipt": "yes",
            "resident_registration_abstract": "unknown",
            "resident_registration_record": "unknown",
            "brokerage_fee_receipts": "yes",
            "legal_scrivener_fee_receipts": "unknown",
            "repair_interior_evidence": "unknown",
            "construction_contract": "unknown",
            "appraisal_report": "no",
            "standard_market_price_docs": "unknown",
            "land_grade_docs": "no"
        },
        "client_confirmation": {
            "confirmed_property_info": "yes",
            "confirmed_dates": "yes",
            "confirmed_acquisition_price_docs": "unknown",
            "confirmed_household_status": "unknown",
            "confirmed_exception_flags": "yes",
            "unknowns_not_guessed": "yes",
            "understands_not_final_tax_opinion": "yes",
            "signature_received": "yes"
        },
        "memo": "부동산 사무실 시연용 데모 사건입니다. 실제 고객 정보가 아닙니다."
    }


def write_case_input(case_dir, case_id):
    input_dir = case_dir / "00_input"
    input_dir.mkdir(exist_ok=True)

    data = build_demo_input(case_id)

    json_path = input_dir / "case_input_form.json"
    md_path = input_dir / "case_input_form.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    lines = []
    lines.append(f"# {case_id} 데모 입력자료")
    lines.append("")
    lines.append("- 본 파일은 부동산 사무실 시연용 가상 사건입니다.")
    lines.append("- 실제 고객 정보가 아닙니다.")
    lines.append("")
    lines.append("## 요약")
    lines.append("")
    lines.append("- 사건유형: 1세대 1주택 고가주택 가능성")
    lines.append("- 주요 쟁점: 배우자/세대원 주택 미확인, 취득가액 증빙 일부 확인 필요")
    lines.append("- 예상 위험등급: ORANGE")
    lines.append("- 예상 취득가액 신뢰도: B_PARTIAL")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return json_path, md_path


def write_case_meta(case_dir, case_id):
    meta = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "demo_case",
        "status": "00_INPUT_IMPORTED",
        "real_estate_office": "데모부동산",
        "manager_name": "김중개",
        "client_name": "홍길동",
        "client_phone": "010-0000-0000",
        "property_address": "서울 강남구 테스트아파트",
        "memo": "부동산 사무실 시연용 가상 사건",
        "next_action": "run_case_pipeline.py --no-audio 실행"
    }

    meta_path = case_dir / "case_meta.json"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta_path


def copy_client_forms(case_dir):
    target_dir = case_dir / "00_input_forms"
    target_dir.mkdir(exist_ok=True)

    copied = []

    if TEMPLATES_FORMS_DIR.exists():
        for src in TEMPLATES_FORMS_DIR.glob("*.md"):
            dst = target_dir / src.name
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            copied.append(dst)

    return copied


def run_pipeline(case_id):
    cmd = [
        sys.executable,
        str(BASE_DIR / "run_case_pipeline.py"),
        case_id,
        "--no-audio"
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    return completed


def write_demo_readme(case_dir, case_id):
    zip_path = EXPORTS_DIR / f"{case_id}.zip"

    content = f"""# {case_id} 부동산 사무실용 데모 사건

## 목적

이 사건은 TaxCaseManager를 부동산 사무실에 설명하기 위한 가상 데모 사건입니다.  
실제 고객 정보가 아닙니다.

## 데모 시나리오

- 고객: 홍길동
- 부동산: 서울 강남구 테스트아파트
- 취득일: 2020년 5월 10일
- 취득가액: 7억 원
- 양도 예정가액: 13억 원
- 거주기간: 2년 6개월
- 본인 명의 주택 수: 1채
- 배우자/세대원 주택: 확인 필요
- 취득가액 증빙: 취득세 자료는 있으나 계약서/금융자료 확인 필요

## 확인할 출력물

1. 고객용 리포트  
   `06_reports\\01_customer_summary.md`

2. 부동산 사무실용 리포트  
   `06_reports\\02_office_check_report.md`

3. 세무사용 검토 리포트  
   `06_reports\\03_tax_accountant_review.md`

4. 고객 보완요청 문구  
   `05_missing\\kakao_request_message.txt`

5. 세무사 전달 ZIP  
   `{zip_path}`

## 설명 포인트

- 고객 작성 서류 기반으로 입력 가능
- 녹음 없이도 리포트 생성 가능
- 취득가액 불명확 검토 자동 표시
- 세무사에게 보낼 ZIP 자동 생성
- 부동산 사무실은 세무 판단을 확정하지 않고 자료 정리/사전진단 역할 수행
- AI 양도세 사전진단 완결 리포트 100,000원
- 세무사 검토 패키지 200,000원
"""

    readme_path = case_dir / "DEMO_README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    return readme_path


def main():
    case_id = DEMO_CASE_ID

    print("[START] 부동산 사무실용 데모 사건 생성")
    print(f"[CASE_ID] {case_id}")

    case_dir = ensure_case_dirs(case_id)
    json_path, md_path = write_case_input(case_dir, case_id)
    meta_path = write_case_meta(case_dir, case_id)
    copied_forms = copy_client_forms(case_dir)

    print(f"[INPUT_JSON] {json_path}")
    print(f"[INPUT_MD] {md_path}")
    print(f"[META] {meta_path}")
    print(f"[FORMS_COPIED] {len(copied_forms)}")

    completed = run_pipeline(case_id)

    print("[PIPELINE_STDOUT]")
    print(completed.stdout)

    if completed.returncode != 0:
        print("[PIPELINE_STDERR]")
        print(completed.stderr)
        raise SystemExit(completed.returncode)

    readme_path = write_demo_readme(case_dir, case_id)

    print("[SUCCESS] 데모 사건 생성 완료")
    print(f"[CASE_DIR] {case_dir}")
    print(f"[DEMO_README] {readme_path}")
    print(f"[ZIP] {EXPORTS_DIR / (case_id + '.zip')}")


if __name__ == "__main__":
    main()
