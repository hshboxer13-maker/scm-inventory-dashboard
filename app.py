import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from sheets_client import load_inventory_df

HISTORY_FILE = "weight_history.csv"

st.set_page_config(page_title="재고 현황 대시보드", page_icon="logo.png", layout="wide")

# ---------------------------------------------------------------------------
# design tokens (dataviz reference palette; hero card intentionally stays
# dark regardless of the app's light/dark theme, matching the requested look)
# ---------------------------------------------------------------------------
BLUE = "#2a78d6"
HERO_BG = "#1a1a19"
HERO_TEXT = "#ffffff"
HERO_SUBTEXT = "#c3c2b7"
HERO_ACCENT = "#3987e5"
MUTED = "#898781"
GRIDLINE = "#e1e0d9"

SEARCH_ICON = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' "
    "fill='none' stroke='%23898781' stroke-width='2' stroke-linecap='round' "
    "stroke-linejoin='round'><circle cx='11' cy='11' r='8'></circle>"
    "<line x1='21' y1='21' x2='16.65' y2='16.65'></line></svg>"
)

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{
        font-family: system-ui, -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    div[data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid {GRIDLINE};
    }}
    button[data-baseweb="tab"] {{
        font-size: 16px;
        font-weight: 700;
        padding: 10px 18px;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {BLUE};
        border-bottom: 3px solid {BLUE};
    }}

    .hero {{
        background: {HERO_BG};
        border-radius: 20px;
        padding: 36px 40px;
        margin-bottom: 28px;
    }}
    .hero h1 {{
        color: {HERO_TEXT};
        font-size: 28px;
        font-weight: 800;
        margin: 0 0 4px 0;
    }}
    .hero p {{
        color: {HERO_SUBTEXT};
        font-size: 14px;
        margin: 0 0 28px 0;
    }}
    .stat-grid {{
        display: flex;
        gap: 48px;
        flex-wrap: wrap;
    }}
    .stat-label {{
        color: {HERO_SUBTEXT};
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .stat-value {{
        color: {HERO_TEXT};
        font-size: 42px;
        font-weight: 800;
        line-height: 1.1;
    }}
    .stat-value .unit {{
        font-size: 22px;
        font-weight: 700;
        color: {HERO_ACCENT};
        margin-left: 4px;
    }}
    .stat-caption {{
        color: {MUTED};
        font-size: 12px;
        margin-top: 6px;
    }}

    .search-title {{
        text-align: center;
        font-size: 22px;
        font-weight: 800;
        color: #0b0b0b;
        margin: 8px 0 20px 0;
    }}
    .search-empty {{
        text-align: center;
        color: {MUTED};
        font-size: 14px;
        padding: 48px 0;
    }}
    div[data-testid="stTextInput"] input {{
        background-color: #f5f5f4;
        background-image: url("{SEARCH_ICON}");
        background-repeat: no-repeat;
        background-position: 18px center;
        background-size: 18px 18px;
        border-radius: 999px;
        border: 1px solid transparent;
        padding: 14px 20px 14px 48px;
        font-size: 15px;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: {BLUE};
        box-shadow: 0 0 0 3px rgba(42, 120, 214, 0.15);
        outline: none;
    }}

    .st-key-refresh_fab {{
        position: fixed;
        right: 22px;
        bottom: 18px;
        width: fit-content !important;
        z-index: 999;
        opacity: 0.35;
        transition: opacity 0.15s ease;
    }}
    .st-key-refresh_fab:hover {{
        opacity: 1;
    }}
    .st-key-refresh_fab button {{
        background: #ffffff;
        border: 1px solid {GRIDLINE};
        border-radius: 999px;
        width: 38px;
        height: 38px;
        padding: 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }}

    .data-table-wrap {{
        max-height: var(--table-height, 480px);
        overflow: auto;
        border: 1px solid {GRIDLINE};
        border-radius: 10px;
    }}
    .data-table-wrap table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}
    .data-table-wrap thead th {{
        position: sticky;
        top: 0;
        background: #fcfcfb;
        text-align: center;
        padding: 10px 14px;
        border-bottom: 1px solid {GRIDLINE};
        font-weight: 700;
        color: #52514e;
        white-space: nowrap;
        z-index: 1;
    }}
    .data-table-wrap tbody td {{
        text-align: center;
        padding: 8px 14px;
        border-bottom: 1px solid {GRIDLINE};
        white-space: nowrap;
    }}
    .data-table-wrap tbody td.col-left {{
        text-align: left;
    }}
    .data-table-wrap tbody tr:hover {{
        background: #f9f9f7;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def record_weight_snapshot(total_weight_ton: float) -> None:
    """오늘 날짜의 마지막 저장 시점 기준으로 총 재고 중량을 히스토리에 기록(같은 날짜는 덮어씀)."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    if os.path.exists(HISTORY_FILE):
        history = pd.read_csv(HISTORY_FILE)
    else:
        history = pd.DataFrame(columns=["날짜", "저장시각", "총중량톤"])

    history = history[history["날짜"] != today]
    new_row = pd.DataFrame(
        [{"날짜": today, "저장시각": now.strftime("%H:%M:%S"), "총중량톤": total_weight_ton}]
    )
    history = pd.concat([history, new_row], ignore_index=True).sort_values("날짜")
    history.to_csv(HISTORY_FILE, index=False)


def load_weight_history() -> pd.DataFrame:
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "저장시각", "총중량톤"])
    return pd.read_csv(HISTORY_FILE)


@st.cache_data(ttl=3600, show_spinner="구글 시트에서 재고 데이터를 불러오는 중...")
def get_data() -> pd.DataFrame:
    df = load_inventory_df()
    record_weight_snapshot(df["중량 합계"].sum() / 1000)
    return df


DETAIL_COLUMNS = ["품목코드", "상품명", "로케이션", "유통기한", "재고", "잔여일수", "잔여 퍼센트", "유통개월"]


def render_table(table: pd.DataFrame, height: int = 480, left_cols=("상품명",)) -> None:
    """헤더는 모두 가운데 정렬, 본문은 left_cols만 좌측 정렬하고 나머지는 가운데 정렬."""
    header_html = "".join(f"<th>{col}</th>" for col in table.columns)
    body_rows = []
    for _, row in table.iterrows():
        cells = "".join(
            f'<td class="{"col-left" if col in left_cols else ""}">{row[col]}</td>'
            for col in table.columns
        )
        body_rows.append(f"<tr>{cells}</tr>")

    html = (
        f'<div class="data-table-wrap" style="--table-height:{height}px;">'
        f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def align_columns(columns, left_cols=("상품명",)) -> dict:
    """상품명(등 left_cols)은 좌측, 나머지 컬럼은 중앙 정렬."""
    return {
        c: st.column_config.Column(c, alignment="left" if c in left_cols else "center")
        for c in columns
    }


if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

st.image("logo.png", width=260)

with st.container(key="refresh_fab"):
    if st.button("🔄", key="refresh_btn", help="새로고침"):
        get_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

df = get_data()
updated_label = st.session_state.last_refresh.strftime("%Y.%m.%d %H:%M")

tab_main, tab_summary, tab_detail, tab_trend = st.tabs(
    ["메인", "품목별 총재고", "재고 상세 현황", "재고 중량 추이"]
)

# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
with tab_main:
    total_items = df["품목코드"].nunique()
    total_stock = int(df["재고"].sum())
    total_weight_ton = df["중량 합계"].sum() / 1000

    st.markdown(
        f"""
        <div class="hero">
            <h1>재고 현황 대시보드</h1>
            <p>구글 시트와 연동된 실시간 재고 요약입니다</p>
            <div class="stat-grid">
                <div>
                    <div class="stat-label">총 품목 수</div>
                    <div class="stat-value">{total_items:,}<span class="unit">개 품목</span></div>
                    <div class="stat-caption">{updated_label} 기준</div>
                </div>
                <div>
                    <div class="stat-label">총 재고 수량</div>
                    <div class="stat-value">{total_stock:,}<span class="unit">개</span></div>
                    <div class="stat-caption">{updated_label} 기준</div>
                </div>
                <div>
                    <div class="stat-label">총 재고 중량</div>
                    <div class="stat-value">{total_weight_ton:,.1f}<span class="unit">톤</span></div>
                    <div class="stat-caption">{updated_label} 기준</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="search-title">재고를 검색해보세요</div>', unsafe_allow_html=True)
    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        query = st.text_input(
            "재고 검색",
            key="main_search",
            placeholder="품목코드 또는 상품명을 검색해보세요",
            label_visibility="collapsed",
        )

    if query:
        mask = df["품목코드"].astype(str).str.contains(query, case=False, na=False) | df[
            "상품명"
        ].str.contains(query, case=False, na=False)
        result = df[mask][DETAIL_COLUMNS].sort_values("재고", ascending=False)
        if result.empty:
            st.info("검색 결과가 없습니다.")
        else:
            st.caption(f"'{query}' 검색 결과 {len(result)}건")
            render_table(result, height=480)
    else:
        st.markdown(
            '<div class="search-empty">품목코드나 상품명을 입력하면 재고 현황을 확인할 수 있어요</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# 품목별 총재고
# ---------------------------------------------------------------------------
with tab_summary:
    st.subheader("품목별 총 재고")

    summary = (
        df.groupby(["품목코드", "상품명"], as_index=False)
        .agg(총재고=("재고", "sum"), 총중량kg=("중량 합계", "sum"))
        .sort_values("총재고", ascending=False)
        .reset_index(drop=True)
    )

    search = st.text_input(
        "품목코드 또는 상품명으로 검색", placeholder="예: 2000001, 크런치", key="summary_search"
    )
    view = summary
    if search:
        mask = summary["품목코드"].astype(str).str.contains(search, case=False, na=False) | summary[
            "상품명"
        ].str.contains(search, case=False, na=False)
        view = summary[mask]

    view_display = view.rename(columns={"총중량kg": "총중량(kg)"})
    config = align_columns(view_display.columns)
    config["총재고"] = st.column_config.NumberColumn("총재고", alignment="center", format="%,d")
    config["총중량(kg)"] = st.column_config.NumberColumn("총중량(kg)", alignment="center", format="%,d")
    st.dataframe(
        view_display,
        use_container_width=True,
        height=560,
        hide_index=True,
        column_config=config,
    )
    st.caption("컬럼 이름을 클릭하면 오름차순/내림차순으로 정렬됩니다.")

# ---------------------------------------------------------------------------
# 재고 상세 현황
# ---------------------------------------------------------------------------
with tab_detail:
    st.subheader("재고 상세 현황")

    search_d = st.text_input(
        "품목코드 또는 상품명으로 검색", placeholder="예: 2000001, 크런치", key="detail_search"
    )
    detail_view = df[DETAIL_COLUMNS]
    if search_d:
        mask = df["품목코드"].astype(str).str.contains(search_d, case=False, na=False) | df[
            "상품명"
        ].str.contains(search_d, case=False, na=False)
        detail_view = df[mask][DETAIL_COLUMNS]

    st.dataframe(
        detail_view,
        use_container_width=True,
        height=650,
        hide_index=True,
        column_config=align_columns(DETAIL_COLUMNS),
    )
    st.caption("컬럼 이름을 클릭하면 오름차순/내림차순으로 정렬됩니다.")

# ---------------------------------------------------------------------------
# 재고 중량 추이
# ---------------------------------------------------------------------------
with tab_trend:
    st.subheader("일자별 총 재고 중량 추이")
    st.caption("매일 마지막으로 새로고침(저장)된 시점의 총 재고 중량을 기록합니다.")

    history = load_weight_history()

    if len(history) < 2:
        st.info("아직 기록된 날짜가 하루뿐이라 추이를 그리기엔 데이터가 부족해요. 내일 이후 새로고침하면 그래프가 이어집니다.")
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        fig = px.line(history, x="날짜", y="총중량톤", markers=True)
        fig.update_traces(
            line=dict(color=BLUE, width=2),
            marker=dict(color=BLUE, size=7),
            hovertemplate="%{x}<br>%{y:,.1f} 톤<extra></extra>",
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(showgrid=False, title=None, dtick="D1", tickformat="%Y-%m-%d"),
            yaxis=dict(showgrid=True, gridcolor=GRIDLINE, title="총 재고 중량 (톤)"),
            margin=dict(l=0, r=10, t=10, b=10),
            height=480,
            font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)
