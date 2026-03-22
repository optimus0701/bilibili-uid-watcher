import logging
import aiohttp
from core import config

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Model hỗ trợ vision (multimodal)
VISION_MODELS = ["google/gemma-3-27b-it"]


def _normalize_image_url(url: str) -> str:
    """Chuẩn hóa URL ảnh về https."""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return url.replace("http://", "https://")
    return url


def _build_messages(system_prompt: str, user_prompt: str, model_name: str, image_urls: list[str] | None = None) -> list[dict]:
    """
    Xây dựng danh sách messages cho API.
    - Nếu model hỗ trợ vision VÀ có ảnh → gửi multimodal (ảnh + text).
    - Ngược lại → gửi text-only.
    """
    messages = [{"role": "system", "content": system_prompt}]

    if image_urls and model_name in VISION_MODELS:
        # Multimodal: gửi ảnh kèm text
        content_parts = []
        for img_url in image_urls:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": _normalize_image_url(img_url)}
            })
        content_parts.append({"type": "text", "text": user_prompt})
        messages.append({"role": "user", "content": content_parts})
    else:
        # Text-only
        messages.append({"role": "user", "content": user_prompt})

    return messages


async def _call_nvidia_api(system_prompt: str, user_prompt: str, max_tokens: int, image_urls: list[str] | None = None) -> str:
    headers = {
        "Authorization": f"Bearer {config.NVIDIA_API_KEY}", 
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Danh sách các model theo thứ tự ưu tiên
    models_to_try = [
        "google/gemma-3-27b-it",
        "moonshotai/kimi-k2-thinking"
    ]
    
    for model_name in models_to_try:
        # Chỉ gửi ảnh cho model hỗ trợ vision
        current_images = image_urls if model_name in VISION_MODELS else None
        
        payload = {
            "model": model_name,
            "messages": _build_messages(system_prompt, user_prompt, model_name, current_images),
            "max_tokens": max_tokens,
            "temperature": 0.20,
            "top_p": 0.70,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=30) as response:
                    response.raise_for_status()
                    data = await response.json()
                    result = data['choices'][0]['message']['content'].strip()
                    
                    img_info = f" (kèm {len(current_images)} ảnh)" if current_images else ""
                    logging.info(f"✅ AI [{model_name}] đã trả lời thành công{img_info}")
                    return result
        except Exception as e:
            logging.warning(f"⚠️ Lỗi khi gọi model {model_name}: {e}. Đang thử model tiếp theo...")
            continue
            
    logging.error("❌ Tất cả các model AI đều bị lỗi hoặc bận.")
    return ""


async def translate_video_content(title: str, text: str, target_lang: str = 'tiếng Việt') -> str:
    system_prompt = f"""Bạn là dịch giả chuyên nghiệp cho game Valorant Mobile.
    QUY TẮC:
    1. Dịch chuẩn xác nội dung sang {target_lang}.
    2. Giữ nguyên các thuật ngữ (Agent, Map, Rank, Bundle, Skin...) bằng tiếng anh.
    3. Tên Skin/Bundle dùng bản quốc tế (VD: 'Reaver, Forsaken, Prime, Recon...').
    4. KHÔNG giải thích luyên thuyên, chỉ trả về nội dung đã dịch.
    5. Trình bày sạch sẽ, dễ đọc."""
    
    # Chỉ thêm tiêu đề nếu có, tránh AI echo lại prefix rỗng
    if title:
        user_prompt = f"Tiêu đề: {title}\nMô tả: {text}"
    else:
        user_prompt = text
    
    res = await _call_nvidia_api(system_prompt, user_prompt, max_tokens=300)
    
    return res if res else f"{title}\n\n{text}"[:500] if title else text[:500]


async def format_opus_content(title: str, content: str, target_lang: str = 'tiếng Việt', image_urls: list[str] | None = None) -> str:
    system_prompt = f"""Bạn là người tóm tắt tin tức Valorant Mobile.
    QUY TẮC TỐI THƯỢNG:
    1. Phân tích ẢNH được gửi kèm (nếu có) để hiểu rõ nội dung bài viết.
    2. Kết hợp thông tin từ ẢNH và TEXT để viết lại nội dung hoàn chỉnh bằng {target_lang}.
    3. BẮT BUỘC NGẮN GỌN: Tổng cộng DƯỚI 200 CHỮ.
    4. Trình bày bằng gạch đầu dòng Markdown (bullet points) để vừa vặn với Discord Embed.
    5. Giữ nguyên thuật ngữ game (Agent, Map, Rank, Bundle, Skin...) bằng tiếng anh.
    6. Tuyệt đối không sinh thêm câu chào hỏi hay giải thích."""
    
    user_prompt = f"Tiêu đề: {title}\nNội dung: {content}"
    res = await _call_nvidia_api(system_prompt, user_prompt, max_tokens=300, image_urls=image_urls)
    return res if res else f"{title}\n{content}"[:200]
