import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "case_input_form_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")

def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir

def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default

def ask_yes_no_unknown(prompt):
    value = input(f"{prompt} (y/n/u=모름): ").strip().lower()
    if value in ["y", "yes", "예", "있음", "있다"]:
        return "yes"
    if value in ["n", "no", "아니오", "없음", "없다"]:
        return "no"
    return "unknown"

def ask_multi(prompt):
    print(f"{prompt}")
    print("여러 항목은 쉼표로 구분해서 입력하세요. 없으면 Enter.")
    value = input("> ").strip()
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

def build_input_data(case_id):
    print("")
    print("=" * 70)
    print(f"[{case_id}] 고객 작성 서류 기반 입력자료 생성")
    print("모르는 항목은 비워두거나 u를 입력하세요.")
    print("=" * 70)

    data = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_method": "manual_from_client_forms",
        "client": {},
        "property": {},
        "household": {},
        "residence": {},
        "acquisition_price": {},
        "expenses": {},
        "exception_flags": {},
        "required_documents": {},
        "client_confirmation": {},
        "memo": "",
    }

    print("")
    print("[1] 고객/사건 정보")
    data["client"]["client_name"] = ask("고객명")
    data["client"]["client_phone"] = ask("연락처")
    data["client"]["real_estate_office"] = ask("부동산 사무실명")
    data["client"]["manager_name"] = ask("담당자")
    data["client"]["consult_purpose"] = ask("상담 목적", "양도세 사전진단")

    print("")
    print("[2] 매도 부동산 정보")
    data["property"]["property_address"] = ask("부동산 주소")
    data["property"]["property_type"] = ask("부동산 종류", "아파트")
    data["property"]["land_area"] = ask("토지면적/전용면적")
    data["property"]["building_area"] = ask("건물면적")
    data["property"]["ownership_type"] = ask("소유 형태 (단독소유/부부공동명의/가족공동명의/일부지분/기타)")
    data["property"]["ownership_share"] = ask("본인 지분율")
    data["property"]["co_owners"] = ask("공동명의자 및 지분율")
    data["property"]["acquisition_method"] = ask("취득 경위 (매매/상속/증여/분양/재개발/교환/기타)")
    data["property"]["acquired_date"] = ask("취득일")
    data["property"]["registration_date"] = ask("등기접수일")
    data["property"]["actual_payment_date"] = ask("실제 잔금일 또는 실제 취득일")
    data["property"]["sale_expected_date"] = ask("양도 예정일")
    data["property"]["sale_balance_date"] = ask("잔금 예정일")
    data["property"]["sale_expected_price"] = ask("양도 예정가액/계약금액")
    data["property"]["sale_status"] = ask("양도 상태 (예정/계약전/계약후잔금전/양도완료)")

    print("")
    print("[3] 주택 수/세대원 정보")
    data["household"]["current_house_count"] = ask("본인 명의 주택 수")
    data["household"]["spouse_house_count"] = ask("배우자 명의 주택 수")
    data["household"]["household_member_house_count"] = ask("세대원 명의 주택 수")
    data["household"]["spouse_same_household"] = ask_yes_no_unknown("배우자와 같은 세대 여부")
    data["household"]["spouse_house_owned"] = ask_yes_no_unknown("배우자 명의 주택 보유 여부")
    data["household"]["household_member_house_owned"] = ask_yes_no_unknown("세대원 주택 보유 여부")
    data["household"]["presale_right_owned"] = ask_yes_no_unknown("분양권 보유 여부")
    data["household"]["occupancy_right_owned"] = ask_yes_no_unknown("입주권 보유 여부")
    data["household"]["inherited_house_owned"] = ask_yes_no_unknown("상속주택 보유 여부")
    data["household"]["co_inherited_house_owned"] = ask_yes_no_unknown("공동상속주택 보유 여부")
    data["household"]["officetel_owned"] = ask_yes_no_unknown("오피스텔 보유 여부")
    data["household"]["rural_house_owned"] = ask_yes_no_unknown("농어촌주택 보유 여부")
    data["household"]["long_term_rental_house_owned"] = ask_yes_no_unknown("장기임대주택 보유 여부")

    print("")
    print("[4] 거주 정보")
    data["residence"]["lived_in"] = ask_yes_no_unknown("실제 거주 여부")
    data["residence"]["first_move_in_date"] = ask("최초 전입일")
    data["residence"]["final_move_out_date"] = ask("최종 전출일")
    data["residence"]["residence_period"] = ask("실제 거주기간")
    data["residence"]["currently_living"] = ask_yes_no_unknown("현재 거주 여부")
    data["residence"]["resident_registration_available"] = ask_yes_no_unknown("주민등록초본 제출 가능 여부")
    data["residence"]["utility_evidence_available"] = ask_yes_no_unknown("관리비/공과금 등 거주 증빙 가능 여부")
    data["residence"]["lease_contract_available"] = ask_yes_no_unknown("임대차계약서 보유 여부")

    print("")
    print("[5] 취득가액/필요경비 증빙")
    data["acquisition_price"]["purchase_contract_available"] = ask_yes_no_unknown("매수계약서 보유 여부")
    data["acquisition_price"]["purchase_contract_type"] = ask("계약서 원본/사본 여부")
    data["acquisition_price"]["bank_transfer_records_available"] = ask_yes_no_unknown("금융거래 내역 보유 여부")
    data["acquisition_price"]["acquisition_tax_records_available"] = ask_yes_no_unknown("취득세 자료 보유 여부")
    data["acquisition_price"]["acquisition_tax_base_visible"] = ask_yes_no_unknown("취득세 자료에 과세표준/취득가액 표시 여부")
    data["acquisition_price"]["registry_acquisition_date_confirmable"] = ask_yes_no_unknown("등기부등본으로 취득일 확인 가능 여부")
    data["acquisition_price"]["acquisition_price_unclear"] = ask_yes_no_unknown("취득가액 불명확 여부")
    data["acquisition_price"]["old_acquisition"] = ask_yes_no_unknown("오래전 취득 여부")
    data["acquisition_price"]["standard_market_price_needed"] = ask_yes_no_unknown("기준시가/공시지가 확인 필요 여부")
    data["acquisition_price"]["land_grade_data_needed"] = ask_yes_no_unknown("토지등급 자료 확인 필요 여부")
    data["acquisition_price"]["comparable_sale_review_needed"] = ask_yes_no_unknown("매매사례가액 검토 필요 여부")
    data["acquisition_price"]["appraisal_value_review_needed"] = ask_yes_no_unknown("감정가액 검토 필요 여부")
    data["acquisition_price"]["conversion_acquisition_value_review_needed"] = ask_yes_no_unknown("환산취득가액 검토 필요 여부")
    data["acquisition_price"]["deemed_acquisition_date_review_needed"] = ask_yes_no_unknown("의제취득일 검토 필요 여부")

    data["expenses"]["expense_evidence_items"] = ask_multi(
        "필요경비 증빙 보유 항목 입력 예: 취득세, 중개수수료, 법무사비, 인테리어, 수리비"
    )

    print("")
    print("[6] 예외사항")
    data["exception_flags"]["temporary_two_house_possible"] = ask_yes_no_unknown("일시적 2주택 가능성")
    data["exception_flags"]["inherited_or_gifted"] = ask_yes_no_unknown("상속/증여 취득 여부")
    data["exception_flags"]["inherited_acquisition"] = ask_yes_no_unknown("상속 취득 여부")
    data["exception_flags"]["gifted_acquisition"] = ask_yes_no_unknown("증여 취득 여부")
    data["exception_flags"]["burdened_gift"] = ask_yes_no_unknown("부담부증여 여부")
    data["exception_flags"]["redevelopment_reconstruction"] = ask_yes_no_unknown("재개발/재건축 관련 여부")
    data["exception_flags"]["member_occupancy_right_conversion"] = ask_yes_no_unknown("조합원입주권 전환 여부")
    data["exception_flags"]["joint_ownership"] = ask_yes_no_unknown("공동명의 여부")
    data["exception_flags"]["partial_share_transfer"] = ask_yes_no_unknown("지분 일부 양도 여부")
    data["exception_flags"]["family_transaction"] = ask_yes_no_unknown("가족 간 거래 여부")
    data["exception_flags"]["special_relation_transaction"] = ask_yes_no_unknown("가족/특수관계자 거래 여부")
    data["exception_flags"]["rental_business_history"] = ask_yes_no_unknown("임대사업자 등록 이력")
    data["exception_flags"]["non_business_land_possible"] = ask_yes_no_unknown("비사업용 토지 가능성")
    data["exception_flags"]["mixed_use_house"] = ask_yes_no_unknown("겸용주택 여부")
    data["exception_flags"]["contract_already_signed"] = ask_yes_no_unknown("이미 계약 완료 여부")
    data["exception_flags"]["balance_date_imminent"] = ask_yes_no_unknown("잔금일 임박 여부")
    data["exception_flags"]["tax_filing_deadline_imminent"] = ask_yes_no_unknown("신고기한 임박 여부")
    data["exception_flags"]["prior_tax_consultation"] = ask_yes_no_unknown("기존 세무상담 이력 여부")
    data["exception_flags"]["tax_office_inquiry_history"] = ask_yes_no_unknown("세무서 문의 이력 여부")

    print("")
    print("[7] 필요서류 제출상태")
    data["required_documents"]["registry_document"] = ask_yes_no_unknown("등기부등본 제출 여부")
    data["required_documents"]["purchase_contract"] = ask_yes_no_unknown("매수계약서 제출 여부")
    data["required_documents"]["sale_contract"] = ask_yes_no_unknown("매도계약서 제출 여부")
    data["required_documents"]["acquisition_tax_receipt"] = ask_yes_no_unknown("취득세 납부확인서 제출 여부")
    data["required_documents"]["resident_registration_abstract"] = ask_yes_no_unknown("주민등록초본 제출 여부")
    data["required_documents"]["resident_registration_record"] = ask_yes_no_unknown("주민등록등본 제출 여부")
    data["required_documents"]["brokerage_fee_receipts"] = ask_yes_no_unknown("중개수수료 영수증 제출 여부")
    data["required_documents"]["legal_scrivener_fee_receipts"] = ask_yes_no_unknown("법무사비 영수증 제출 여부")
    data["required_documents"]["repair_interior_evidence"] = ask_yes_no_unknown("인테리어/수리비 증빙 제출 여부")
    data["required_documents"]["construction_contract"] = ask_yes_no_unknown("공사계약서 제출 여부")
    data["required_documents"]["appraisal_report"] = ask_yes_no_unknown("감정평가서 제출 여부")
    data["required_documents"]["standard_market_price_docs"] = ask_yes_no_unknown("기준시가/공시지가 확인자료 제출 여부")
    data["required_documents"]["land_grade_docs"] = ask_yes_no_unknown("토지등급 자료 제출 여부")

    print("")
    print("[8] 고객 최종 확인")
    data["client_confirmation"]["confirmed_property_info"] = ask_yes_no_unknown("고객이 부동산 정보를 확인했는가")
    data["client_confirmation"]["confirmed_dates"] = ask_yes_no_unknown("고객이 취득일/양도예정일 정보를 확인했는가")
    data["client_confirmation"]["confirmed_acquisition_price_docs"] = ask_yes_no_unknown("고객이 취득가액 및 필요경비 제출상태를 확인했는가")
    data["client_confirmation"]["confirmed_household_status"] = ask_yes_no_unknown("고객이 세대/주택 보유 현황을 확인했는가")
    data["client_confirmation"]["confirmed_exception_flags"] = ask_yes_no_unknown("고객이 예외사항을 확인했는가")
    data["client_confirmation"]["unknowns_not_guessed"] = ask_yes_no_unknown("모르는 항목을 임의 작성하지 않았음을 확인했는가")
    data["client_confirmation"]["understands_not_final_tax_opinion"] = ask_yes_no_unknown("세무 판단 확정이 아님을 이해했는가")
    data["client_confirmation"]["signature_received"] = ask_yes_no_unknown("고객 서명 수령 여부")

    print("")
    data["memo"] = ask("기타 특이사항 메모")

    return data

