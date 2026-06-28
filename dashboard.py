import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(page_title="고객 피드백 대시보드", layout="wide")

RAW = """id,받은날짜,경로,별점,내용,유형
1,2026-05-02,앱리뷰,2,"신메뉴 라떼 시켰는데 너무 달아요. 당도 조절 옵션 있으면 좋겠어요.",요청
2,2026-05-03,설문,,"매장이 항상 깨끗해서 좋아요. 직원분들도 친절하세요.",칭찬
3,2026-05-04,전화메모,,"기프티콘 쓰려는데 앱에서 자꾸 오류나요. 확인 부탁드려요.",불만
4,2026-05-05,앱리뷰,5,"여기 아메리카노 진짜 맛있어요. 완전 단골 됐어요!",칭찬
5,2026-05-06,인스타DM,,"비건 디저트도 있나요? 우유 알레르기가 있어서요.",문의
6,2026-05-07,설문,1,"주문하고 20분 기다렸어요. 너무 오래 걸려요.",불만
7,2026-05-08,앱리뷰,3,"음료는 괜찮은데 자리가 너무 좁아요.",불만
8,2026-05-09,전화메모,,"진동벨이 안 울려서 음료가 다 식었어요. 불만입니다.",불만
9,2026-05-10,설문,4,"시즌 한정 메뉴 자주 나왔으면 좋겠어요.",요청
10,2026-05-11,앱리뷰,2,"와이파이가 자꾸 끊겨요. 카공하기 불편해요.",불만
11,2026-05-12,인스타DM,,"단체 예약도 가능한가요? 10명 정도 인원이에요.",문의
12,2026-05-13,설문,5,"강아지 동반 가능하게 해주셔서 감사해요!",칭찬
13,2026-05-14,앱리뷰,1,"결제는 됐는데 포인트가 안 쌓였어요. 환불해주세요.",불만
14,2026-05-15,전화메모,,"개인 텀블러 가져가면 할인 되나요? 다른 매장은 된다던데.",문의
15,2026-05-16,설문,3,"화장실이 멀고 찾기 어려워요. 안내 표시가 있으면 좋겠어요.",요청
16,2026-05-17,앱리뷰,5,"케이크 퀄리티가 베이커리급이에요. 강력 추천!",칭찬
17,2026-05-18,인스타DM,,"영업시간이 어떻게 되나요? 주말에도 여나요?",문의
18,2026-05-19,설문,2,"가격이 좀 올랐네요. 부담스러워요.",불만
19,2026-05-20,앱리뷰,4,"콘센트 자리가 많아서 좋아요. 조금만 더 있으면 완벽해요.",칭찬
20,2026-05-21,전화메모,,"두고 간 우산 찾으러 가도 될까요?",문의
21,2026-05-22,설문,1,"직원이 주문을 잘못 받았어요. 그것도 두 번이나요.",불만
22,2026-05-23,앱리뷰,5,"라떼아트가 너무 예뻐서 인스타에 올렸어요.",칭찬"""

df = pd.read_csv(StringIO(RAW))

COLOR_MAP = {"불만": "#EF4444", "요청": "#F59E0B", "칭찬": "#10B981", "문의": "#3B82F6"}

# ── Keyword-based Classifier ────────────────────────────────────────────────
_POS_KEYWORDS = ["좋아", "좋아요", "맛있", "친절", "감사", "예뻐", "추천", "완벽", "단골", "깨끗"]

_CAT_KEYWORDS = {
    "금전": ["가격", "올랐", "비싸", "부담", "포인트", "환불", "결제", "할인"],
    "서비스": ["직원", "주문", "기다", "진동벨", "오류", "앱", "와이파이", "끊겨", "식었", "잘못", "좁아", "자리", "화장실", "안내"],
    "맛": ["달아", "당도", "맛없", "싱거"],
}

def _classify(text: str):
    sentiment = "긍정" if any(k in text for k in _POS_KEYWORDS) else "부정"
    for cat, keywords in _CAT_KEYWORDS.items():
        if any(k in text for k in keywords):
            return sentiment, cat
    return sentiment, "기타"

sentiments, categories = zip(*df["내용"].map(_classify))

df = df.copy()
df["감정"] = list(sentiments)
df["AI카테고리"] = list(categories)
df.loc[df["유형"] == "문의", "감정"] = "중립"

# ── TOP 3: 부정 감정만 대상, 긍정은 제외 ──────────────────────────────────
neg_df = df[df["감정"] == "부정"].copy()
neg_df = neg_df.sort_values("받은날짜")  # Rule 1: 오래된 날짜순으로 정렬

