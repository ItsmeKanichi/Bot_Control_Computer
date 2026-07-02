<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Telegram_Bot_API-v20+-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/Discord.py-2.3+-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
  <img src="https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Ngrok-1F1E37?style=for-the-badge&logo=ngrok&logoColor=white" alt="Ngrok">
</div>

<h1 align="center">🖥️ Bot Control Computer</h1>
<h3 align="center">Telegram &amp; Discord — Điều khiển máy tính từ xa</h3>

<p align="center">
  <strong>Điều khiển, giám sát và tự động hóa máy tính của bạn từ xa thông qua Telegram hoặc Discord.<br>Clone về, điền token, chạy một lệnh — xong.</strong>
</p>

<div align="center">
  <a href="#tinh-nang">Tính năng</a> •
  <a href="#cau-truc">Cấu trúc</a> •
  <a href="#yeu-cau">Yêu cầu</a> •
  <a href="#cai-dat">Cài đặt</a> •
  <a href="#lenh">Lệnh</a> •
  <a href="#tac-gia">Tác giả</a>
</div>

---

<a name="tinh-nang"></a>
## ✨ Tính năng

| Nhóm | Tính năng |
| :--- | :--- |
| 🔌 **Hệ thống** | Tắt máy, khởi động lại, chế độ ngủ — tất cả có xác nhận trước khi thực hiện |
| 📸 **Màn hình** | Chụp ảnh màn hình chất lượng cao, quay video tối đa 30 giây |
| 📂 **File** | Upload file lên máy tính, download file về chat, xóa file từ xa |
| 🖥️ **Thông tin** | Danh sách tiến trình, thông tin phần cứng/OS, tài khoản người dùng |
| 🌐 **Mạng** | Xem cấu hình IP, release/renew IP address |
| 🌍 **Trình duyệt** | Mở web, phát YouTube, điều khiển trình duyệt (Chrome/Brave/Edge/Opera) |
| 🖱️ **Touchpad ảo** | Điều khiển chuột qua điện thoại (Flask + Ngrok), thanh điều chỉnh âm lượng |
| ⌨️ **Bàn phím ảo** | Gõ phím, phím tắt từ xa qua chat |

---

<a name="cau-truc"></a>
## 📁 Cấu trúc Project

```
Bot_Control_Computer/
│
├── ⚡ start.bat                       ← 🚀 Click đúp để chạy nhanh (Windows)
├── 📄 run.py                          ← Launcher tự động bằng Python
│
├── 🤖 Bot_Telegram.py                  ← Telegram Bot (toàn bộ logic)
├── 🤖 Bot_Discord.py                   ← Discord Bot (toàn bộ logic)
│
├── 📦 requirements.txt                ← Tất cả Python dependencies
├── ⚙️  .env.example                   ← Mẫu cấu hình (copy → .env)
├── 📖 README.md
│
└── 🌐 templates/                      ← Giao diện web cho Touchpad ảo
    ├── touchpad.html                  ← Touchpad điều khiển chuột
    └── volume_touchpad.html           ← Thanh điều chỉnh âm lượng
```

---

<a name="yeu-cau"></a>
## 📋 Yêu cầu

| | |
| :--- | :--- |
| **Hệ điều hành** | Windows 10/11 *(Linux/macOS: một số tính năng Windows-only bị giới hạn)* |
| **Python** | **3.10** trở lên *(đã test trên Python 3.14)* |
| **Quyền hạn** | Khuyến nghị chạy với quyền **Administrator** cho các lệnh hệ thống/mạng |

---

<a name="cai-dat"></a>
## 🚀 Cài đặt & Chạy

### Bước 0 — Cài đặt Python (Nếu chưa có)

Nếu máy tính của bạn chưa có Python hoặc phiên bản cũ hơn `3.10`:

