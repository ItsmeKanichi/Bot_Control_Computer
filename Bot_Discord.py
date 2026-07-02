import os
import sys
import re
import time
import math
import asyncio
import pyautogui
import numpy as np
import cv2
import comtypes
import threading
import platform
import logging
import discord
from discord.ext import commands
from discord import app_commands
from threading import Thread
from datetime import datetime
from pynput.mouse import Controller, Button

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tắt cảnh báo voice không sử dụng (PyNaCl, davey) từ thư viện discord.py
logging.getLogger('discord.client').setLevel(logging.ERROR)

# Thêm thư viện dotenv để đọc file .env
from dotenv import load_dotenv

# Thêm các thư viện mới cho virtual touchpad
try:
    from flask import Flask, request as flask_request, render_template, jsonify
    from pyngrok import ngrok, conf
    FLASK_NGROK_AVAILABLE = True
except ImportError:
    logger.warning("Flask hoặc pyngrok không có sẵn. Các tính năng touchpad ảo sẽ bị vô hiệu hóa.")
    FLASK_NGROK_AVAILABLE = False

# Import thư viện playwright để điều khiển trình duyệt
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("playwright không có sẵn. Các tính năng trình duyệt sẽ bị vô hiệu hóa.")
    PLAYWRIGHT_AVAILABLE = False

# Import thư viện pycaw để điều khiển âm thanh
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception as e:
    logger.warning(f"Lỗi khi import pycaw: {e}")
    PYCAW_AVAILABLE = False

# =============================================
# THIẾT LẬP CHUNG VÀ CẤU HÌNH
# =============================================

# Xác định thư mục chứa file chạy
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(BASE_DIR, '.env')

# Tải biến môi trường từ file .env
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# Lấy Token Discord Bot từ biến môi trường
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Lấy danh sách người dùng được phép sử dụng bot (Discord User ID)
try:
    ALLOWED_USERS = [int(user_id) for user_id in os.getenv('DISCORD_ALLOWED_USERS', '').split(',') if user_id.strip()]
except (ValueError, TypeError) as e:
    logger.error(f"Lỗi khi phân tích danh sách DISCORD_ALLOWED_USERS: {e}")
    ALLOWED_USERS = []

# Đường dẫn lưu file tải về
if platform.system() == "Windows":
    DEFAULT_UPLOAD_FOLDER = "D:/"  # REPLACE YOUR UPLOAD FOLDER
else:
    DEFAULT_UPLOAD_FOLDER = os.path.expanduser("~/Downloads/")

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', DEFAULT_UPLOAD_FOLDER)

# Tạo thư mục nếu chưa tồn tại
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
except Exception as e:
    logger.error(f"Không thể tạo thư mục tại {UPLOAD_FOLDER}: {e}")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Đã tạo thư mục dự phòng tại {UPLOAD_FOLDER}")

# Định nghĩa các nhóm lệnh để hiển thị trong menu (đồng bộ với Telegram)
COMMAND_GROUPS = {
    "intro": {
        "title": "⚡️ GIỚI THIỆU",
        "commands": {
            "/introduce": "Giới thiệu về tôi."
        }
    },
    "system": {
        "title": "⚡️ ĐIỀU KHIỂN HỆ THỐNG",
        "commands": {
            "/shutdown": "Lệnh tắt máy.",
            "/sleep": "Lệnh vào chế độ ngủ.",
            "/restart": "Lệnh khởi động máy.",
            "/cancel": "Huỷ toàn bộ các lệnh."
        }
    },
    "image": {
        "title": "⚡️ LỆNH HÌNH ẢNH",
        "commands": {
            "/screenshot": "Chụp ảnh màn hình và gửi về máy.",
            "/recordvideo": "Quay video màn hình và gửi về máy."
        }
    },
    "file": {
        "title": "⚡️ QUẢN LÝ FILE",
        "commands": {
            "/uploadfile": "Người dùng gửi file để tải lên máy.",
            "/downloadfile": "Người dùng nhập đường dẫn để tải về.",
            "/deletefile": "Người dùng nhập đường dẫn để xoá file."
        }
    },
    "info": {
        "title": "⚡️ THÔNG TIN HỆ THỐNG",
        "commands": {
            "/tasklist": "Danh sách các tiến trình đang chạy.",
            "/systeminfo": "Thông tin hệ thống.",
            "/netuser": "Danh sách người dùng trên máy tính.",
            "/whoami": "Tên tài khoản đang đăng nhập.",
            "/hostname": "Hiển thị tên máy tính."
        }
    },
    "network": {
        "title": "⚡️ MẠNG",
        "commands": {
            "/ipconfig": "Thông tin cấu hình mạng.",
            "/release": "Giải phóng địa chỉ IP hiện tại.",
            "/renew": "Gia hạn địa chỉ IP mới."
        }
    },
    "browser": {
        "title": "⚡️ TRÌNH DUYỆT",
        "commands": {
            "/playvideo": "Phát video YouTube từ link.",
            "/openweb": "Mở các trang web.",
            "/setbrowser": "Chọn trình duyệt mặc định (chrome, brave, edge, opera)."
        }
    },
    "utility": {
        "title": "⚡️ TIỆN ÍCH",
        "commands": {
            "/mousevirtualsystem": "Điều khiển chuột với touchpad ảo.",
            "/volumevirtualsystem": "Điều khiển âm lượng với touchpad ảo.",
            "/keyboardemulator": "Điều khiển bàn phím ảo.",
            "/stoptouchpad": "Dừng touchpad đang chạy."
        }
    },
    "help": {
        "title": "⚡️ TRỢ GIÚP",
        "commands": {
            "/menu": "Hiển thị danh sách các lệnh."
        }
    }
}

# Đường dẫn đến các trình duyệt
if platform.system() == "Windows":
    BROWSER_PATHS = {
        "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "brave": "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
        "edge": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "opera": "C:/Program Files/Opera/launcher.exe"
    }
    USER_DATA_DIRS = {
        "chrome": os.path.join(os.getenv('LOCALAPPDATA', ''), "Google/Chrome/User Data"),
        "brave": os.path.join(os.getenv('LOCALAPPDATA', ''), "BraveSoftware/Brave-Browser/User Data"),
        "edge": os.path.join(os.getenv('LOCALAPPDATA', ''), "Microsoft/Edge/User Data"),
        "opera": os.path.join(os.getenv('APPDATA', ''), "Opera Software/Opera Stable")
    }
else:
    BROWSER_PATHS = {
        "chrome": "/usr/bin/google-chrome",
        "brave": "/usr/bin/brave-browser",
        "edge": "/usr/bin/microsoft-edge",
        "opera": "/usr/bin/opera"
    }
    USER_DATA_DIRS = {
        "chrome": os.path.expanduser("~/.config/google-chrome"),
        "brave": os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
        "edge": os.path.expanduser("~/.config/microsoft-edge"),
        "opera": os.path.expanduser("~/.config/opera")
    }

# Biến toàn cục cho Playwright
playwright_instance = None
browser = None
page = None
current_browser_type = "brave"

# Biến toàn cục cho quay video
is_recording = False
recording_thread = None

# Tạo đối tượng điều khiển chuột
try:
    mouse = Controller()
