import json
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

APP_PAGE_TITLE = "家貓情緒標註系統｜第 2 組"
OUTPUT_CSV = Path("hci_cat_annotation_group2.csv")
GROUP_ID = "2"

SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyMDrGh8WRV-ZyuEFY8uzmVASLSm9JEfZC4pqqGg398KFT8uKWBpNXaLO-9NGGqM17vLQ/exec"
SHEET_SECRET = "hci_cat_annotation_secret"

IMAGE_SET_1 = [
    {"image_id": "set1_preview_001", "path": ""},
    {"image_id": "set1_preview_002", "path": ""},
    {"image_id": "set1_preview_003", "path": ""},
]

IMAGE_SET_2 = [
    {"image_id": "set2_preview_001", "path": ""},
    {"image_id": "set2_preview_002", "path": ""},
    {"image_id": "set2_preview_003", "path": ""},
]

STAGE_PLAN = [
    {
        "stage_name": "第一階段",
        "flow_type": "B",
        "flow_name": "情緒導向",
        "photo_set_name": "照片組 1",
        "images": IMAGE_SET_1,
        "description": "先選擇初步情緒，再檢查部位特徵，最後確認或修改情緒。",
    },
    {
        "stage_name": "第二階段",
        "flow_type": "A",
        "flow_name": "特徵導向",
        "photo_set_name": "照片組 2",
        "images": IMAGE_SET_2,
        "description": "先標註眼睛、耳朵、尾巴、身體姿勢，再選擇最終情緒。",
    },
]

st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide")

DATA_COLUMNS = [
    "group_id",
    "stage_name",
    "photo_set_name",
    "participant_id",
    "flow_type",
    "image_id",
    "initial_emotion",
    "selected_features",
    "final_emotion",
    "uncertain_reason",
    "uncertain_other_text",
    "confidence",
    "annotation_time",
    "emotion_changed",
    "workload_score",
    "clarity_score",
    "confidence_score",
    "usefulness_score",
    "intention_score",
    "open_feedback",
]

EMOTION_OPTIONS = [
    "害怕",
    "生氣",
    "滿意",
    "好奇",
    "中性",
    "其他／無法判斷",
]

FEATURE_OPTIONS = {
    "眼睛": [
        "瞳孔放大",
        "眼睛半閉",
        "直視或凝視",
        "目光集中",
        "眼睛狀態不明顯",
        "無法觀察",
        "其他",
    ],
    "耳朵": [
        "耳朵後壓",
        "耳朵側壓",
        "耳朵自然",
        "耳朵朝向刺激來源",
        "耳朵狀態不明顯",
        "無法觀察",
        "其他",
    ],
    "尾巴": [
        "尾巴快速擺動",
        "尾巴放鬆",
        "尾巴夾起或壓低",
        "尾巴豎起或水平",
        "尾巴狀態不明顯",
        "無法觀察",
        "其他",
    ],
    "身體姿勢": [
        "身體壓低",
        "身體緊繃",
        "姿勢放鬆",
        "身體前傾或探索姿勢",
        "整體狀態平穩",
        "無法觀察",
        "其他",
    ],
}

