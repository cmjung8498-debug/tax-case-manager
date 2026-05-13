import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"


DOCUMENT_GUIDE = {
    "매도 예정 부동산 주소": [
        "매도 예정 부동산의 정확한 주소",
        "가능하면 등기부등본 또는 건축물대장"
    ],
    "취득일": [
        "매수 계약서",
        "등기부등본",
        "취득세 납부 확인서"
    ],
    "취득가액": [
        "매수 계약서",
        "취득 당시 거래금액 확인 자료"
    ],
    "양도 예정일": [
        "매도 예정일 또는 잔금 예정일",
        "매도 계약서가 있으면 계약서 사본"
    ],
    "양도 예정가액": [
        "매도 예정금액",
        "매도 계약서가 있으면 계약서 사본"
    ],
    "현재 보유 주택 수": [
        "본인 명의 보유 주택 현황",
        "필요 시 재산세 고지서 또는 등기부 확인"
    ],
    "배우자 명의 주택 보유 여부": [
        "배우자 명의 주택 보유 여부 확인",
        "보유 중이면 해당 주택 주소와 취득일"
    ],
    "세대원 주택 보유 여부": [
        "같은 세대에 속한 가족의 주택 보유 여부",
        "필요 시 주민등록등본 기준 세대원 확인"
    ],
    "실제 거주기간": [
        "주민등록초본",
        "전입일과 전출일 확인",
        "실제 거주기간 확인 자료"
    ],
    "상속주택 여부": [
        "상속받은 주택 보유 여부",
        "상속주택이 있으면 상속일, 지분, 주소"
    ],
    "분양권/입주권 여부": [
        "보유 중인 분양권 또는 입주권 여부",
        "있으면 계약서 또는 관련 확인 자료"
    ],
    "필요경비 증빙자료": [
        "중개수수료 영수증",
        "취득세 납부확인서",
        "법무사 비용 영수증",
        "인테리어/수리비 중 자본적 지출 증빙"
    ],
}


def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "missing_request_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_kakao_message(case_id, meta, tax_data):
    missing_items = tax_data.get("missing_items", [])
    case_type = tax_data.get("case_type", "미확정")
    risk_level = tax_data.get("risk_level", "미확정")

    client_name = meta.get("client_name", "") or "고객님"
    property_address = tax_data.get("facts", {}).get("property_address") or meta.get("property_address", "") or "매도 예정 부동산"

    lines = []

    lines.append(f"{client_name}, 안녕하세요.")
    lines.append("양도세 사전검토를 위해 상담 내용을 1차 정리했습니다.")
    lines.append("")
    lines.append(f"사건번호: {case_id}")
    lines.append(f"검토유형: {case_type}")
    lines.append(f"현재 위험등급: {risk_level}")
    lines.append(f"대상 부동산: {property_address}")
    lines.append("")

    if not missing_items:
        lines.append("현재 1차 필수 확인 항목 기준으로는 추가 요청 자료가 없습니다.")
        lines.append("다만 세무사 검토 과정에서 추가 자료 요청이 있을 수 있습니다.")
    else:
        lines.append("정확한 검토를 위해 아래 내용을 추가로 확인 부탁드립니다.")
        lines.append("")

        for idx, item in enumerate(missing_items, start=1):
            lines.append(f"{idx}. {item}")
            guides = DOCUMENT_GUIDE.get(item, [])
            for guide in guides[:3]:
                lines.append(f"   - {guide}")

    lines.append("")
    lines.append("※ 현재 단계는 세금 확정 판단이 아니라, 세무사 검토 전 사실관계와 증빙자료를 정리하는 단계입니다.")
    lines.append("※ 확인되지 않은 내용이 있으면 '모름' 또는 '확인 필요'라고 말씀해 주셔도 됩니다.")

    return "\n".join(lines) + "\n"