except Exception as e:
    logger.error(f"Không thể khởi tạo Controller chuột: {e}")
    mouse = None

# Port cho Flask server
FLASK_PORT = 5500

# Các biến cho Ngrok và quản lý touchpad
ngrok_tunnel = None
ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
flask_server_thread = None
current_touchpad_type = None
active_touchpad_channel_id = None
touchpad_active = False

# =============================================
# DISCORD BOT SETUP
# =============================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =============================================
# KIỂM TRA QUYỀN NGƯỜI DÙNG
# =============================================

def check_permission(user_id: int) -> bool:
    """Kiểm tra xem người dùng có được phép sử dụng bot hay không"""
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS

async def permission_denied(interaction: discord.Interaction):
    """Gửi thông báo từ chối quyền"""
    await interaction.response.send_message(
        "⚠️ **Bạn không có quyền sử dụng bot này!**\n\nBot này chỉ phục vụ cho người dùng được ủy quyền.",
        ephemeral=True
    )
    logger.warning(f"Người dùng không được phép: ID {interaction.user.id}, Tên: {interaction.user.name}")

# =============================================
# CHỤP MÀN HÌNH
# =============================================

def capture_high_quality_screenshot():
    """Chụp màn hình chất lượng cao"""
    try:
        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img
    except Exception as e:
        logger.error(f"Lỗi khi chụp màn hình: {e}")
        return None

# =============================================
# QUAY VIDEO
# =============================================

def start_recording(output_path, fps=10, duration=30):
    """Bắt đầu ghi video màn hình"""
    global is_recording, recording_thread

    if is_recording:
        return False

    is_recording = True

    def record():
        global is_recording
        try:
            screen_size = pyautogui.size()
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, screen_size)

            start_time = time.time()
            while is_recording and (time.time() - start_time) < duration:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
                time.sleep(1 / fps)

            out.release()
            is_recording = False
        except Exception as e:
            logger.error(f"Lỗi khi ghi video: {e}")
            is_recording = False

    recording_thread = Thread(target=record, daemon=True)
    recording_thread.start()
    return True

def stop_recording():
    """Dừng ghi video"""
    global is_recording, recording_thread
    is_recording = False
    if recording_thread and recording_thread.is_alive():
        recording_thread.join(timeout=5)
    return True

# =============================================
# TRÌNH DUYỆT (PLAYWRIGHT)
# =============================================

async def initialize_browser():
    """Khởi tạo trình duyệt Playwright"""
    global playwright_instance, browser, page, current_browser_type

    if not PLAYWRIGHT_AVAILABLE:
        return False, "playwright chưa được cài đặt."

    try:
        playwright_instance = await async_playwright().start()
        browser_path = BROWSER_PATHS.get(current_browser_type)
        user_data_dir = USER_DATA_DIRS.get(current_browser_type)

        if not browser_path or not os.path.exists(browser_path):
            return False, f"Không tìm thấy trình duyệt {current_browser_type}"

        browser = await playwright_instance.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=browser_path,
            headless=False,
            args=["--start-maximized"]
        )
        page = await browser.new_page()
        return True, "Thành công"
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo trình duyệt: {e}")
        return False, str(e)

async def close_browser():
    """Đóng trình duyệt"""
    global playwright_instance, browser, page
    try:
        if page:
            await page.close()
            page = None
        if browser:
            await browser.close()
            browser = None
        if playwright_instance:
            await playwright_instance.stop()
            playwright_instance = None
        return True, "Đã đóng trình duyệt"
    except Exception as e:
        logger.error(f"Lỗi khi đóng trình duyệt: {e}")
        return False, str(e)

# =============================================
# ÂM LƯỢNG (PYCAW)
# =============================================

def get_windows_volume_interface():
    """Lấy interface điều khiển âm lượng của Windows"""
    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        return None
        
    try:
        # Khởi tạo COM trước khi truy cập các API âm thanh của Windows
        comtypes.CoInitialize()
        
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, 'EndpointVolume'):
            return devices.EndpointVolume
        elif hasattr(devices, 'Activate'):
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        else:
            dev = getattr(devices, '_dev', devices)
            interface = dev.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        logger.error(f"Lỗi khi lấy interface âm lượng: {e}")
        return None
    finally:
        # Giải phóng tài nguyên COM sau khi sử dụng
        try:
            comtypes.CoUninitialize()
        except:
            pass

def get_current_volume():
    """Lấy mức âm lượng hiện tại (0.0 đến 1.0)"""
    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        return 0.5
        
    try:
        # Khởi tạo COM trước khi truy cập
        com_initialized = False
        comtypes.CoInitialize()
        com_initialized = True
        
        volume = get_windows_volume_interface()
        if volume:
            current_volume = volume.GetMasterVolumeLevelScalar()
            return current_volume
        return 0.5  # Giá trị mặc định nếu không lấy được
    except Exception as e:
        logger.error(f"Lỗi khi lấy mức âm lượng: {e}")
        return 0.5
    finally:
        # Giải phóng tài nguyên COM
        if com_initialized:
            try:
                comtypes.CoUninitialize()
            except:
                pass

def set_windows_volume(volume_level):
    """Đặt mức âm lượng (0.0 đến 1.0)"""
    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        return False
        
    try:
        # Khởi tạo COM trước khi truy cập
        com_initialized = False
        comtypes.CoInitialize()
        com_initialized = True
        
        # Đảm bảo giá trị âm lượng nằm trong khoảng hợp lệ
        volume_level = max(0.0, min(1.0, volume_level))
        
        # Lấy interface âm lượng
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, 'EndpointVolume'):
            volume = devices.EndpointVolume
        elif hasattr(devices, 'Activate'):
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
        else:
            dev = getattr(devices, '_dev', devices)
            interface = dev.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Đặt âm lượng
        volume.SetMasterVolumeLevelScalar(volume_level, None)
        return True
    except Exception as e:
        logger.error(f"Lỗi khi đặt mức âm lượng: {e}")
        return False
    finally:
        # Giải phóng tài nguyên COM
        if com_initialized:
            try:
                comtypes.CoUninitialize()
            except:
                pass

def get_volume_percentage():
    """Lấy mức âm lượng dưới dạng phần trăm"""
    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        return 50
        
    try:
        volume_scalar = get_current_volume()
        return round(volume_scalar * 100)
    except Exception as e:
        logger.error(f"Lỗi khi tính phần trăm âm lượng: {e}")
        return 50

# =============================================
# FLASK + NGROK CHO TOUCHPAD ẢO
# =============================================

