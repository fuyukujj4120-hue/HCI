import time
import requests
import streamlit as st

# =========================
# 基本設定
# =========================
APP_TITLE = "HCI 實驗分組抽籤系統"

# 請貼上 Google Apps Script 部署後的 /exec 網址
ASSIGNMENT_WEBHOOK_URL = "請貼上你的 Apps Script Web App /exec URL"

ASSIGNMENT_SECRET = "hci_group_assignment_secret"

GROUP_APP_URLS = {
    "A": "https://hci-group1.streamlit.app/",
    "B": "https://hci-group2.streamlit.app/",
}

GROUP_LABELS = {
    "A": "A 組｜特徵導向 → 情緒導向",
    "B": "B 組｜情緒導向 → 特徵導向",
}

GROUP_LIMIT_PER_HOUR = 16

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎰",
    layout="centered",
)

# =========================
# CSS 美化
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top, rgba(255, 238, 196, 0.9), transparent 35%),
            linear-gradient(135deg, #2b1708 0%, #6a3d13 45%, #1b0e05 100%);
    }

    .main-container {
        max-width: 760px;
        margin: 0 auto;
        padding-top: 30px;
    }

    .hero-card {
        background: rgba(255, 250, 240, 0.96);
        border: 2px solid #e7c073;
        border-radius: 26px;
        padding: 34px 34px 30px 34px;
        box-shadow:
            0 18px 45px rgba(0, 0, 0, 0.32),
            inset 0 0 0 1px rgba(255,255,255,0.6);
        text-align: center;
        margin-bottom: 22px;
    }

    .slot-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 34px;
        font-weight: 900;
        color: #3a210b;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }

    .slot-subtitle {
        font-size: 15px;
        color: #8a6841;
        line-height: 1.7;
        margin-bottom: 20px;
    }

    .slot-machine {
        background: linear-gradient(180deg, #8d1515 0%, #4a0808 100%);
        border: 5px solid #f0c15b;
        border-radius: 28px;
        padding: 22px;
        box-shadow:
            inset 0 0 18px rgba(0,0,0,0.35),
            0 8px 25px rgba(0,0,0,0.25);
        margin: 16px auto 20px auto;
    }

    .slot-window {
        background: #fffaf0;
        border: 4px solid #ffd36a;
        border-radius: 18px;
        padding: 28px 18px;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 4px 12px rgba(0,0,0,0.14);
    }

    .slot-reel {
        font-family: 'Noto Serif TC', serif;
        font-size: 42px;
        font-weight: 900;
        color: #3a210b;
        letter-spacing: 0.08em;
    }

    .limit-card {
        background: rgba(255, 250, 240, 0.92);
        border: 1.5px solid #e7c073;
        border-radius: 18px;
        padding: 16px 20px;
        color: #5b3a16;
        font-size: 14px;
        line-height: 1.8;
        margin-bottom: 18px;
    }

    .result-card {
        background: linear-gradient(135deg, #fff9e8 0%, #fff2c7 100%);
        border: 2px solid #f0c15b;
        border-radius: 22px;
        padding: 26px 24px;
        text-align: center;
        box-shadow: 0 10px 28px rgba(0,0,0,0.2);
        margin-top: 22px;
    }

    .result-group {
        font-family: 'Noto Serif TC', serif;
        font-size: 36px;
        font-weight: 900;
        color: #8d1515;
        margin-bottom: 8px;
    }

    .result-label {
        font-size: 19px;
        font-weight: 800;
        color: #3a210b;
        margin-bottom: 14px;
    }

    .result-note {
        font-size: 14px;
        color: #7a5a32;
        line-height: 1.7;
        margin-bottom: 18px;
    }

    .error-card {
        background: #fff2f2;
        border: 2px solid #d9534f;
        border-radius: 18px;
        padding: 18px 20px;
        color: #8a1f1b;
        font-weight: 700;
        text-align: center;
        margin-top: 20px;
    }

    .info-small {
        color: #7a6650;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 8px;
    }

    div[data-testid="stTextInput"] label {
        font-size: 17px !important;
        font-weight: 800 !important;
        color: #fff4d9 !important;
    }

    .stTextInput input {
        background: #fffaf0 !important;
        border: 2px solid #e7c073 !important;
        border-radius: 12px !important;
        color: #2b1708 !important;
        font-size: 16px !important;
        padding: 12px 14px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #f3c65f 0%, #b97a18 100%) !important;
        color: #2b1708 !important;
        border: 2px solid #ffe39a !important;
        border-radius: 999px !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        letter-spacing: 0.08em !important;
        padding: 13px 30px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.28) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 12px 26px rgba(0,0,0,0.34) !important;
    }

    .stLinkButton > a {
        background: linear-gradient(135deg, #8d1515 0%, #4a0808 100%) !important;
        color: #fff8e8 !important;
        border: 2px solid #f0c15b !important;
        border-radius: 999px !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        padding: 12px 30px !important;
        text-decoration: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 後端呼叫
# =========================
def assign_group(participant_id: str):
    if not ASSIGNMENT_WEBHOOK_URL or "請貼上" in ASSIGNMENT_WEBHOOK_URL:
        raise ValueError("尚未設定 Apps Script Web App /exec URL")

    payload = {
        "secret": ASSIGNMENT_SECRET,
        "participant_id": participant_id.strip(),
        "limit_per_group_per_hour": GROUP_LIMIT_PER_HOUR,
    }

    resp = requests.post(ASSIGNMENT_WEBHOOK_URL, json=payload, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "分組失敗"))

    return data


def render_slot_display(text="READY"):
    st.markdown(
        f"""
        <div class="slot-machine">
            <div class="slot-window">
                <div class="slot-reel">{text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def slot_animation():
    placeholder = st.empty()
    reels = ["A 組", "B 組", "🎲", "A 組", "B 組", "🎰", "A 組", "B 組"]

    for i in range(18):
        text = reels[i % len(reels)]
        placeholder.markdown(
            f"""
            <div class="slot-machine">
                <div class="slot-window">
                    <div class="slot-reel">{text}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.07 + i * 0.01)

    return placeholder


# =========================
# Session State
# =========================
if "assigned_result" not in st.session_state:
    st.session_state.assigned_result = None

if "last_participant_id" not in st.session_state:
    st.session_state.last_participant_id = ""


# =========================
# UI
# =========================
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero-card">
        <div style="font-size:52px;margin-bottom:8px;">🎰</div>
        <div class="slot-title">{APP_TITLE}</div>
        <div class="slot-subtitle">
            請輸入受試者代號後按下抽籤。系統會自動分配至 A 組或 B 組。<br>
            每一小時內 A 組與 B 組各最多 {GROUP_LIMIT_PER_HOUR} 人。
        </div>
    """,
    unsafe_allow_html=True,
)

render_slot_display("A / B")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="limit-card">
        <b>分組規則</b><br>
        1. 系統會在 A 組與 B 組之間隨機分配。<br>
        2. 每小時 A 組最多 {GROUP_LIMIT_PER_HOUR} 人，B 組最多 {GROUP_LIMIT_PER_HOUR} 人。<br>
        3. 同一個受試者代號在同一小時內重複抽籤，會回傳原本分配結果。<br>
        4. 若其中一組額滿，系統會自動分配至另一組。
    </div>
    """,
    unsafe_allow_html=True,
)

participant_id = st.text_input(
    "受試者學號／代號",
    placeholder="例如：S001",
).strip()

col1, col2, col3 = st.columns([1, 1.4, 1])
with col2:
    draw_clicked = st.button(
        "開始抽籤",
        type="primary",
        use_container_width=True,
        disabled=not bool(participant_id),
    )

if draw_clicked:
    try:
        slot_placeholder = slot_animation()
        result = assign_group(participant_id)

        assigned_group = result.get("assigned_group")
        label = GROUP_LABELS.get(assigned_group, assigned_group)
        app_url = GROUP_APP_URLS.get(assigned_group, "")

        st.session_state.assigned_result = {
            **result,
            "label": label,
            "app_url": app_url,
        }
        st.session_state.last_participant_id = participant_id

        slot_placeholder.markdown(
            f"""
            <div class="slot-machine">
                <div class="slot-window">
                    <div class="slot-reel">{assigned_group} 組</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.session_state.assigned_result = {
            "error": str(e)
        }

result = st.session_state.assigned_result

if result:
    if result.get("error"):
        st.markdown(
            f"""
            <div class="error-card">
                ⚠️ 抽籤失敗<br>
                {result.get("error")}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        assigned_group = result.get("assigned_group")
        label = result.get("label")
        app_url = result.get("app_url")
        is_existing = result.get("existing_assignment", False)

        existing_text = "此代號已抽過籤，以下為原本分配結果。" if is_existing else "抽籤完成，請依照分配結果進入實驗。"

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-group">你被分配到 {assigned_group} 組</div>
                <div class="result-label">{label}</div>
                <div class="result-note">
                    {existing_text}<br>
                    本小時目前人數：A 組 {result.get("count_a", "-")} 人，B 組 {result.get("count_b", "-")} 人。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if app_url:
            st.link_button(
                "進入實驗頁面",
                app_url,
                use_container_width=True,
            )

st.markdown("</div>", unsafe_allow_html=True)
