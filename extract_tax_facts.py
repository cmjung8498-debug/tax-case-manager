import argparse
import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

REQUIRED_FIELDS = [
    "property_address",
    "acquired_date",
    "acquired_price",
    "sale_expected_date",
    "sale_expected_price",
    "current_house_count",
    "spouse_house_owned",
    "household_member_house_owned",
    "residence_period",
    "inherited_house",
    "presale_right_or_occupancy_right",
    "necessary_expense_evidence",
]


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


def read_transcript(case_dir):
    transcript_path = case_dir / "02_transcript" / "transcript.txt"
    if not transcript_path.exists():
        raise FileNotFoundError(f"transcript.txt를 찾을 수 없습니다: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError("transcript.txt가 비어 있습니다.")

    return transcript_path, text


def find_input_source(case_dir):
    form_path = case_dir / "00_input" / "case_input_form.json"
    if form_path.exists():
        return "form_json_v1", form_path
    
    transcript_path = case_dir / "02_transcript" / "transcript.txt"
    if transcript_path.exists():
        return "transcript_v1", transcript_path
        
    raise FileNotFoundError("입력 소스를 찾을 수 없습니다 (transcript.txt 또는 case_input_form.json 필요)")

def read_form_input(form_path):
    with open(form_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_facts_from_form(data):
    prop = data.get("property", {})
    household = data.get("household", {})
    residence = data.get("residence", {})
    acq = data.get("acquisition_price", {})
    expenses = data.get("expenses", {})
    exceptions = data.get("exception_flags", {})

    required_docs = data.get("required_documents", {})
    client_conf = data.get("client_confirmation", {})

    presale = household.get("presale_right_owned", "unknown")
    occupancy = household.get("occupancy_right_owned", "unknown")

    if presale == "yes" or occupancy == "yes":
        presale_or_occupancy = "yes"
    elif presale == "no" and occupancy == "no":
        presale_or_occupancy = "no"
    else:
        presale_or_occupancy = "unknown"

    facts = {
        "property_address": prop.get("property_address", ""),
        "property_type": prop.get("property_type", ""),
        "acquired_date": prop.get("acquired_date", ""),
        "acquired_price": prop.get("acquired_price", ""),
        "sale_expected_date": prop.get("sale_expected_date", ""),
        "sale_expected_price": prop.get("sale_expected_price", ""),
        "current_house_count": household.get("current_house_count", ""),
        "spouse_house_owned": household.get("spouse_house_owned", "unknown"),
        "household_member_house_owned": household.get("household_member_house_owned", "unknown"),
        "residence_period": residence.get("residence_period", ""),
        "lived_in": residence.get("lived_in", "unknown"),
        "resident_registration_available": residence.get("resident_registration_available", "unknown"),
        "inherited_house": household.get("inherited_house_owned", "unknown"),
        "presale_right_or_occupancy_right": presale_or_occupancy,
        "necessary_expense_evidence": expenses.get("expense_evidence_items", []),

        "purchase_contract_available": acq.get("purchase_contract_available", "unknown"),
        "bank_transfer_records_available": acq.get("bank_transfer_records_available", "unknown"),
        "acquisition_tax_records_available": acq.get("acquisition_tax_records_available", "unknown"),
        "acquisition_tax_base_visible": acq.get("acquisition_tax_base_visible", "unknown"),
        "acquisition_price_unclear": acq.get("acquisition_price_unclear", "unknown"),

        "temporary_two_house_possible": exceptions.get("temporary_two_house_possible", "unknown"),
        "inherited_or_gifted": exceptions.get("inherited_or_gifted", "unknown"),
        "redevelopment_reconstruction": exceptions.get("redevelopment_reconstruction", "unknown"),
        "joint_ownership": exceptions.get("joint_ownership", "unknown"),
        "rental_business_history": exceptions.get("rental_business_history", "unknown"),
        "special_relation_transaction": exceptions.get("special_relation_transaction", "unknown"),

        "property_details": prop,
        "exception_details": exceptions,
        "redevelopment_details": data.get("redevelopment_details", {}),
        "asset_units": data.get("asset_units", []),
        "required_documents": required_docs,
        "client_confirmation": client_conf,

        "raw_evidence_sentences": [],
    }

    return facts


def find_first(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()
    return ""


def yes_no_unknown(text, yes_keywords=None, no_keywords=None, unknown_keywords=None):
    yes_keywords = yes_keywords or []
    no_keywords = no_keywords or []
    unknown_keywords = unknown_keywords or ["모른", "확인하지 못", "미확인", "아직 확인"]

    for kw in unknown_keywords:
        if kw in text:
            return "unknown"

    for kw in no_keywords:
        if kw in text:
            return "no"

    for kw in yes_keywords:
        if kw in text:
            return "yes"

    return "unknown"


def extract_basic_facts(text):
    facts = {
        "property_address": "",
        "acquired_date": "",
        "acquired_price": "",
        "sale_expected_date": "",
        "sale_expected_price": "",
        "current_house_count": "",
        "spouse_house_owned": "unknown",
        "household_member_house_owned": "unknown",
        "residence_period": "",
        "inherited_house": "unknown",
        "presale_right_or_occupancy_right": "unknown",
        "necessary_expense_evidence": [],
        "raw_evidence_sentences": [],
    }

    # 주소 후보
    facts["property_address"] = find_first([
        r"([가-힣A-Za-z0-9\s]+(?:구|시|군)[가-힣A-Za-z0-9\s]*아파트)",
        r"([가-힣A-Za-z0-9\s]+(?:아파트|주택|빌라|오피스텔))",
    ], text)

    # 취득일 후보
    facts["acquired_date"] = find_first([
        r"취득일은\s*([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)",
        r"([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일).*취득",
    ], text)

    # 취득가액 후보
    facts["acquired_price"] = find_first([
        r"취득가액은\s*(약\s*)?([0-9]+억\s*원)",
        r"취득가액은\s*(약\s*)?([0-9,]+만\s*원)",
    ], text)

    # 위 패턴에서 group 문제 보정
    if isinstance(facts["acquired_price"], str) and facts["acquired_price"] == "약":
        facts["acquired_price"] = ""

    m = re.search(r"취득가액은\s*(?:약\s*)?([0-9]+억\s*원)", text)
    if m:
        facts["acquired_price"] = m.group(1).strip()

    # 양도 예정가액 후보
    m = re.search(r"양도\s*예정가액은\s*([0-9]+억\s*원)", text)
    if m:
        facts["sale_expected_price"] = m.group(1).strip()
    else:
        m = re.search(r"([0-9]+억\s*원)\s*정도로\s*예상", text)
        if m:
            facts["sale_expected_price"] = m.group(1).strip()

    # 양도 예정일은 테스트 문장에 없으면 미확인
    facts["sale_expected_date"] = find_first([
        r"양도\s*예정일은\s*([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)",
        r"매도\s*예정일은\s*([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)",
    ], text)

    # 거주기간
    facts["residence_period"] = find_first([
        r"실제\s*거주는\s*(약\s*)?([0-9]+년\s*[0-9]+개월)",
        r"거주.*?([0-9]+년\s*[0-9]+개월)",
        r"([0-9]+년\s*[0-9]+개월)\s*정도\s*했",
    ], text)
    m = re.search(r"실제\s*거주는\s*(?:약\s*)?([0-9]+년\s*[0-9]+개월)", text)
    if m:
        facts["residence_period"] = m.group(1).strip()

    # 현재 보유 주택 수
    if "1채" in text or "1주택" in text or "한 채" in text:
        facts["current_house_count"] = "1"
    elif "2채" in text or "2주택" in text:
        facts["current_house_count"] = "2"

    # 배우자 명의 주택
    if "배우자" in text:
        spouse_context = text[text.find("배우자"): text.find("배우자") + 80]
        facts["spouse_house_owned"] = yes_no_unknown(
            spouse_context,
            yes_keywords=["있다", "보유"],
            no_keywords=["없다", "없다고"],
            unknown_keywords=["확인하지 못", "모른", "미확인"]
        )

    # 세대원 주택
    if "세대원" in text or "자녀" in text:
        idx = min([i for i in [text.find("세대원"), text.find("자녀")] if i != -1])
        hh_context = text[idx: idx + 120]
        facts["household_member_house_owned"] = yes_no_unknown(
            hh_context,
            yes_keywords=["있다", "가지고"],
            no_keywords=["없다", "없다고"],
            unknown_keywords=["모른", "확인하지 못", "미확인"]
        )

    # 상속주택
    if "상속" in text:
        idx = text.find("상속")
        context = text[idx: idx + 80]
        facts["inherited_house"] = yes_no_unknown(
            context,
            yes_keywords=["있다", "받은"],
            no_keywords=["없다", "없다고"],
            unknown_keywords=["모른", "확인하지 못", "미확인"]
        )

    # 분양권/입주권
    if "분양권" in text or "입주권" in text:
        idxs = [i for i in [text.find("분양권"), text.find("입주권")] if i != -1]
        idx = min(idxs)
        context = text[idx: idx + 100]
        facts["presale_right_or_occupancy_right"] = yes_no_unknown(
            context,
            yes_keywords=["있다", "보유"],
            no_keywords=["없다", "없다고"],
            unknown_keywords=["모른", "확인하지 못", "미확인"]
        )

    # 필요경비 증빙
    expense_items = []
    for kw in ["중개수수료", "취득세", "법무사비", "인테리어", "수리비"]:
        if kw in text:
            expense_items.append(kw)
    facts["necessary_expense_evidence"] = expense_items

    # 증거 문장 후보
    sentences = re.split(r"[.\n]", text)
    facts["raw_evidence_sentences"] = [
        s.strip() for s in sentences
        if any(kw in s for kw in ["취득", "양도", "거주", "주택", "배우자", "세대원", "상속", "분양권", "입주권", "필요경비", "중개수수료", "취득세"])
    ]

    return facts


def build_missing_items(facts):
    labels = {
        "property_address": "매도 예정 부동산 주소",
        "acquired_date": "취득일",
        "acquired_price": "취득가액",
        "sale_expected_date": "양도 예정일",
        "sale_expected_price": "양도 예정가액",
        "current_house_count": "현재 보유 주택 수",
        "spouse_house_owned": "배우자 명의 주택 보유 여부",
        "household_member_house_owned": "세대원 주택 보유 여부",
        "residence_period": "실제 거주기간",
        "inherited_house": "상속주택 여부",
        "presale_right_or_occupancy_right": "분양권/입주권 여부",
        "necessary_expense_evidence": "필요경비 증빙자료",
    }

    missing = []

    for key in REQUIRED_FIELDS:
        value = facts.get(key)

        if value is None:
            missing.append(labels[key])
        elif value == "":
            missing.append(labels[key])
        elif value == "unknown":
            missing.append(labels[key])
        elif isinstance(value, list) and len(value) == 0:
            missing.append(labels[key])

    return missing


def estimate_case_type(facts):
    if facts.get("current_house_count") == "1":
        if facts.get("sale_expected_price") and "13억" in facts.get("sale_expected_price"):
            return "1세대 1주택 고가주택 가능성"
        return "1세대 1주택 비과세 검토 가능성"

    if facts.get("current_house_count") == "2":
        return "일시적 2주택 또는 다주택 쟁점 가능성"

    return "사건유형 미확정"


def estimate_risk_level(facts, missing_items):
    if len(missing_items) >= 5:
        return "RED"

    if facts.get("spouse_house_owned") == "unknown" or facts.get("household_member_house_owned") == "unknown":
        return "ORANGE"

    if missing_items:
        return "YELLOW"

    return "GREEN"


def write_outputs(case_dir, case_id, input_method, input_path, facts, missing_items):
    extract_dir = case_dir / "04_extract"
    missing_dir = case_dir / "05_missing"
    extract_dir.mkdir(exist_ok=True)
    missing_dir.mkdir(exist_ok=True)

    case_type = estimate_case_type(facts)
    risk_level = estimate_risk_level(facts, missing_items)

    result = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_source": input_method,
        "source_input_file": str(input_path),
        "extract_method": input_method,
        "case_type": case_type,
        "risk_level": risk_level,
        "facts": facts,
        "missing_items": missing_items,
        "verdict": "세무판단 확정 아님. 사실관계 정리 및 누락자료 확인 단계.",
    }
    
    if input_method == "transcript_v1":
        result["source_transcript"] = str(input_path)

    json_path = extract_dir / "tax_facts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    missing_path = missing_dir / "missing_items.md"
    lines = []
    lines.append(f"# {case_id} 누락자료 및 추가확인 목록\n")
    lines.append(f"- 사건유형 추정: {case_type}")
    lines.append(f"- 위험등급: {risk_level}")
    lines.append("")
    lines.append("## 추가 확인 필요 항목")
    if missing_items:
        for item in missing_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 현재 1차 필수항목 기준 누락 없음")
    lines.append("")
    lines.append("## 주의")
    lines.append("이 결과는 세무 판단 확정이 아니며, 고객 진술 기반의 1차 사실관계 정리 결과이다.")
    lines.append("미확인 항목은 부동산 사무실에서 고객에게 재확인해야 한다.")

    with open(missing_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return json_path, missing_path, case_type, risk_level


def update_case_meta(case_dir, case_type, risk_level):
    meta_path = case_dir / "case_meta.json"
    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["status"] = "03_EXTRACTED"
        meta["extracted_at"] = datetime.now().isoformat(timespec="seconds")
        meta["case_type"] = case_type
        meta["risk_level"] = risk_level
        meta["next_action"] = "missing_items.md 기준으로 부동산 사무실에 보완자료 요청"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(case_dir.name, f"case_meta update failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 양도세 사실관계 추출기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        case_dir = get_case_dir(case_id)
        
        input_method, input_path = find_input_source(case_dir)

        print("[START] 양도세 사실관계 추출 시작")
        print(f"[CASE_ID] {case_id}")
        print(f"[INPUT_SOURCE] {input_method}")
        print(f"[INPUT_FILE] {input_path}")

        if input_method == "form_json_v1":
            form_data = read_form_input(input_path)
            facts = extract_facts_from_form(form_data)
            missing_items = build_missing_items(facts)
        else:
            _, text = read_transcript(case_dir)
            facts = extract_basic_facts(text)
            missing_items = build_missing_items(facts)

        json_path, missing_path, case_type, risk_level = write_outputs(
            case_dir,
            case_id,
            input_method,
            input_path,
            facts,
            missing_items
        )

        update_case_meta(case_dir, case_type, risk_level)

        write_log(case_id, f"extracted case_type={case_type} risk_level={risk_level} missing_count={len(missing_items)}")

        print("[SUCCESS] 양도세 사실관계 추출 완료")
        print(f"[CASE_TYPE] {case_type}")
        print(f"[RISK_LEVEL] {risk_level}")
        print(f"[MISSING_COUNT] {len(missing_items)}")
        print(f"[JSON] {json_path}")
        print(f"[MISSING] {missing_path}")
        print("")
        print("[NEXT]")
        print(f"python C:\\TaxCaseManager\\generate_tax_report.py {case_id}")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 양도세 사실관계 추출 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
