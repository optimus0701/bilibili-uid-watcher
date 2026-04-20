import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
LOGS_CHANNEL_ID = int(os.getenv('LOGS_CHANNEL_ID', 0))
OWNER_ID = int(os.getenv('OWNER_ID', 0))
ROLES_ID_STR = os.getenv('DISCORD_ROLES_ID', '')
BILIBILI_UID = os.getenv('BILIBILI_UID', '3546856908917475')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 5)) # Mặc định 5 phút
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
NVIDIA_API_URL = os.getenv('NVIDIA_API_URL', 'https://integrate.api.nvidia.com/v1/chat/completions')

# Prefix ưu tiên cho AI models (phân tách bằng dấu phẩy, theo thứ tự ưu tiên)
AI_MODEL_PREFIXES = [p.strip() for p in os.getenv('AI_MODEL_PREFIXES', 'qwen/qwen3.5,google/gemma-3').split(',') if p.strip()]

# Prefix cho model hỗ trợ vision/multimodal
VISION_MODEL_PREFIXES = [p.strip() for p in os.getenv('VISION_MODEL_PREFIXES', 'google/gemma-3').split(',') if p.strip()]

# Fallback models khi không thể lấy danh sách từ API
_ai_fallback_str = os.getenv('AI_MODELS_FALLBACK', 'google/gemma-3-27b-it')
AI_MODELS_FALLBACK = [m.strip() for m in _ai_fallback_str.split(',') if m.strip()]

_vision_fallback_str = os.getenv('VISION_MODELS_FALLBACK', 'google/gemma-3-27b-it')
VISION_MODELS_FALLBACK = [m.strip() for m in _vision_fallback_str.split(',') if m.strip()]

# Thời gian cache danh sách models (tính theo giờ)
MODELS_CACHE_TIME = float(os.getenv('MODELS_CACHE_TIME', 1)) * 3600  # Convert giờ → giây

ENV_MODE = os.getenv('ENV_MODE', 'debug').lower()

def get_mention_text():
    mention_text = ""
    if ENV_MODE == 'release' and ROLES_ID_STR:
        role_ids = [r.strip() for r in ROLES_ID_STR.split(',') if r.strip()]
        mention_text = " ".join([f"<@&{role_id}>" for role_id in role_ids])
    return mention_text