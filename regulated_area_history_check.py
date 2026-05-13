import argparse
import json
import csv
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"
HISTORY_CSV_PATH = BASE_DIR / "data" / "regulated_area_history.csv"

SIDO_ALIASES = {
    "서울": "서울특별시",
    "서울시": "서울특별시",
    "부산": "부산광역시",
    "부산시": "부산광역시",
    "대구": "대구광역시",
    "대구시": "대구광역시",
    "인천": "인천광역시",
    "인천시": "인천광역시",
    "광주": "광주광역시",
    "광주시": "광주광역시",
    "대전": "대전광역시",
    "대전시": "대전광역시",
    "울산": "울산광역시",
    "울산시": "울산광역시",
    "세종": "세종특별자치시",
    "세종시": "세종특별자치시",
    "경기": "경기도",
    "경기도": "경기도",
    "강원": "강원특별자치도",
    "강원도": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
    "제주도": "제주특별자치도"
}

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "regulated_area_history_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")

def read_json_if_exists(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def normalize_date(date_str):
    if not date_str:
        return ""
    
    # Try to find year, month, day with regex
    match = re.search(r'(\d{4})\D+(\d{1,2})\D+(\d{1,2})', date_str)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        
    s = re.sub(r'[^0-9]', '', date_str)
    if len(s) == 8:
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return date_str

def normalize_address_for_region(address):
    text = str(address or "").strip()
    text = text.replace("  ", " ")

    tokens = text.split()
    if not tokens:
        return {
            "sido": "",
            "sigungu": "",
            "region_name": "",
            "raw_address": address
        }

    sido = ""
    sigungu = ""

    # 시도 추출
    first = tokens[0]
    if first in SIDO_ALIASES:
        sido = SIDO_ALIASES[first]
        if len(tokens) >= 2:
            sigungu = tokens[1]
    else:
        # 시도 없이 강남구처럼 들어온 경우
        for token in tokens:
            if token.endswith("구") or token.endswith("시") or token.endswith("군"):
                sigungu = token
                break

    # 서울 구 단독 입력 보정
    SEOUL_GU = {
        "강남구", "서초구", "송파구", "강동구", "마포구", "용산구", "성동구",
        "광진구", "동대문구", "중랑구", "성북구", "강북구", "도봉구",
        "노원구", "은평구", "서대문구", "양천구", "강서구", "구로구",
        "금천구", "영등포구", "동작구", "관악구", "종로구", "중구"
    }

    if not sido and sigungu in SEOUL_GU:
        sido = "서울특별시"

    region_name = f"{sido} {sigungu}".strip()

    return {
        "sido": sido,
        "sigungu": sigungu,
        "region_name": region_name,
        "raw_address": address
    }

def load_history():
    history = []
    if not HISTORY_CSV_PATH.exists():
        return history
    with open(HISTORY_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            history.append(row)
    return history

def find_basis_date(form_data, tax_facts):
    redev_details = form_data.get("redevelopment_details", tax_facts.get("facts", {}).get("redevelopment_details", {}))
    is_redev = redev_details.get("is_redevelopment_case") == "yes" or tax_facts.get("facts", {}).get("exception_details", {}).get("redevelopment_reconstruction") == "yes"
    
    if is_redev:
        date = redev_details.get("management_disposal_approval_date")
        if date:
            return normalize_date(date), "management_disposal_approval_date"

    # 일반 주택
    date = form_data.get("property", {}).get("acquired_date")
    if not date:
        date = tax_facts.get("facts", {}).get("acquired_date")
        
    if date:
        return normalize_date(date), "acquired_date"

    return "", "unknown"

def check_regulated_area(norm_region, basis_date, history):
    region_name = norm_region["region_name"]
    sido = norm_region["sido"]
    sigungu = norm_region["sigungu"]
    raw_address = str(norm_region["raw_address"] or "")

    if not region_name or not basis_date:
        return "unknown", "D_NEEDS_MANUAL_REVIEW", "주소 또는 기준일이 불명확하여 조정대상지역 여부를 자동 판정할 수 없습니다.", ""

    try:
        b_date = datetime.strptime(basis_date, "%Y-%m-%d")
    except ValueError:
        return "unknown", "D_NEEDS_MANUAL_REVIEW", f"날짜 형식을 파싱할 수 없습니다: {basis_date}", ""

    matched_records = []
    for row in history:
        db_region = row["region_name"]
        db_sido = row["sido"]
        db_sigungu = row["sigungu"]
        
        is_match = False
        if db_region == region_name:
            is_match = True
        elif sido and sigungu and db_sido == sido and db_sigungu == sigungu:
            is_match = True
        elif db_region and db_region in raw_address:
            is_match = True
        elif sigungu and db_sigungu == sigungu:
            is_match = True
            
        if is_match:
            matched_records.append(row)
            
    if not matched_records:
        return "unknown", "D_NEEDS_MANUAL_REVIEW", "DB에 해당 지역의 이력이 없습니다. 수동 확인이 필요합니다.", ""
        
    # Sort by start_date
    matched_records.sort(key=lambda x: x["start_date"] if x["start_date"] else "")
    
    for row in matched_records:
        if row["status"] == "RELEASED":
            # Check if released before basis date
            if row["start_date"]:
                r_date = datetime.strptime(row["start_date"], "%Y-%m-%d")
                if b_date >= r_date:
                    return False, "A_MATCHED_HISTORY_DB", "기준일이 조정대상지역 해제일 이후입니다.", row["notice_no"]
        elif row["status"] == "ACTIVE":
            if row["start_date"]:
                s_date = datetime.strptime(row["start_date"], "%Y-%m-%d")
                e_date = datetime.strptime(row["end_date"], "%Y-%m-%d") if row["end_date"] else datetime.max
                if s_date <= b_date <= e_date:
                    return True, "A_MATCHED_HISTORY_DB", "기준일이 조정대상지역 ACTIVE 기간에 포함됩니다.", row["notice_no"]
                    
    return "unknown", "D_NEEDS_MANUAL_REVIEW", "해당 기간에 대한 명확한 지정/해제 이력을 찾을 수 없습니다.", ""

def write_result(case_dir, case_id, result):
    out_dir = case_dir / "04_extract"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "regulated_area_check.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    args = parser.parse_args()

    case_id = args.case_id
    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        print(f"Error: case {case_id} not found")
        return

    try:
        form_data = read_json_if_exists(case_dir / "00_input" / "case_input_form.json")
        tax_facts = read_json_if_exists(case_dir / "04_extract" / "tax_facts.json")
        
        address = form_data.get("property", {}).get("property_address") or tax_facts.get("facts", {}).get("property_address")
        norm_region = normalize_address_for_region(address)
        
        basis_date, date_type = find_basis_date(form_data, tax_facts)
        
        history = load_history()
        
        is_regulated, confidence, reason, notice = check_regulated_area(norm_region, basis_date, history)
        
        result = {
            "case_id": case_id,
            "basis_date_type": date_type,
            "basis_date": basis_date,
            "region": norm_region["region_name"],
            "raw_address": address,
            "normalized_region": norm_region["region_name"],
            "is_adjustment_target_area": is_regulated,
            "confidence": confidence,
            "source_notice": notice,
            "tax_review_required": is_regulated == "unknown" or is_regulated is True,
            "reason": reason
        }
        
        out_path = write_result(case_dir, case_id, result)
        
        write_log(case_id, f"regulated_area check: {is_regulated} conf: {confidence}")
        print(f"[SUCCESS] 조정대상지역 조회 완료 -> {out_path}")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    main()
