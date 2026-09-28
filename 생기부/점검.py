"""생기부 초안 자동 점검.

사용법:
    python3 생기부/점검.py 초안.csv            # 결과를 화면에 출력
    python3 생기부/점검.py 초안.csv -o 결과.csv  # 검수경고·바이트 열을 붙여 저장

입력 CSV 열: 탭, 학년, 반, 번호, 초안 (검수경고 열이 있으면 기존 경고 뒤에 이어 붙임)
"""
import argparse
import csv
import re
import sys
from collections import defaultdict

LIMIT_BYTES = 1500

FORBIDDEN = [
    # 속마음·평가 종결
    "보임", "돋보", "모습을", "이해함", "이해하고", "깨달", "알게 됨", "느낌", "느꼈",
    "생각함", "흥미를", "노력함", "노력하", "성장함", "성장하",
    # 과장·AI 상투어
    "뛰어", "탁월", "우수", "역량", "잠재력", "인상적", "깊이 있는", "깊은 이해",
    "남다른", "두각", "훌륭", "인상 깊", "인상깊", "할 수 있음", "예쁜", "사랑스러",
]
NOT_ALLOWED = [
    # 기재요령상 기재 금지
    "수상", "대회", "올림피아드", "경시", "인증", "자격증", "토익", "토플", "텝스",
    "논문", "학회", "특허", "출판", "해외", "어학연수", "학원", "과외",
    "아버지", "어머니", "부모님", "대학교", "골든벨", "방과후",
    # 건강·출결은 다른 란에 기록
    "우울", "질병", "미인정", "결석", "지각한", "잦은 지각", "지각이 잦",
]
UNITS = {"mL", "mm", "cm", "km", "kg", "mg", "pH", "Hz", "kPa", "hPa", "DNA", "RNA", "kJ", "kW", "kcal", "cal"}


def neis_bytes(text):
    """나이스 기준: 한글·특수문자 3, ASCII 1, 줄바꿈 2."""
    total = 0
    for ch in text:
        if ch == "\n":
            total += 2
        elif ord(ch) < 128:
            total += 1
        else:
            total += 3
    return total


def has_m_final(ch):
    """한글 음절의 받침이 ㅁ인지 (명사형 종결: 함, 음, 움, 됨 …)."""
    code = ord(ch) - 0xAC00
    return 0 <= code < 11172 and code % 28 == 16


def split_sentences(text):
    # 소수점(1.5)은 자르지 않고, 온점 뒤가 공백이거나 끝일 때만 자른다.
    parts = re.split(r"(?<=\.)(?=\s|$)", text.strip())
    return [p.strip() for p in parts if p.strip()]


def check_text(text):
    warnings = []
    text = text.strip()
    if not text:
        return ["초안 없음"]

    b = neis_bytes(text)
    if b > LIMIT_BYTES:
        warnings.append(f"바이트 초과({b}/{LIMIT_BYTES})")

    for s in split_sentences(text):
        if not s.endswith("."):
            warnings.append(f"온점 없음: …{s[-12:]}")
        elif not has_m_final(s[:-1].rstrip()[-1:] or " "):
            warnings.append(f"종결 형식: …{s[-12:]}")

    for w in FORBIDDEN:
        if w in text:
            warnings.append(f"금지 표현 '{w}'")
    for w in NOT_ALLOWED:
        if w in text:
            warnings.append(f"기재 금지 확인 '{w}'")

    for d in re.findall(r"\d{4}\.\d{2}\.\d{2}(?![.\d])", text):
        warnings.append(f"날짜 끝 온점 누락: {d}")

    if "[?]" in text:
        warnings.append("판독 불확실 [?] 남음")

    english = [t for t in re.findall(r"[A-Za-z]{2,}", text) if t not in UNITS]
    if english:
        warnings.append(f"영문 확인: {', '.join(sorted(set(english)))}")

    return warnings


def normalize(sentence):
    return re.sub(r"\s+", "", sentence)


def check_rows(rows, common=()):
    """행마다 경고 목록을 붙이고, 같은 탭 안의 중복 문장도 표시한다.
    common: 여러 학생에게 똑같이 들어가도 되는 공통 문구(행사목록)."""
    common = {normalize(c) for c in common}
    seen = defaultdict(list)  # (탭, 문장) -> [학생 키]
    for row in rows:
        key = f"{row['학년']}-{row['반']}-{row['번호']}"
        for s in split_sentences(row.get("초안", "")):
            if normalize(s) not in common:
                seen[(row["탭"], normalize(s))].append(key)

    results = []
    for row in rows:
        key = f"{row['학년']}-{row['반']}-{row['번호']}"
        warnings = check_text(row.get("초안", ""))
        dup = set()
        for s in split_sentences(row.get("초안", "")):
            others = [k for k in seen[(row["탭"], normalize(s))] if k != key]
            dup.update(others)
        if dup:
            warnings.append(f"다른 학생과 같은 문장: {', '.join(sorted(dup))}")
        results.append((row, warnings, neis_bytes(row.get("초안", "").strip())))
    return results


def main():
    parser = argparse.ArgumentParser(description="생기부 초안 자동 점검")
    parser.add_argument("csv")
    parser.add_argument("-o", "--output")
    parser.add_argument("--common", help="중복 검사에서 뺄 공통 문구 파일 (한 줄에 한 문장)")
    args = parser.parse_args()

    common = []
    if args.common:
        with open(args.common, encoding="utf-8-sig") as f:
            common = [line.strip() for line in f if line.strip()]

    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    results = check_rows(rows, common)

    if args.output:
        fields = list(rows[0].keys()) if rows else []
        for extra in ("검수경고", "바이트"):
            if extra not in fields:
                fields.append(extra)
        with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row, warnings, b in results:
                out = dict(row)
                prev = (row.get("검수경고") or "").strip()
                out["검수경고"] = " / ".join(([prev] if prev else []) + warnings)
                out["바이트"] = b
                writer.writerow(out)

    problems = 0
    for row, warnings, b in results:
        if warnings:
            problems += 1
            print(f"[{row['탭']}] {row['학년']}-{row['반']}-{row['번호']} ({b}B): " + " / ".join(warnings))
    print(f"\n점검 {len(results)}명, 경고 있는 학생 {problems}명")
    return 0


if __name__ == "__main__":
    sys.exit(main())
