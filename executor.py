import subprocess
import sys
import tempfile
import os
import re


# ==============================
# Extract imports from code
# ==============================
def extract_imports(code):
    imports = re.findall(r'^(?:import|from)\s+([a-zA-Z0-9_]+)', code, re.MULTILINE)
    return list(set(imports))


# ==============================
# Auto install missing packages
# ==============================
def install_if_missing(package):
    pip_names = {
        "cv2": "opencv-python",
        "PIL": "pillow",
        "pynput": "pynput",
        "pyautogui": "pyautogui",
        "psutil": "psutil",
        "requests": "requests",
        "pyttsx3": "pyttsx3",
        "qrcode": "qrcode",
        "fpdf": "fpdf",
        "bs4": "beautifulsoup4",
        "sklearn": "scikit-learn",
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "pandas": "pandas",
        "speedtest": "speedtest-cli",
        "pyzbar": "pyzbar",
        "docx": "python-docx",
        "flask": "flask",
        "pyperclip": "pyperclip",
        "keyboard": "keyboard",
        "mouse": "mouse",
        "playsound": "playsound",
        "gtts": "gtts",
    }

    pip_package = pip_names.get(package, package)

    try:
        __import__(package)
    except ImportError:
        print(f"[JARVIS] Installing {pip_package}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_package],
            capture_output=True,
            text=True
        )


# ==============================
# Run code safely
# ==============================
def run_code(code: str, timeout=30):
    imports = extract_imports(code)

    # install missing deps
    for imp in imports:
        install_if_missing(imp)

    # write temp script
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            timeout=timeout,
            text=True,
            errors="replace"
        )

        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""

        # ❌ real crash
        if result.returncode != 0:
            error = stderr or stdout or "Execution error"

            # 🔥 detect admin requirement
            if "WinError 740" in error or "requires elevation" in error.lower():
                return "ADMIN_REQUIRED", stdout, error, tmp_path

            return False, stdout, error, tmp_path

        # ⚠️ detect logical failure
        failure_keywords = ["error", "failed", "exception", "traceback", "not found"]
        combined = (stdout + " " + stderr).lower()

        if any(k in combined for k in failure_keywords):
            return False, stdout, combined, tmp_path

        # ✅ silent success (like opening apps)
        if stdout == "" and stderr == "":
            return True, "Action executed.", None, tmp_path

        return True, stdout, None, tmp_path

    except subprocess.TimeoutExpired:
        return False, "", "Execution timed out (script hung)", tmp_path

    except Exception as e:
        return False, "", str(e), tmp_path

    finally:
        # ⚠️ DO NOT delete immediately if admin needed
        pass


# ==============================
# Run command as admin
# ==============================
def run_as_admin(script_path):
    import ctypes
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        "cmd.exe",
        f'/c python "{script_path}"',
        None,
        1
    )