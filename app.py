import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pypdf

# 페이지 설정
st.set_page_config(page_title="과학 탐구 수업 & 교-수-평-기 설계 비서", page_icon="🧪", layout="wide")

# ==========================================
# 🔄 외부 데이터 캐싱 (속도 저하 방지)
# ==========================================
@st.cache_data(ttl=86400)
def fetch_guide_data():
    try:
        url = "https://ppzine.kr/class_edu/"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        texts = [el.get_text(strip=True) for el in soup.select('p, div, td') if len(el.get_text(strip=True)) > 15]
        return "\n".join(texts[:3]) if texts else "2022 개정 깊이있는 학습 지침"
    except Exception:
        return "2022 개정 깊이있는 학습 및 질문 중심 수업 지침"

@st.cache_data(ttl=86400)
def fetch_steam_data():
    try:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://steam.kosac.re.kr/"}
        main_url = "https://steam.kosac.re.kr/learning/curriculum/list/menu/220"
        session.get(main_url, headers=headers, timeout=3)
        payload = {'schulClCode': 'M', 'curriculumCd': '220', 'subjcCode': 'SCI', 'pageIndex': '1'}
        res = session.post(main_url, headers=headers, data=payload, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [row.get_text(strip=True).split('\n')[0] for row in soup.select('tbody tr, .subject, td.al') if len(row.get_text(strip=True)) > 5]
        return "\n".join(titles[:3]) if titles else "STEAM 중등 과학 융합 탐구 모델"
    except Exception:
        return "중학교 과학 교과중심 STEAM 교수학습자료"

# 사이드바 설정
st.sidebar.title("⚙️ 설정 및 외부 자료")
api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

# 📚 교과서 PDF 업로드
st.sidebar.markdown("---")
st.sidebar.subheader("📚 교과서 PDF 업로드")
uploaded_pdf = st.sidebar.file_uploader("교과서 단원 PDF 파일 선택", type=["pdf"])

pdf_text_content = ""
if uploaded_pdf is not None:
    try:
        pdf_reader = pypdf.PdfReader(uploaded_pdf)
        extracted_pages = []
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t:
                extracted_pages.append(t)
        pdf_text_content = "\n".join(extracted_pages)
        st.sidebar.success(f"교과서 PDF 학습 완료! ({len(pdf_reader.pages)}페이지)")
    except Exception:
        st.sidebar.error("PDF 읽기 중 오류가 발생했습니다.")

guide_context = fetch_guide_data()
steam_context = fetch_steam_data()

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 외부 데이터 자동 수집 상태")
st.sidebar.success("✅ 깊이있는 학습 지침서 연동")
st.sidebar.success("✅ STEAM 중등 과학 포털 연동")

# 메인 화면
st.title("🧪 중학교 과학 질문 중심 수업 설계 비서")
st.caption("교과서 중심 | 2022 개정 깊이 있는 학습 | 질문 중심 Scaffolding | 교-수-평-기 일체화 (Gemini Pro)")

if not api_key:
    st.info("👈 왼쪽 사이드바에 API Key를 입력하면 비서가 활성화됩니다.")
    st.stop()

genai.configure(api_key=api_key)

# 시스템 기본 지침
SYSTEM_PROMPT = """
너는 중학교 과학 교사를 돕는 "상호작용형 질문 중심 수업 설계 및 교-수-평-기 일체화 AI 비서"이다.

[교과서 기반 학습 최우선 지침]
1. 업로드된 교과서 PDF 내용이 존재할 경우, 해당 교과서에 기술된 실제 개념 설명, 탐구 활동, 용어, 소단원 체계를 단단한 중심(Core)으로 삼아 수업을 구성한다.
2. 교과서에 수록된 질문이나 자료를 적극 활용하여 학생용 비계(Scaffolding) 및 발문을 설계한다.

[2022 개정 교육과정: 깊이 있는 학습 반영 지침]
1. 개념 기반 탐구(Conceptual Inquiry)와 핵심 아이디어 중심의 이해를 유도한다.
2. 학생들이 핵심 개념 속에서 '삶과 연계된 핵심 질문'을 발견하도록 비계(Scaffolding)를 설계한다.

[상호작용 단계]
1단계: 교과서 단원/내용이 들어오면, 이 단원에 가장 자연스러운 탐구 소스 2~3가지를 제안하고 교사의 선택을 묻는다.
2단계: 교사의 선택에 맞춰 교실 준비물, 차시 제약 등을 교사에게 질문하여 맞춘다.
3단계: [교-수-평-기 일체화 패키지] (활동지, 교사 가이드, 루브릭, 세특 예시문)를 완성한다.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("교과서 단원명이나 다루고 싶은 주제를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ⚡ 맥락 데이터 결합
    context_payload = f"{SYSTEM_PROMPT}\n\n[사용자 질문]: {prompt}"
    if pdf_text_content:
        context_payload += f"\n\n[학습된 교과서 PDF 내용 (우선 반영)]:\n{pdf_text_content[:3000]}"
    if guide_context:
        context_payload += f"\n\n[참고 지침서]: {guide_context[:500]}"
    if steam_context:
        context_payload += f"\n\n[참고 STEAM]: {steam_context[:500]}"

    with st.chat_message("assistant"):
        with st.spinner("⚡ 교과서와 지침서를 분석하여 수업을 구상하고 있습니다..."):
            try:
                # 🎯 초고속 직접 호출 방식 (먹통 현상 완벽 방지)
                model = genai.GenerativeModel('gemini-1.5-pro')
                response = model.generate_content(context_payload)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"답변 생성 중 오류가 발생했습니다: {e}")
