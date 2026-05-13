import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "grade_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")

def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir

def read_json_if_exists(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def load_fee_policy():
    policy_path = CONFIG_DIR / "fee_policy.json"
    if not policy_path.exists():
        raise FileNotFoundError("fee_policy.json을 찾을 수 없습니다.")
    with open(policy_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_grade(case_id):
    case_dir = get_case_dir(case_id)
    
    tax_facts = read_json_if_exists(case_dir / "04_extract" / "tax_facts.json")
    acq_review = read_json_if_exists(case_dir / "04_extract" / "acquisition_price_review.json")
    multi_review = read_json_if_exists(case_dir / "04_extract" / "multi_asset_split_review.json")
    redev_review = read_json_if_exists(case_dir / "04_extract" / "redevelopment_legal_review.json")
    reg_review = read_json_if_exists(case_dir / "04_extract" / "regulated_area_check.json")
    
    reasons = []
    grade = "A"
    
    case_type = tax_facts.get("case_type", "")
    facts = tax_facts.get("facts", {})
    missing_items = tax_facts.get("missing_items", [])
    
    is_redev = (
        "재건축" in case_type or "재개발" in case_type or "입주권" in case_type or "분양권" in case_type or
        redev_review.get("needs_redev_review") or multi_review.get("multi_asset_review_required")
    )
    
    is_acq_unclear = acq_review.get("tax_accountant_required") or acq_review.get("needs_replacement_review")
    
    # D Grade checks
    if is_redev:
        reasons.append("재개발/재건축 사건")
        grade = "D"
    if multi_review.get("multi_asset_review_required"):
        reasons.append("기존 1주택에서 2개 이상 아파트/입주권 발생")
        grade = "D"
    if "장기임대주택" in case_type and "거주주택 비과세" in case_type:
        reasons.append("장기임대주택 특례와 거주주택 비과세 동시 검토")
        grade = "D"
    if reg_review.get("tax_review_required"):
        # Adjusting the phrasing to closely match typical cases like DEMO-20260511-001
        reasons.append("조정대상지역 기준일별 확인 필요")
        if grade != "D": grade = "D"  # Just to ensure D
    sale_expected_price_raw = facts.get("sale_expected_price", 0)
    try:
        sale_expected_price = int(sale_expected_price_raw)
    except (ValueError, TypeError):
        sale_expected_price = 0

    if is_acq_unclear and sale_expected_price > 1000000000:
        reasons.append("취득가액 불명확 + 고액 양도")
        grade = "D"
        
    # C Grade checks
    if grade < "C":
        if is_acq_unclear:
            reasons.append("취득가액 불명확")
            grade = "C"
        elif "장기임대주택" in case_type:
            reasons.append("장기임대주택 검토")
            grade = "C"
        elif "상속" in case_type or "증여" in case_type:
            reasons.append("상속/증여 특례 검토")
            grade = "C"
        elif "다주택" in case_type:
            reasons.append("다주택 가능성")
            grade = "C"
        elif sale_expected_price > 1200000000:
            reasons.append("고가주택(12억 초과)")
            grade = "C"
        elif facts.get("necessary_expense_evidence") == "yes":
            # Just an indicator for multiple expenses
            reasons.append("필요경비 증빙 다수")
            grade = "C"
            
    # B Grade checks
    if grade < "B":
        if facts.get("joint_ownership") == "yes":
            reasons.append("공동명의")
            grade = "B"
        elif missing_items:
            reasons.append("일부 보완자료 필요")
            grade = "B"
        elif facts.get("residence_period") in ["미확인", "모름", "", None]:
            reasons.append("거주기간 확인 필요")
            grade = "B"
            
    # Default is A
    if grade == "A":
        reasons.append("단순 1물건 검토")
        
    policy = load_fee_policy()
    grade_info = policy.get("grades", {}).get(grade, {})
    
    notice_text = "본 사건은 단순 사건으로 기본 진단이 가능합니다."
    if grade == "D":
        notice_text = "본 사건은 고위험 사건으로 세무사 검토가 필수입니다."
    elif grade == "C":
        notice_text = "본 사건은 복합 검토 사건으로 세무사 검토가 강력 권장됩니다."
    elif grade == "B":
        notice_text = "본 사건은 확인이 필요한 일반 사건입니다."

    result = {
        "case_id": case_id,
        "grade": grade,
        "color": grade_info.get("color"),
        "grade_name": grade_info.get("grade_name"),
        "tax_accountant_required": grade_info.get("tax_accountant_required"),
        "recommended_report_fee": grade_info.get("report_fee"),
        "recommended_tax_review_fee": grade_info.get("tax_review_fee"),
        "tax_filing_fee": grade_info.get("tax_filing_fee"),
        "reasons": reasons,
        "customer_notice": notice_text,
        "fee_notice": policy.get("common_notice")
    }
    
    output_path = case_dir / "04_extract" / "case_risk_grade.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    return output_path, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    args = parser.parse_args()
    
    case_id = args.case_id
    try:
        path, result = evaluate_grade(case_id)
        write_log(case_id, f"grade_evaluated grade={result['grade']} color={result['color']}")
        print(f"[SUCCESS] 사건등급 판정 완료: {path}")
        print(f"[GRADE] {result['grade']} / {result['color']}")
    except Exception as e:
        write_log(case_id, f"ERROR: {e}")
        print(f"[FAIL] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
