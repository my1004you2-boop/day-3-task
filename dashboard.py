import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="고객 피드백 대시보드", layout="wide")

COLOR_MAP = {"불만": "#EF4444", "요청": "#F59E0B", "칭찬": "#10B981", "문의": "#3B82F6"}

_POS_KEYWORDS = [
    "좋아", "좋아요", "맛있", "친절", "감사", "예뻐", "추천", "완벽", "단골", "깨끗", "편안", "재방문",
    "쉬웠", "신선", "청결", "빨랐", "기대", "만족", "편리", "좋았",
]
_INQ_KEYWORDS = ["인가요", "되나요", "있나요", "어떻게", "가능한가요", "찾으러", "영업시간", "여나요"]
_REQ_KEYWORDS = ["있으면", "좋겠어요", "해주세요", "해줬으면", "원해요", "요청", "개선", "늘려주"]

_CAT_KEYWORDS = {
    "금전": ["가격", "올랐", "비싸", "부담", "포인트", "환불", "결제", "할인", "적립"],
    "서비스": [
        "직원", "주문", "기다", "진동벨", "오류", "앱", "와이파이", "끊겨", "식었", "잘못",
        "좁아", "자리", "화장실", "안내", "느려", "음악", "주차", "배달", "불편",
    ],
    "맛": ["달아", "당도", "맛없", "싱거", "미지근", "음료"],
}


def _classify_type(text: str) -> str:
    if any(k in text for k in _INQ_KEYWORDS):
        return "문의"
    if any(k in text for k in _REQ_KEYWORDS):
        return "요청"
    if any(k in text for k in _POS_KEYWORDS):
        return "칭찬"
    return "불만"


def _classify_sentiment_category(text: str):
    sentiment = "긍정" if any(k in text for k in _POS_KEYWORDS) else "부정"
    for cat, keywords in _CAT_KEYWORDS.items():
        if any(k in text for k in keywords):
            return sentiment, cat
    return sentiment, "기타"


