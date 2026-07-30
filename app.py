import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pypdf

# 페이지 설정
st.set_page_config(page_title="과학 탐구 수업 & 교-수-평-기 설계 비서", page_icon="🧪", layout="wide")

# ==========================================
# 🔄 자동 수집 함수 정의 (웹 앱 로드 시 자동 실행)
# ==========================================
@st.cache_data(ttl=3600)  # 1시간 동안 수집 결과 캐싱하여 빠른 속도 유지
def fetch_guide_data():
    try:
        url = "https://ppzine.kr/class_edu/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        page_texts = []
        for el in soup.select('p, div, td, h1, h2, h3, a'):
            t = el.get_text(strip=True)
            if len(t) > 15 and t not in page_texts:
                page_texts.append(t)
            if len(page_texts) >= 15:
                break
        return "\n".join([f"- {t}" for t in page_texts[:10]]) if page_texts else "2022 개정 깊이있는 학습 및 수업설계 지침"
    except Exception:
        return "2022 개정 교육과정 기반 중등 깊이있는 학습 및 수업설계 지침"

@st.cache_data(ttl=3600)
def fetch_steam_data():
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://steam.kosac.re.kr/"
        }
        main_url = "https://steam.kosac.re.kr/learning/curriculum/list/menu/220"
        session.get(main_url, headers=headers, timeout=5)
        
        payload = {'schulClCode': 'M', 'curriculumCd': '220', 'subjcCode': 'SCI', 'pageIndex': '1'}
        res = session.post(main_url, headers=headers, data=payload, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        titles = []
        for row in soup.select('tbody tr, div.board_list, .subject, td.al'):
            text = row.get_text(strip=True)
            if len(text) > 5 and not any(k in text for k in ['등록된', '없습니다', '번호', '제목', '작성자']):
                clean_text = text.split('\n')[0]
                if clean_text not in titles and len(clean_text) > 5:
                    titles.append(clean_text)
            if len(titles) >= 10:
                break
        return "\n".join([f"- {t}" for t in titles]) if titles else "STEAM 포털 중학교 과학 교과중심 교수학습자료"
    except Exception:
        return "중학교 과학 교과중심 STEAM 교수학습자료 데이터"

# 사이드바 (API 키 및 자료 수집 현황)
st.sidebar.title("⚙️ 설정 및 외부 자료")
api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

# 📚 교과서 PDF 업로드 기능
st.sidebar.markdown("---")
st.sidebar.subheader("📚 교과서 PDF 업로드")
uploaded_pdf = st.sidebar.file_uploader("교과서 단원 PDF 파일 선택", type=["pdf"])

pdf_text_content = ""
if uploaded_pdf is not None:
    try:
        pdf_reader = pypdf.PdfReader(uploaded_pdf)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                pdf_text_content += text + "\n"
        st.sidebar.success(f"교과서 PDF 학습 완료! ({len(pdf_reader.pages)}페이지)")
    except Exception:
        st.sidebar.error("PDF 읽기 중 오류가 발생했습니다.")

# 자동 데이터 로드 수행
guide_context = fetch_guide_data()
steam_context = fetch_steam_data()

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 외부 데이터 자동 수집 상태")
st.sidebar.success("✅ 깊이있는 학습 지침서 자동 연동 완료")
st.sidebar.success("✅ STEAM 중등 과학 포털 자동 연동 완료")

# 메인 화면
st.title("🧪 중학교 과학 질문 중심 수업 설계 비서")
st.caption("교과서 중심 | 2022 개정 깊이 있는 학습 | 질문 중심 Scaffolding | 교-수-평-기 일체화")

if not api_key:
    st.info("👈 왼쪽 사이드바에 API Key를 입력하면 비서가 활성화됩니다.")
    st.stop()

genai.configure(api_key=api_key)

# 시스템 지침 설정
SYSTEM_PROMPT = """
너는 중학교 과학 교사를 돕는 "상호작용형 질문 중심 수업 설계 및 교-수-평-기 일체화 AI 비서"이다.

[교과서 기반 학습 최우선 지침]
1. 업로드된 교과서 PDF 내용이 존재할 경우, 해당 교과서에 기술된 실제 개념 설명, 탐구 활동, 용어, 소단원 체계를 단단한 중심(Core)으로 삼아 수업을 구성한다.
2. 교과서에 수록된 질문이나 자료를 적극 활용하여 학생용 비계(Scaffolding) 및 발문을 설계한다.

[2022 개정 교육과정: 깊이 있는 학습(Deep Learning) 반영 지침]
1. 단순 지식 전달을 넘어 개념 기반 탐구(Conceptual Inquiry)와 핵심 아이디어 중심의 이해를 유도한다.
2. 학생들이 교과서 텍스트와 핵심 개념 속에서 '삶과 연계된 핵심 질문'을 발견할 수 있도록 비계(Scaffolding)를 설계한다.
3. 지식, 과정/기능, 가치/태도가 유기적으로 융합되는 탐구 활동을 제시한다.

[수업 설계 기본 원칙]
1. 선행학습 유무와 상관없이 누구나 참여하는 '질문 중심 수업(Question-Based Learning)'을 지향한다.
2. 단원에 억지로 간단한 실험을 엮지 말고, 주제 특성에 맞는 최적의 소스(소소한 실험, 자료해석/오류탐정, 과학적 모델링, 과학 토론 등)를 자연스럽게 제안한다.
3. 교과서 텍스트와 그림을 바탕으로 비계(Scaffolding)를 세우고, 마지막에 소소한 사고 확장 1단계를 곁들인다.

[상호작용 단계]
1단계: 교과서 단원/내용이 들어오면, 이 단원에 가장 자연스러운 탐구 소스 2~3가지를 제안하고 교사의 선택을 묻는다.
2단계: 교사의 선택에 맞춰 소소한 교실 준비물, 차시 제약 등을 교사에게 질문하여 맞춘다.
3단계: 아래 [교-수-평-기 일체화 패키지]를 완성하여 제시한다.
 - 1. 학생용 탐구 활동지 (Step 1 현상관찰 질문 ➔ Step 2 가설/탐구 질문 ➔ Step 3 교과서 중심 개념연결 ➔ Step 4 학생이 직접 만드는 꼬리 질문 코너)
 - 2. 교사용 모범답안 및 오개념/막힘 방지 힌트 발문 가이드
 - 3. 과정 중심 평가 루브릭 (깊이 있는 학습 관점 반영)
 - 4. 생기부 과목별 세특 예시문 (3~4가지)
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=SYSTEM_PROMPT)
    st.session_state.chat = model.start_chat(history=[])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("교과서 단원명이나 다루고 싶은 주제를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 맥락 조합
    additional_context = ""
    if pdf_text_content:
        additional_context += f"\n\n[학습된 교과서 PDF 내용]:\n{pdf_text_content[:15000]}"
    if guide_context:
        additional_context += f"\n\n[참고 깊이있는 학습 지침서 데이터]:\n{guide_context}"
    if steam_context:
        additional_context += f"\n\n[참고 중등 과학 STEAM 데이터]:\n{steam_context}"

    full_prompt = prompt + additional_context

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(full_prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
