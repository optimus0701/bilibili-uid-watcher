# 🎮 Valorant Mobile CN - Bilibili Discord Bot

> **Note:** Vietnamese version below. / Bản tiếng Việt ở bên dưới.

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.4.0-red)
![NVIDIA AI](https://img.shields.io/badge/AI-NVIDIA%20Gemma--3-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

A powerful and lightweight Discord Bot designed to synchronize the latest news from **Valorant Mobile CN (Bilibili)** directly to your Discord server.

## ✨ Key Features

- 🤖 **Advanced Multimodal AI:** Powered by **NVIDIA Gemma-3-27b-it**, the bot analyzes both text and images from Bilibili's Opus posts to provide concise, context-aware summaries.
- 🖼️ **Smart Image Optimization:** Automatically detects image aspect ratios (Portrait, Landscape, Square) and applies optimal cropping/scaling for the best possible Discord Embed preview.
- 🚀 **High Performance & Low Latency:** built with `aiohttp` and pure API integration. No heavy browsers like Selenium or Chrome are required, making it ideal for low-spec VPS (using < 50MB RAM).
- 🌍 **Bilingual UI:** Each message includes a `[🇺🇸 Translate to English]` button, allowing international communities to instantly translate Vietnamese content back to English.
- 🚨 **Self-Healing & Alerts:** Automatically monitors Bilibili API health. If an error occurs, it notifies the owner in a private log channel with a `[✅ Fixed]` resolution button.
- ⏱️ **Zero-Delay Tracking:** Runs 24/7 with customizable polling intervals to ensure your community is the first to know.

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=optimus0701/docker-bili-bot-valm&type=Date)](https://star-history.com/#optimus0701/docker-bili-bot-valm&Date)

## 🛠️ Installation

### Prerequisites
- **Python 3.11+**
- **Discord Bot Token** ([Discord Developer Portal](https://discord.com/developers/applications))
- **NVIDIA API Key** ([NVIDIA build](https://build.nvidia.com/google/gemma-3-27b-it))

### Local Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/optimus0701/docker-bili-bot-valm.git
   cd docker-bili-bot-valm
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (see [Configuration](#configuration)).
4. Run the bot:
   ```bash
   python bot.py
   ```

### Docker Setup (Recommended)
```bash
# Build the image
docker build -t optimus0701/bili-bot-valm .

# Run the container
docker run -d --name valo-bot --env-file .env optimus0701/bili-bot-valm
```

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
# --- Discord Config ---
DISCORD_BOT_TOKEN=your_token_here
DISCORD_CHANNEL_ID=your_news_channel_id
LOGS_CHANNEL_ID=your_log_channel_id
OWNER_ID=your_discord_id
DISCORD_ROLES_ID=role_id_1,role_id_2  # Roles to ping in Release mode

# --- AI Config ---
NVIDIA_API_KEY=nvapi-xxxxxx

# --- Bilibili Config ---
BILIBILI_UID=3546856908917475  # Valorant Mobile CN Official UID
CHECK_INTERVAL=300             # Polling interval in seconds

# --- Bot Config ---
ENV_MODE=debug                 # 'debug' or 'release'
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

# 🇻🇳 Tiếng Việt (Vietnamese Version)

# 🎮 Valorant Mobile CN - Bilibili Discord Bot

Một Discord Bot mạnh mẽ và siêu nhẹ giúp đồng bộ hóa tin tức mới nhất từ **Valorant Mobile CN (Bilibili)** trực tiếp về Server Discord của bạn.

## ✨ Tính năng nổi bật

- 🤖 **AI Đa phương thức (Multimodal):** Sử dụng model **NVIDIA Gemma-3-27b-it**, bot có khả năng phân tích cả hình ảnh và văn bản từ các bài đăng Bilibili để đưa ra tóm tắt thông minh, chuẩn xác.
- 🖼️ **Tối ưu hóa hình ảnh:** Tự động nhận diện tỉ lệ ảnh (Ảnh dọc, Ảnh ngang, Ảnh vuông) để cắt/chỉnh size tối ưu nhất cho Discord Embed, tránh việc ảnh bị dài quá khổ.
- 🚀 **Tốc độ cao & Tiết kiệm tài nguyên:** Sử dụng `aiohttp` và API thuần. Không dùng Selenium/Chrome, giúp chạy mượt mà trên VPS yếu (chỉ tốn < 50MB RAM).
- 🌍 **Giao diện song ngữ:** Tích hợp sẵn nút bấm `[🇺🇸 Translate to English]` dưới mỗi bài đăng để các thành viên quốc tế có thể dịch ngược sang tiếng Anh ngay lập tức.
- 🚨 **Cảnh báo lỗi thông minh:** Kiểm tra sức khỏe API Bilibili 24/7. Nếu có lỗi, bot sẽ ping Owner trong kênh log riêng kèm nút `[✅ Đã khắc phục]`.
- ⏱️ **Theo dõi không độ trễ:** Chạy 24/7 với thời gian quét tùy chỉnh, đảm bảo cộng đồng của bạn nhận tin tức nhanh nhất.

## 🛠️ Hướng dẫn cài đặt

### Yêu cầu
- **Python 3.11+**
- **Discord Bot Token**
- **NVIDIA API Key**

### Cài đặt thủ công
1. Clone dự án:
   ```bash
   git clone https://github.com/optimus0701/docker-bili-bot-valm.git
   cd docker-bili-bot-valm
   ```
2. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo file `.env` và điền cấu hình.
4. Chạy bot:
   ```bash
   python bot.py
   ```

### Chạy bằng Docker
```bash
docker build -t optimus0701/bili-bot-valm .
docker run -d --name valo-bot --env-file .env optimus0701/bili-bot-valm
```

## 📄 License

Dự án này được phát hành dưới giấy phép **MIT License**.

---
*Developed with ❤️ for the Valorant Mobile community.*