
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

APP_PAGE_TITLE = "家貓情緒標註系統｜第 1 組"
OUTPUT_CSV = Path("hci_cat_annotation_group1.csv")
GROUP_ID = "1"

# Google Sheet 自動儲存設定：請貼上 Apps Script Web App 的 /exec URL。
# 若先保持空白，程式仍會正常儲存本機 CSV，不會送到 Google Sheet。
SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwuq0gOYl6fCuiR6Y_Pfr4_eMiTPbRFzUGdeQCVp6UNYcxAXNd6RN6xx1eg_3KDhBifwg/exec"
SHEET_SECRET = "hci_cat_annotation_secret"
# ============================================================
# 照片資料尚未決定：先放空白 placeholder，讓你可以先看完整流程。
# 之後把 path 改成實際圖片路徑即可，例如："images/cat_001.jpg"
# ============================================================
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
        "flow_type": "A",
        "flow_name": "特徵導向",
        "photo_set_name": "照片組 1",
        "images": IMAGE_SET_1,
        "description": "先標註眼睛、耳朵、尾巴、身體姿勢，再選擇最終情緒。",
    },
    {
        "stage_name": "第二階段",
        "flow_type": "B",
        "flow_name": "情緒導向",
        "photo_set_name": "照片組 2",
        "images": IMAGE_SET_2,
        "description": "先選擇初步情緒，再檢查部位特徵，最後確認或修改情緒。",
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
    .main-title {
        font-size: 30px;
        font-weight: 850;
        margin-bottom: 4px;
    }
    .sub-title {
        color: #555;
        font-size: 16px;
        margin-bottom: 16px;
    }
    .flow-card {
        padding: 14px 18px;
        border: 1px solid #ddd;
        border-radius: 14px;
        background: #fafafa;
        margin-bottom: 14px;
    }
    .active-card {
        padding: 14px 18px;
        border: 2px solid #635bff;
        border-radius: 14px;
        background: #f7f5ff;
        margin-bottom: 14px;
    }
    .warn-box {
        padding: 12px 16px;
        border-radius: 12px;
        background: #fff8e1;
        border: 1px solid #f0c36d;
        margin: 10px 0 16px 0;
    }
    .placeholder {
        height: 430px;
        border: 2px dashed #cfcfcf;
        border-radius: 16px;
        background: linear-gradient(135deg, #fafafa, #f2f2f2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #777;
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        padding: 20px;
    }
    section[data-testid="stSidebar"] {
        width: 520px !important;
        min-width: 520px !important;
    }
    section[data-testid="stSidebar"] img {
        max-height: 520px;
        object-fit: contain;
        border-radius: 12px;
    }
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


def append_records_to_google_sheet(records):
    """把資料同步寫入 Google Sheet。SHEET_WEBHOOK_URL 空白時會自動略過。"""
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
    """保留原本 CSV 儲存，同時嘗試同步 Google Sheet。Google Sheet 失敗不會刪掉 CSV。"""
    rows = [{col: record.get(col, "") for col in DATA_COLUMNS} for record in records]
    df_new = pd.DataFrame(rows, columns=DATA_COLUMNS)
    if OUTPUT_CSV.exists():
        df_old = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        # 若舊 CSV 沒有新欄位，補空值，避免 concat 後欄位不一致。
        for col in DATA_COLUMNS:
            if col not in df_old.columns:
                df_old[col] = ""
        df_old = df_old[DATA_COLUMNS]
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all = df_all[DATA_COLUMNS]
    df_all.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    try:
        ok, msg = append_records_to_google_sheet(rows)
        st.session_state["last_save_message"] = msg
    except Exception as e:
        st.session_state["last_save_message"] = f"CSV 已儲存，但 Google Sheet 同步失敗：{e}"

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


def likert(label, key):
    return st.radio(label, [1, 2, 3, 4, 5], index=None, horizontal=True, key=key)


def avg_or_none(values):
    if any(v is None for v in values):
        return None
    return round(sum(values) / len(values), 2)


def render_stage_questionnaire():
    stage = current_stage()
    st.markdown(f'<div class="main-title">{stage["stage_name"]}問卷回饋｜版本 {stage["flow_type"]}：{stage["flow_name"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">此問卷會套用到剛完成的這一階段所有照片紀錄。</div>', unsafe_allow_html=True)
    st.caption("1 = 非常不同意，5 = 非常同意")

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

    if st.button("儲存此階段並進入下一階段", type="primary", disabled=not complete):
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
            <span style="color:#666;">{stage['description']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 儲存欄位")
    st.info(f"本網頁會自動寫入 group_id = {GROUP_ID}，用來區分第 1 組或第 2 組。")
    st.code(", ".join(DATA_COLUMNS), language="text")
    st.markdown('<div class="warn-box">目前照片先使用空白 placeholder，所以可以直接進入流程預覽。之後只要修改 IMAGE_SET_1 / IMAGE_SET_2 的 path 即可。</div>', unsafe_allow_html=True)

    if st.button("開始本組實驗", type="primary", disabled=not bool(st.session_state.participant_id)):
        st.session_state.page = "task"
        st.session_state.stage_index = 0
        st.session_state.image_index = 0
        st.session_state.pending_stage_records = []
        reset_task_timer()
        st.rerun()


def render_task():
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
    st.success("此組兩個階段皆已完成。")
    if st.session_state.get("last_save_message"):
        st.info(st.session_state["last_save_message"])
    st.markdown(f"輸出檔案：`{OUTPUT_CSV.name}`")
    if OUTPUT_CSV.exists():
        st.download_button(
            "下載 CSV",
            OUTPUT_CSV.read_bytes(),
            file_name=OUTPUT_CSV.name,
            mime="text/csv",
        )
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

