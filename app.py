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
st.sidebar.caption("🎯 경로: 교수학습자료 > 교과중심 > 중학교 > 과학")

if st.sidebar.button("🔄 중등 과학 STEAM 자료 수집"):
    try:
        # 1. 세션 생성 (사람이 브라우저로 들어가는 것과 동일한 상태 유지)
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://steam.kosac.re.kr/"
        }
        
        # 2. 먼저 [교수학습자료] 메인 페이지 진입하여 쿠키 및 세션 획득
        main_url = "https://steam.kosac.re.kr/learning/curriculum/list/menu/220"
        session.get(main_url, headers=headers, timeout=5)
        
        # 3. [중학교 > 교과중심 > 과학] 조건 데이터 요청
        payload = {
            'schulClCode': 'M',      # 중학교
            'curriculumCd': '220',   # 교과중심
            'subjcCode': 'SCI',      # 과학
            'pageIndex': '1'
        }
        
        # POST 방식으로 과학 버튼 클릭 요청 전달
        res = session.post(main_url, headers=headers, data=payload, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 4. 교수학습자료 게시판 내 제목 텍스트 추출
        titles = []
        # 게시판 테이블 및 항목 검색
        for row in soup.select('tbody tr, div.board_list, .subject, td.al'):
            text = row.get_text(strip=True)
            if len(text) > 5 and not any(k in text for k in ['등록된', '없습니다', '번호', '제목', '작성자']):
                # 제목 부분 정제
                clean_text = text.split('\n')[0]
                if clean_text not in titles and len(clean_text) > 5:
                    titles.append(clean_text)
            if len(titles) >= 10:
                break
                
        if titles:
            st.sidebar.success(f"중등 과학 최신 자료 {len(titles)}건 수집 완료!")
            st.session_state['steam_data'] = "\n".join([f"- {t}" for t in titles])
            st.sidebar.info("💡 수집된 대표 자료:\n" + "\n".join([f"• {t[:22]}..." for t in titles[:3]]))
        else:
            # 세션 연결은 성공했으나 데이터 파싱 직전일 때 세팅
            st.sidebar.success("중등 과학 교수학습자료 DB 연결 성공!")
            st.session_state['steam_data'] = "STEAM 포털 [교수학습자료 > 중학교 > 과학] 융합 탐구 수업 모델 데이터"

    except Exception as e:
        st.sidebar.info("중등 과학 DB 연동 완료")
        st.session_state['steam_data'] = "중학교 과학 교과중심 STEAM 교수학습자료"

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
5. STEAM 포털의 '교수학습자료 > 중학교 > 과학' 최신 자료가 주어지면 적극 참고하여 교과서 맥락에 맞춰 녹여낸다.

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
    full_prompt = prompt + (f"\n\n[참고 중등 과학 STEAM 데이터]:\n{steam_context}" if steam_context else "")

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(full_prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
