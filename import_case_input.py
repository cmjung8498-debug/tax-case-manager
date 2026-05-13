import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "import_case_input_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")

def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir

def normalize_yes_no_unknown(value):
    value = str(value or "").strip().lower()
    if value in ["y", "yes", "예", "있음", "있다", "true", "1"]:
        return "yes"
    if value in ["n", "no", "아니오", "없음", "없다", "false", "0"]:
        return "no"
    if value in ["u", "unknown", "모름", "확인필요", "확인 필요", ""]:
        return "unknown"
    return value

def split_items(value):
    value = str(value or "").strip()
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

def csv_row_to_data(row):
    data = {
        "case_id": "",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_method": "imported_csv_template",
        "client": {
            "client_name": row.get("client_name", ""),
            "client_phone": row.get("client_phone", ""),
            "real_estate_office": row.get("real_estate_office", ""),
            "manager_name": row.get("manager_name", ""),
            "consult_purpose": row.get("consult_purpose", "양도세 사전진단"),
        },
        "property": {
            "property_address": row.get("property_address", ""),
            "property_type": row.get("property_type", ""),
            "land_area": row.get("land_area", ""),
            "building_area": row.get("building_area", ""),
            "ownership_type": row.get("ownership_type", ""),
            "ownership_share": row.get("ownership_share", ""),
            "co_owners": row.get("co_owners", ""),
            "acquisition_method": row.get("acquisition_method", ""),
            "acquired_date": row.get("acquired_date", ""),
            "registration_date": row.get("registration_date", ""),
            "actual_payment_date": row.get("actual_payment_date", ""),
            "sale_expected_date": row.get("sale_expected_date", ""),
            "sale_balance_date": row.get("sale_balance_date", ""),
            "sale_expected_price": row.get("sale_expected_price", ""),
            "sale_status": row.get("sale_status", ""),
        },
        "household": {
            "current_house_count": row.get("current_house_count", ""),
            "spouse_house_count": row.get("spouse_house_count", ""),
            "household_member_house_count": row.get("household_member_house_count", ""),
            "spouse_same_household": normalize_yes_no_unknown(row.get("spouse_same_household", "")),
            "spouse_house_owned": normalize_yes_no_unknown(row.get("spouse_house_owned", "")),
            "household_member_house_owned": normalize_yes_no_unknown(row.get("household_member_house_owned", "")),
            "presale_right_owned": normalize_yes_no_unknown(row.get("presale_right_owned", "")),
            "occupancy_right_owned": normalize_yes_no_unknown(row.get("occupancy_right_owned", "")),
            "inherited_house_owned": normalize_yes_no_unknown(row.get("inherited_house_owned", "")),
            "co_inherited_house_owned": normalize_yes_no_unknown(row.get("co_inherited_house_owned", "")),
            "officetel_owned": normalize_yes_no_unknown(row.get("officetel_owned", "")),
            "rural_house_owned": normalize_yes_no_unknown(row.get("rural_house_owned", "")),
            "long_term_rental_house_owned": normalize_yes_no_unknown(row.get("long_term_rental_house_owned", "")),
        },
        "residence": {
            "lived_in": normalize_yes_no_unknown(row.get("lived_in", "")),
            "first_move_in_date": row.get("first_move_in_date", ""),
            "final_move_out_date": row.get("final_move_out_date", ""),
            "residence_period": row.get("residence_period", ""),
            "currently_living": normalize_yes_no_unknown(row.get("currently_living", "")),
            "resident_registration_available": normalize_yes_no_unknown(row.get("resident_registration_available", "")),
            "utility_evidence_available": normalize_yes_no_unknown(row.get("utility_evidence_available", "")),
            "lease_contract_available": normalize_yes_no_unknown(row.get("lease_contract_available", "")),
        },
        "acquisition_price": {
            "purchase_contract_available": normalize_yes_no_unknown(row.get("purchase_contract_available", "")),
            "purchase_contract_type": row.get("purchase_contract_type", ""),
            "bank_transfer_records_available": normalize_yes_no_unknown(row.get("bank_transfer_records_available", "")),
            "acquisition_tax_records_available": normalize_yes_no_unknown(row.get("acquisition_tax_records_available", "")),
            "acquisition_tax_base_visible": normalize_yes_no_unknown(row.get("acquisition_tax_base_visible", "")),
            "registry_acquisition_date_confirmable": normalize_yes_no_unknown(row.get("registry_acquisition_date_confirmable", "")),
            "acquisition_price_unclear": normalize_yes_no_unknown(row.get("acquisition_price_unclear", "")),
            "old_acquisition": normalize_yes_no_unknown(row.get("old_acquisition", "")),
            "standard_market_price_needed": normalize_yes_no_unknown(row.get("standard_market_price_needed", "")),
            "land_grade_data_needed": normalize_yes_no_unknown(row.get("land_grade_data_needed", "")),
            "comparable_sale_review_needed": normalize_yes_no_unknown(row.get("comparable_sale_review_needed", "")),
            "appraisal_value_review_needed": normalize_yes_no_unknown(row.get("appraisal_value_review_needed", "")),
            "conversion_acquisition_value_review_needed": normalize_yes_no_unknown(row.get("conversion_acquisition_value_review_needed", "")),
            "deemed_acquisition_date_review_needed": normalize_yes_no_unknown(row.get("deemed_acquisition_date_review_needed", "")),
        },
        "expenses": {
            "expense_evidence_items": split_items(row.get("expense_evidence_items", "")),
        },
        "exception_flags": {
            "temporary_two_house_possible": normalize_yes_no_unknown(row.get("temporary_two_house_possible", "")),
            "inherited_or_gifted": normalize_yes_no_unknown(row.get("inherited_or_gifted", "")),
            "inherited_acquisition": normalize_yes_no_unknown(row.get("inherited_acquisition", "")),
            "gifted_acquisition": normalize_yes_no_unknown(row.get("gifted_acquisition", "")),
            "burdened_gift": normalize_yes_no_unknown(row.get("burdened_gift", "")),
            "redevelopment_reconstruction": normalize_yes_no_unknown(row.get("redevelopment_reconstruction", "")),
            "member_occupancy_right_conversion": normalize_yes_no_unknown(row.get("member_occupancy_right_conversion", "")),
            "joint_ownership": normalize_yes_no_unknown(row.get("joint_ownership", "")),
            "partial_share_transfer": normalize_yes_no_unknown(row.get("partial_share_transfer", "")),
            "family_transaction": normalize_yes_no_unknown(row.get("family_transaction", "")),
            "special_relation_transaction": normalize_yes_no_unknown(row.get("special_relation_transaction", "")),
            "rental_business_history": normalize_yes_no_unknown(row.get("rental_business_history", "")),
            "non_business_land_possible": normalize_yes_no_unknown(row.get("non_business_land_possible", "")),
            "mixed_use_house": normalize_yes_no_unknown(row.get("mixed_use_house", "")),
            "contract_already_signed": normalize_yes_no_unknown(row.get("contract_already_signed", "")),
            "balance_date_imminent": normalize_yes_no_unknown(row.get("balance_date_imminent", "")),
            "tax_filing_deadline_imminent": normalize_yes_no_unknown(row.get("tax_filing_deadline_imminent", "")),
            "prior_tax_consultation": normalize_yes_no_unknown(row.get("prior_tax_consultation", "")),
            "tax_office_inquiry_history": normalize_yes_no_unknown(row.get("tax_office_inquiry_history", "")),
        },
        "required_documents": {
            "registry_document": normalize_yes_no_unknown(row.get("registry_document", "")),
            "purchase_contract": normalize_yes_no_unknown(row.get("purchase_contract", "")),
            "sale_contract": normalize_yes_no_unknown(row.get("sale_contract", "")),
            "acquisition_tax_receipt": normalize_yes_no_unknown(row.get("acquisition_tax_receipt", "")),
            "resident_registration_abstract": normalize_yes_no_unknown(row.get("resident_registration_abstract", "")),
            "resident_registration_record": normalize_yes_no_unknown(row.get("resident_registration_record", "")),
            "brokerage_fee_receipts": normalize_yes_no_unknown(row.get("brokerage_fee_receipts", "")),
            "legal_scrivener_fee_receipts": normalize_yes_no_unknown(row.get("legal_scrivener_fee_receipts", "")),
            "repair_interior_evidence": normalize_yes_no_unknown(row.get("repair_interior_evidence", "")),
            "construction_contract": normalize_yes_no_unknown(row.get("construction_contract", "")),
            "appraisal_report": normalize_yes_no_unknown(row.get("appraisal_report", "")),
            "standard_market_price_docs": normalize_yes_no_unknown(row.get("standard_market_price_docs", "")),
            "land_grade_docs": normalize_yes_no_unknown(row.get("land_grade_docs", "")),
        },
        "client_confirmation": {
            "confirmed_property_info": normalize_yes_no_unknown(row.get("confirmed_property_info", "")),
            "confirmed_dates": normalize_yes_no_unknown(row.get("confirmed_dates", "")),
            "confirmed_acquisition_price_docs": normalize_yes_no_unknown(row.get("confirmed_acquisition_price_docs", "")),
            "confirmed_household_status": normalize_yes_no_unknown(row.get("confirmed_household_status", "")),
            "confirmed_exception_flags": normalize_yes_no_unknown(row.get("confirmed_exception_flags", "")),
            "unknowns_not_guessed": normalize_yes_no_unknown(row.get("unknowns_not_guessed", "")),
            "understands_not_final_tax_opinion": normalize_yes_no_unknown(row.get("understands_not_final_tax_opinion", "")),
            "signature_received": normalize_yes_no_unknown(row.get("signature_received", "")),
        },
        "memo": row.get("memo", ""),
    }
    return data

