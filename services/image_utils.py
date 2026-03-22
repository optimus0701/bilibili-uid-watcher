def optimize_bili_image(cover_data):
    """
    Tối ưu hóa link ảnh dựa trên tỉ lệ ngang/dọc của ảnh gốc.
    cover_data: Object 'cover' từ JSON của Bilibili.
    """
    if not cover_data or 'url' not in cover_data:
        return ""
        
    url = cover_data['url']
    width = cover_data.get('width', 1)
    height = cover_data.get('height', 1)
    
    # Chuẩn hóa URL
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("http://"):
        url = url.replace("http://", "https://")
    
    # Tính tỉ lệ (Ratio)
    ratio = width / height
    
    # TRƯỜNG HỢP 1: Ảnh cực kỳ dài (Infographic, Patch Notes...)
    # Tỉ lệ Rộng < 0.8 * Cao (Ví dụ: 1080x15228)
    if ratio < 0.8:
        # Cắt lấy phần đầu ảnh để làm cover đẹp, không bị quá dài trên Discord
        return url + "@400w_600h_1c.webp"
    
    # TRƯỜNG HỢP 2: Ảnh ngang (Landscape - Thường là ảnh chụp/wallpaper)
    # Tỉ lệ Rộng > 1.5 * Cao
    elif ratio > 1.5:
        return url + "@600w_338h_1c.webp"  # Tỉ lệ gần 16:9
        
    # TRƯỜNG HỢP 3: Ảnh gần vuông hoặc ảnh tiêu chuẩn
    # Sử dụng cấu hình bạn đã chọn
    return url + "@378w_496h_1c.webp"
