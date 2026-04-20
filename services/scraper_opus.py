import logging
import aiohttp
import discord
from core import config
from core.state import load_state, save_state
from services.ai_helper import format_opus_content
from services.image_utils import optimize_bili_image
from ui.views import TranslateView, FixAlertView

C_TAG = "\033[1;35m[Opus]\033[0m"
C_NEW = "\033[1;32m"
C_ERR = "\033[1;31m"
C_OK  = "\033[32m"
C_END = "\033[0m"

API_URL = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/opus/feed/space?host_mid={config.BILIBILI_UID}&page=1&offset=&type=all&web_location=333.1387"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": f"https://space.bilibili.com/{config.BILIBILI_UID}/upload/opus",
    "Origin": "https://space.bilibili.com",
    "Accept": "application/json, text/plain, */*"
}

async def send_error_alert(bot, error_msg):
    state = load_state()
    if state.get("opus_error_notified", False):
        return

    log_channel = bot.get_channel(config.LOGS_CHANNEL_ID)
    if not log_channel: return

    embed = discord.Embed(title="⚠️ Lỗi API Cào Opus", description=f"**Chi tiết:** {error_msg}", color=discord.Color.orange())
    ping_text = f"<@{config.OWNER_ID}> Hệ thống cào Opus đang gặp sự cố!"
    
    try:
        await log_channel.send(content=ping_text, embed=embed, view=FixAlertView())
        save_state("opus_error_notified", True)
    except Exception as e:
        logging.error(f"{C_TAG} {C_ERR}Lỗi gửi log alert: {e}{C_END}")

async def check_bilibili_opus(bot):
    channel = bot.get_channel(config.CHANNEL_ID)
    if not channel: return

    logging.info(f"{C_TAG} 🔍 Đang gọi API Feed để check Opus mới...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL, headers=HEADERS, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"{C_TAG} {C_ERR}Lỗi HTTP {response.status} khi gọi API Opus:{C_END}\n{error_text[:500]}")
                    await send_error_alert(bot, f"HTTP Status {response.status}")
                    return
                
                try:
                    data = await response.json()
                except Exception as e:
                    error_text = await response.text()
                    logging.error(f"{C_TAG} {C_ERR}Không thể parse JSON từ API Opus. Có thể bị limit. Response ({len(error_text)} chars):{C_END}\n{error_text[:800]}")
                    await send_error_alert(bot, f"Parse JSON Error: Có thể bị limit (xem console log).")
                    return

                if data.get("code") != 0:
                    logging.error(f"{C_TAG} {C_ERR}Lỗi API Code: {data.get('code')} - {data.get('message')}{C_END}")
                    await send_error_alert(bot, f"API Error Code: {data.get('code')} - {data.get('message')}")
                    return

                items = data.get("data", {}).get("items", [])
                if not items: 
                    logging.warning(f"{C_TAG} ⚠️ Không tìm thấy bài viết Opus nào (items rỗng hoặc bị ẩn).")
                    return
                
                # Lấy bài viết đầu tiên
                latest_post = items[0]
                post_id = str(latest_post.get("opus_id", ""))
                if not post_id:
                    post_id = str(latest_post.get("id_str", ""))

                # Tách link bài viết (jump_url)
                jump_url = latest_post.get("jump_url", "")
                if jump_url.startswith("//"):
                    jump_url = "https:" + jump_url
                if not jump_url:
                    jump_url = f"https://t.bilibili.com/{post_id}"

                # Tách nội dung (content) theo logic test.py
                raw_content = latest_post.get("content", "Không có nội dung")

                # Tách ảnh bìa (cover) và tối ưu hóa theo tỉ lệ
                cover_data = latest_post.get("cover", None)
                image_url = optimize_bili_image(cover_data)
                
                # Chuẩn bị URL ảnh gốc (không optimize) để gửi cho AI phân tích
                ai_image_urls = []
                if cover_data and "url" in cover_data:
                    raw_cover_url = cover_data["url"]
                    if raw_cover_url.startswith("//"):
                        raw_cover_url = "https:" + raw_cover_url
                    ai_image_urls.append(raw_cover_url)

        except Exception as e:
            logging.error(f"{C_TAG} {C_ERR}Exception hệ thống khi gọi API Feed Opus: {e}{C_END}")
            await send_error_alert(bot, f"Exception khi gọi API Feed: {e}")
            return

    state = load_state()
    latest_saved_id = str(state.get("latest_opus_id", ""))

    if not latest_saved_id:
        save_state("latest_opus_id", post_id)
        logging.info(f"{C_TAG} Đã thiết lập mốc theo dõi Opus với ID: {post_id}")
        return

    if post_id != latest_saved_id and post_id != "":
        logging.info(f"{C_TAG} {C_NEW}🎉 Phát hiện bài Opus mới (ID: {post_id})!{C_END}")
        
        # Nhờ AI phân tích ảnh + text và viết lại nội dung
        discord_formatted = await format_opus_content("Tin tức Opus", raw_content, target_lang="tiếng Việt", image_urls=ai_image_urls)
        
        # Tạo Discord Embed
        embed = discord.Embed(
            title="📰 TIN TỨC MỚI TỪ VALORANT MOBILE CN", 
            url=jump_url, 
            description=f"{discord_formatted}\n\n[🔗 Nhấn vào đây để xem bài viết gốc]({jump_url})", 
            color=discord.Color(0xFD4556)
        )
        embed.set_author(name="Valorant Mobile VN", icon_url="https://i.imgur.com/vHq9P9B.png")
        
        # Gắn ảnh bìa
        if image_url: 
            embed.set_image(url=image_url)
            
        embed.set_footer(text=f"Dịch bởi NVIDIA AI | Bilibili Opus | Dev by Dominator", icon_url="https://i.imgur.com/lMjaA3T.png")

        try:
            await channel.send(content=config.get_mention_text(), embed=embed, view=TranslateView())
            save_state("latest_opus_id", post_id)
            logging.info(f"{C_TAG} {C_OK}✅ Đã đăng bài Opus thành công!{C_END}")
        except Exception as e:
            logging.error(f"{C_TAG} {C_ERR}❌ Lỗi gửi tin nhắn Opus: {e}{C_END}")