def load_data(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    missing = {"내용"} - set(df.columns)
    if missing:
        st.error(f"파일에 필수 컬럼이 없습니다: {', '.join(missing)}")
        st.stop()

    if "유형" not in df.columns:
        df["유형"] = df["내용"].astype(str).map(_classify_type)

    return df


def render_type_cards(counts: dict) -> None:
    cols = st.columns(4)
    for col, label in zip(cols, ["불만", "요청", "칭찬", "문의"]):
        color = COLOR_MAP[label]
        value = counts.get(label, "—")
        display = f"{value}건" if isinstance(value, int) else value
        col.markdown(
            f"""
            <div style="background:{color}; border-radius:10px; padding:18px 16px 14px;
                        text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.15);">
                <div style="font-size:14px; font-weight:600; color:rgba(255,255,255,0.85);
                            letter-spacing:1px; margin-bottom:6px;">{label}</div>
                <div style="font-size:32px; font-weight:800; color:white;">{display}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def empty_pie() -> go.Figure:
    fig = go.Figure(go.Pie(values=[1, 1, 1, 1], labels=["불만", "요청", "칭찬", "문의"],
                           marker_colors=["#E5E7EB"] * 4, hole=0.4,
                           textinfo="none", hoverinfo="none"))
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10),
                      annotations=[dict(text="데이터 없음", x=0.5, y=0.5,
                                        font_size=14, font_color="#9CA3AF", showarrow=False)])
    return fig


def empty_bar() -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="데이터 없음", xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=14, color="#9CA3AF"))
    fig.update_layout(margin=dict(t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      plot_bgcolor="#F9FAFB", paper_bgcolor="#F9FAFB", height=300)
    return fig


PLACEHOLDER_CARD = """
<div style="border-left: 5px solid {color}; padding: 10px 16px; margin-bottom: 10px;
            background: #F9FAFB; border-radius: 4px;">
    <span style="font-size:18px; font-weight:700; color:{color};">#{rank}</span>
    &nbsp;&nbsp;
    <span style="font-size:12px; font-weight:700; background:#D1D5DB; color:#6B7280;
                 padding:2px 8px; border-radius:12px;">— 건</span>
    &nbsp;&nbsp;
    <span style="font-size:14px; color:#D1D5DB;">피드백 내용이 여기에 표시됩니다.</span>
    <br/>
    <span style="font-size:12px; color:#D1D5DB;">경로: — | 별점 없음 | 날짜: —</span>
</div>
"""


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 데이터 업로드")
    uploaded_file = st.file_uploader(
        "CSV 또는 XLSX 파일을 업로드하세요",
        type=["csv", "xlsx", "xls"],
        help="컬럼: id, 받은날짜, 경로, 별점, 내용, 유형(선택)\n유형 컬럼이 없으면 자동 분류됩니다.",
    )

    if uploaded_file is not None:
        st.success(f"✅ {uploaded_file.name} 로드됨")
    else:
        st.info("CSV 또는 XLSX 파일을 업로드하면\n대시보드가 활성화됩니다.")


# ── Title ─────────────────────────────────────────────────────────────────────
st.title("☕ 카페 고객 피드백 대시보드")

# ── No file uploaded: skeleton UI ────────────────────────────────────────────
if uploaded_file is None:
    st.caption("파일을 업로드하면 데이터가 표시됩니다.")

    render_type_cards({})

    st.divider()

    # TOP 3 (skeleton)
    st.subheader("🚨 가장 급한 불만 TOP 3")
    st.caption("AI 감정 분류 → 부정만 대상 | 중복 건수 많은순 → 카테고리 우선순위(금전 > 서비스 > 맛) → 별점 낮은순 | 카테고리별 대표 1건")
    badge_colors = ["#EF4444", "#F97316", "#EAB308"]
    for rank in range(1, 4):
        st.markdown(PLACEHOLDER_CARD.format(rank=rank, color=badge_colors[rank - 1]),
                    unsafe_allow_html=True)

    st.divider()

    # Charts (skeleton)
    left, right = st.columns([1, 1])
    with left:
        st.subheader("유형별 분포")
        st.plotly_chart(empty_pie(), use_container_width=True)
    with right:
        st.subheader("경로별 피드백 수")
        st.plotly_chart(empty_bar(), use_container_width=True)

    st.divider()

    # Table (skeleton)
    st.subheader("전체 피드백 목록")
    st.multiselect("유형 필터", options=["불만", "요청", "칭찬", "문의"],
                   default=["불만", "요청", "칭찬", "문의"])
    st.dataframe(
        pd.DataFrame(columns=["id", "받은날짜", "경로", "별점", "유형", "감정", "AI카테고리", "내용"]),
        use_container_width=True, hide_index=True,
    )
    st.stop()

# ── Load & Enrich Data ────────────────────────────────────────────────────────
df = load_data(uploaded_file)

sentiments, categories = zip(*df["내용"].astype(str).map(_classify_sentiment_category))
df = df.copy()
df["감정"] = list(sentiments)
df["AI카테고리"] = list(categories)
df.loc[df["유형"] == "문의", "감정"] = "중립"

# ── TOP 3 ─────────────────────────────────────────────────────────────────────
neg_df = df[df["감정"] == "부정"].copy()
if "받은날짜" in neg_df.columns:
    neg_df = neg_df.sort_values("받은날짜")

cat_counts = neg_df.groupby("AI카테고리").size()
neg_df["카테고리_건수"] = neg_df["AI카테고리"].map(cat_counts)
CATEGORY_PRIORITY = {"금전": 3, "서비스": 2, "맛": 1, "기타": 0}
neg_df["카테고리_우선순위"] = neg_df["AI카테고리"].map(CATEGORY_PRIORITY).fillna(0)
neg_df["별점_긴급도"] = (
    neg_df["별점"].apply(lambda x: 0 if pd.isna(x) else (6 - int(float(x))))
    if "별점" in neg_df.columns else 0
)

top3_complaints = (
    neg_df
    .sort_values(["카테고리_건수", "카테고리_우선순위", "별점_긴급도"], ascending=[False, False, False])
    .drop_duplicates(subset=["AI카테고리"])
    .head(3)
)

# ── Dashboard UI ──────────────────────────────────────────────────────────────
type_counts = df["유형"].value_counts().reset_index()
type_counts.columns = ["유형", "건수"]

total = len(df)
date_range = ""
if "받은날짜" in df.columns:
    dates = pd.to_datetime(df["받은날짜"], errors="coerce").dropna()
    if not dates.empty:
        date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')} | "

st.caption(f"기간: {date_range}총 {total}건 | 출처: {uploaded_file.name}")

type_cnt_map = {
    label: int(type_counts[type_counts["유형"] == label]["건수"].values[0])
    if label in type_counts["유형"].values else 0
    for label in ["불만", "요청", "칭찬", "문의"]
}
render_type_cards(type_cnt_map)

st.divider()

# ── TOP 3 (data) ──────────────────────────────────────────────────────────────
st.subheader("🚨 가장 급한 불만 TOP 3")
st.caption("AI 감정 분류 → 부정만 대상 | 중복 건수 많은순 → 카테고리 우선순위(금전 > 서비스 > 맛) → 별점 낮은순 | 카테고리별 대표 1건")

if top3_complaints.empty:
    st.info("부정 감정의 피드백이 없습니다.")
else:
    for rank, (_, row) in enumerate(top3_complaints.iterrows(), 1):
        has_star = "별점" in row and not pd.isna(row.get("별점"))
        star_str = f"⭐ {int(float(row['별점']))}점" if has_star else "별점 없음"
        badge_color = "#EF4444" if rank == 1 else ("#F97316" if rank == 2 else "#EAB308")
        cat_label = row["AI카테고리"]
        cat_cnt = int(row["카테고리_건수"])
        path_str = row["경로"] if "경로" in row and pd.notna(row.get("경로")) else "-"
        date_str = row["받은날짜"] if "받은날짜" in row and pd.notna(row.get("받은날짜")) else "-"
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
                <span style="font-size:12px; color:#6B7280;">경로: {path_str} | {star_str} | 날짜: {date_str}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
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
    if "경로" in df.columns:
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
    else:
        st.subheader("AI 카테고리별 분포")
        cat_dist = df["AI카테고리"].value_counts().reset_index()
        cat_dist.columns = ["카테고리", "건수"]
        fig_bar = px.bar(cat_dist, x="카테고리", y="건수", text_auto=True)
        fig_bar.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("전체 피드백 목록")

type_filter = st.multiselect(
    "유형 필터",
    options=df["유형"].unique().tolist(),
    default=df["유형"].unique().tolist(),
)

display_cols = [c for c in ["id", "받은날짜", "경로", "별점", "유형", "감정", "AI카테고리", "내용"] if c in df.columns]
filtered = df[df["유형"].isin(type_filter)][display_cols]


def color_type(val):
    c = COLOR_MAP.get(val, "#6B7280")
    return f"color: white; background-color: {c}; border-radius: 4px; padding: 2px 6px; font-weight:600;"


def color_sentiment(val):
    c = {"부정": "#EF4444", "긍정": "#10B981", "중립": "#6B7280"}.get(val, "#6B7280")
    return f"color: white; background-color: {c}; border-radius: 4px; padding: 2px 6px; font-weight:600;"


styled = filtered.style.applymap(color_type, subset=["유형"])
if "감정" in display_cols:
    styled = styled.applymap(color_sentiment, subset=["감정"])

st.dataframe(styled, use_container_width=True, hide_index=True)
