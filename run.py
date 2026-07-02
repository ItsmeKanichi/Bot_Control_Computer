"""
run.py — Launcher tự động cho Bot Control Computer
====================================================
Script này sẽ tự động:
  1. Tạo virtual environment (.venv) nếu chưa có
  2. Cài đặt tất cả dependencies từ requirements.txt nếu cần
  3. Cho phép chọn platform (Telegram / Discord) rồi chạy bot

Cách dùng: python run.py
"""

import os
import sys
import subprocess
import platform
import time

# =============================================
# CẤU HÌNH
# =============================================

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
VENV_DIR   = os.path.join(BASE_DIR, ".venv")
REQ_FILE   = os.path.join(BASE_DIR, "requirements.txt")
MARKER     = os.path.join(VENV_DIR, ".deps_installed")   # file đánh dấu đã cài xong

IS_WINDOWS = platform.system() == "Windows"

# Đường dẫn python / pip bên trong venv
if IS_WINDOWS:
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
    VENV_PIP    = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")
    VENV_PIP    = os.path.join(VENV_DIR, "bin", "pip")

# =============================================
# HELPERS IN / OUT
# =============================================

def clr(code: str, text: str) -> str:
    """Bọc màu ANSI cho terminal (bỏ qua trên Windows cũ)"""
    return f"\033[{code}m{text}\033[0m"

def ok(msg):   print(clr("92", f"  ✅  {msg}"))
def info(msg): print(clr("96", f"  ℹ️   {msg}"))
def warn(msg): print(clr("93", f"  ⚠️   {msg}"))
def err(msg):  print(clr("91", f"  ❌  {msg}"))
def step(msg): print(clr("1;97", f"\n  ── {msg}"))

def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """Chạy lệnh, in output realtime, raise nếu lỗi."""
    return subprocess.run(cmd, check=True, **kwargs)

# =============================================
# BANNER
# =============================================

def print_banner():
    os.system("cls" if IS_WINDOWS else "clear")
    print()
    print(clr("1;97", "  🖥️  BOT CONTROL COMPUTER"))
    print(clr("0;37", "     by Kanichi"))
    print(clr("1;34", "  ──────────────────────────────────────────"))
    print(clr("0;96", "  [1] 🔵 Telegram Bot"))
    print(clr("0;35", "  [2] 🟣 Discord Bot"))
    print(clr("0;90", "  [0] ❌ Thoát"))
    print(clr("1;34", "  ──────────────────────────────────────────"))
    print()

# =============================================
# BƯỚC 1 — TẠO VENV
# =============================================

def ensure_venv():
    step("Kiểm tra Virtual Environment (.venv)")

    if os.path.isfile(VENV_PYTHON):
        ok("Virtual environment đã tồn tại, bỏ qua bước tạo mới.")
        return

    info(f"Chưa có .venv → Đang tạo tại: {VENV_DIR}")
    try:
        run([sys.executable, "-m", "venv", VENV_DIR])
        ok("Đã tạo .venv thành công.")
    except subprocess.CalledProcessError as e:
        err(f"Không thể tạo virtual environment: {e}")
        err("Hãy chắc chắn rằng Python ≥ 3.10 đã được cài đặt đúng.")
        sys.exit(1)

# =============================================
# BƯỚC 2 — CÀI REQUIREMENTS
# =============================================

