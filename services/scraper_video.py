import logging
import json
import subprocess
import aiohttp
import discord
from core import config
from core.state import load_state, save_state
from services.ai_helper import translate_video_content
from ui.views import TranslateView

C_TAG = "\033[1;36m[Video]\033[0m"
C_NEW = "\033[1;32m"
C_ERR = "\033[1;31m"
C_OK  = "\033[32m"
C_END = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
}

def get_latest_video_cli(uid):
    """Chỉ dùng CLI để lấy BVID mới nhất"""
    try:
        logging.info(f"{C_TAG} 🔍 Đang gọi lệnh bili CLI để lấy bvid video...")
        result = subprocess.run(['bili', 'user-videos', str(uid), '--max', '1', '--json'], capture_output=True, text=True, check=True)
        
        if not result.stdout.strip(): return None
            
        data = json.loads(result.stdout)

        if isinstance(data, list) and len(data) > 0: 
            return data[0]
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                return data['data'][0]
            elif 'vlist' in data: 
                return data['vlist'][0] if data['vlist'] else None
            elif 'list' in data and 'vlist' in data['list']: 
                return data['list']['vlist'][0] if data['list']['vlist'] else None
    except Exception as e:
        logging.error(f"{C_TAG} {C_ERR}Lỗi khi fetch video từ CLI: {e}{C_END}")
        
    return None

async def fetch_video_detail(bvid):
    """GỌI API CHÍNH THỨC CỦA BILIBILI ĐỂ LẤY FULL ẢNH VÀ DỮ LIỆU"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 0:
                        return data.get("data", {})
    except Exception as e:
        logging.error(f"{C_TAG} Lỗi khi gọi API chi tiết video: {e}")
    return {}

async def check_bilibili_video(bot):
    channel = bot.get_channel(config.CHANNEL_ID)
    if not channel: return

    state = load_state()
    latest_bvid = state.get("latest_bvid", "")
    
    # 1. Lấy dữ liệu cơ bản từ CLI
    video_item = get_latest_video_cli(config.BILIBILI_UID)
    if not video_item: return

    current_bvid = video_item.get('bvid', '') or video_item.get('id', '')
    if not current_bvid: return

    if not latest_bvid:
        save_state("latest_bvid", current_bvid)
        return
        
    if current_bvid != latest_bvid:
        logging.info(f"{C_TAG} {C_NEW}🎉 Có video mới! BVID: {current_bvid}. Đang lấy data chuẩn từ API...{C_END}")
        
        # 2. GỌI API ĐỂ LẤY DỮ LIỆU GỐC CHUẨN XÁC NHẤT
        detail_data = await fetch_video_detail(current_bvid)
        
        # Lấy title/desc từ API, nếu lỗi thì dùng tạm của CLI
        title = detail_data.get('title') or video_item.get('title', 'Không có tiêu đề')
        desc = detail_data.get('desc') or video_item.get('description', '')
        
        # Lấy ảnh chuẩn và đổi http thành https
        image_url = detail_data.get('pic', '')
        if image_url:
            if image_url.startswith('//'): 
                image_url = 'https:' + image_url
            elif image_url.startswith('http://'):
                image_url = image_url.replace('http://', 'https://')

        # Dịch nội dung bằng AI
        translated_text = await translate_video_content(title, desc, target_lang="tiếng Việt")
        video_url = f"https://www.bilibili.com/video/{current_bvid}"
        
        # Tạo Embed
        embed = discord.Embed(
            title="🎬 VIDEO MỚI TỪ VALORANT MOBILE CN", 
            url=video_url, 
            description=f"{translated_text}\n\n[▶️ Nhấn vào đây để xem Video]({video_url})", 
            color=discord.Color(0xFD4556)
        )
        embed.set_author(name="Valorant Mobile VN", icon_url="https://i.imgur.com/vHq9P9B.png")
        
        # Set ảnh vào Embed
        if image_url: 
            embed.set_image(url=image_url)
            
        embed.set_footer(text=f"Dịch bởi NVIDIA AI | Bilibili Video | Dev by Dominator", icon_url="https://i.imgur.com/lMjaA3T.png")

        try:
            # Ẩn link bằng ký tự tàng hình để tạo preview đẹp
            msg_content = f"{config.get_mention_text()}"
            await channel.send(content=msg_content, embed=embed, view=TranslateView())
            save_state("latest_bvid", current_bvid)
            logging.info(f"{C_TAG} {C_OK}✅ Đã gửi Video Embed lên Discord!{C_END}")
        except Exception as e:
            logging.error(f"{C_TAG} {C_ERR}❌ Lỗi gửi tin nhắn Video: {e}{C_END}")