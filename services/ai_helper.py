import time
import logging
import aiohttp
from core import config

# Cache cho danh sách models khả dụng
_cached_models: list[str] | None = None
_cache_timestamp: float = 0


def _normalize_image_url(url: str) -> str:
    """Chuẩn hóa URL ảnh về https."""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return url.replace("http://", "https://")
    return url


def _build_messages(system_prompt: str, user_prompt: str, image_urls: list[str] | None = None) -> list[dict]:
    """
    Xây dựng danh sách messages cho API.
    - Nếu có ảnh → gửi multimodal (ảnh + text).
    - Ngược lại → gửi text-only.
    Lưu ý: caller đã kiểm tra vision support, chỉ truyền image_urls khi model hỗ trợ.
    """
    messages = [{"role": "system", "content": system_prompt}]

    if image_urls:
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


async def _fetch_available_models() -> list[str]:
    """Lấy danh sách models khả dụng từ NVIDIA API (có cache)."""
    global _cached_models, _cache_timestamp

    now = time.time()
    if _cached_models is not None and (now - _cache_timestamp) < config.MODELS_CACHE_TIME:
        return _cached_models

    # Derive models URL từ completions URL
    models_url = config.NVIDIA_API_URL.replace('/chat/completions', '/models')
    headers = {
        "Authorization": f"Bearer {config.NVIDIA_API_KEY}",
        "Accept": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(models_url, headers=headers, timeout=15) as response:
                response.raise_for_status()
                data = await response.json()
                model_ids = [m['id'] for m in data.get('data', [])]
                _cached_models = model_ids
                _cache_timestamp = now
                logging.info(f"📋 Đã lấy {len(model_ids)} models khả dụng từ NVIDIA API")
                return model_ids
    except Exception as e:
        logging.warning(f"⚠️ Không thể lấy danh sách models: {e}")
        # Trả về cache cũ nếu có, nếu không trả list rỗng
        return _cached_models if _cached_models is not None else []


def _filter_models_by_prefixes(available: list[str], prefixes: list[str]) -> list[str]:
    """
    Lọc và sắp xếp models theo prefix ưu tiên.
    Prefix đứng trước trong danh sách sẽ có độ ưu tiên cao hơn.
    """
    result = []
    for prefix in prefixes:
        for model_id in available:
            if model_id.startswith(prefix) and model_id not in result:
                result.append(model_id)
    return result


async def _resolve_models() -> tuple[list[str], set[str]]:
    """
    Lấy danh sách models khả dụng từ API, lọc theo prefix ưu tiên.
    Returns: (models_to_try, vision_models)
    """
    available = await _fetch_available_models()

    if available:
        # Lọc AI models theo prefix ưu tiên (qwen/qwen3.5 trước, google/gemma-3 sau...)
        ai_models = _filter_models_by_prefixes(available, config.AI_MODEL_PREFIXES)
        # Lọc vision models theo prefix (google/gemma-3...)
        vision_models = set(_filter_models_by_prefixes(available, config.VISION_MODEL_PREFIXES))

        if ai_models:
            logging.info(f"🤖 AI Models ({len(ai_models)}): {ai_models[:5]}{'...' if len(ai_models) > 5 else ''}")
            logging.info(f"👁️ Vision Models ({len(vision_models)}): {list(vision_models)[:5]}{'...' if len(vision_models) > 5 else ''}")
            return ai_models, vision_models

    # Fallback khi API không trả về models hoặc không match prefix nào
    logging.warning("⚠️ Dùng danh sách model fallback")
    return config.AI_MODELS_FALLBACK, set(config.VISION_MODELS_FALLBACK)


async def _call_nvidia_api(system_prompt: str, user_prompt: str, max_tokens: int, image_urls: list[str] | None = None) -> str:
    headers = {
        "Authorization": f"Bearer {config.NVIDIA_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Lấy danh sách models khả dụng từ API (có cache)
    models_to_try, vision_models = await _resolve_models()

    for model_name in models_to_try:
        # Chỉ gửi ảnh cho model hỗ trợ vision
        current_images = image_urls if model_name in vision_models else None

        payload = {
            "model": model_name,
            "messages": _build_messages(system_prompt, user_prompt, current_images),
            "max_tokens": max_tokens,
            "temperature": 0.20,
            "top_p": 0.70,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.NVIDIA_API_URL, headers=headers, json=payload, timeout=30) as response:
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
