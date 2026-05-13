import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "redevelopment_log.txt"
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

def build_redev_review():
    return """## 도시 및 주거환경정비법상 확인사항

본 사건은 단독주택이 재건축사업을 거쳐 2개의 아파트로 전환된 사건입니다.
따라서 양도소득세 판단과 별도로 도시 및 주거환경정비법상 정비사업 사실관계를 확인해야 합니다.

확인할 도정법상 사실관계:
- 정비사업 종류
- 조합설립인가일
- 사업시행인가일
- 관리처분계획인가일
- 권리가액
- 추가분담금
- 청산금 여부
- 신축주택 배정 수
- 준공검사일
- 이전고시일
- 개별등기일

도정법상 사실관계는 세법상 취득시기, 조합원입주권 전환 시점, 물건별 취득가액 배분, 양도차익 구분에 영향을 줄 수 있습니다."""

def review_redevelopment(case_id):
    case_dir = get_case_dir(case_id)
    tax_facts_path = case_dir / "04_extract" / "tax_facts.json"
    
    tax_facts = read_json_if_exists(tax_facts_path)
    case_type = tax_facts.get("case_type", "")
    
    is_redev = "재건축" in case_type or "재개발" in case_type or "입주권" in case_type or "분양권" in case_type
    
    result = {
        "case_id": case_id,
        "is_redevelopment_case": is_redev,
        "review_text": build_redev_review() if is_redev else "",
        "needs_redev_review": is_redev,
        "timestamp": datetime.now().isoformat()
    }
    
    output_path = case_dir / "04_extract" / "redevelopment_legal_review.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    return output_path, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    args = parser.parse_args()
    
    case_id = args.case_id
    try:
        path, result = review_redevelopment(case_id)
        write_log(case_id, f"redevelopment_review_completed is_redev={result['is_redevelopment_case']}")
        print(f"[SUCCESS] 재개발/재건축 검토 완료: {path}")
    except Exception as e:
        write_log(case_id, f"ERROR: {e}")
        print(f"[FAIL] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
