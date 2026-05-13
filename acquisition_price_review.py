import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "acquisition_price_review_log.txt"
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

def evaluate_acquisition_price(tax_data):
    facts = tax_data.get("facts", {})
    missing_items = tax_data.get("missing_items", [])
    
    acquired_price = facts.get("acquired_price", "")
    acquired_date = facts.get("acquired_date", "")
    expense_evidence = facts.get("necessary_expense_evidence", [])
    raw_sentences = facts.get("raw_evidence_sentences", [])
    
    if isinstance(expense_evidence, str):
        expense_evidence = [expense_evidence]
    if isinstance(raw_sentences, str):
        raw_sentences = [raw_sentences]
        
    has_price = bool(acquired_price and "unknown" not in acquired_price.lower() and "미확인" not in acquired_price and "모름" not in acquired_price)
    has_date = bool(acquired_date and "unknown" not in acquired_date.lower() and "미확인" not in acquired_date)
    
    price_missing = "취득가액" in missing_items
    date_missing = "취득일" in missing_items
    
    confirmed_evidence = []
    partial_evidence = []
    missing_core_evidence = ["매수계약서", "금융거래 내역", "취득세 과세표준 확인자료"]
    
    # Check raw sentences and expense_evidence for A_CONFIRMED conditions
    # A_CONFIRMED conditions: 계약서 있음, 매수계약서 있음, 금융자료 있음, 계좌이체 내역 있음, 취득세 과세표준 확인, 취득세 자료상 취득가액 확인, 실제 취득가액 증빙 확인
    all_text = " ".join([str(e) for e in expense_evidence] + [str(s) for s in raw_sentences])
    
    # Concrete proofs
    if "매수계약서 있음" in all_text or "매수계약서 제출" in all_text or "계약서 있음" in all_text or "계약서 확인" in all_text:
        confirmed_evidence.append("매수계약서 확인")
        if "매수계약서" in missing_core_evidence: missing_core_evidence.remove("매수계약서")
    
    if "금융자료 있음" in all_text or "계좌이체 내역 있음" in all_text or "이체내역" in all_text:
        confirmed_evidence.append("금융거래 내역 확인")
        if "금융거래 내역" in missing_core_evidence: missing_core_evidence.remove("금융거래 내역")
        
    if "취득세 과세표준 확인" in all_text or "취득세 자료상 취득가액 확인" in all_text or "실제 취득가액 증빙 확인" in all_text:
        confirmed_evidence.append("취득세 과세표준/취득가액 확인자료")
        if "취득세 과세표준 확인자료" in missing_core_evidence: missing_core_evidence.remove("취득세 과세표준 확인자료")

    # Partial proofs
    if "취득세 영수증" in all_text or "취득세는 냈다" in all_text or "취득세 자료는 있을 것" in all_text or "취득세" in " ".join([str(e) for e in expense_evidence]):
        partial_evidence.append("취득세 납부 진술/일부 자료")
    
    if has_price:
        partial_evidence.append("취득가액 고객 진술")
        
    if "중개수수료" in all_text:
        partial_evidence.append("중개수수료 일부 증빙")

    # Determine grade
    if not has_price and not has_date and price_missing and date_missing:
        grade = "D_HIGH_RISK"
        reason = "취득일, 취득가액 등 필수 정보가 모두 불명확함"
        needs_replacement_review = True
    elif not has_price or price_missing:
        grade = "C_REPLACEMENT_REVIEW"
        reason = "고객이 취득가액을 알지 못하며, 핵심 증빙 자료 확인 안 됨. 대체 취득가액 산정 검토 필요"
        needs_replacement_review = True
    else:
        if len(confirmed_evidence) > 0:
            grade = "A_CONFIRMED"
            reason = "취득가액 고객 진술과 함께 계약서/금융자료/과세표준 등 핵심 증빙 확인됨"
            needs_replacement_review = False
        else:
            grade = "B_PARTIAL"
            reason = "취득가액 진술과 일부 증빙 가능성은 있으나 매매계약서/금융자료/취득세 과세표준 등 핵심 증빙 확인 전"
            needs_replacement_review = False  # B_PARTIAL can conditionally need review, but let's say False for standard.

    tax_accountant_required = needs_replacement_review or grade in ["D_HIGH_RISK", "C_REPLACEMENT_REVIEW", "B_PARTIAL"]

    return {
        "confidence_grade": grade,
        "confidence_reason": reason,
        "confirmed_evidence": confirmed_evidence,
        "partial_evidence": partial_evidence,
        "missing_core_evidence": missing_core_evidence,
        "tax_accountant_required": tax_accountant_required,
        "needs_replacement_review": needs_replacement_review,
        "flags": {
            "check_deemed_acquisition_date": needs_replacement_review,
            "check_base_price": needs_replacement_review,
            "check_land_grade": needs_replacement_review
        }
    }