if FLASK_NGROK_AVAILABLE:
    flask_app = Flask(__name__)

    TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)

    def start_flask_server():
        """Khởi động Flask server"""
        import logging as _logging
        _logging.getLogger('werkzeug').setLevel(_logging.ERROR)
        flask_app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)

    def start_ngrok():
        """Khởi động Ngrok và trả về URL công khai"""
        global ngrok_tunnel
        try:
            if ngrok_auth_token:
                conf.get_default().auth_token = ngrok_auth_token
            if ngrok_tunnel:
                try:
                    ngrok.disconnect(ngrok_tunnel.public_url)
                except:
                    pass
            ngrok_tunnel = ngrok.connect(FLASK_PORT, "http")
            return ngrok_tunnel.public_url
        except Exception as e:
            logger.error(f"Lỗi khi khởi động Ngrok: {e}")
            return None

    def stop_ngrok():
        """Dừng Ngrok"""
        global ngrok_tunnel
        try:
            if ngrok_tunnel:
                ngrok.disconnect(ngrok_tunnel.public_url)
                ngrok_tunnel = None
        except Exception as e:
            logger.error(f"Lỗi khi dừng Ngrok: {e}")

    @flask_app.route('/')
    def index():
        return render_template('touchpad.html')

    @flask_app.route('/move', methods=['POST'])
    def move_mouse():
        try:
            data = flask_request.json
            dx = data.get('dx', 0)
            dy = data.get('dy', 0)
            if mouse:
                mouse.move(dx, dy)
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    @flask_app.route('/click', methods=['POST'])
    def click_mouse():
        try:
            data = flask_request.json
            button_type = data.get('button', 'left')
            if mouse:
                btn = Button.left if button_type == 'left' else Button.right
                mouse.click(btn)
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    @flask_app.route('/scroll', methods=['POST'])
    def scroll_mouse():
        try:
            data = flask_request.json
            # JS gửi key 'amount' (dy từ touchmove, dương = kéo xuống = scroll down)
            amount = data.get('amount', data.get('dy', 0))
            if mouse:
                # Scroll: amount dương → kéo xuống → cuộn lên (âm); âm → cuộn xuống (dương)
                scroll_clicks = -int(amount) // 10 if int(amount) != 0 else 0
                if scroll_clicks != 0:
                    mouse.scroll(0, scroll_clicks)
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    @flask_app.route('/doubleclick', methods=['POST'])
    def doubleclick_mouse():
        try:
            if mouse:
                mouse.click(Button.left, 2)  # Click 2 lần
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    @flask_app.route('/volume')
    def volume_touchpad_page():
        return render_template('volume_touchpad.html')

    @flask_app.route('/getvolume', methods=['GET'])
    def get_volume_api():
        try:
            if platform.system() == "Windows":
                comtypes.CoInitialize()
            volume_percent = get_volume_percentage()
            return jsonify({"volume": volume_percent})
        except Exception as e:
            return jsonify({"volume": 50, "error": str(e)})
        finally:
            if platform.system() == "Windows":
                try:
                    comtypes.CoUninitialize()
                except:
                    pass

    @flask_app.route('/setvolume', methods=['POST'])
    def set_volume_api():
        try:
            if platform.system() == "Windows":
                comtypes.CoInitialize()
            data = flask_request.json
            volume_percent = data.get('volume', 50)
            volume_scalar = volume_percent / 100.0
            success = set_windows_volume(volume_scalar)
            actual_volume = get_volume_percentage() if success else volume_percent
            return jsonify({"status": "success" if success else "failed", "volume": actual_volume})
        except Exception as e:
            return jsonify({"status": "failed", "volume": 50, "error": str(e)})
        finally:
            if platform.system() == "Windows":
                try:
                    comtypes.CoUninitialize()
                except:
                    pass

# =============================================
# HELPER: CHẠY LỆNH HỆ THỐNG
# =============================================

async def run_system_command(command: str, encoding: str = 'utf-8') -> str:
    """Chạy lệnh CMD/shell và trả về kết quả dưới dạng chuỗi"""
    try:
        if platform.system() != "Windows":
            if command == "tasklist":
                command = "ps aux"
            elif command == "systeminfo":
                command = "uname -a && lsb_release -a"
            elif command.startswith("ipconfig"):
                command = command.replace("ipconfig", "ifconfig")

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            result = ""
            if stdout:
                result += stdout.decode(encoding, errors='replace')
            if stderr:
                result += "\nStderr:\n" + stderr.decode(encoding, errors='replace')
            return result.strip() if result.strip() else "Lệnh không trả về kết quả."
        except asyncio.TimeoutError:
            process.terminate()
            return "Lệnh thực thi quá thời gian (30 giây). Đã hủy."
    except Exception as e:
        return f"Lỗi khi thực thi lệnh: {str(e)}"