def build_office_checklist(case_id, meta, tax_data):
    missing_items = tax_data.get("missing_items", [])
    case_type = tax_data.get("case_type", "미확정")
    risk_level = tax_data.get("risk_level", "미확정")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(f"# {case_id} 부동산 사무실 보완자료 확인 체크리스트")
    lines.append("")
    lines.append(f"- 생성일시: {now}")
    lines.append(f"- 사건유형: {case_type}")
    lines.append(f"- 위험등급: {risk_level}")
    lines.append(f"- 부동산 사무실: {meta.get('real_estate_office', '') or '미입력'}")
    lines.append(f"- 담당자: {meta.get('manager_name', '') or '미입력'}")
    lines.append(f"- 고객명: {meta.get('client_name', '') or '미입력'}")
    lines.append("")

    lines.append("## 1. 고객에게 재확인할 항목")
    if not missing_items:
        lines.append("- 현재 1차 필수항목 기준 누락 없음")
    else:
        for item in missing_items:
            lines.append(f"- [ ] {item}")
            for guide in DOCUMENT_GUIDE.get(item, []):
                lines.append(f"  - 확인자료: {guide}")

    lines.append("")
    lines.append("## 2. 고객에게 안내할 때 주의할 문구")
    lines.append("- 부동산 사무실은 세무 판단을 확정하지 않는다.")
    lines.append("- 고객에게 '비과세 확정', '세금 없음' 등 단정 표현을 사용하지 않는다.")
    lines.append("- 모든 답변은 '세무사 검토 전 자료 정리 단계'라고 안내한다.")
    lines.append("- 고객이 모르는 항목은 추정해서 채우지 말고 미확인으로 둔다.")
    lines.append("")

    lines.append("## 3. 세무사 전송 전 확인")
    lines.append("- [ ] 누락항목에 대한 고객 답변을 받았는가?")
    lines.append("- [ ] 관련 증빙자료를 추가로 받았는가?")
    lines.append("- [ ] case_meta.json 또는 추후 보완 메모에 반영했는가?")
    lines.append("- [ ] 리포트를 다시 생성했는가?")
    lines.append("- [ ] 세무사용 리포트의 미확인 항목이 남아 있는지 확인했는가?")
    lines.append("")

    lines.append("## 4. 현재 판정")
    if risk_level in ["ORANGE", "RED"]:
        lines.append("- 현재 사건은 세무사 검토 권장 또는 필수 대상이다.")
    elif risk_level == "YELLOW":
        lines.append("- 보완자료 확인 후 세무사 검토 여부를 판단한다.")
    else:
        lines.append("- 단순 사건으로 보이나 최종 세무 판단은 세무사 확인이 필요할 수 있다.")

    return "\n".join(lines) + "\n"


def write_outputs(case_dir, kakao_message, office_checklist):
    missing_dir = case_dir / "05_missing"
    missing_dir.mkdir(exist_ok=True)

    kakao_path = missing_dir / "kakao_request_message.txt"
    checklist_path = missing_dir / "office_followup_checklist.md"

    with open(kakao_path, "w", encoding="utf-8") as f:
        f.write(kakao_message)

    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(office_checklist)

    return kakao_path, checklist_path


def update_case_meta(case_dir):
    meta_path = case_dir / "case_meta.json"
    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["status"] = "05_MISSING_REQUESTED"
        meta["missing_requested_at"] = datetime.now().isoformat(timespec="seconds")
        meta["next_action"] = "고객에게 보완자료 요청 후 추가자료 수신 시 inbox 또는 사건 폴더에 저장"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(case_dir.name, f"case_meta update failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 보완자료 요청문 생성기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        case_dir = get_case_dir(case_id)

        meta_path = case_dir / "case_meta.json"
        tax_json_path = case_dir / "04_extract" / "tax_facts.json"

        print("[START] 보완자료 요청문 생성 시작")
        print(f"[CASE_ID] {case_id}")

        meta = read_json(meta_path)
        tax_data = read_json(tax_json_path)

        kakao_message = build_kakao_message(case_id, meta, tax_data)
        office_checklist = build_office_checklist(case_id, meta, tax_data)

        kakao_path, checklist_path = write_outputs(case_dir, kakao_message, office_checklist)
        update_case_meta(case_dir)

        missing_count = len(tax_data.get("missing_items", []))
        write_log(case_id, f"missing_request_created missing_count={missing_count}")

        print("[SUCCESS] 보완자료 요청문 생성 완료")
        print(f"[KAKAO_MESSAGE] {kakao_path}")
        print(f"[OFFICE_CHECKLIST] {checklist_path}")
        print(f"[MISSING_COUNT] {missing_count}")
        print("")
        print("[NEXT]")
        print("1. kakao_request_message.txt 내용을 복사해 고객에게 전송하세요.")
        print("2. 고객이 보완자료를 보내면 사건 폴더에 추가 저장하세요.")
        print("3. 보완 후 extract_tax_facts.py와 generate_tax_report.py를 재실행하세요.")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 보완자료 요청문 생성 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
