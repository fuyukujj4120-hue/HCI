
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="家貓情緒標註系統 - 版本 A", layout="wide")

# ============================================================
# 可修改區：照片資料尚未決定，先保持空白
# 之後只要把照片放到 images/ 資料夾，並在 IMAGE_ITEMS 加入資料即可。
# 範例：{"image_id": "cat_001", "path": "images/cat_001.jpg"}
# ============================================================
IMAGE_ITEMS = []

FLOW_TYPE = "A"
FLOW_NAME = "特徵導向"
OUTPUT_CSV = Path("hci_cat_annotation_a.csv")

DATA_COLUMNS = [
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
    .step-box {
        padding: 14px 18px;
        border: 1px solid #ddd;
        border-radius: 14px;
        background: #fafafa;
        margin-bottom: 14px;
    }
    .hint-box {
        padding: 12px 16px;
        border-radius: 12px;
        background: #f7f5ff;
        border: 1px solid #d6ccff;
        margin: 10px 0 16px 0;
    }
    .warn-box {
        padding: 12px 16px;
        border-radius: 12px;
        background: #fff8e1;
        border: 1px solid #f0c36d;
        margin: 10px 0 16px 0;
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


def init_state():
    defaults = {
        "participant_id": "",
        "current_index": 0,
        "page": "intro",
        "task_start_time": None,
        "feature_values": {},
        "feature_other_text": {},
        "initial_emotion": "",
        "final_emotion": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_current_image():
    if not IMAGE_ITEMS:
        return None
    if st.session_state.current_index >= len(IMAGE_ITEMS):
        return None
    return IMAGE_ITEMS[st.session_state.current_index]


def reset_task_state():
    st.session_state.task_start_time = time.time()
    st.session_state.feature_values = {}
    st.session_state.feature_other_text = {}
    st.session_state.initial_emotion = ""
    st.session_state.final_emotion = ""


def save_record(record: dict):
    row = {col: record.get(col, "") for col in DATA_COLUMNS}
    if OUTPUT_CSV.exists():
        df_old = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    else:
        df_old = pd.DataFrame(columns=DATA_COLUMNS)
    df_new = pd.concat([df_old, pd.DataFrame([row])], ignore_index=True)
    df_new = df_new[DATA_COLUMNS]
    df_new.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")


def render_sidebar_image():
    with st.sidebar:
        st.markdown("### 家貓照片")
        current = get_current_image()
        if current is None:
            st.info("目前 IMAGE_ITEMS 是空白。等照片決定後，請把 image_id 與 path 加進程式上方的 IMAGE_ITEMS。")
            return
        st.caption(f"image_id：{current['image_id']}")
        image_path = current.get("path", "")
        if image_path and Path(image_path).exists():
            st.image(image_path, use_container_width=True)
        elif image_path:
            st.warning(f"找不到圖片：{image_path}")
        else:
            st.warning("此筆資料尚未設定圖片路徑。")


def render_feature_selector():
    selected = {}
    other_text = {}
    for group_name, options in FEATURE_OPTIONS.items():
        st.markdown(f"#### {group_name}")
        key = f"feature_{group_name}_{st.session_state.current_index}"
        choice = st.radio(
            f"請選擇{group_name}最符合的觀察結果",
            options,
            index=None,
            key=key,
            horizontal=False,
        )
        selected[group_name] = choice or ""
        if choice == "其他":
            other_key = f"feature_other_{group_name}_{st.session_state.current_index}"
            other_text[group_name] = st.text_input(f"請補充{group_name}其他特徵", key=other_key)
        else:
            other_text[group_name] = ""
        st.divider()

    st.session_state.feature_values = selected
    st.session_state.feature_other_text = other_text
    return selected, other_text


def build_selected_features(selected: dict, other_text: dict):
    result = {}
    for group_name, choice in selected.items():
        if choice == "其他":
            text = other_text.get(group_name, "").strip()
            result[group_name] = f"其他：{text}" if text else "其他"
        else:
            result[group_name] = choice
    return json.dumps(result, ensure_ascii=False)


def render_uncertain_reason(final_emotion: str):
    if final_emotion != "其他／無法判斷":
        return "", ""

    st.markdown("### 其他／無法判斷原因")
    reason = st.radio(
        "若選擇其他／無法判斷，請記錄原因",
        UNCERTAIN_REASONS,
        index=None,
        key=f"uncertain_reason_{st.session_state.current_index}",
    )
    other_text = ""
    if reason == "其他":
        other_text = st.text_input(
            "請補充其他原因",
            key=f"uncertain_other_text_{st.session_state.current_index}",
        )
    return reason or "", other_text


def likert(label: str, key: str):
    return st.radio(label, [1, 2, 3, 4, 5], index=None, horizontal=True, key=key)


def render_questionnaire():
    st.markdown("## 問卷回饋")
    st.caption("1 = 非常不同意，5 = 非常同意")

    st.markdown("### 認知負荷")
    wl1 = likert("我覺得此標註流程需要花費較多心力。", f"wl1_{st.session_state.current_index}")
    wl2 = likert("我在使用此流程時需要反覆思考才能完成標註。", f"wl2_{st.session_state.current_index}")
    wl3 = likert("我覺得此流程的判斷負擔較高。", f"wl3_{st.session_state.current_index}")

    st.markdown("### 標註信心")
    cf1 = likert("我對自己最後選擇的情緒結果有信心。", f"cf1_{st.session_state.current_index}")
    cf2 = likert("我認為自己的標註結果有足夠依據。", f"cf2_{st.session_state.current_index}")
    cf3 = likert("我能根據照片中的特徵做出合理判斷。", f"cf3_{st.session_state.current_index}")

    st.markdown("### 流程清楚度、有用性與使用意圖")
    clarity = likert("我能清楚理解此標註流程的操作順序。", f"clarity_{st.session_state.current_index}")
    usefulness = likert("我認為此流程有助於我判斷家貓情緒。", f"usefulness_{st.session_state.current_index}")
    intention = likert("若未來需要標註家貓情緒，我願意使用此流程。", f"intention_{st.session_state.current_index}")

    open_feedback = st.text_area(
        "開放式回饋：請說明此流程的使用感受、判斷困難或改進建議。",
        key=f"open_feedback_{st.session_state.current_index}",
    )

    def avg(values):
        if any(v is None for v in values):
            return None
        return round(sum(values) / len(values), 2)

    return {
        "workload_score": avg([wl1, wl2, wl3]),
        "confidence_score": avg([cf1, cf2, cf3]),
        "clarity_score": clarity,
        "usefulness_score": usefulness,
        "intention_score": intention,
        "open_feedback": open_feedback,
        "is_complete": all(v is not None for v in [wl1, wl2, wl3, cf1, cf2, cf3, clarity, usefulness, intention]),
    }


def render_intro():
    st.markdown(f'<div class="main-title">家貓情緒標註系統：版本 {FLOW_TYPE}｜{FLOW_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">本版本依 proposal 的流程與資料欄位設計，照片資料目前先保留空白。</div>', unsafe_allow_html=True)

    participant_id = st.text_input("受試者學號／代號", value=st.session_state.participant_id)
    st.session_state.participant_id = participant_id.strip()

    st.markdown("### 本版本流程")
    st.markdown("""
1. 觀看家貓照片。  
2. 標註眼睛、耳朵、尾巴、身體姿勢等部位特徵。  
3. 根據前述特徵選擇最終情緒。  
4. 若選擇「其他／無法判斷」，需進一步選擇原因。  
5. 填寫標註信心程度。  
""")

    st.markdown("### 儲存欄位")
    st.code(", ".join(DATA_COLUMNS), language="text")

    if not IMAGE_ITEMS:
        st.markdown(
            '<div class="warn-box">目前照片資料尚未決定，因此 IMAGE_ITEMS 先保持空白。加入照片後即可開始標註。</div>',
            unsafe_allow_html=True,
        )

    disabled = not bool(st.session_state.participant_id) or not bool(IMAGE_ITEMS)
    if st.button("開始標註", type="primary", disabled=disabled):
        st.session_state.page = "annotation"
        st.session_state.current_index = 0
        reset_task_state()
        st.rerun()


def render_annotation():
    current = get_current_image()
    if current is None:
        st.success("已完成所有照片標註，或目前尚未設定照片資料。")
        if OUTPUT_CSV.exists():
            st.download_button(
                "下載目前 CSV",
                OUTPUT_CSV.read_bytes(),
                file_name=OUTPUT_CSV.name,
                mime="text/csv",
            )
        if st.button("回到首頁"):
            st.session_state.page = "intro"
            st.rerun()
        return

    render_sidebar_image()

    st.markdown(f'<div class="main-title">版本 {FLOW_TYPE}：{FLOW_NAME}</div>', unsafe_allow_html=True)
    st.caption(f"第 {st.session_state.current_index + 1} / {len(IMAGE_ITEMS)} 張｜image_id：{current['image_id']}")

    if st.session_state.task_start_time is None:
        st.session_state.task_start_time = time.time()

    
    st.markdown('<div class="hint-box">流程 A：先標註眼睛、耳朵、尾巴與身體姿勢等可見特徵，再根據前述特徵選擇最終情緒。</div>', unsafe_allow_html=True)

    st.markdown("## Step 1：觀看家貓照片")
    st.write("請先觀察左側照片，再進行特徵標註。")

    st.markdown("## Step 2：標註部位特徵")
    selected, other_text = render_feature_selector()

    st.markdown("## Step 3：根據前述特徵選擇最終情緒")
    final_emotion = st.radio(
        "最終情緒",
        EMOTION_OPTIONS,
        index=None,
        key=f"final_emotion_{st.session_state.current_index}",
    )
    initial_emotion = ""
    emotion_changed = ""

    uncertain_reason, uncertain_other_text = render_uncertain_reason(final_emotion or "")

    st.markdown("## Step 4：填寫標註信心程度")
    confidence = st.radio(
        "標註信心程度",
        [1, 2, 3, 4, 5],
        index=None,
        horizontal=True,
        key=f"confidence_{st.session_state.current_index}",
    )

    questionnaire = render_questionnaire()

    required_ok = bool(final_emotion) and confidence is not None and questionnaire["is_complete"]
    if final_emotion == "其他／無法判斷" and not uncertain_reason:
        required_ok = False

    if st.button("送出並儲存", type="primary", disabled=not required_ok):
        annotation_time = round(time.time() - st.session_state.task_start_time, 2)
        record = {
            "participant_id": st.session_state.participant_id,
            "flow_type": FLOW_TYPE,
            "image_id": current["image_id"],
            "initial_emotion": initial_emotion,
            "selected_features": build_selected_features(selected, other_text),
            "final_emotion": final_emotion,
            "uncertain_reason": uncertain_reason,
            "uncertain_other_text": uncertain_other_text,
            "confidence": confidence,
            "annotation_time": annotation_time,
            "emotion_changed": emotion_changed,
            "workload_score": questionnaire["workload_score"],
            "clarity_score": questionnaire["clarity_score"],
            "confidence_score": questionnaire["confidence_score"],
            "usefulness_score": questionnaire["usefulness_score"],
            "intention_score": questionnaire["intention_score"],
            "open_feedback": questionnaire["open_feedback"],
        }
        save_record(record)
        st.success("已儲存。")
        st.session_state.current_index += 1
        reset_task_state()
        st.rerun()



def main():
    init_state()
    if st.session_state.page == "intro":
        render_intro()
    else:
        render_annotation()


if __name__ == "__main__":
    main()
