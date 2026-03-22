import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
LOGS_CHANNEL_ID = int(os.getenv('LOGS_CHANNEL_ID', 0))
OWNER_ID = int(os.getenv('OWNER_ID', 0))
ROLES_ID_STR = os.getenv('DISCORD_ROLES_ID', '')
BILIBILI_UID = os.getenv('BILIBILI_UID', '3546856908917475')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY') # Đã sửa thành NVIDIA
ENV_MODE = os.getenv('ENV_MODE', 'debug').lower()

def get_mention_text():
    mention_text = ""
    if ENV_MODE == 'release' and ROLES_ID_STR:
        role_ids = [r.strip() for r in ROLES_ID_STR.split(',') if r.strip()]
        mention_text = " ".join([f"<@&{role_id}>" for role_id in role_ids])
    return mention_text