cat_counts = neg_df.groupby("AI카테고리").size()
neg_df["카테고리_건수"] = neg_df["AI카테고리"].map(cat_counts)       # Rule 2: 중복 건수
CATEGORY_PRIORITY = {"금전": 3, "서비스": 2, "맛": 1, "기타": 0}
neg_df["카테고리_우선순위"] = neg_df["AI카테고리"].map(CATEGORY_PRIORITY).fillna(0)  # Rule 3
neg_df["별점_긴급도"] = neg_df["별점"].apply(                         # Rule 4: 별점 낮을수록 우선
    lambda x: 0 if pd.isna(x) else (6 - int(x))
)

top3_complaints = (
    neg_df
    .sort_values(["카테고리_건수", "카테고리_우선순위", "별점_긴급도"], ascending=[False, False, False])
    .drop_duplicates(subset=["AI카테고리"])
    .head(3)
)

# ── Dashboard UI ───────────────────────────────────────────────────────────
type_counts = df["유형"].value_counts().reset_index()
type_counts.columns = ["유형", "건수"]

st.title("☕ 카페 고객 피드백 대시보드")
st.caption("기간: 2026-05-02 ~ 2026-05-23 | 총 22건")

col1, col2, col3, col4 = st.columns(4)
for col, label, color in zip(
    [col1, col2, col3, col4],
    ["불만", "요청", "칭찬", "문의"],
    ["#EF4444", "#F59E0B", "#10B981", "#3B82F6"],
):
    cnt = int(type_counts[type_counts["유형"] == label]["건수"].values[0]) if label in type_counts["유형"].values else 0
    col.metric(label=f"{label}", value=f"{cnt}건")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("유형별 분포")
    fig_pie = px.pie(
        type_counts,
        names="유형",
        values="건수",
        color="유형",
        color_discrete_map=COLOR_MAP,
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="label+percent+value", textfont_size=13)
    fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("경로별 피드백 수")
    path_counts = df.groupby(["경로", "유형"]).size().reset_index(name="건수")
    fig_bar = px.bar(
        path_counts,
        x="경로",
        y="건수",
        color="유형",
        color_discrete_map=COLOR_MAP,
        barmode="stack",
        text_auto=True,
    )
    fig_bar.update_layout(margin=dict(t=10, b=10), legend_title_text="유형")
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.subheader("🚨 가장 급한 불만 TOP 3")
st.caption("AI 감정 분류 → 부정만 대상 | 중복 건수 많은순 → 카테고리 우선순위(금전 > 서비스 > 맛) → 별점 낮은순 | 카테고리별 대표 1건")

for rank, (_, row) in enumerate(top3_complaints.iterrows(), 1):
    star_str = f"⭐ {int(row['별점'])}점" if not pd.isna(row["별점"]) else "별점 없음"
    badge_color = "#EF4444" if rank == 1 else ("#F97316" if rank == 2 else "#EAB308")
    cat_label = row["AI카테고리"]
    cat_cnt = int(row["카테고리_건수"])
    st.markdown(
        f"""
        <div style="border-left: 5px solid {badge_color}; padding: 10px 16px; margin-bottom: 10px;
                    background: #FEF2F2; border-radius: 4px;">
            <span style="font-size:18px; font-weight:700; color:{badge_color};">#{rank}</span>
            &nbsp;&nbsp;
            <span style="font-size:12px; font-weight:700; background:{badge_color}; color:white;
                         padding:2px 8px; border-radius:12px;">{cat_label} {cat_cnt}건</span>
            &nbsp;&nbsp;
            <span style="font-size:12px; background:#6B7280; color:white;
                         padding:2px 6px; border-radius:8px;">부정</span>
            &nbsp;&nbsp;
            <span style="font-size:14px; color:#374151;">{row['내용']}</span>
            <br/>
            <span style="font-size:12px; color:#6B7280;">경로: {row['경로']} | {star_str} | 날짜: {row['받은날짜']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("전체 피드백 목록")

type_filter = st.multiselect(
    "유형 필터",
    options=["불만", "요청", "칭찬", "문의"],
    default=["불만", "요청", "칭찬", "문의"],
)

filtered = df[df["유형"].isin(type_filter)][["id", "받은날짜", "경로", "별점", "유형", "감정", "AI카테고리", "내용"]]

def color_type(val):
    c = COLOR_MAP.get(val, "#6B7280")
    return f"color: white; background-color: {c}; border-radius: 4px; padding: 2px 6px; font-weight:600;"

def color_sentiment(val):
    c = {"부정": "#EF4444", "긍정": "#10B981", "중립": "#6B7280"}.get(val, "#6B7280")
    return f"color: white; background-color: {c}; border-radius: 4px; padding: 2px 6px; font-weight:600;"

styled = filtered.style.applymap(color_type, subset=["유형"]).applymap(color_sentiment, subset=["감정"])
st.dataframe(styled, use_container_width=True, hide_index=True)
