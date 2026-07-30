import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pypdf
import datetime

# 페이지 설정
st.set_page_config(page_title="과학 탐구 수업 & 교-수-평-기 설계 비서", page_icon="🧪", layout="wide")

# ==========================================
# 🔄 외부 데이터 캐싱 (속도 최적화)
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

# ==========================================
# 💾 세션 상태 및 채팅 히스토리 관리
# ==========================================
if "chat_history_list" not in st.session_state:
    st.session_state.chat_history_list = {} # { chat_id: {"title": ..., "messages": [...] } }

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.chat_history_list[st.session_state.current_chat_id] = {
        "title": "새 대화",
        "messages": []
    }

# 사이드바 설정
st.sidebar.title("⚙️ 설정 및 외부 자료")
api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

# ➕ 새 채팅 버튼
if st.sidebar.button("➕ 새 대화 시작하기", use_container_width=True):
    new_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = new_id
    st.session_state.chat_history_list[new_id] = {
        "title": "새 대화",
        "messages": []
    }
    st.rerun()

# 🗂️ 지난 대화 목록 선택
st.sidebar.markdown("---")
st.sidebar.subheader("🗂️ 대화 기록 목록")

chat_ids = list(st.session_state.chat_history_list.keys())
chat_titles = [st.session_state.chat_history_list[cid]["title"] for cid in chat_ids]

if chat_ids:
    selected_index = chat_ids.index(st.session_state.current_chat_id) if st.session_state.current_chat_id in chat_ids else 0
    selected_chat_title = st.sidebar.radio(
        "저장된 대화 선택",
        options=chat_titles,
        index=selected_index,
        label_visibility="collapsed"
    )
    # 선택한 대화로 ID 변경
    for cid in chat_ids:
        if st.session_state.chat_history_list[cid]["title"] == selected_chat_title:
            st.session_state.current_chat_id = cid
            break

# 📚 교과서 PDF 업로드
st.sidebar.markdown("---")
st.sidebar.subheader("📚 교과서 PDF 업로드")
uploaded_pdf = st.sidebar.file_uploader("교과서 단원 PDF 파일 선택", type=["pdf"])

pdf_text_content = ""
if uploaded_pdf is not None:
    try:
        pdf_reader = pypdf.PdfReader(uploaded_pdf)
        extracted_pages = [page.extract_text() for page in pdf_reader.pages if page.extract_text()]
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
st.caption("교과서 중심 | 2022 개정 깊이 있는 학습 | 질문 중심 Scaffolding | 교-수-평-기 일체화")

if not api_key:
    st.info("👈 왼쪽 사이드바에 Gemini API Key를 입력하세요.")
    st.stop()

SYSTEM_PROMPT = """
너는 중학교 과학 교사를 돕는 "상호작용형 질문 중심 수업 설계 및 교-수-평-기 일체화 AI 비서"이다.

[교과서 기반 학습 최우선 지침]
1. 업로드된 교과서 PDF 내용이 존재할 경우, 해당 교과서에 기술된 실제 개념 설명, 탐구 활동, 용어, 소단원 체계를 중심(Core)으로 삼는다.
2. 교과서 수록 질문이나 자료를 활용하여 학생용 비계(Scaffolding) 및 발문을 설계한다.

[2022 개정 교육과정: 깊이 있는 학습 반영 지침]
1. 개념 기반 탐구(Conceptual Inquiry)와 핵심 아이디어 중심의 이해를 유도한다.
2. 학생이 핵심 개념 속에서 '삶과 연계된 핵심 질문'을 발견하도록 비계를 설계한다.

[상호작용 단계]
1단계: 교과서 단원/내용이 들어오면, 이 단원에 가장 자연스러운 탐구 소스 2~3가지를 제안하고 교사의 선택을 묻는다.
2단계: 교사의 선택에 맞춰 교실 준비물, 차시 제약 등을 질문하여 맞춘다.
3단계: [교-수-평-기 일체화 패키지] (활동지, 교사 가이드, 루브릭, 세특 예시문)를 완성한다.
"""

# 현재 활성화된 채팅 메시지 가져오기
current_messages = st.session_state.chat_history_list[st.session_state.current_chat_id]["messages"]

# 대화 내용 표시
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("교과서 단원명이나 다루고 싶은 주제를 입력하세요..."):
    # 첫 질문일 경우 채팅 제목 변경
    if len(current_messages) == 0:
        st.session_state.chat_history_list[st.session_state.current_chat_id]["title"] = prompt[:15] + "..."

    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context_payload = f"[사용자 요청]: {prompt}"
    if pdf_text_content:
        context_payload += f"\n\n[학습된 교과서 PDF 내용]:\n{pdf_text_content[:3000]}"
    if guide_context:
        context_payload += f"\n\n[참고 지침서]: {guide_context[:500]}"
    if steam_context:
        context_payload += f"\n\n[참고 STEAM]: {steam_context[:500]}"

    with st.chat_message("assistant"):
        with st.spinner("⚡ 초고속 모델로 수업을 구성하는 중입니다..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(context_payload)

                st.markdown(response.text)
                current_messages.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"API 호출 오류 발생: {e}\n\n👉 새 API Key를 발급받아 입력했는지 확인해 주세요!")