def _req_hash() -> str:
    """Tính hash đơn giản của requirements.txt để phát hiện thay đổi."""
    try:
        with open(REQ_FILE, "rb") as f:
            import hashlib
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def _saved_hash() -> str:
    try:
        with open(MARKER, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

def ensure_requirements():
    step("Kiểm tra & cài đặt thư viện (requirements.txt)")

    if not os.path.isfile(REQ_FILE):
        warn("Không tìm thấy requirements.txt — bỏ qua bước cài thư viện.")
        return

    current_hash = _req_hash()

    # Nếu marker tồn tại VÀ hash khớp → đã cài rồi, bỏ qua
    if os.path.isfile(MARKER) and _saved_hash() == current_hash:
        ok("Các thư viện đã được cài đặt đầy đủ, bỏ qua.")
        return

    info("Đang nâng cấp pip...")
    try:
        run([VENV_PYTHON, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    except subprocess.CalledProcessError:
        warn("Không thể nâng cấp pip, tiếp tục cài thư viện...")

    info("Đang cài đặt requirements.txt (có thể mất vài phút lần đầu)...")
    print()
    try:
        # Chạy với output hiện lên màn hình (không dùng -q)
        run([VENV_PYTHON, "-m", "pip", "install", "-r", REQ_FILE])
        # Lưu marker
        with open(MARKER, "w") as f:
            f.write(current_hash)
        print()
        ok("Cài đặt thư viện hoàn tất!")
    except subprocess.CalledProcessError as e:
        print()
        err(f"Cài đặt thất bại: {e}")
        err("Kiểm tra kết nối mạng hoặc file requirements.txt rồi thử lại.")
        sys.exit(1)

# =============================================
# BƯỚC 3 — KIỂM TRA PLAYWRIGHT
# =============================================

def ensure_playwright():
    step("Kiểm tra Playwright browsers")

    # Chạy thử playwright install nếu chưa có chromium
    try:
        result = subprocess.run(
            [VENV_PYTHON, "-c", "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.stop()"],
            capture_output=True, timeout=15
        )
        if result.returncode == 0:
            ok("Playwright đã sẵn sàng.")
            return
    except Exception:
        pass

    info("Đang cài đặt Playwright browsers (chromium)...")
    try:
        run([VENV_PYTHON, "-m", "playwright", "install", "chromium"])
        ok("Playwright browsers đã cài xong.")
    except subprocess.CalledProcessError:
        warn("Không thể cài Playwright browsers tự động.")
        warn("Chạy thủ công: playwright install")

# =============================================
# BƯỚC 4 — MENU CHỌN VÀ CHẠY BOT
# =============================================

def pick_and_run():
    print_banner()

    scripts = {
        "1": ("Telegram Bot", os.path.join(BASE_DIR, "Bot_Telegram.py"), "🔵"),
        "2": ("Discord Bot",  os.path.join(BASE_DIR, "Bot_Discord.py"),          "🟣"),
    }

    while True:
        try:
            choice = input(clr("1;97", "  👉 Chọn platform (0/1/2): ")).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            info("Đã hủy.")
            sys.exit(0)

        if choice in scripts:
            name, script_path, icon = scripts[choice]

            if not os.path.isfile(script_path):
                err(f"Không tìm thấy file: {script_path}")
                continue

            print()
            info(f"{icon} Đang khởi động {name}...")
            print(clr("90", "  " + "─" * 46))
            print()
            time.sleep(0.5)

            try:
                subprocess.run([VENV_PYTHON, script_path])
            except KeyboardInterrupt:
                print()
                info("Bot đã dừng.")
            break

        elif choice == "0":
            print()
            info("👋 Thoát.")
            sys.exit(0)

        else:
            warn("Lựa chọn không hợp lệ. Hãy nhập 0, 1 hoặc 2.")

# =============================================
# ENTRY POINT
# =============================================

def main():
    # Bật màu ANSI trên Windows 10+
    if IS_WINDOWS:
        os.system("color")

    print()
    print(clr("1;97", "  ══════════════════════════════════════════════"))
    print(clr("1;97", "    Bot Control Computer - Launcher"))
    print(clr("1;97", "  ══════════════════════════════════════════════"))

    ensure_venv()
    ensure_requirements()
    ensure_playwright()

    print()
    ok("Môi trường đã sẵn sàng!")
    time.sleep(0.4)

    pick_and_run()


if __name__ == "__main__":
    main()
