import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
MANUALS_DIR = BASE_DIR / "manuals"
LOGS_DIR = BASE_DIR / "logs"

def write_log(message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "manuals_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")

MANUALS = {
    "real_estate_office_operation_manual.md": """# TaxCaseManager 부동산 사무실 운영 매뉴얼

## 1. 서비스 목적

TaxCaseManager는 부동산 사무실에서 고객의 양도세 관련 기초자료를 정리하고,
AI/룰 기반 사전진단 리포트와 세무사 검토용 사건 파일을 생성하기 위한 업무지원 도구입니다.

본 시스템은 세무 판단을 확정하지 않습니다.
최종 양도세 판단 및 신고는 세무사 검토 후 진행됩니다.

---

## 가격 정책 및 상품 구분

### 1단계: AI 양도세 사전진단 완결 리포트

- 고객 결제금액: 100,000원
- 제공 내용:
  - 고객 작성서류 정리
  - 제출자료 기준 사실관계 정리
  - 개략 양도세 범위 산출
  - 누락자료 체크
  - 위험등급 산정
  - 취득가액 불명확 검토
  - 절세 검토 포인트
  - 고객용/부동산용/세무사용 리포트 생성

- 제외 내용:
  - 세무사 최종 판단
  - 양도세 신고대행
  - 홈택스 신고
  - 세무조사 대응
  - 조세불복
  - 복잡 사건 추가 세무 검토

### 2단계: 세무사 검토 패키지

- 고객 결제금액: 200,000원
- 제공 내용:
  - 세무사 검토용 사건 패키지 전달
  - 세무사용 리포트 검토
  - 추가 필요서류 확인
  - 최종 검토 의견 제공
  - 신고대행 필요 여부 판단

- 제외 내용:
  - 실제 양도소득세 신고대행 수수료
  - 복잡 사건 추가 검토비
  - 상속/증여/법인/재개발 등 고난도 사건 추가비

주의:
세무사 검토 패키지는 세무사 소개비 또는 알선비가 아니라, 세무사의 검토 용역을 포함하는 별도 검토 상품으로 안내한다.

---

## 2. 전체 업무 흐름

1. 고객에게 양도세 사전진단 서비스 안내
2. 고객 작성용 서류 9종 출력
3. 고객 작성 및 서명
4. 제출서류 확인
5. 담당자가 CSV/JSON 또는 CLI로 입력
6. TaxCaseManager 파이프라인 실행
7. 고객용/부동산용/세무사용 리포트 확인
8. 누락자료가 있으면 고객에게 보완 요청
9. 보완 후 재입력 또는 재실행
10. 세무사 검토가 필요하면 ZIP 패키지 전달
11. 세무사 회신 후 고객 안내

---

## 3. 고객에게 출력할 서류

아래 9종을 출력하여 고객에게 작성받습니다.

1. 양도세 사전진단 상담 신청서
2. 양도 부동산 기본정보 확인서
3. 주택 보유 및 세대원 확인서
4. 거주기간 확인서
5. 취득가액 및 필요경비 증빙 확인서
6. 양도세 예외사항 체크리스트
7. 개인정보 및 세무사 전달 동의서
8. 양도세 사전진단 필요서류 체크리스트
9. 고객 최종 확인서

생성 명령:

```powershell
cd C:\\TaxCaseManager
python .\\create_client_forms.py --case-id GT-YYYYMMDD-001
```

---

## 4. 고객에게 반드시 설명할 내용

부동산 담당자는 고객에게 다음 취지를 안내해야 합니다.

- 이 서비스는 양도세 확정 신고가 아니다.
- 고객이 제공한 자료와 진술을 기준으로 1차 사전진단 리포트를 만든다.
- 누락자료나 예외사항이 있으면 결과가 달라질 수 있다.
- 세무사 검토가 필요한 사건은 별도 검토 또는 신고대행으로 연결될 수 있다.
- 모르는 항목은 추정하지 말고 “모름/확인 필요”로 작성해야 한다.
- 녹음파일 제출은 선택사항이다.

---

## 5. 부동산 사무실이 절대 하면 안 되는 표현

**금지 표현:**

- “비과세 확정입니다.”
- “세금 안 나옵니다.”
- “이 금액으로 신고하면 됩니다.”
- “세무사 안 가도 됩니다.”
- “무조건 절세됩니다.”
- “취득가액은 대충 적어도 됩니다.”
- “자료 없어도 알아서 맞춰드립니다.”

**허용 표현:**

- “현재 자료 기준으로 사전진단을 해보겠습니다.”
- “세무사 검토가 필요한 쟁점이 있는지 확인해보겠습니다.”
- “모르는 항목은 모름으로 두고 추가 확인하겠습니다.”
- “최종 판단은 세무사 검토 후 확정됩니다.”
- “필요경비 증빙이 있으면 세액에 영향을 줄 수 있습니다.”

---

## 6. 입력 방식

**방식 A: CLI 입력**
```powershell
cd C:\\TaxCaseManager
python .\\case_input_form_to_json.py GT-YYYYMMDD-001
```

**방식 B: CSV/엑셀 입력**
1. 샘플 CSV를 복사합니다.
   `C:\\TaxCaseManager\\templates\\case_input_samples\\sample_case_input_form.csv`
2. 엑셀로 열어 고객 정보를 한 줄 입력합니다.
3. CSV로 저장합니다.
4. 아래 명령으로 import합니다.
```powershell
cd C:\\TaxCaseManager
python .\\import_case_input.py GT-YYYYMMDD-001 --csv C:\\경로\\입력파일.csv
```

**방식 C: JSON 입력**
```powershell
cd C:\\TaxCaseManager
python .\\import_case_input.py GT-YYYYMMDD-001 --json C:\\경로\\입력파일.json
```

---

## 7. 리포트 생성

입력자료가 준비되면 아래 명령을 실행합니다.

```powershell
cd C:\\TaxCaseManager
python .\\run_case_pipeline.py GT-YYYYMMDD-001 --no-audio
```

생성 결과:

- `06_reports\\01_customer_summary.md`
- `06_reports\\02_office_check_report.md`
- `06_reports\\03_tax_accountant_review.md`
- `05_missing\\kakao_request_message.txt`
- `exports\\GT-YYYYMMDD-001.zip`

---

## 8. 리포트 확인 순서

부동산 담당자는 아래 순서로 확인합니다.

1. `02_office_check_report.md`
2. `kakao_request_message.txt`
3. `01_customer_summary.md`
4. `03_tax_accountant_review.md`
5. `README_FOR_TAX_ACCOUNTANT.md`

---

## 9. 보완자료 요청

누락자료가 있으면 아래 파일을 열어 고객에게 전송합니다.

`C:\\TaxCaseManager\\cases\\사건번호\\05_missing\\kakao_request_message.txt`

**주의:**

- 고객에게 세액을 확정해서 말하지 않는다.
- 누락자료 요청은 “세무사 검토 전 자료 정리”라고 안내한다.
- 고객이 모르는 항목은 추정하게 하지 않는다.

---

## 10. 세무사 전달

세무사에게 전달할 ZIP 파일:

`C:\\TaxCaseManager\\exports\\사건번호.zip`

**기본은 녹음파일 제외 권장:**

```powershell
python .\\run_case_pipeline.py 사건번호 --no-audio
```

**전달 전 확인:**

- [ ] 수신 세무사 확인
- [ ] 고객 동의서 작성 여부 확인
- [ ] 개인정보 포함 여부 확인
- [ ] 녹음파일 포함 여부 확인
- [ ] 사건번호 확인
- [ ] ZIP 파일명 확인

---

## 11. 세무사 신고대행 전환 단계

세무사 검토 후 실제 신고대행으로 진행하는 경우, 고객에게 아래 사항을 안내해야 합니다.

- 세무사 검토 패키지와 신고대행은 별도 업무입니다.
- 신고대행 수수료는 세무사가 별도 산정합니다.
- 고액 부동산 또는 복잡 사건은 추가 수수료가 발생할 수 있습니다.
- 고객은 위임장, 신분증, 인감증명서 또는 본인서명사실확인서, 홈택스 수임동의 등을 요청받을 수 있습니다.
- 고객은 최종 신고내용을 제출 전 확인해야 합니다.
- 고객 제공자료가 사실과 다르거나 누락된 경우 가산세 등 불이익이 발생할 수 있습니다.

---

## 12. 위험등급별 처리

- **GREEN:** 단순 사건 가능성 (그래도 단정 안내 금지)
- **YELLOW:** 일부 보완자료 필요 (고객에게 추가 확인 요청)
- **ORANGE:** 세무사 검토 권장 (주택 수, 취득가액, 고가주택, 세대원 쟁점 가능)
- **RED:** 세무사 필수 검토 (자료 부족, 복합 쟁점, 취득가액 불명확, 상속/증여 등)

---

## 13. 취득가액 불명확 사건 처리

아래 중 하나라도 해당되면 세무사 검토 대상으로 분류합니다.

- 취득가액을 모름
- 매수계약서 없음
- 금융자료 없음
- 취득세 과세표준 확인 불가
- 오래전 취득
- 기준시가/토지등급 확인 필요
- 감정가액 검토 필요
- 환산취득가액 검토 필요
- 의제취득일 검토 필요

부동산 사무실은 임의 취득가액을 확정하지 않습니다.

---

## 14. 대시보드 확인

전체 사건 상태 확인:

```powershell
cd C:\\TaxCaseManager
python .\\case_status_dashboard.py
```

결과 파일:

- `C:\\TaxCaseManager\\outputs\\case_status_dashboard.csv`
- `C:\\TaxCaseManager\\outputs\\case_status_dashboard.md`

---

## 15. 고객 응대 원칙

- 모르면 모른다고 표시한다.
- 추정값을 확정값처럼 입력하지 않는다.
- 세무 판단은 세무사에게 넘긴다.
- 모든 자료는 사건번호 기준으로 관리한다.
- 개인정보 파일은 외부로 임의 전송하지 않는다.
""",
    "real_estate_office_quick_guide.md": """# TaxCaseManager 빠른 사용 가이드

## 1. 사건 생성

카카오톡/문서 파일이 있는 경우:

```powershell
cd C:\\TaxCaseManager
python .\\intake_kakao_files.py
```

## 2. 고객 작성용 서류 출력
```powershell
python .\\create_client_forms.py --case-id 사건번호
```

## 3. CSV 입력
```powershell
python .\\import_case_input.py 사건번호 --csv C:\\경로\\입력파일.csv
```

## 4. 전체 리포트 생성
```powershell
python .\\run_case_pipeline.py 사건번호 --no-audio
```

## 5. 고객 보완요청 문구 확인
`cases\\사건번호\\05_missing\\kakao_request_message.txt`

## 6. 세무사 전달 ZIP 확인
`exports\\사건번호.zip`

## 7. 전체 사건 상태 확인
```powershell
python .\\case_status_dashboard.py
```

---

## ⚠️ 주의

- 비과세 확정, 세금 없음 등 단정 표현 금지
- 녹음파일은 선택사항
- 최종 판단은 세무사 검토 필요

---

## 비용 안내 요약

- AI 양도세 사전진단 완결 리포트: 100,000원
- 세무사 검토 패키지: 200,000원
- 양도세 신고대행: 별도 견적

주의:
세무사 검토 패키지를 “소개비” 또는 “연결비”로 설명하지 않는다.
고객에게는 “세무사 검토비” 또는 “세무사 검토 패키지”로 안내한다.
""",
    "customer_notice_script.md": """# 고객 안내 표준 문구

## 1. 서비스 안내

고객님, 양도세는 주택 수, 거주기간, 취득가액, 필요경비, 세대원 주택 여부 등에 따라 결과가 크게 달라질 수 있습니다.

저희 사무실에서는 세금을 확정해서 말씀드리는 것이 아니라,
고객님이 제공하신 자료를 기준으로 양도세 사전진단 리포트를 만들고,
필요 시 세무사 검토까지 연결해드리는 방식으로 진행합니다.

## 2. 작성 요청 안내

정확한 검토를 위해 몇 가지 서류를 작성해주셔야 합니다.

모르는 항목은 임의로 적지 마시고 “모름” 또는 “확인 필요”로 표시해 주세요.
자료가 부족한 부분은 리포트 생성 후 다시 안내드리겠습니다.

## 3. 녹음 관련 안내

녹음은 필수가 아닙니다.
고객님이 원하시는 경우에만 상담 내용을 보조자료로 남길 수 있습니다.
기본은 작성 서류와 제출자료 기준으로 진행합니다.

## 4. 세무사 검토 안내

사건에 따라 세무사 검토가 필요할 수 있습니다.
특히 2주택 이상, 상속/증여, 취득가액 불명확, 고가주택, 분양권/입주권, 재개발/재건축 등은 세무사 검토가 권장됩니다.

## 5. 비용 안내 예시

AI 양도세 사전진단 완결 리포트 비용은 1회 기준 100,000원입니다.

이 리포트는 고객님이 작성한 자료와 제출서류를 기준으로 개략 세액 범위, 누락자료, 위험등급, 취득가액 검토, 절세 검토 포인트, 세무사 검토 필요 여부를 정리하는 사전진단 자료입니다.

이 비용에는 세무사의 최종 세무 판단, 홈택스 신고, 신고대행, 세무조사 대응은 포함되지 않습니다.

세무사 검토를 원하시는 경우 별도 세무사 검토 패키지 비용 200,000원이 발생할 수 있습니다.

세무사 검토 패키지는 정리된 사건 리포트와 증빙자료를 세무사가 검토하고, 추가 필요서류 및 최종 검토 의견을 제공하는 단계입니다.

실제 양도소득세 신고대행이 필요한 경우 신고 수수료는 사건 난이도에 따라 별도 안내됩니다.

## 6. 금지 표현 대체 문구

**고객 질문:** “그럼 세금 안 나오나요?”

**답변:**
“현재 자료만으로는 확정해서 말씀드릴 수 없습니다. 리포트로 비과세 가능성과 추가 확인사항을 정리한 뒤, 필요하면 세무사 검토를 연결해드리겠습니다.”

**고객 질문:** “취득가액은 대충 적으면 되나요?”

**답변:**
“취득가액은 양도세 계산에 매우 중요한 항목이라 임의로 적으면 안 됩니다. 계약서, 금융자료, 취득세 자료를 먼저 확인하고, 자료가 없으면 세무사 검토가 필요합니다.”

**고객 질문:** “녹음 꼭 해야 하나요?”

**답변:**
“아닙니다. 녹음은 선택사항입니다. 기본은 고객님이 작성해주신 서류와 제출자료를 기준으로 진행합니다.”
"""
}

def main():
    MANUALS_DIR.mkdir(exist_ok=True, parents=True)
    
    written = []
    try:
        for filename, content in MANUALS.items():
            path = MANUALS_DIR / filename
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            written.append(path)
            
        print("[SUCCESS] 부동산 사무실 운영 매뉴얼 가격 정책 업데이트 완료")
        print(f"[MANUALS_DIR] {MANUALS_DIR}")
        print(f"[COUNT] {len(written)}")
        for p in written:
            print(f"- {p.name}")
            
        write_log(f"manuals_updated count={len(written)}")
        
    except Exception as e:
        write_log(f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 운영 매뉴얼 업데이트 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
