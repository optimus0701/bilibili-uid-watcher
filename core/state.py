import os
import json
import logging

# Tạo tag màu vàng cho log của State
C_TAG = "\033[1;33m[State]\033[0m"

STATE_FILE = '/app/data/state.json'
TRANS_FILE = '/app/data/translations.json'

if not os.path.exists('/app/data'):
    STATE_FILE = './data/state.json'
    TRANS_FILE = './data/translations.json'
    os.makedirs('./data', exist_ok=True)
    logging.info(f"{C_TAG} Đã tạo thư mục ./data cục bộ.")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"{C_TAG} ❌ Lỗi khi đọc {STATE_FILE}: {e}")
            
    return {
        "latest_bvid": "", 
        "latest_opus_id": "", 
        "opus_error_notified": False 
    }

def save_state(key, value):
    state = load_state()
    state[key] = value
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        # Log khi lưu trạng thái (ẩn bớt log opus_error_notified để tránh spam)
        if key != "opus_error_notified":
            logging.info(f"{C_TAG} 💾 Đã cập nhật State -> [{key}]: {value}")
    except Exception as e:
        logging.error(f"{C_TAG} ❌ Lỗi khi ghi {STATE_FILE}: {e}")

# ==========================================
# CÁC HÀM QUẢN LÝ DỮ LIỆU DỊCH THUẬT (CACHE)
# ==========================================
def load_translations():
    if os.path.exists(TRANS_FILE):
        try:
            with open(TRANS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"{C_TAG} ❌ Lỗi khi đọc {TRANS_FILE}: {e}")
            return {}
    return {}

def save_translation(post_id, lang, text):
    trans = load_translations()
    
    if post_id not in trans:
        trans[post_id] = {}
        
    trans[post_id][lang] = text
    
    try:
        with open(TRANS_FILE, 'w', encoding='utf-8') as f:
            json.dump(trans, f, indent=4, ensure_ascii=False)
        logging.info(f"{C_TAG} 📝 Đã lưu Cache bản dịch [{lang.upper()}] cho ID: {post_id}")
    except Exception as e:
        logging.error(f"{C_TAG} ❌ Lỗi khi ghi {TRANS_FILE}: {e}")