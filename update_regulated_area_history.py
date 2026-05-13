import argparse
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(r"C:\TaxCaseManager")
HISTORY_CSV_PATH = BASE_DIR / "data" / "regulated_area_history.csv"
NOTICES_CSV_PATH = BASE_DIR / "data" / "regulated_area_notices.csv"
LOGS_DIR = BASE_DIR / "logs"

def write_log(message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "regulated_area_history_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")

def validate_csv():
    if not HISTORY_CSV_PATH.exists():
        print(f"[ERROR] CSV file not found: {HISTORY_CSV_PATH}")
        return False
        
    if not NOTICES_CSV_PATH.exists():
        print(f"[ERROR] CSV file not found: {NOTICES_CSV_PATH}")
        return False

    req_history_cols = ["area_type", "region_level", "region_name", "sido", "sigungu", "sub_area", "start_date", "end_date", "status", "notice_no", "notice_date", "effective_date", "source_name", "source_url", "confidence", "note"]
    req_notices_cols = ["notice_id", "notice_no", "notice_title", "notice_date", "effective_date", "action_type", "source_name", "source_url", "download_url", "verified", "status", "note"]

    with open(NOTICES_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or header != req_notices_cols:
            print("[ERROR] NOTICES CSV schema mismatch")
            return False

    with open(HISTORY_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or header != req_history_cols:
            print("[ERROR] HISTORY CSV schema mismatch")
            return False

    notices_set = set()
    with open(NOTICES_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            notices_set.add(row["notice_no"])

    history_records = []
    with open(HISTORY_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            history_records.append((i, row))

    active_intervals = defaultdict(list)
    
    fails = []
    warns = defaultdict(int)

    for i, row in history_records:
        status = row["status"]
        conf = row["confidence"]
        n_no = row["notice_no"]
        s_url = row["source_url"]

        if status not in ["ACTIVE", "RELEASED", "PARTIAL", "UNKNOWN"]:
            fails.append(f"Row {i}: Invalid status {status}")
            
        if conf not in ["A_OFFICIAL", "B_PARTIAL", "C_MANUAL", "D_NEEDS_REVIEW"]:
            fails.append(f"Row {i}: Invalid confidence {conf}")

        if conf == "A_OFFICIAL" and not s_url:
            fails.append(f"[FAIL_OFFICIAL_MISSING_SOURCE] Row {i}: A_OFFICIAL requires source_url")
        elif not s_url:
            warns["WARN_MISSING_SOURCE_URL"] += 1

        if conf == "A_OFFICIAL" and (not n_no or n_no == "확인필요"):
            fails.append(f"[FAIL_OFFICIAL_MISSING_NOTICE] Row {i}: A_OFFICIAL requires real notice_no")

        if n_no and n_no != "확인필요" and n_no not in notices_set:
            fails.append(f"Row {i}: notice_no {n_no} not found in notices.csv")

        if "샘플" in row["note"] or conf == "D_NEEDS_REVIEW" or "확인 필요" in row["note"]:
            warns["WARN_SAMPLE_DATA"] += 1
            
        if status == "PARTIAL" or conf == "B_PARTIAL":
            warns["WARN_PARTIAL_REGION"] += 1
            
        if conf == "C_MANUAL" or not n_no:
            warns["WARN_REVIEW_REQUIRED"] += 1

        s_date, e_date = None, None
        try:
            if row["start_date"]:
                s_date = datetime.strptime(row["start_date"], "%Y-%m-%d")
            if row["end_date"]:
                e_date = datetime.strptime(row["end_date"], "%Y-%m-%d")
        except ValueError:
            fails.append(f"Row {i}: Invalid start/end date format")

        if s_date and e_date and s_date > e_date:
            fails.append(f"[FAIL_DATE_RANGE] Row {i}: start_date > end_date")

        region = row["region_name"]
        
        if status == "ACTIVE" and s_date:
            active_intervals[region].append((s_date, e_date, i))

    for region, intervals in active_intervals.items():
        for a_start, a_end, a_idx in intervals:
            for b_start, b_end, b_idx in intervals:
                if a_idx >= b_idx:
                    continue
                a_e = a_end if a_end else datetime.max
                b_e = b_end if b_end else datetime.max
                
                if max(a_start, b_start) <= min(a_e, b_e):
                    fails.append(f"[FAIL_OVERLAP] Row {a_idx} and Row {b_idx}: ACTIVE intervals overlap for {region}")

    for i, row in history_records:
        if row["status"] == "RELEASED" and row["start_date"]:
            r_date = datetime.strptime(row["start_date"], "%Y-%m-%d")
            region = row["region_name"]
            
            for a_start, a_end, a_idx in active_intervals.get(region, []):
                if a_start < r_date:
                    if not a_end or a_end >= r_date:
                        fails.append(f"Row {a_idx}: ACTIVE interval is not closed correctly for RELEASED row {i}")

    for fail in fails:
        print(f"[ERROR] {fail}")
        
    for warn_type, count in warns.items():
        if count > 0:
            print(f"[WARN] {warn_type}: {count} occurrences")

    if not fails:
        print("[SUCCESS] CSV validation passed")
        write_log("CSV schema and format validated successfully. fails=0")
        return True
    else:
        print(f"[FAIL] CSV validation failed with {len(fails)} errors")
        write_log(f"CSV validation failed with {len(fails)} errors")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    
    if args.validate:
        validate_csv()

if __name__ == "__main__":
    main()
