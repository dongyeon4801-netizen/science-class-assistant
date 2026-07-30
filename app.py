import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# 페이지 설정
st.set_page_config(page_title="과학 탐구 수업 & 교-수-평-기 설계 비서", page_icon="🧪", layout="wide")

# 사이드바 (API 키 및 크롤링)
st.sidebar.title("⚙️ 설정 및 외부 자료")
api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 STEAM 포털 연동")
if st.sidebar.button("🔄 최신 융합자료 수집"):
    try:
        url = "https://steam.kosac.re.kr/learning/curriculum/list/menu/220"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [item.get_text(strip=True) for item in soup.select('.title, .subject')[:5]]
        st.sidebar.success(f"최신 자료 {len(titles)}건 수집 완료!")
        st.session_state['steam_data'] = "\n".join(titles)
    except Exception:
        st.sidebar.error("수집 완료 (기본 DB 사용)")

# 메인 화면
st.title("🧪 중학교 과학 질문 중심 수업 설계 비서")
st.caption("교과서 중심 | 질문 중심 Scaffolding | 주제별 맞춤 소스 | 교-수-평-기 일체화")

if not api_key:
    st.info("👈 왼쪽 사이드바에 API Key를 입력하면 비서가 활성화됩니다.")
    st.stop()

genai.configure(api_key=api_key)

# 지침 설정
SYSTEM_PROMPT = """
너는 중학교 과학 교사를 돕는 "상호작용형 질문 중심 수업 설계 및 교-수-평-기 일체화 AI 비서"이다.

[수업 설계 핵심 원칙]
1. 교사가 제시한 교과서 내용을 단단한 중심(Core)으로 삼는다.
2. 선행학습 유무와 상관없이 누구나 참여하는 '질문 중심 수업(Question-Based Learning)'을 지향한다.
3. 단원에 억지로 간단한 실험을 엮지 말고, 주제 특성에 맞는 최적의 소스(소소한 실험, 자료해석/오류탐정, 과학적 모델링, 과학 토론 등)를 자연스럽게 제안한다.
4. 교과서 텍스트와 그림을 바탕으로 비계(Scaffolding)를 세우고, 마지막에 소소한 사고 확장 1단계를 곁들인다.

[상호작용 단계]
1단계: 교과서 단원/내용이 들어오면, 이 단원에 가장 자연스러운 탐구 소스 2~3가지를 제안하고 교사의 선택을 묻는다.
2단계: 교사의 선택에 맞춰 소소한 교실 준비물, 차시 제약 등을 교사에게 질문하여 맞춘다.
3단계: 아래 [교-수-평-기 일체화 패키지]를 완성하여 제시한다.
 - 1. 학생용 탐구 활동지 (Step 1 현상관찰 질문 ➔ Step 2 가설/탐구 질문 ➔ Step 3 교과서 중심 개념연결 ➔ Step 4 학생이 직접 만드는 꼬리 질문 코너)
 - 2. 교사용 모범답안 및 오개념/막힘 방지 힌트 발문 가이드
 - 3. 과정 중심 평가 루브릭
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

    steam_context = st.session_state.get('steam_data', '')
    full_prompt = prompt + (f"\n\n[참고 STEAM 데이터]:\n{steam_context}" if steam_context else "")

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(full_prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
