import re
import discord
import logging
import time
from core.state import save_state, load_translations, save_translation

# Tạo tag màu xanh dương cho UI
C_TAG = "\033[1;34m[UI]\033[0m"

class TranslateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldowns = {} 

    @discord.ui.button(label="Translate to English", style=discord.ButtonStyle.primary, custom_id="btn_translate_en", emoji="🇺🇸")
    async def translate_en(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        current_time = time.time()
        
        if user_id in self.cooldowns:
            time_passed = current_time - self.cooldowns[user_id]
            if time_passed < 10: 
                wait_time = int(10 - time_passed)
                logging.warning(f"{C_TAG} ⚠️ User {interaction.user.name} đang spam nút dịch. Chặn {wait_time}s.")
                await interaction.response.send_message(
                    f"⏳ Đừng spam nút nhé! Vui lòng đợi **{wait_time} giây** nữa để thao tác.", 
                    ephemeral=True
                )
                return
        
        self.cooldowns[user_id] = current_time
        logging.info(f"{C_TAG} 👤 User {interaction.user.name} yêu cầu dịch sang Tiếng Anh.")
        await self._do_translate(interaction, "English")

    @staticmethod
    def _extract_clean_content(embed: discord.Embed) -> tuple[str, str, str, str]:
        """
        Tách nội dung sạch từ embed gốc.
        Returns: (original_url, image_url, title_text, clean_description)
        """
        original_url = embed.url or ""
        
        # Lấy ảnh từ embed gốc
        image_url = ""
        if embed.image and embed.image.url:
            image_url = embed.image.url
        
        # Title gốc (bỏ emoji ở đầu nếu cần)
        title_text = embed.title or ""
        
        # Tách description: loại bỏ dòng markdown link ở cuối
        # VD: "[🔗 Nhấn vào đây để xem bài viết gốc](https://...)" hoặc "[▶️ ...](https://...)"
        desc = embed.description or ""
        desc = re.sub(r'\n*\[.*?\]\(https?://[^)]+\)\s*$', '', desc).strip()
        
        return original_url, image_url, title_text, desc

    async def _do_translate(self, interaction: discord.Interaction, target_lang: str):
        from services.ai_helper import translate_video_content
        
        message = interaction.message
        embed = message.embeds[0] if message.embeds else None
        
        post_id = str(message.id)
        original_url = ""
        image_url = ""
        
        if embed:
            original_url, image_url, _, clean_desc = self._extract_clean_content(embed)
            if original_url:
                post_id = original_url.strip('/').split('/')[-1]

        # KIỂM TRA CACHE
        translations = load_translations()
        if post_id in translations and "en" in translations[post_id]:
            logging.info(f"{C_TAG} ⚡ Trúng Cache! Trả ngay bản dịch Tiếng Anh cho ID: {post_id}")
            cached_en = translations[post_id]["en"]
            new_embed = discord.Embed(
                title=f"🌐 Translated to {target_lang}",
                url=original_url if original_url else None,
                description=cached_en,
                color=discord.Color(0x00E5FF) 
            )
            if image_url:
                new_embed.set_image(url=image_url)
            new_embed.set_footer(text="Translated by AI (Cached)", icon_url="https://i.imgur.com/lMjaA3T.png")
            await interaction.response.send_message(embed=new_embed, ephemeral=True)
            return

        logging.info(f"{C_TAG} ⏳ Không có sẵn Cache cho ID {post_id}. Đang gửi yêu cầu cho AI...")
        thinking_embed = discord.Embed(
            title="⏳ Bot is thinking...",
            description="Sending data to the AI translator, please wait a moment...",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=thinking_embed, ephemeral=True)
        
        # Lấy nội dung sạch để dịch (không lấy title embed vì nó là label cứng)
        desc_to_translate = clean_desc if embed else message.content

        if not desc_to_translate:
            logging.error(f"{C_TAG} ❌ Không tìm thấy nội dung để dịch trong tin nhắn.")
            error_embed = discord.Embed(description="❌ Không tìm thấy nội dung để dịch!", color=discord.Color.red())
            await interaction.edit_original_response(embed=error_embed)
            return

        try:
            # Chỉ dịch phần description sạch, không gửi title embed (vì title là label cứng)
            translated = await translate_video_content(
                "",  # Không cần gửi title cứng
                desc_to_translate, 
                target_lang=target_lang
            )
            
            if desc_to_translate[:100] in translated:
                logging.warning(f"{C_TAG} ⚠️ Fallback kích hoạt: AI đang bận hoặc lỗi mạng.")
                error_embed = discord.Embed(
                    title="⚠️ AI Đang Bận", 
                    description="Máy chủ AI đang quá tải. Vui lòng thử lại sau nhé!", 
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=error_embed)
                return
            
            logging.info(f"{C_TAG} ✅ AI đã dịch xong! Đang lưu Cache và hiển thị...")
            save_translation(post_id, "vi", desc_to_translate)
            save_translation(post_id, "en", translated)
            
            new_embed = discord.Embed(
                title=f"🌐 Translated to {target_lang}",
                url=original_url if original_url else None,
                description=translated,
                color=discord.Color(0x00E5FF) 
            )
            if image_url:
                new_embed.set_image(url=image_url)
            new_embed.set_footer(text="Translated by AI", icon_url="https://i.imgur.com/lMjaA3T.png")
            
            await interaction.edit_original_response(embed=new_embed)
            logging.info(f"{C_TAG} 🎉 Đã gửi thành công bản dịch lên Discord!")
            
        except Exception as e:
            logging.error(f"{C_TAG} ❌ Lỗi khi xử lý dịch UI: {e}")
            error_embed = discord.Embed(
                title="❌ Có lỗi xảy ra", 
                description=f"Không thể hoàn thành bản dịch: {e}", 
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=error_embed)

class FixAlertView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Đã khắc phục", style=discord.ButtonStyle.success, custom_id="btn_fixed_alert")
    async def fixed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"{C_TAG} 🔧 User {interaction.user.name} đã đánh dấu khắc phục lỗi Opus.")
        save_state("opus_error_notified", False)
        
        embed = interaction.message.embeds[0]
        embed.title = "✅ Lỗi đã được xử lý"
        embed.color = discord.Color.green()
        
        self.clear_items()
        
        await interaction.response.edit_message(embed=embed, view=None)
        await interaction.followup.send("Đã reset trạng thái cảnh báo Opus.", ephemeral=True)