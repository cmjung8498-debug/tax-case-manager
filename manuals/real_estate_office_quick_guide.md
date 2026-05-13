# TaxCaseManager 빠른 사용 가이드

## 1. 사건 생성

카카오톡/문서 파일이 있는 경우:

```powershell
cd C:\TaxCaseManager
python .\intake_kakao_files.py
```

## 2. 고객 작성용 서류 출력
```powershell
python .\create_client_forms.py --case-id 사건번호
```

## 3. CSV 입력
```powershell
python .\import_case_input.py 사건번호 --csv C:\경로\입력파일.csv
```

## 4. 전체 리포트 생성
```powershell
python .\run_case_pipeline.py 사건번호 --no-audio
```

## 5. 고객 보완요청 문구 확인
`cases\사건번호\05_missing\kakao_request_message.txt`

## 6. 세무사 전달 ZIP 확인
`exports\사건번호.zip`

## 7. 전체 사건 상태 확인
```powershell
python .\case_status_dashboard.py
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