UNCERTAIN_REASONS = [
    "影像品質不足",
    "線索不足",
    "多種情緒並存",
    "超出現有分類",
    "其他",
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

    /* ── Global reset & base ── */
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }

    /* Subtle warm parchment background */
    .stApp {
        background: #f7f4ef;
    }

    /* ── Main title ── */
    .main-title {
        font-family: 'Noto Serif TC', serif;
        font-size: 26px;
        font-weight: 700;
        color: #1a1208;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
        line-height: 1.35;
    }

    /* ── Headings override ── */
    h2 {
        font-family: 'Noto Serif TC', serif !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #2c1f0e !important;
        letter-spacing: 0.03em !important;
        margin-top: 28px !important;
        margin-bottom: 10px !important;
        padding-bottom: 6px;
        border-bottom: 2px solid #d4b896;
    }

    h3 {
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #4a3520 !important;
        letter-spacing: 0.04em !important;
        margin-top: 20px !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
    }

    h4 {
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #5c4433 !important;
        margin-top: 14px !important;
        margin-bottom: 6px !important;
    }

    /* ── Subtitle ── */
    .sub-title {
        color: #7a6650;
        font-size: 14px;
        font-weight: 300;
        margin-bottom: 24px;
        letter-spacing: 0.02em;
    }

    /* ── Cards ── */
    .flow-card {
        padding: 16px 20px;
        border: 1px solid #e0d4c0;
        border-left: 4px solid #c9a96e;
        border-radius: 4px;
        background: #fffdf8;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(180,140,80,0.07);
        transition: box-shadow 0.2s;
        font-size: 14px;
        line-height: 1.7;
        color: #3b2e1e;
    }

    .flow-card:hover {
        box-shadow: 0 3px 12px rgba(180,140,80,0.14);
    }

    .active-card {
        padding: 14px 20px;
        border: 1.5px solid #b07d3a;
        border-left: 5px solid #b07d3a;
        border-radius: 4px;
        background: linear-gradient(135deg, #fffdf5 0%, #fff8e8 100%);
        margin-bottom: 16px;
        box-shadow: 0 2px 10px rgba(176,125,58,0.12);
        font-size: 14px;
        line-height: 1.7;
        color: #3b2e1e;
    }

    /* ── Warning box ── */
    .warn-box {
        padding: 12px 16px;
        border-radius: 4px;
        background: #fffbf0;
        border: 1px solid #e8c76d;
        border-left: 4px solid #e8a800;
        margin: 10px 0 16px 0;
        font-size: 13px;
        color: #5a4000;
    }

    /* ── Placeholder image area ── */
    .placeholder {
        height: 400px;
        border: 1.5px dashed #c9b08a;
        border-radius: 8px;
        background: linear-gradient(160deg, #faf6ef 0%, #f0e9db 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #9e8060;
        font-size: 16px;
        font-weight: 500;
        text-align: center;
        padding: 20px;
        letter-spacing: 0.04em;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        width: 480px !important;
        min-width: 480px !important;
        background: #fdf9f3 !important;
        border-right: 1px solid #e0d4c0;
    }

    section[data-testid="stSidebar"] img {
        max-height: 480px;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(140,100,40,0.15);
    }

    section[data-testid="stSidebar"] h3 {
        color: #4a3520 !important;
        border-bottom: 1px solid #e0d4c0 !important;
        padding-bottom: 6px;
        text-transform: none !important;
    }

    /* ── Streamlit widget tweaks ── */
    div[data-testid="stRadio"] > label {
        font-size: 14px !important;
        color: #3b2e1e !important;
    }

    div[data-testid="stRadio"] > div {
        gap: 6px !important;
    }

    /* Radio button accent */
    div[data-testid="stRadio"] input[type="radio"]:checked + div {
        color: #b07d3a !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #b07d3a 0%, #8c5f20 100%) !important;
        color: #fffdf8 !important;
        border: none !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 8px rgba(140,95,32,0.25) !important;
        transition: all 0.2s !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(140,95,32,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary / default button */
    .stButton > button:not([kind="primary"]) {
        background: #fffdf8 !important;
        color: #5c4433 !important;
        border: 1.5px solid #c9a96e !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 13px !important;
        transition: all 0.2s !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: #f5ede0 !important;
        border-color: #b07d3a !important;
    }

    /* Text input */
    .stTextInput input, .stTextArea textarea {
        background: #fffdf8 !important;
        border: 1.5px solid #d4c4a8 !important;
        border-radius: 4px !important;
        color: #1a1208 !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 14px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #b07d3a !important;
        box-shadow: 0 0 0 3px rgba(176,125,58,0.12) !important;
    }

    /* Divider */
    hr {
        border-color: #e0d4c0 !important;
        margin: 16px 0 !important;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 4px !important;
        font-size: 13px !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #fffdf8 !important;
        color: #5c4433 !important;
        border: 1.5px solid #c9a96e !important;
        border-radius: 4px !important;
        font-family: 'Noto Sans TC', sans-serif !important;
        font-size: 13px !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f0e9db; }
    ::-webkit-scrollbar-thumb { background: #c9a96e; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_stage_plan():
    return STAGE_PLAN


def init_state():
    defaults = {
        "participant_id": "",
        "page": "intro",
        "stage_index": 0,
        "image_index": 0,
        "task_start_time": None,
        "pending_stage_records": [],
        "pending_cloud_rows": [],
        "cloud_sync_attempted": False,
        "last_save_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_stage():
    return get_stage_plan()[st.session_state.stage_index]


def current_image():
    stage = current_stage()
    images = stage["images"]
    if st.session_state.image_index >= len(images):
        return None
    return images[st.session_state.image_index]


def reset_task_timer():
    st.session_state.task_start_time = time.time()


def reset_all():
    st.session_state.page = "intro"
    st.session_state.stage_index = 0
    st.session_state.image_index = 0
    st.session_state.task_start_time = None
    st.session_state.pending_stage_records = []
    st.session_state.pending_cloud_rows = []
    st.session_state.cloud_sync_attempted = False
    st.session_state.last_save_message = ""


def append_records_to_google_sheet(records):
    if not SHEET_WEBHOOK_URL.strip():
        return False, "尚未設定 SHEET_WEBHOOK_URL，因此只儲存本機 CSV。"

    payload = {
        "secret": SHEET_SECRET,
        "records": records,
    }
    resp = requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "Unknown Google Sheet error"))
    return True, f"已同步 {data.get('inserted', len(records))} 筆到 Google Sheet。"


def save_records(records):
    """只把資料寫入本機 CSV，不做雲端同步（雲端同步統一在完成頁面處理）。"""
    rows = [{col: record.get(col, "") for col in DATA_COLUMNS} for record in records]
    df_new = pd.DataFrame(rows, columns=DATA_COLUMNS)

    if OUTPUT_CSV.exists():
        df_old = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        for col in DATA_COLUMNS:
            if col not in df_old.columns:
                df_old[col] = ""
        df_old = df_old[DATA_COLUMNS]
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = df_all[DATA_COLUMNS]
    df_all.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    # 把這批 rows 加入「待上傳」清單，等全部完成後統一送雲端
    st.session_state.setdefault("pending_cloud_rows", []).extend(rows)


def sync_to_cloud():
    """把 pending_cloud_rows 全部送到 Google Sheet。成功後清空 pending，失敗保留以便重試。"""
    rows = st.session_state.get("pending_cloud_rows", [])
    if not rows:
        return True, "沒有需要同步的資料。"

    ok, msg = append_records_to_google_sheet(rows)
    if ok:
        st.session_state["pending_cloud_rows"] = []
    st.session_state["last_save_message"] = msg
    return ok, msg



def go_previous_page():
    """返回上一頁，不刪除已儲存的 CSV。主要用於流程預覽與操作修正。"""
    page = st.session_state.get("page", "intro")

    if page == "task":
        if st.session_state.image_index > 0:
            st.session_state.image_index -= 1
            if st.session_state.pending_stage_records:
                st.session_state.pending_stage_records.pop()
            reset_task_timer()
        elif st.session_state.stage_index > 0:
            st.session_state.stage_index -= 1
            prev_stage = get_stage_plan()[st.session_state.stage_index]
            st.session_state.image_index = max(len(prev_stage["images"]) - 1, 0)
            st.session_state.page = "task"
            reset_task_timer()
        else:
            st.session_state.page = "intro"

    elif page == "stage_questionnaire":
        stage = current_stage()
        st.session_state.page = "task"
        st.session_state.image_index = max(len(stage["images"]) - 1, 0)
        reset_task_timer()

    elif page == "done":
        st.session_state.page = "stage_questionnaire"

    else:
        st.session_state.page = "intro"

    st.rerun()


def render_back_button():
    if st.session_state.get("page") != "intro":
        if st.button("← 上一頁"):
            go_previous_page()



def render_placeholder(image_id):
    st.markdown(
        f'<div class="placeholder">圖片預覽區<br>目前尚未放入實際照片<br>image_id：{image_id}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_image():
    with st.sidebar:
        stage = current_stage()
        image = current_image()
        st.markdown("### 家貓照片")
        st.caption(f"{stage['stage_name']}｜版本 {stage['flow_type']}｜{stage['photo_set_name']}")
        if image is None:
            st.info("此階段已完成。")
            return
        st.caption(f"image_id：{image['image_id']}")
        path = image.get("path", "")
        if path and Path(path).exists():
            st.image(path, use_container_width=True)
        else:
            render_placeholder(image["image_id"])


def build_selected_features(feature_values, feature_other_text):
    result = {}
    for group_name, choice in feature_values.items():
        if choice == "其他":
            text = feature_other_text.get(group_name, "").strip()
            result[group_name] = f"其他：{text}" if text else "其他"
        else:
            result[group_name] = choice or ""
    return json.dumps(result, ensure_ascii=False)


def render_feature_selector(prefix):
    feature_values = {}
    feature_other_text = {}
    for group_name, options in FEATURE_OPTIONS.items():
        st.markdown(f"#### {group_name}")
        choice = st.radio(
            f"請選擇{group_name}最符合的觀察結果",
            options,
            index=None,
            key=f"{prefix}_feature_{group_name}",
        )
        feature_values[group_name] = choice or ""
        if choice == "其他":
            feature_other_text[group_name] = st.text_input(
                f"請補充{group_name}其他特徵",
                key=f"{prefix}_feature_other_{group_name}",
            )
        else:
            feature_other_text[group_name] = ""
        st.divider()
    return feature_values, feature_other_text


def render_uncertain_reason(prefix, final_emotion):
    if final_emotion != "其他／無法判斷":
        return "", ""
    st.markdown("### 其他／無法判斷原因")
    reason = st.radio(
        "若選擇其他／無法判斷，請記錄原因",
        UNCERTAIN_REASONS,
        index=None,
        key=f"{prefix}_uncertain_reason",
    )
    other_text = ""
    if reason == "其他":
        other_text = st.text_input("請補充其他原因", key=f"{prefix}_uncertain_other_text")
    return reason or "", other_text


def build_base_record(stage, image, initial_emotion, selected_features, final_emotion, uncertain_reason, uncertain_other_text, confidence):
    annotation_time = round(time.time() - st.session_state.task_start_time, 2)
    if stage["flow_type"] == "B":
        emotion_changed = str(initial_emotion != final_emotion)
    else:
        emotion_changed = ""

    return {
        "group_id": GROUP_ID,
        "stage_name": stage["stage_name"],
        "photo_set_name": stage["photo_set_name"],
        "participant_id": st.session_state.participant_id,
        "flow_type": stage["flow_type"],
        "image_id": image["image_id"],
        "initial_emotion": initial_emotion,
        "selected_features": selected_features,
        "final_emotion": final_emotion,
        "uncertain_reason": uncertain_reason,
        "uncertain_other_text": uncertain_other_text,
        "confidence": confidence,
        "annotation_time": annotation_time,
        "emotion_changed": emotion_changed,
        "workload_score": "",
        "clarity_score": "",
        "confidence_score": "",
        "usefulness_score": "",
        "intention_score": "",
        "open_feedback": "",
    }


def go_next_image_or_questionnaire(record):
    st.session_state.pending_stage_records.append(record)
    stage = current_stage()
    st.session_state.image_index += 1
    st.session_state.task_start_time = None
    if st.session_state.image_index >= len(stage["images"]):
        st.session_state.page = "stage_questionnaire"
    st.rerun()


def render_flow_a(stage, image, prefix):
    st.markdown("## Step 1：觀看家貓照片")
    st.write("請先觀察左側照片，再進行部位特徵標註。")

    st.markdown("## Step 2：標註部位特徵")
    feature_values, feature_other_text = render_feature_selector(prefix)

    st.markdown("## Step 3：根據前述特徵選擇最終情緒")
    final_emotion = st.radio(
        "最終情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_final_emotion",
    )

    uncertain_reason, uncertain_other_text = render_uncertain_reason(prefix, final_emotion or "")

    st.markdown("## Step 4：填寫標註信心程度")
    confidence = st.radio(
        "標註信心程度",
        [1, 2, 3, 4, 5],
        index=None,
        horizontal=True,
        key=f"{prefix}_confidence",
    )

    required_ok = bool(final_emotion) and confidence is not None
    if final_emotion == "其他／無法判斷" and not uncertain_reason:
        required_ok = False

    if st.button("送出此張標註", type="primary", disabled=not required_ok):
        record = build_base_record(
            stage=stage,
            image=image,
            initial_emotion="",
            selected_features=build_selected_features(feature_values, feature_other_text),
            final_emotion=final_emotion,
            uncertain_reason=uncertain_reason,
            uncertain_other_text=uncertain_other_text,
            confidence=confidence,
        )
        go_next_image_or_questionnaire(record)


def render_flow_b(stage, image, prefix):
    st.markdown("## Step 1：觀看家貓照片")
    st.write("請先觀察左側照片，依照整體感受選擇初步情緒。")

    st.markdown("## Step 2：依整體感受選擇初步情緒")
    initial_emotion = st.radio(
        "初步情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_initial_emotion",
    )

    st.markdown("## Step 3：標註部位特徵")
    feature_values, feature_other_text = render_feature_selector(prefix)

    st.markdown("## Step 4：再次確認或修改最終情緒")
    final_emotion = st.radio(
        "最終情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"{prefix}_final_emotion",
    )

    if initial_emotion and final_emotion:
        if initial_emotion == final_emotion:
            st.success("初步情緒與最終情緒相同，emotion_changed = False")
        else:
            st.warning("初步情緒與最終情緒不同，emotion_changed = True")

    uncertain_reason, uncertain_other_text = render_uncertain_reason(prefix, final_emotion or "")

    st.markdown("## Step 5：填寫標註信心程度")
    confidence = st.radio(
        "標註信心程度",
        [1, 2, 3, 4, 5],
        index=None,
        horizontal=True,
        key=f"{prefix}_confidence",
    )

    required_ok = bool(initial_emotion) and bool(final_emotion) and confidence is not None
    if final_emotion == "其他／無法判斷" and not uncertain_reason:
        required_ok = False

    if st.button("送出此張標註", type="primary", disabled=not required_ok):
        record = build_base_record(
            stage=stage,
            image=image,
            initial_emotion=initial_emotion,
            selected_features=build_selected_features(feature_values, feature_other_text),
            final_emotion=final_emotion,
            uncertain_reason=uncertain_reason,
            uncertain_other_text=uncertain_other_text,
            confidence=confidence,
        )
        go_next_image_or_questionnaire(record)


LIKERT_OPTIONS = [
    "非常不同意",
    "不同意",
    "普通",
    "同意",
    "非常同意",
]

LIKERT_SCORE_MAP = {
    "非常不同意": 1,
    "不同意": 2,
    "普通": 3,
    "同意": 4,
    "非常同意": 5,
}


def likert(label, key):
    choice = st.radio(label, LIKERT_OPTIONS, index=None, horizontal=True, key=key)
    return LIKERT_SCORE_MAP.get(choice) if choice is not None else None


def avg_or_none(values):
    if any(v is None for v in values):
        return None
    return round(sum(values) / len(values), 2)


def render_stage_questionnaire():
    render_back_button()
    stage = current_stage()

    left, center, right = st.columns([1, 2.2, 1])
    with center:
        st.markdown(
            f'<div class="main-title" style="text-align:center;">{stage["stage_name"]}問卷回饋｜版本 {stage["flow_type"]}：{stage["flow_name"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### 認知負荷")
        wl1 = likert("我覺得此標註流程需要花費較多心力。", f"q_{st.session_state.stage_index}_wl1")
        wl2 = likert("我在使用此流程時需要反覆思考才能完成標註。", f"q_{st.session_state.stage_index}_wl2")
        wl3 = likert("我覺得此流程的判斷負擔較高。", f"q_{st.session_state.stage_index}_wl3")

        st.markdown("### 標註信心")
        cf1 = likert("我對自己最後選擇的情緒結果有信心。", f"q_{st.session_state.stage_index}_cf1")
        cf2 = likert("我認為自己的標註結果有足夠依據。", f"q_{st.session_state.stage_index}_cf2")
        cf3 = likert("我能根據照片中的特徵做出合理判斷。", f"q_{st.session_state.stage_index}_cf3")

        st.markdown("### 流程清楚度、有用性與使用意圖")
        clarity = likert("我能清楚理解此標註流程的操作順序。", f"q_{st.session_state.stage_index}_clarity")
        usefulness = likert("我認為此流程有助於我判斷家貓情緒。", f"q_{st.session_state.stage_index}_usefulness")
        intention = likert("若未來需要標註家貓情緒，我願意使用此流程。", f"q_{st.session_state.stage_index}_intention")

        open_feedback = st.text_area(
            "開放式回饋：請說明此流程的使用感受、判斷困難或改進建議。",
            key=f"q_{st.session_state.stage_index}_open_feedback",
        )

        complete = all(v is not None for v in [wl1, wl2, wl3, cf1, cf2, cf3, clarity, usefulness, intention])

        if st.button("儲存此階段並進入下一階段", type="primary", disabled=not complete, use_container_width=True):
            stage_records = []
            for record in st.session_state.pending_stage_records:
                record = dict(record)
                record["workload_score"] = avg_or_none([wl1, wl2, wl3])
                record["confidence_score"] = avg_or_none([cf1, cf2, cf3])
                record["clarity_score"] = clarity
                record["usefulness_score"] = usefulness
                record["intention_score"] = intention
                record["open_feedback"] = open_feedback
                stage_records.append(record)

            save_records(stage_records)
            st.session_state.pending_stage_records = []
            st.session_state.stage_index += 1
            st.session_state.image_index = 0
            st.session_state.task_start_time = None

            if st.session_state.stage_index >= len(get_stage_plan()):
                st.session_state.page = "done"
            else:
                st.session_state.page = "task"
                reset_task_timer()
            st.rerun()


def render_intro():
    st.markdown(f'<div class="main-title">{APP_PAGE_TITLE}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">一個網頁完成同一組受試者的兩個階段：A 與 B 都會做，但順序與照片組不同。</div>', unsafe_allow_html=True)

    participant_id = st.text_input("受試者學號／代號", value=st.session_state.participant_id)
    st.session_state.participant_id = participant_id.strip()

    st.markdown("### 本組實驗安排")
    for idx, stage in enumerate(get_stage_plan(), start=1):
        st.markdown(
            f"""
            <div class="flow-card">
            <b>{idx}. {stage['stage_name']}</b><br>
            版本 {stage['flow_type']}：{stage['flow_name']} ＋ {stage['photo_set_name']}<br>
            <span style="color:#7a6650;">{stage['description']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("開始本組實驗", type="primary", disabled=not bool(st.session_state.participant_id)):
        st.session_state.page = "task"
        st.session_state.stage_index = 0
        st.session_state.image_index = 0
        st.session_state.pending_stage_records = []
        reset_task_timer()
        st.rerun()


def render_task():
    render_back_button()
    render_sidebar_image()
    stage = current_stage()
    image = current_image()

    if image is None:
        st.session_state.page = "stage_questionnaire"
        st.rerun()
        return

    st.markdown(f'<div class="main-title">{stage["stage_name"]}｜版本 {stage["flow_type"]}：{stage["flow_name"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="active-card">{stage["description"]}<br>目前照片：{st.session_state.image_index + 1} / {len(stage["images"])}｜image_id：{image["image_id"]}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.task_start_time is None:
        reset_task_timer()

    prefix = f"s{st.session_state.stage_index}_i{st.session_state.image_index}_{stage['flow_type']}"

    if stage["flow_type"] == "A":
        render_flow_a(stage, image, prefix)
    else:
        render_flow_b(stage, image, prefix)


def render_done():
    render_back_button()
    st.success("此組兩個階段皆已完成。")

    # 進入 done 頁面時自動嘗試一次雲端同步（只跑一次）
    # 若第一次失敗，會先顯示失敗訊息，並保留資料給下方「上傳雲端」按鈕重試。
    if not st.session_state.get("cloud_sync_attempted", False):
        st.session_state["cloud_sync_attempted"] = True
        try:
            ok, msg = sync_to_cloud()
            st.session_state["last_save_message"] = msg
        except Exception as e:
            st.session_state["last_save_message"] = f"CSV 已儲存，但 Google Sheet 同步失敗：{e}"

    msg = st.session_state.get("last_save_message", "")
    pending_count = len(st.session_state.get("pending_cloud_rows", []))

    st.markdown("### 雲端同步狀態")
    if pending_count == 0:
        if msg:
            st.success(f"☁️ {msg}")
        else:
            st.success("☁️ Google Sheet 已同步完成。")
    else:
        st.warning(f"第一次 Google Sheet 同步未成功，尚有 {pending_count} 筆資料未上傳。")
        if msg:
            st.error(msg)

    # 最後固定提供一個「上傳雲端」按鈕。
    # 成功後 pending_cloud_rows 會清空，失敗訊息會在 rerun 後消失並改成成功訊息。
    if st.button("☁️ 上傳雲端", type="primary", disabled=(pending_count == 0)):
        try:
            ok, msg2 = sync_to_cloud()
            st.session_state["last_save_message"] = msg2
            st.rerun()
        except Exception as e:
            st.session_state["last_save_message"] = f"Google Sheet 重新同步失敗：{e}"
            st.rerun()

    st.markdown("### 匯出資料")
    if OUTPUT_CSV.exists():
        st.download_button(
            "📄 下載 CSV",
            OUTPUT_CSV.read_bytes(),
            file_name=OUTPUT_CSV.name,
            mime="text/csv",
            type="primary",
        )
        st.caption(f"輸出檔案：{OUTPUT_CSV.name}")

    if st.button("回首頁重新開始"):
        reset_all()
        st.rerun()


def main():
    init_state()
    if st.session_state.page == "intro":
        render_intro()
    elif st.session_state.page == "task":
        render_task()
    elif st.session_state.page == "stage_questionnaire":
        render_stage_questionnaire()
    elif st.session_state.page == "done":
        render_done()


if __name__ == "__main__":
    main()