def write_review_outputs(case_dir, review_data):
    extract_dir = case_dir / "04_extract"
    extract_dir.mkdir(exist_ok=True)
    
    json_path = extract_dir / "acquisition_price_review.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(review_data, f, ensure_ascii=False, indent=2)
        
    missing_dir = case_dir / "05_missing"
    missing_dir.mkdir(exist_ok=True)
    
    md_path = missing_dir / "acquisition_price_missing_items.md"
    
    lines = []
    lines.append("# 취득가액 불명확 검토")
    lines.append("")
    
    grade = review_data["confidence_grade"]
    reason = review_data["confidence_reason"]
    lines.append(f"현재 취득가액 신뢰도: {grade}")
    lines.append(f"판정 사유: {reason}")
    lines.append("")
    
    if review_data["needs_replacement_review"] or grade in ["B_PARTIAL", "C_REPLACEMENT_REVIEW", "D_HIGH_RISK"]:
        lines.append("## 누락된 핵심 증빙 (보완 필요)")
        for item in review_data["missing_core_evidence"]:
            lines.append(f"- [ ] {item}")
        lines.append("")

    if review_data["needs_replacement_review"]:
        lines.append("본 사건은 실제 취득가액 또는 취득 증빙자료 확인이 불충분하여")
        lines.append("대체 취득가액 산정 가능성 검토가 필요합니다.")
        lines.append("")
        lines.append("대체 취득가액 검토 필요 항목:")
        lines.append("- 취득 당시 또는 의제취득일 기준 기준시가")
        lines.append("- 매매사례가액 가능성")
        lines.append("- 감정가액 가능성")
        lines.append("- 환산취득가액 적용 가능성")
        lines.append("")
        
    if review_data["tax_accountant_required"]:
        lines.append("주의:")
        lines.append("본 검토는 취득가액을 확정하는 것이 아니며,")
        lines.append("최종 취득가액 산정은 세무사 검토가 필수적입니다.")
        lines.append("")
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        
    return json_path, md_path

def main():
    parser = argparse.ArgumentParser(description="취득가액 불명확 사건 대체 취득가액 검토")
    parser.add_argument("case_id", help="사건번호")
    args = parser.parse_args()

    case_id = args.case_id
    
    try:
        case_dir = get_case_dir(case_id)
        tax_facts_path = case_dir / "04_extract" / "tax_facts.json"
        
        tax_data = read_json_if_exists(tax_facts_path)
        if not tax_data:
            raise ValueError("tax_facts.json 파일이 존재하지 않거나 잘못되었습니다.")
            
        review_data = evaluate_acquisition_price(tax_data)
        
        json_path, md_path = write_review_outputs(case_dir, review_data)
        
        write_log(case_id, f"acquisition_price_review_created grade={review_data['confidence_grade']}")
        
        print("[SUCCESS] 취득가액 불명확 검토 완료")
        print(f"[CASE_ID] {case_id}")
        print(f"[GRADE] {review_data['confidence_grade']}")
        print(f"[NEEDS_REPLACEMENT_REVIEW] {review_data['needs_replacement_review']}")
        print(f"[TAX_ACCOUNTANT_REQUIRED] {review_data['tax_accountant_required']}")
        print(f"[JSON] {json_path}")
        print(f"[MD] {md_path}")
        
    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 취득가액 불명확 검토 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