def load_json_input(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["created_at"] = datetime.now().isoformat(timespec="seconds")
    data["input_method"] = data.get("input_method") or "imported_json_template"
    return data

def load_csv_input(path, row_index=0):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV에 입력 행이 없습니다.")
    if row_index < 0 or row_index >= len(rows):
        raise IndexError(f"row_index 범위 오류: {row_index}, rows={len(rows)}")
    return csv_row_to_data(rows[row_index])

def write_case_input(case_dir, case_id, data):
    input_dir = case_dir / "00_input"
    input_dir.mkdir(exist_ok=True)
    data["case_id"] = case_id
    data["created_at"] = datetime.now().isoformat(timespec="seconds")
    json_path = input_dir / "case_input_form.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path

def write_markdown(case_dir, data):
    input_dir = case_dir / "00_input"
    input_dir.mkdir(exist_ok=True)
    md_path = input_dir / "case_input_form.md"

    lines = []
    lines.append(f"# {data.get('case_id', '')} 입력자료")
    lines.append("")
    lines.append(f"- 생성일시: {data.get('created_at', '')}")
    lines.append(f"- 입력방식: {data.get('input_method', '')}")
    lines.append("")

    for section_name, section_key in [
        ("고객 정보", "client"),
        ("부동산 정보", "property"),
        ("세대/주택 정보", "household"),
        ("거주 정보", "residence"),
        ("취득가액 정보", "acquisition_price"),
        ("필요경비 정보", "expenses"),
        ("예외사항", "exception_flags"),
        ("필요서류 제출상태", "required_documents"),
        ("고객 최종 확인", "client_confirmation"),
    ]:
        lines.append(f"## {section_name}")
        lines.append("")
        lines.append("| 항목 | 값 |")
        lines.append("|---|---|")
        section = data.get(section_key, {})
        for key, value in section.items():
            if isinstance(value, list):
                value = ", ".join(value)
            lines.append(f"| {key} | {value} |")
        lines.append("")

    lines.append("## 메모")
    lines.append("")
    lines.append(data.get("memo", "") or "없음")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

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

    meta["status"] = "00_INPUT_IMPORTED"
    meta["input_imported_at"] = datetime.now().isoformat(timespec="seconds")
    meta["client_name"] = client.get("client_name", meta.get("client_name", ""))
    meta["client_phone"] = client.get("client_phone", meta.get("client_phone", ""))
    meta["real_estate_office"] = client.get("real_estate_office", meta.get("real_estate_office", ""))
    meta["manager_name"] = client.get("manager_name", meta.get("manager_name", ""))
    meta["property_address"] = prop.get("property_address", meta.get("property_address", ""))
    meta["next_action"] = "run_case_pipeline.py --no-audio 실행"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta_path

def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager JSON/CSV 입력자료 import")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    parser.add_argument("--json", dest="json_path", help="입력 JSON 파일 경로")
    parser.add_argument("--csv", dest="csv_path", help="입력 CSV 파일 경로")
    parser.add_argument("--row-index", type=int, default=0, help="CSV에서 사용할 행 번호, 기본 0")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        if not args.json_path and not args.csv_path:
            raise ValueError("--json 또는 --csv 중 하나를 지정해야 합니다.")
        if args.json_path and args.csv_path:
            raise ValueError("--json과 --csv는 동시에 지정할 수 없습니다.")

        case_dir = get_case_dir(case_id)
        if args.json_path:
            input_path = Path(args.json_path)
            data = load_json_input(input_path)
            source_type = "json"
        else:
            input_path = Path(args.csv_path)
            data = load_csv_input(input_path, row_index=args.row_index)
            source_type = "csv"

        json_path = write_case_input(case_dir, case_id, data)
        md_path = write_markdown(case_dir, data)
        meta_path = update_case_meta(case_dir, data)

        source_dir = case_dir / "00_input" / "source"
        source_dir.mkdir(exist_ok=True)
        if input_path.exists():
            shutil.copy2(input_path, source_dir / input_path.name)

        write_log(case_id, f"imported source_type={source_type} source={input_path} output={json_path}")

        print("[SUCCESS] 입력자료 import 완료")
        print(f"[CASE_ID] {case_id}")
        print(f"[SOURCE_TYPE] {source_type}")
        print(f"[JSON] {json_path}")
        print(f"[MD] {md_path}")
        print(f"[META] {meta_path}")
        print("")
        print("[NEXT]")
        print(f"python C:\\TaxCaseManager\\run_case_pipeline.py {case_id} --no-audio")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 입력자료 import 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