async def send_result_as_file(interaction: discord.Interaction, content: str, filename: str, command: str = ""):
    """Gửi kết quả của lệnh. Nếu ngắn sẽ gửi dạng text trực tiếp (chia nhỏ nếu cần), nếu quá dài (>30000 ký tự) sẽ gửi dạng file .txt"""
    # Nếu kết quả <= 30000 ký tự, gửi trực tiếp dưới dạng các tin nhắn text
    if len(content) <= 30000:
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_size = 1900
        
        for line in lines:
            # Cộng thêm 1 ký tự cho '\n'
            if current_length + len(line) + 1 > chunk_size:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line) + 1
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                prefix = f"✅ **Kết quả lệnh '{command}':**\n" if command else "✅ **Kết quả lệnh:**\n"
            else:
                prefix = ""
            await interaction.followup.send(content=f"{prefix}```text\n{chunk}\n```")
        return

    # Nếu kết quả > 30000 ký tự, ghi vào file và gửi file như trước
    time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(UPLOAD_FOLDER, f"{time_str}_{filename}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        file_size = os.path.getsize(file_path) / 1024
        await interaction.followup.send(
            content=f"✅ Đã chạy lệnh thành công. Kích thước file: **{file_size:.2f} KB**. Đang gửi file:",
            file=discord.File(file_path, filename=filename)
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi gửi file: {e}")
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

# =============================================
# DISCORD UI VIEWS (BUTTONS)
# =============================================

class ConfirmView(discord.ui.View):
    """View xác nhận lệnh hệ thống nguy hiểm"""

    def __init__(self, action: str):
        super().__init__(timeout=60)
        self.action = action

    @discord.ui.button(label="✅ Xác nhận", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return

        try:
            if self.action == "shutdown":
                await interaction.response.edit_message(content="🔄 **Máy sẽ tắt sau 3 giây.**", view=None)
                os.system("shutdown /s /t 3" if platform.system() == "Windows" else "sudo shutdown -h +1")

            elif self.action == "restart":
                await interaction.response.edit_message(content="🔄 **Máy sẽ khởi động lại sau 3 giây.**", view=None)
                os.system("shutdown /r /t 3" if platform.system() == "Windows" else "sudo shutdown -r +1")

            elif self.action == "sleep":
                await interaction.response.edit_message(content="🔄 **Máy tính sẽ vào chế độ ngủ ngay bây giờ.**", view=None)
                if platform.system() == "Windows":
                    import ctypes
                    # SetSuspendState(Hibernate=0, ForceCritical=1, DisableWakeEvent=0)
                    # Hibernate=0 → Sleep (S3), không phải Hibernate
                    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                else:
                    os.system("sudo systemctl suspend")

            elif self.action == "cancel":
                await interaction.response.edit_message(content="🔄 **Đang hủy lệnh tắt/khởi động lại...**", view=None)
                result = os.system("shutdown -a" if platform.system() == "Windows" else "sudo shutdown -c")
                msg = "✅ Đã hủy toàn bộ lệnh tắt/khởi động lại." if result == 0 else "ℹ️ Không có lệnh nào để hủy."
                await interaction.edit_original_response(content=msg)

        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Có lỗi xảy ra: {e}", view=None)

        self.stop()

    @discord.ui.button(label="❎ Hủy", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❎ **Hành động đã bị hủy.**", view=None)
        self.stop()


class VideoControlView(discord.ui.View):
    """View điều khiển video trong trình duyệt"""

    def __init__(self):
        super().__init__(timeout=3600)

    @discord.ui.button(label="⏯ Phát / Tạm dừng", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            await page.evaluate("document.querySelector('video').paused ? document.querySelector('video').play() : document.querySelector('video').pause()")
            await interaction.response.send_message("✅ Đã chuyển trạng thái phát / tạm dừng.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="⏪ Tua lại 10s", style=discord.ButtonStyle.secondary)
    async def rewind(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            await page.evaluate("document.querySelector('video').currentTime -= 10")
            await interaction.response.send_message("⏪ Đã tua lại 10 giây.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="⏩ Tua tới 10s", style=discord.ButtonStyle.secondary)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            await page.evaluate("document.querySelector('video').currentTime += 10")
            await interaction.response.send_message("⏩ Đã tua tới 10 giây.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="❌ Đóng trình duyệt", style=discord.ButtonStyle.danger)
    async def close_browser_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        success, msg = await close_browser()
        await interaction.response.edit_message(
            content=f"✅ Đã đóng trình duyệt {current_browser_type.capitalize()}.",
            view=None
        )
        self.stop()


class WebControlView(discord.ui.View):
    """View điều khiển trình duyệt web"""

    def __init__(self):
        super().__init__(timeout=3600)

    @discord.ui.button(label="🔄 Tải lại", style=discord.ButtonStyle.primary)
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            await page.reload()
            await interaction.response.send_message("🔄 Đã tải lại trang.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="⬅️ Quay lại", style=discord.ButtonStyle.secondary)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            has_history = await page.evaluate("window.history.length > 1")
            if has_history:
                await page.go_back()
                await interaction.response.send_message("⬅️ Đã quay lại trang trước.", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Không có trang trước để quay lại.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="➡️ Tiến tới", style=discord.ButtonStyle.secondary)
    async def go_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not page:
            await interaction.response.send_message("❌ Không có trình duyệt nào đang mở.", ephemeral=True)
            return
        try:
            await page.go_forward()
            await interaction.response.send_message("➡️ Đã tiến tới trang sau.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @discord.ui.button(label="❌ Đóng trình duyệt", style=discord.ButtonStyle.danger)
    async def close_browser_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        success, msg = await close_browser()
        await interaction.response.edit_message(
            content=f"✅ Đã đóng trình duyệt {current_browser_type.capitalize()}.",
            view=None
        )
        self.stop()


class StopRecordingView(discord.ui.View):
    """View dừng quay video"""

    def __init__(self, recording_path: str):
        super().__init__(timeout=60)
        self.recording_path = recording_path

    @discord.ui.button(label="⏹️ Dừng quay", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return

        global is_recording
        if not is_recording:
            await interaction.response.edit_message(content="❌ Không có quá trình ghi video nào đang diễn ra.", view=None)
            return

        await interaction.response.edit_message(content="⏳ Đang dừng và xử lý video, vui lòng đợi...", view=None)

        is_recording = False
        stop_recording()
        time.sleep(1)

        if not os.path.exists(self.recording_path):
            await interaction.edit_original_response(content="❌ Không tìm thấy file video ghi màn hình.")
            return

        file_size_mb = os.path.getsize(self.recording_path) / (1024 * 1024)

        if file_size_mb > 25:
            await interaction.edit_original_response(
                content=f"❌ Video quá lớn ({file_size_mb:.2f} MB) vượt quá giới hạn Discord (25MB).\n"
                        f"📁 Đã lưu tại: `{self.recording_path}`"
            )
            return

        if file_size_mb < 0.01:
            await interaction.edit_original_response(
                content=f"⚠️ Video có vẻ không hợp lệ (kích thước quá nhỏ: {file_size_mb:.4f} MB). Vui lòng thử lại."
            )
            try:
                os.remove(self.recording_path)
            except:
                pass
            return

        try:
            await interaction.edit_original_response(content="📤 Đang gửi video...")
            await interaction.channel.send(
                content="🎬 **Video ghi màn hình của bạn.**",
                file=discord.File(self.recording_path, filename=os.path.basename(self.recording_path))
            )
            await interaction.edit_original_response(content="✅ Video đã được gửi thành công!")
        except Exception as e:
            await interaction.edit_original_response(
                content=f"❌ Lỗi khi gửi video: {e}\n📁 Đã lưu tại: `{self.recording_path}`"
            )
        finally:
            try:
                if os.path.exists(self.recording_path):
                    os.remove(self.recording_path)
            except:
                pass

        self.stop()


class TouchpadRefreshView(discord.ui.View):
    """View làm mới kết nối Ngrok cho touchpad"""

    def __init__(self, touchpad_type: str):
        super().__init__(timeout=7200)
        self.touchpad_type = touchpad_type

    @discord.ui.button(label="🔄 Làm mới kết nối", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        if not FLASK_NGROK_AVAILABLE:
            await interaction.response.send_message("❌ Flask/pyngrok không có sẵn.", ephemeral=True)
            return

        await interaction.response.edit_message(content="🔄 Đang làm mới kết nối Ngrok, vui lòng đợi...", view=None)

        try:
            stop_ngrok()
            public_url = start_ngrok()
            if not public_url:
                await interaction.edit_original_response(content="❌ Không thể khởi động lại Ngrok. Vui lòng kiểm tra kết nối mạng.")
                return

            endpoint = "/volume" if self.touchpad_type == "volume" else ""
            action_info = ""
            if self.touchpad_type == "mouse":
                action_info = "• Chạm và kéo trên màn hình touchpad để di chuyển chuột\n• Nhấn nút để thực hiện các thao tác chuột\n• Chế độ cuộn cho phép bạn cuộn trang lên/xuống"
            elif self.touchpad_type == "volume":
                action_info = "• Kéo thanh trượt sang trái/phải để điều chỉnh âm lượng\n• Nhấn các nút để nhanh chóng đặt mức âm lượng cụ thể"

            new_view = TouchpadRefreshView(self.touchpad_type)
            await interaction.edit_original_response(
                content=f"✅ **Đã làm mới kết nối thành công!**\n\n"
                        f"🔗 **Truy cập URL mới trên điện thoại của bạn:**\n`{public_url}{endpoint}`\n\n"
                        f"📱 **Hướng dẫn sử dụng:**\n"
                        f"{action_info}\n\n"
                        f"⚠️ Kết nối này sẽ hết hạn sau khoảng 2 giờ\n"
                        f"💡 Dùng `/stoptouchpad` để dừng khi không cần nữa",
                view=new_view
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Lỗi khi làm mới kết nối: {e}")


class BrowserSelectView(discord.ui.View):
    """View chọn trình duyệt"""

    def __init__(self, available_browsers: list):
        super().__init__(timeout=60)
        for b in available_browsers:
            self.add_item(BrowserButton(b))


class BrowserButton(discord.ui.Button):
    """Button chọn trình duyệt"""

    def __init__(self, browser_name: str):
        super().__init__(label=browser_name.capitalize(), style=discord.ButtonStyle.primary)
        self.browser_name = browser_name

    async def callback(self, interaction: discord.Interaction):
        global current_browser_type
        if not check_permission(interaction.user.id):
            await permission_denied(interaction)
            return
        current_browser_type = self.browser_name
        msg = f"✅ Đã đặt **{self.browser_name.capitalize()}** làm trình duyệt mặc định."
        if self.browser_name == "edge":
            msg += "\n\n⚠️ *Lưu ý: Microsoft Edge có thể gặp vấn đề. Nếu gặp lỗi, hãy chạy bot với quyền Admin và đóng các cửa sổ Edge đang mở.*"
        await interaction.response.edit_message(content=msg, view=None)

# =============================================
# SLASH COMMANDS
# =============================================

# --- GIỚI THIỆU & MENU ---

@tree.command(name="introduce", description="Giới thiệu về bot và tác giả")
async def introduce(interaction: discord.Interaction):
    """Hiển thị thông tin giới thiệu"""
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    intro_text = (
        "**👨‍💻 DEVELOPER | LỤC KIM AN**\n\n"
        
        "**Just a human.**\n\n"
        
        "**📩 CONTACT FOR WORK:**\n"
        "• Discord: `kanichi_`\n"
        "• Email: [kanichi@duck.com](mailto:kanichi@duck.com)\n"
        "• GitHub: [Kanichi](https://github.com/ItsmeKanichi)\n"
        "• My Website: [kanichi.dev](https://kanichi.dev/)\n\n"
        
        "**🌟 DONATE ME:**\n"
        "• 💳 **Bank:** `11111111169` | LUC VAN AN | Techcombank\n\n"
        
        "Nhấn **/menu** để xem danh sách các lệnh"
    )
    await interaction.response.send_message(intro_text)


@tree.command(name="menu", description="Hiển thị danh sách tất cả các lệnh")
async def menu(interaction: discord.Interaction):
    """Hiển thị menu lệnh"""
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    menu_text = "**📋 DANH SÁCH CÁC LỆNH**\n**📌 Author:** `Kanichi`\n\n"
    
    # Tạo danh sách lệnh theo từng nhóm
    for group_key, group_info in COMMAND_GROUPS.items():
        group_title = group_info["title"]
        commands = group_info["commands"]
        
        # Định dạng lệnh trong nhóm
        command_list = "\n".join([
            f"**🔻** `{command}` **➡️** {desc}" for command, desc in commands.items()
        ])
        
        # Thêm nhóm vào menu
        menu_text += f"**{group_title}**\n{command_list}\n\n"
        
    await interaction.response.send_message(menu_text)

# --- ĐIỀU KHIỂN HỆ THỐNG ---

@tree.command(name="shutdown", description="Tắt máy tính")
async def shutdown(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    view = ConfirmView("shutdown")
    await interaction.response.send_message("⚠️ **Bạn có chắc chắn muốn tắt máy tính không?**", view=view)


@tree.command(name="restart", description="Khởi động lại máy tính")
async def restart(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    view = ConfirmView("restart")
    await interaction.response.send_message("⚠️ **Bạn có chắc chắn muốn khởi động lại máy tính không?**", view=view)


@tree.command(name="sleep", description="Đưa máy tính vào chế độ ngủ")
async def sleep(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    view = ConfirmView("sleep")
    await interaction.response.send_message("⚠️ **Bạn có chắc chắn muốn đưa máy tính vào chế độ ngủ không?**", view=view)


@tree.command(name="cancel", description="Hủy lệnh tắt/khởi động lại đang chờ")
async def cancel(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    view = ConfirmView("cancel")
    await interaction.response.send_message("⚠️ **Bạn có chắc chắn muốn hủy tất cả các lệnh tắt/khởi động không?**", view=view)

# --- HÌNH ẢNH & VIDEO ---

@tree.command(name="screenshot", description="Chụp ảnh màn hình và gửi về Discord")
async def screen_shot(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    await interaction.response.defer()

    file_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    screenshot_path = os.path.join(UPLOAD_FOLDER, file_name)

    try:
        img = capture_high_quality_screenshot()
        if img is None:
            await interaction.followup.send("❌ Không thể chụp ảnh màn hình.")
            return

        cv2.imwrite(screenshot_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        if not os.path.exists(screenshot_path):
            await interaction.followup.send("❌ Không thể lưu ảnh chụp màn hình.")
            return

        file_size = os.path.getsize(screenshot_path) / (1024 * 1024)
        if file_size > 25:
            await interaction.followup.send(f"⚠️ Ảnh quá lớn ({file_size:.2f} MB) vượt quá giới hạn Discord (25MB).")
            try:
                os.remove(screenshot_path)
            except:
                pass
            return

        await interaction.followup.send(
            content="📸 **Ảnh chụp màn hình**",
            file=discord.File(screenshot_path, filename=file_name)
        )

    except Exception as e:
        logger.error(f"Lỗi khi chụp màn hình: {e}")
        await interaction.followup.send(f"❌ Có lỗi xảy ra khi chụp màn hình: {e}")
    finally:
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except:
            pass


@tree.command(name="recordvideo", description="Quay video màn hình (tối đa 30 giây)")
async def record_video(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    global is_recording

    if is_recording:
        await interaction.response.send_message("⚠️ **Đang quay video rồi. Vui lòng dừng ghi hiện tại trước.**")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(UPLOAD_FOLDER, f"screen_recording_{timestamp}.mp4")

    success = start_recording(output_path)

    if not success:
        await interaction.response.send_message("❌ **Không thể bắt đầu quay video màn hình.**")
        return

    view = StopRecordingView(output_path)
    await interaction.response.send_message(
        "🎥 **Đã bắt đầu quay video màn hình (tối đa 30 giây).** Nhấn nút dưới đây để dừng và lưu video.",
        view=view
    )

# --- QUẢN LÝ FILE ---

@tree.command(name="uploadfile", description="Hướng dẫn tải file lên máy tính")
async def upload_file(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.send_message(
        f"📤 **Hãy gửi file bạn muốn tải lên. File sẽ được lưu vào thư mục** `{UPLOAD_FOLDER}`"
    )


@tree.command(name="downloadfile", description="Tải file từ máy tính và gửi về Discord")
@app_commands.describe(path="Đường dẫn đầy đủ đến file cần tải về")
async def download_file(interaction: discord.Interaction, path: str):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    await interaction.response.defer()

    file_path = path.strip()

    if not os.path.isfile(file_path):
        await interaction.followup.send(f"❌ Không tìm thấy file tại đường dẫn: `{file_path}`")
        return

    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 25:
            await interaction.followup.send(
                f"❌ File quá lớn ({file_size:.2f} MB). Discord chỉ cho phép gửi file tối đa **25MB** (server thường)."
            )
            return

        await interaction.followup.send(
            content=f"✅ File đã được gửi thành công: `{file_path}`",
            file=discord.File(file_path, filename=os.path.basename(file_path))
        )

    except Exception as e:
        logger.error(f"Lỗi khi gửi file {file_path}: {e}")
        await interaction.followup.send(f"❌ Có lỗi xảy ra khi gửi file: {e}")


@tree.command(name="deletefile", description="Xóa file trên máy tính")
@app_commands.describe(path="Đường dẫn đầy đủ đến file cần xóa")
async def deletefile(interaction: discord.Interaction, path: str):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    file_path = path.strip()

    if not os.path.exists(file_path):
        await interaction.response.send_message(f"❌ Không tìm thấy file hoặc thư mục tại đường dẫn: `{file_path}`")
        return

    if os.path.isdir(file_path):
        await interaction.response.send_message(f"⚠️ `{file_path}` là thư mục. Lệnh này chỉ xóa file, không xóa thư mục.")
        return

    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            await interaction.response.send_message(f"✅ File tại đường dẫn `{file_path}` đã được xóa thành công.")
        except PermissionError:
            await interaction.response.send_message(
                f"❌ Không có quyền xóa file: `{file_path}`. File có thể đang được sử dụng bởi chương trình khác."
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Có lỗi xảy ra khi xóa file: {e}")

# --- THÔNG TIN HỆ THỐNG ---

@tree.command(name="tasklist", description="Danh sách các tiến trình đang chạy")
async def tasklist(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    result = await run_system_command("tasklist", encoding='cp850' if platform.system() == "Windows" else 'utf-8')
    
    # Định dạng lại danh sách tiến trình trên Windows để tránh xô lệch cột trên mobile
    if platform.system() == "Windows" and not result.startswith("Lỗi") and not result.startswith("Stderr:"):
        lines = result.split('\n')
        formatted = [f"{'Image Name':<25} | {'PID':<8} | {'Mem Usage':>12}", "-" * 51]
        for line in lines:
            line_strip = line.strip()
            if not line_strip or line_strip.startswith('Image Name') or line_strip.startswith('==='):
                continue
            if len(line) >= 64:
                img = line[0:25].strip()
                pid = line[26:34].strip()
                mem = line[64:].strip()
                formatted.append(f"{img:<25} | {pid:<8} | {mem:>12}")
            else:
                formatted.append(line_strip)
        result = '\n'.join(formatted)

    await send_result_as_file(interaction, result, "tasklist_output.txt", "tasklist")


@tree.command(name="systeminfo", description="Thông tin hệ thống")
async def systeminfo(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    result = await run_system_command("systeminfo", encoding='cp850' if platform.system() == "Windows" else 'utf-8')
    await send_result_as_file(interaction, result, "systeminfo_output.txt", "systeminfo")


@tree.command(name="ipconfig", description="Thông tin cấu hình mạng")
async def ipconfig(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    cmd = "ipconfig /all" if platform.system() == "Windows" else "ifconfig -a"
    result = await run_system_command(cmd, encoding='cp850' if platform.system() == "Windows" else 'utf-8')
    await send_result_as_file(interaction, result, "ipconfig_output.txt", cmd)


@tree.command(name="release", description="Giải phóng địa chỉ IP (Windows only)")
async def release(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    if platform.system() != "Windows":
        await interaction.response.send_message("❌ Lệnh này chỉ hỗ trợ trên Windows.")
        return
    await interaction.response.defer()
    result = await run_system_command("ipconfig /release", encoding='cp850')
    await send_result_as_file(interaction, result, "release_output.txt", "ipconfig /release")


@tree.command(name="renew", description="Yêu cầu địa chỉ IP mới (Windows only)")
async def renew(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    if platform.system() != "Windows":
        await interaction.response.send_message("❌ Lệnh này chỉ hỗ trợ trên Windows.")
        return
    await interaction.response.defer()
    result = await run_system_command("ipconfig /renew", encoding='cp850')
    await send_result_as_file(interaction, result, "renew_output.txt", "ipconfig /renew")


@tree.command(name="netuser", description="Danh sách người dùng trên máy tính")
async def netuser(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    cmd = "net user" if platform.system() == "Windows" else "cat /etc/passwd | cut -d: -f1"
    result = await run_system_command(cmd, encoding='cp850' if platform.system() == "Windows" else 'utf-8')
    await send_result_as_file(interaction, result, "netuser_output.txt", cmd)


@tree.command(name="whoami", description="Tên tài khoản đang đăng nhập")
async def whoami(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    result = await run_system_command("whoami")
    await interaction.followup.send(f"👤 **Tài khoản hiện tại:** `{result.strip()}`")


@tree.command(name="hostname", description="Hiển thị tên máy tính")
async def hostname(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return
    await interaction.response.defer()
    result = await run_system_command("hostname")
    await interaction.followup.send(f"🖥️ **Tên máy tính:** `{result.strip()}`")

# --- TRÌNH DUYỆT ---

@tree.command(name="playvideo", description="Phát video YouTube từ link")
@app_commands.describe(url="Link YouTube cần phát")
async def playvideo(interaction: discord.Interaction, url: str):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    await interaction.response.defer()
    global page, browser

    youtube_url = url.strip()
    if not youtube_url.startswith(('http://', 'https://')):
        youtube_url = 'https://' + youtube_url

    if 'youtube.com' not in youtube_url and 'youtu.be' not in youtube_url:
        await interaction.followup.send("❌ URL không hợp lệ. Vui lòng nhập link YouTube.")
        return

    if not browser or not page:
        await interaction.followup.send(f"🔄 Đang khởi động trình duyệt {current_browser_type.capitalize()}...")
        success, message = await initialize_browser()
        if not success:
            await interaction.followup.send(f"❌ Không thể khởi động trình duyệt: {message}")
            return

    try:
        await page.goto(youtube_url, timeout=30000)
        view = VideoControlView()
        await interaction.followup.send(
            f"✅ **Đã mở video YouTube thành công trên {current_browser_type.capitalize()}.**\n🎮 **Chọn hành động:**",
            view=view
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Không thể mở URL. Kiểm tra kết nối mạng hoặc URL: {e}")


@tree.command(name="openweb", description="Mở trang web trong trình duyệt")
@app_commands.describe(url="URL trang web cần mở")
async def openweb(interaction: discord.Interaction, url: str):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    await interaction.response.defer()
    global page, browser

    web_url = url.strip()
    if not web_url.startswith(('http://', 'https://')):
        web_url = 'https://' + web_url

    if not browser or not page:
        await interaction.followup.send(f"🔄 Đang khởi động trình duyệt {current_browser_type.capitalize()}...")
        success, message = await initialize_browser()
        if not success:
            await interaction.followup.send(f"❌ Không thể khởi động trình duyệt: {message}")
            return

    try:
        await page.goto(web_url, timeout=30000)
        view = WebControlView()
        await interaction.followup.send(
            f"✅ **Đã mở trang web {web_url} trong trình duyệt {current_browser_type.capitalize()}.**\n🎮 **Chọn hành động:**",
            view=view
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Không thể mở URL. Kiểm tra kết nối mạng hoặc URL: {e}")


@tree.command(name="setbrowser", description="Chọn trình duyệt mặc định")
async def setbrowser(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    available_browsers = [b for b, p in BROWSER_PATHS.items() if os.path.exists(p)]

    if not available_browsers:
        await interaction.response.send_message("❌ Không tìm thấy trình duyệt nào được cài đặt trên hệ thống.")
        return

    view = BrowserSelectView(available_browsers)
    note = ""
    if "edge" in available_browsers:
        note = "\n\n*⚠️ Lưu ý: Microsoft Edge có thể gặp vấn đề. Nếu muốn dùng Edge, hãy chạy bot với quyền Admin và đóng tất cả cửa sổ Edge đang mở trước.*"

    await interaction.response.send_message(
        f"**Trình duyệt hiện tại:** `{current_browser_type.capitalize()}`\n"
        f"**Vui lòng chọn trình duyệt mặc định:**{note}",
        view=view
    )

# --- TIỆN ÍCH ---

@tree.command(name="keyboardemulator", description="Mô phỏng gõ phím trên máy tính")
@app_commands.describe(text="Văn bản hoặc phím cần gõ (Enter, Backspace, space)")
async def keyboard_emulator(interaction: discord.Interaction, text: str):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    try:
        key_input = text.strip()
        if key_input.lower() == 'backspace':
            pyautogui.press('backspace')
        elif key_input.lower() == 'enter':
            pyautogui.press('enter')
        elif key_input.lower() == 'space':
            pyautogui.press('space')
        elif key_input.lower().startswith('key:'):
            # Cho phép gõ phím đặc biệt: /keyboardemulator key:ctrl+c
            special_key = key_input[4:].strip()
            keys = [k.strip() for k in special_key.split('+')]
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys[0])
        else:
            pyautogui.typewrite(key_input, interval=0.05)

        await interaction.response.send_message(
            f"⌨️ Đã gõ: `{key_input}`",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Lỗi khi mô phỏng phím: {e}")
        await interaction.response.send_message(f"❌ Lỗi khi mô phỏng phím: {e}", ephemeral=True)


@tree.command(name="mousevirtualsystem", description="Khởi động touchpad ảo điều khiển chuột qua Ngrok")
async def mouse_virtual_system(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    global current_touchpad_type, active_touchpad_channel_id, flask_server_thread, ngrok_tunnel, touchpad_active

    if not FLASK_NGROK_AVAILABLE:
        await interaction.response.send_message(
            "❌ **Tính năng này yêu cầu Flask và pyngrok.**\n"
            "Vui lòng cài đặt thư viện bằng lệnh:\n`pip install flask pyngrok`"
        )
        return

    await interaction.response.defer()

    # Nếu đang chạy chính touchpad này
    if current_touchpad_type == "mouse" and touchpad_active and active_touchpad_channel_id == interaction.channel_id and ngrok_tunnel:
        view = TouchpadRefreshView("mouse")
        await interaction.followup.send(
            f"✅ **Touchpad chuột đã đang chạy!**\n\n"
            f"🔗 **Truy cập URL sau trên điện thoại của bạn:**\n`{ngrok_tunnel.public_url}`\n\n"
            f"📱 **Để điều khiển chuột:**\n"
            f"• Chạm và kéo trên màn hình touchpad để di chuyển chuột\n"
            f"• Nhấn nút để thực hiện các thao tác chuột\n"
            f"• Chế độ cuộn cho phép bạn cuộn trang lên/xuống\n\n"
            f"⚠️ Kết nối này sẽ hết hạn sau khoảng 2 giờ",
            view=view
        )
        return

    # Nếu có touchpad khác đang chạy, dừng nó
    if current_touchpad_type is not None and touchpad_active:
        stop_ngrok()
        current_touchpad_type = None
        active_touchpad_channel_id = None
        touchpad_active = False

    # Khởi động Flask server nếu chưa chạy
    global flask_server_thread
    if flask_server_thread is None or not flask_server_thread.is_alive():
        flask_server_thread = Thread(target=start_flask_server, daemon=True)
        flask_server_thread.start()
        time.sleep(2)

    current_touchpad_type = "mouse"
    active_touchpad_channel_id = interaction.channel_id
    touchpad_active = True

    public_url = start_ngrok()

    if not public_url:
        await interaction.followup.send("❌ Không thể khởi động Ngrok. Vui lòng kiểm tra kết nối mạng và cài đặt Ngrok.")
        current_touchpad_type = None
        active_touchpad_channel_id = None
        touchpad_active = False
        return

    view = TouchpadRefreshView("mouse")
    await interaction.followup.send(
        f"✅ **Touchpad ảo đã sẵn sàng!**\n\n"
        f"🔗 **Truy cập URL sau trên điện thoại của bạn:**\n`{public_url}`\n\n"
        f"📱 **Để điều khiển chuột:**\n"
        f"• Chạm và kéo trên màn hình touchpad để di chuyển chuột\n"
        f"• Nhấn nút để thực hiện các thao tác chuột\n"
        f"• Chế độ cuộn cho phép bạn cuộn trang lên/xuống\n\n"
        f"⚠️ Kết nối này sẽ hết hạn sau khoảng 2 giờ\n"
        f"💡 Sử dụng /stoptouchpad để dừng khi không cần nữa",
        view=view
    )


@tree.command(name="volumevirtualsystem", description="Khởi động touchpad ảo điều chỉnh âm lượng qua Ngrok")
async def volume_virtual_system(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    global current_touchpad_type, active_touchpad_channel_id, flask_server_thread, ngrok_tunnel, touchpad_active

    if not FLASK_NGROK_AVAILABLE:
        await interaction.response.send_message(
            "❌ **Tính năng này yêu cầu Flask và pyngrok.**\n"
            "Vui lòng cài đặt thư viện bằng lệnh:\n`pip install flask pyngrok`"
        )
        return

    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        await interaction.response.send_message(
            "❌ Không thể điều khiển âm lượng vì thư viện pycaw không khả dụng hoặc bạn đang sử dụng hệ điều hành không phải Windows. Vui lòng kiểm tra cài đặt thư viện và hệ điều hành."
        )
        return

    await interaction.response.defer()

    if current_touchpad_type == "volume" and touchpad_active and active_touchpad_channel_id == interaction.channel_id and ngrok_tunnel:
        view = TouchpadRefreshView("volume")
        await interaction.followup.send(
            f"✅ **Touchpad âm lượng đã đang chạy!**\n\n"
            f"🔗 **Truy cập URL sau trên điện thoại của bạn:**\n`{ngrok_tunnel.public_url}/volume`\n\n"
            f"📱 **Hướng dẫn sử dụng:**\n"
            f"• Kéo thanh trượt sang trái/phải để điều chỉnh âm lượng\n"
            f"• Nhấn các nút để nhanh chóng đặt mức âm lượng cụ thể\n\n"
            f"⚠️ Kết nối này sẽ hết hạn sau khoảng 2 giờ",
            view=view
        )
        return

    # Dừng touchpad cũ nếu có
    if current_touchpad_type is not None and touchpad_active:
        stop_ngrok()
        current_touchpad_type = None
        active_touchpad_channel_id = None
        touchpad_active = False

    # Khởi động Flask server nếu chưa chạy
    global flask_server_thread
    if flask_server_thread is None or not flask_server_thread.is_alive():
        flask_server_thread = Thread(target=start_flask_server, daemon=True)
        flask_server_thread.start()
        time.sleep(2)

    current_touchpad_type = "volume"
    active_touchpad_channel_id = interaction.channel_id
    touchpad_active = True

    public_url = start_ngrok()

    if not public_url:
        await interaction.followup.send("❌ Không thể khởi động Ngrok. Vui lòng kiểm tra kết nối mạng và cài đặt Ngrok.")
        current_touchpad_type = None
        active_touchpad_channel_id = None
        touchpad_active = False
        return

    view = TouchpadRefreshView("volume")
    await interaction.followup.send(
        f"✅ **Touchpad điều chỉnh âm lượng đã sẵn sàng!**\n\n"
        f"🔗 **Truy cập URL sau trên điện thoại của bạn:**\n`{public_url}/volume`\n\n"
        f"📱 **Hướng dẫn sử dụng:**\n"
        f"• Kéo thanh trượt sang trái/phải để điều chỉnh âm lượng\n"
        f"• Nhấn các nút để nhanh chóng đặt mức âm lượng cụ thể\n\n"
        f"⚠️ Kết nối này sẽ hết hạn sau khoảng 2 giờ\n"
        f"💡 Dùng `/stoptouchpad` để dừng khi không cần nữa",
        view=view
    )


@tree.command(name="stoptouchpad", description="Dừng touchpad ảo đang chạy")
async def stop_touchpad(interaction: discord.Interaction):
    if not check_permission(interaction.user.id):
        await permission_denied(interaction)
        return

    global current_touchpad_type, active_touchpad_channel_id, touchpad_active

    if current_touchpad_type is None or not touchpad_active:
        await interaction.response.send_message("❌ Không có touchpad nào đang chạy.")
        return

    old_type = current_touchpad_type
    try:
        stop_ngrok()
        current_touchpad_type = None
        active_touchpad_channel_id = None
        touchpad_active = False
        await interaction.response.send_message(f"✅ Đã dừng {old_type} touchpad thành công.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Không thể dừng touchpad: {e}")

# =============================================
# XỬ LÝ FILE ĐÍNH KÈM (UPLOAD)
# =============================================

@bot.event
async def on_message(message: discord.Message):
    """Xử lý khi người dùng gửi file vào channel"""
    # Bỏ qua tin nhắn của bot
    if message.author.bot:
        return

    # Xử lý prefix commands (nếu có)
    await bot.process_commands(message)

    # Chỉ xử lý khi có attachments
    if not message.attachments:
        return

    # Kiểm tra quyền người dùng
    if not check_permission(message.author.id):
        return

    for attachment in message.attachments:
        try:
            file_name = attachment.filename
            # Xử lý tên file trùng lặp
            original_name = file_name
            counter = 1
            while os.path.exists(os.path.join(UPLOAD_FOLDER, file_name)):
                name, ext = os.path.splitext(original_name)
                file_name = f"{name}_{counter}{ext}"
                counter += 1

            file_path = os.path.join(UPLOAD_FOLDER, file_name)

            # Tải file về
            await attachment.save(file_path)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024
                size_str = f"{file_size:.2f} KB" if file_size < 1024 else f"{file_size/1024:.2f} MB"
                await message.reply(
                    f"✅ File `{file_name}` ({size_str}) đã được tải và lưu trong thư mục `{UPLOAD_FOLDER}`"
                )
            else:
                await message.reply(f"❌ Không thể tải file `{file_name}`.")

        except Exception as e:
            logger.error(f"Lỗi khi tải file đính kèm: {e}")
            await message.reply(f"❌ Có lỗi xảy ra khi tải file: {e}")

# =============================================
# BOT EVENTS
# =============================================

@bot.event
async def on_ready():
    """Sự kiện khi bot sẵn sàng"""
    logger.info(f"Discord Bot đã đăng nhập với tên: {bot.user} (ID: {bot.user.id})")
    logger.info(f"Hệ điều hành: {platform.system()} {platform.release()}")
    logger.info(f"Thư mục lưu file: {UPLOAD_FOLDER}")

    # Đồng bộ slash commands
    try:
        synced = await tree.sync()
        logger.info(f"Đã đồng bộ {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Lỗi khi đồng bộ slash commands: {e}")

    # Hiển thị trạng thái bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="máy tính của bạn 🖥️"
        )
    )

    # Kiểm tra trình duyệt có sẵn
    if platform.system() == "Windows":
        available_browsers = [b for b, p in BROWSER_PATHS.items() if os.path.exists(p)]
        if available_browsers:
            logger.info(f"Các trình duyệt khả dụng: {', '.join(available_browsers)}")
        else:
            logger.warning("Không tìm thấy trình duyệt nào trên hệ thống!")

    logger.info("Bot đã sẵn sàng hoạt động!")


@bot.event
async def on_command_error(ctx, error):
    """Xử lý lỗi lệnh"""
    logger.error(f"Lỗi lệnh: {error}")

# =============================================
# KHỞI CHẠY BOT
# =============================================

def main():
    """Hàm chính để khởi chạy Discord bot"""

    # Kiểm tra file .env
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# Telegram Bot\n")
            f.write("TOKEN=REPLACE-YOUR-TELEGRAM-TOKEN\n")
            f.write("ALLOWED_USERS=REPLACE-YOUR-TELEGRAM-USER-ID\n\n")
            f.write("# Discord Bot\n")
            f.write("DISCORD_TOKEN=REPLACE-YOUR-DISCORD-BOT-TOKEN\n")
            f.write("DISCORD_ALLOWED_USERS=REPLACE-YOUR-DISCORD-USER-ID\n\n")
            f.write("# Shared\n")
            f.write("NGROK_AUTH_TOKEN=REPLACE-YOUR-NGROK-TOKEN\n")
        logger.info(f"Đã tạo file .env tại {env_path}. Vui lòng cập nhật thông tin!")

    if not DISCORD_TOKEN:
        logger.error("CẢNH BÁO: Không tìm thấy DISCORD_TOKEN trong file .env! Hãy kiểm tra lại.")
        return

    logger.info("Discord Bot đang khởi động...")

    import atexit
    def cleanup():
        logger.info("Đang dọn dẹp trước khi thoát...")
        if ngrok_tunnel:
            try:
                ngrok.disconnect(ngrok_tunnel.public_url)
            except:
                pass

    atexit.register(cleanup)

    try:
        bot.run(DISCORD_TOKEN, log_handler=None)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error(
            "\n"
            "========================================================================\n"
            "❌ LỖI KHỞI CHẠY DISCORD BOT: THIẾU PRIVILEGED INTENTS!\n"
            "------------------------------------------------------------------------\n"
            "Để bot hoạt động và tải file từ xa, bạn phải bật 'MESSAGE CONTENT INTENT'.\n"
            "Hướng dẫn sửa:\n"
            "  1. Truy cập vào trang: https://discord.com/developers/applications/\n"
            "  2. Chọn Application (Bot) của bạn.\n"
            "  3. Nhấp vào tab 'Bot' ở menu bên trái.\n"
            "  4. Cuộn xuống phần 'Privileged Gateway Intents'.\n"
            "  5. Gạt công tắc BẬT (Enable) tại mục 'MESSAGE CONTENT INTENT'.\n"
            "  6. Nhấn 'Save Changes' ở phía dưới cùng.\n"
            "  7. Chạy lại launcher run.py hoặc file bot.\n"
            "========================================================================\n"
        )
    except Exception as e:
        logger.error(f"Lỗi không xác định khi khởi chạy bot: {e}")


if __name__ == "__main__":
    main()