def write_json(case_dir, data):
    input_dir = case_dir / "00_input"
    input_dir.mkdir(exist_ok=True)
    json_path = input_dir / "case_input_form.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path

def format_value(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(value)
    if value == "yes":
        return "예"
    if value == "no":
        return "아니오"
    if value == "unknown":
        return "모름/확인 필요"
    return str(value)

def write_markdown(case_dir, data):
    input_dir = case_dir / "00_input"
    input_dir.mkdir(exist_ok=True)
    md_path = input_dir / "case_input_form.md"

    lines = []
    lines.append(f"# {data['case_id']} 고객 작성 서류 기반 입력자료")
    lines.append("")
    lines.append(f"- 생성일시: {data.get('created_at', '')}")
    lines.append(f"- 입력방식: {data.get('input_method', '')}")
    lines.append("")

    sections = [
        ("고객/사건 정보", data.get("client", {})),
        ("매도 부동산 정보", data.get("property", {})),
        ("주택 수/세대원 정보", data.get("household", {})),
        ("거주 정보", data.get("residence", {})),
        ("취득가액 정보", data.get("acquisition_price", {})),
        ("필요경비 정보", data.get("expenses", {})),
        ("예외사항", data.get("exception_flags", {})),
        ("필요서류 제출상태", data.get("required_documents", {})),
        ("고객 최종 확인", data.get("client_confirmation", {})),
    ]

    for title, section in sections:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| 항목 | 입력값 |")
        lines.append("|---|---|")
        for key, value in section.items():
            lines.append(f"| {key} | {format_value(value)} |")
        lines.append("")

    lines.append("## 기타 메모")
    lines.append("")
    lines.append(data.get("memo", "") or "없음")
    lines.append("")

    lines.append("## 주의")
    lines.append("")
    lines.append("본 입력자료는 고객 작성 서류를 바탕으로 정리한 기초자료입니다.")
    lines.append("최종 세무 판단은 세무사 검토가 필요합니다.")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return md_path

def update_case_meta(case_dir, data):
    meta_path = case_dir / "case_meta.json"
    meta = {}
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}

    client = data.get("client", {})
    prop = data.get("property", {})

    meta["status"] = "00_INPUT_FORM_CREATED"
    meta["input_form_created_at"] = datetime.now().isoformat(timespec="seconds")
    meta["client_name"] = client.get("client_name", meta.get("client_name", ""))
    meta["client_phone"] = client.get("client_phone", meta.get("client_phone", ""))
    meta["real_estate_office"] = client.get("real_estate_office", meta.get("real_estate_office", ""))
    meta["manager_name"] = client.get("manager_name", meta.get("manager_name", ""))
    meta["property_address"] = prop.get("property_address", meta.get("property_address", ""))
    meta["next_action"] = "case_input_form.json 기반으로 tax_facts 생성 또는 파이프라인 실행"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta_path

def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 고객 작성내용 JSON 입력자료 변환기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    args = parser.parse_args()

    case_id = args.case_id
    try:
        case_dir = get_case_dir(case_id)
        data = build_input_data(case_id)
        json_path = write_json(case_dir, data)
        md_path = write_markdown(case_dir, data)
        meta_path = update_case_meta(case_dir, data)

        write_log(case_id, f"case_input_form_created json={json_path}")

        print("")
        print("[SUCCESS] 고객 작성내용 JSON 입력자료 생성 완료")
        print(f"[JSON] {json_path}")
        print(f"[MD] {md_path}")
        print(f"[META] {meta_path}")
        print("")
        print("[NEXT]")
        print("1. case_input_form.json 내용을 확인하세요.")
        print("2. 다음 단계에서 extract_tax_facts.py가 이 JSON을 읽도록 연결합니다.")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 고객 작성내용 JSON 입력자료 생성 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
