import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "extract_log.txt"
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
    except:
        return {}

def check_multi_asset(form_data, tax_facts):
    # Try to find redevelopment details and asset units in form data or tax facts
    redev_details = form_data.get("redevelopment_details", tax_facts.get("facts", {}).get("redevelopment_details", {}))
    asset_units = form_data.get("asset_units", tax_facts.get("facts", {}).get("asset_units", []))
    
    # Also check exception flags
    exception_flags = form_data.get("exception_flags", tax_facts.get("facts", {}).get("exception_details", {}))
    
    is_redev = exception_flags.get("redevelopment_reconstruction") == "yes" or redev_details.get("is_redevelopment_case") == "yes"
    
    rights_count = str(redev_details.get("rights_count", ""))
    new_units_count = str(redev_details.get("new_units_count", ""))
    
    multi_asset = False
    if rights_count and rights_count.isdigit() and int(rights_count) >= 2:
        multi_asset = True
    elif new_units_count and new_units_count.isdigit() and int(new_units_count) >= 2:
        multi_asset = True
    elif redev_details.get("one_house_to_multiple_rights") == "yes":
        multi_asset = True
    elif len(asset_units) >= 2:
        multi_asset = True
        
    return is_redev, multi_asset, redev_details, asset_units

def build_missing_items(asset_units):
    asset_results = []
    
    if not asset_units:
        # Create dummy units if not provided but multi asset detected
        asset_units = [
            {"asset_id": "A", "asset_name": "신축아파트 또는 입주권 1"},
            {"asset_id": "B", "asset_name": "신축아파트 또는 입주권 2"}
        ]
        
    for asset in asset_units:
        missing = []
        if not asset.get("expected_sale_price"):
            missing.append(f"{asset.get('asset_id', '')}물건 양도예정가액")
        if not asset.get("acquisition_cost_allocation"):
            missing.append(f"{asset.get('asset_id', '')}물건 취득가액 배분")
        if not asset.get("expense_allocation"):
            missing.append(f"{asset.get('asset_id', '')}물건 필요경비 배분")
            
        asset_results.append({
            "asset_id": asset.get("asset_id", ""),
            "review_required": True,
            "missing_items": missing
        })
        
    return asset_results

def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 다중 물건/분양권 분리 검토기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        case_dir = get_case_dir(case_id)
        print("[START] 물건별 분리 검토 시작")
        print(f"[CASE_ID] {case_id}")

        form_path = case_dir / "00_input" / "case_input_form.json"
        tax_path = case_dir / "04_extract" / "tax_facts.json"
        
        form_data = read_json_if_exists(form_path)
        tax_facts = read_json_if_exists(tax_path)
        
        is_redev, multi_asset, redev_details, asset_units = check_multi_asset(form_data, tax_facts)
        
        extract_dir = case_dir / "04_extract"
        missing_dir = case_dir / "05_missing"
        extract_dir.mkdir(exist_ok=True)
        missing_dir.mkdir(exist_ok=True)
        
        json_path = extract_dir / "multi_asset_split_review.json"
        missing_path = missing_dir / "multi_asset_missing_items.md"
        
        if multi_asset or is_redev:
            # Generate the review result
            reason = "기존 1주택에서 2개 이상의 입주권/신축 아파트가 발생한 가능성이 있음" if multi_asset else "재개발/재건축/입주권 사건으로 확인됨"
            
            asset_results = build_missing_items(asset_units) if multi_asset else []
            
            result = {
                "case_id": case_id,
                "multi_asset_review_required": multi_asset,
                "is_redevelopment": is_redev,
                "reason": reason,
                "tax_accountant_required": True,
                "required_checks": [
                    "관리처분계획인가일 확인",
                    "관리처분인가일 당시 조정대상지역 여부 확인",
                    "입주권/분양권 수 확인",
                    "각 물건별 양도가액 확인",
                    "각 물건별 취득가액/필요경비 배분 확인",
                    "양도 순서 확인",
                    "실거주 요건 검토"
                ],
                "asset_units": asset_results
            }
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            # Create missing items md
            lines = [f"# {case_id} 물건별 추가 확인 목록\n"]
            lines.append(f"- 사유: {reason}")
            lines.append("- 세무사 필수 검토: Y\n")
            lines.append("## 필수 검토 항목")
            for req in result["required_checks"]:
                lines.append(f"- {req}")
                
            if asset_results:
                lines.append("\n## 물건별 누락 자료")
                for asset in asset_results:
                    lines.append(f"### {asset['asset_id']} 물건")
                    if asset["missing_items"]:
                        for m in asset["missing_items"]:
                            lines.append(f"- {m}")
                    else:
                        lines.append("- 누락 항목 없음")
                        
            with open(missing_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
                
            print(f"[DETECTED] 재개발 또는 다중 물건 감지됨: {reason}")
            write_log(case_id, "multi_asset_split_review detected")
        else:
            # Not a multi-asset or redev case, just create dummy empty file
            result = {
                "case_id": case_id,
                "multi_asset_review_required": False,
                "is_redevelopment": False,
                "reason": "해당 없음",
                "tax_accountant_required": False
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            with open(missing_path, "w", encoding="utf-8") as f:
                f.write("해당 없음\n")
            print("[SKIP] 일반 주택 사건으로 다중 물건 검토 불필요")
            write_log(case_id, "multi_asset_split_review skipped")

        print("[SUCCESS] 물건별 분리 검토 완료")
        print(f"[JSON] {json_path}")
        print(f"[MISSING] {missing_path}")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 물건별 분리 검토 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