1. Truy cập [python.org/downloads](https://www.python.org/downloads/) và tải bộ cài đặt Python mới nhất cho hệ điều hành của bạn.
2. Mở trình cài đặt vừa tải về.
3. Tích chọn ô **"Add python.exe to PATH"** (hoặc **"Add Python to PATH"**) ở màn hình cài đặt đầu tiên.

> ⚠️ **QUAN TRỌNG:** Bước chọn **"Add python.exe to PATH"** là **bắt buộc**. Nếu bỏ qua bước này, hệ thống sẽ không nhận diện được lệnh `python` từ Command Prompt / PowerShell ở các bước sau.

4. Chọn **Install Now** và hoàn tất quá trình cài đặt.
5. Kiểm tra cài đặt thành công bằng cách mở CMD/PowerShell và chạy lệnh: `python --version`.

### Bước 1 — Clone repository

```bash
git clone https://github.com/ItsmeKanichi/Bot_Control_Computer.git
cd Bot_Control_Computer
```

### Bước 2 — Tạo file `.env`

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Mở file `.env` và điền thông tin:

```env
# === Telegram Bot ===
TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ALLOWED_USERS=YOUR_TELEGRAM_USER_ID

# === Discord Bot ===
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
DISCORD_ALLOWED_USERS=YOUR_DISCORD_USER_ID

# === Ngrok (cho Virtual Touchpad) ===
NGROK_AUTH_TOKEN=YOUR_NGROK_AUTH_TOKEN
```

> ℹ️ **LƯU Ý:**
>
> **Telegram:** Lấy `TOKEN` từ [@BotFather](https://t.me/BotFather) · Lấy User ID từ [@userinfobot](https://t.me/userinfobot)
>
> **Discord:** Tạo bot tại [discord.com/developers](https://discord.com/developers/applications) → **Bot** → bật **MESSAGE CONTENT INTENT** → copy token vào `DISCORD_TOKEN`. Lấy User ID: bật **Developer Mode** trong Discord → chuột phải tên mình → **Copy User ID**
>
> **Ngrok:** Đăng ký tại [ngrok.com](https://ngrok.com) → lấy token tại [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken). Cũng cần tải [Ngrok CLI](https://ngrok.com/download) và chạy `ngrok config add-authtoken <TOKEN>`

### Bước 3 — Chạy bot

- **Windows:** Click đúp vào file `start.bat` để khởi chạy nhanh.
- **Cách khác (mọi OS):** Mở terminal và chạy lệnh:
  ```bash
  python run.py
  ```

**Launcher (`run.py` / `start.bat`) sẽ tự động:**

```
1️⃣  Tạo .venv virtual environment (nếu chưa có)
2️⃣  Cài tất cả thư viện từ requirements.txt   (bỏ qua nếu đã cài, MD5 check)
3️⃣  Cài Playwright browsers (Chromium)         (nếu chưa có)
4️⃣  Hiện menu chọn platform → chạy bot
```

```
  🖥️  BOT CONTROL COMPUTER
     by Kanichi
  ──────────────────────────────────────────
  [1] 🔵 Telegram Bot
  [2] 🟣 Discord Bot
  [0] ❌ Thoát
  ──────────────────────────────────────────
```

> 💡 **MẸO:** Từ lần thứ hai trở đi `run.py` khởi động gần như ngay lập tức vì bỏ qua bước cài đặt (trừ khi `requirements.txt` có thay đổi).

<details>
<summary>⚙️ Chạy thủ công (không dùng run.py)</summary>

```bash
# Tạo & kích hoạt venv
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# Cài thư viện
pip install -r requirements.txt

# Cài Playwright browsers
playwright install chromium

# Chạy bot
python Bot_Telegram.py          # Telegram
python Bot_Discord.py           # Discord
```
</details>

---

<a name="lenh"></a>
## ⚡ Danh sách Lệnh

> Tất cả lệnh hoạt động trên **cả Telegram và Discord**.
> Telegram dùng `/lệnh` · Discord dùng slash command `/lệnh`

### 🌟 Thông tin

| Lệnh | Mô tả |
| :--- | :--- |
| `/introduce` | Giới thiệu bot và tác giả |
| `/menu` | Hiển thị toàn bộ danh sách lệnh |

### 🔌 Điều khiển hệ thống

| Lệnh | Mô tả |
| :--- | :--- |
| `/shutdown` | Tắt máy tính *(có xác nhận)* |
| `/restart` | Khởi động lại máy *(có xác nhận)* |
| `/sleep` | Chế độ ngủ *(có xác nhận)* |
| `/cancel` | Hủy lệnh tắt/khởi động đang chờ |

### 📸 Màn hình

| Lệnh | Mô tả |
| :--- | :--- |
| `/screenshot` | Chụp màn hình và gửi về |
| `/recordvideo` | Quay video màn hình (tối đa 30 giây) |

### 📂 Quản lý file

| Lệnh | Mô tả |
| :--- | :--- |
| `/uploadfile` | Hướng dẫn gửi file lên máy tính |
| `/downloadfile [path]` | Gửi file từ máy tính về chat |
| `/deletefile [path]` | Xóa file trên máy tính |

> ⚠️ **LƯU Ý VỀ GIỚI HẠN TỆP:** Giới hạn file: **Telegram** → 50 MB · **Discord** → 25 MB (server thường)

### 🖥️ Thông tin hệ thống

| Lệnh | Mô tả |
| :--- | :--- |
| `/tasklist` | Danh sách tiến trình đang chạy |
| `/systeminfo` | Thông tin phần cứng và OS |
| `/netuser` | Danh sách tài khoản người dùng |
| `/whoami` | Tên tài khoản đang đăng nhập |
| `/hostname` | Tên máy tính |

### 🌐 Mạng

| Lệnh | Mô tả |
| :--- | :--- |
| `/ipconfig` | Cấu hình mạng đầy đủ |
| `/release` | Giải phóng địa chỉ IP *(Windows only)* |
| `/renew` | Gia hạn địa chỉ IP mới *(Windows only)* |

### 🌍 Trình duyệt

| Lệnh | Mô tả |
| :--- | :--- |
| `/playvideo [url]` | Phát video YouTube từ link |
| `/openweb [url]` | Mở trang web bất kỳ |
| `/setbrowser` | Chọn trình duyệt mặc định |

### 🖱️ Touchpad & Tiện ích

| Lệnh | Mô tả |
| :--- | :--- |
| `/mousevirtualsystem` | Touchpad ảo điều khiển chuột (Flask + Ngrok) |
| `/volumevirtualsystem` | Thanh điều chỉnh âm lượng (Flask + Ngrok) |
| `/stoptouchpad` | Dừng touchpad đang chạy |
| `/keyboardemulator [text]` | Mô phỏng gõ phím trên máy tính |


---

<a name="tac-gia"></a>
## 👨‍💻 Tác giả

<div align="center">
  <h3>Luc Kim An (Kanichi)</h3>
  <a href="https://github.com/ItsmeKanichi" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="https://kanichi.dev/" target="_blank">
    <img src="https://img.shields.io/badge/Website-FF7139?style=for-the-badge&logo=Firefox-Browser&logoColor=white" alt="Website">
  </a>
</div>

<p align="center">Made with ❤️ by <a href="https://github.com/ItsmeKanichi">Kanichi</a></p>
