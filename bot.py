import logging
import asyncio
import datetime
import discord
from discord.ext import commands

from core import config
from ui.views import TranslateView, FixAlertView
from services.scraper_video import check_bilibili_video
from services.scraper_opus import check_bilibili_opus

# Cấu hình logging
class ColorLogFormatter(logging.Formatter):
    """Custom Formatter để tô màu Log Terminal"""
    COLORS = {
        logging.DEBUG: "\033[38;5;240m",  # Xám
        logging.INFO: "\033[34m",         # Xanh dương
        logging.WARNING: "\033[33m",      # Vàng
        logging.ERROR: "\033[31m",        # Đỏ
        logging.CRITICAL: "\033[1;31m",   # Đỏ in đậm
    }
    RESET = "\033[0m"
    TIME_COLOR = "\033[36m"               # Xanh lơ (Cyan)

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        log_fmt = f"{self.TIME_COLOR}%(asctime)s{self.RESET} - {color}%(levelname)s{self.RESET} - %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorLogFormatter())
logger.addHandler(console_handler)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def _wait_until_next_round_interval():
    """Hẹn giờ theo chu kỳ CHECK_INTERVAL (vd: 9:00, 9:05) tính bằng phút"""
    now = datetime.datetime.now()
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    interval_seconds = config.CHECK_INTERVAL * 60
    remainder = seconds_since_midnight % interval_seconds
    wait_seconds = interval_seconds - remainder if remainder > 0 else interval_seconds
    next_time = now + datetime.timedelta(seconds=wait_seconds)
    logging.info(f"⏰ Lần check tiếp theo lúc {next_time.strftime('%H:%M:%S')} (chờ {wait_seconds}s)")
    await asyncio.sleep(wait_seconds)

async def _scheduled_loop(name, check_func):
    await bot.wait_until_ready()
    logging.info(f"[{name}] 🚀 Chạy lần kiểm tra đầu tiên...")
    try: await check_func(bot)
    except Exception as e: logging.error(f"[{name}] ❌ Lỗi lần đầu: {e}")
    
    while not bot.is_closed():
        await _wait_until_next_round_interval()
        try: await check_func(bot)
        except Exception as e: logging.error(f"[{name}] ❌ Lỗi loop: {e}")

_tasks_started = False

@bot.event
async def on_ready():
    global _tasks_started
    logging.info(f"Bot đã đăng nhập dưới tên {bot.user.name} | Môi trường: {config.ENV_MODE.upper()}")
    
    # Đăng ký các Button View để nhận sự kiện sau khi bot restart
    bot.add_view(TranslateView())
    bot.add_view(FixAlertView())
    
    if not _tasks_started:
        _tasks_started = True
        bot.loop.create_task(_scheduled_loop("Video", check_bilibili_video))
        bot.loop.create_task(_scheduled_loop("Opus", check_bilibili_opus))

if __name__ == "__main__":
    if not config.DISCORD_TOKEN or not config.NVIDIA_API_KEY:
        logging.error("Thiếu DISCORD_BOT_TOKEN hoặc NVIDIA_API_KEY trong .env")
    else:
        bot.run(config.DISCORD_TOKEN)