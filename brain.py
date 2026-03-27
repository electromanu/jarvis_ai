from groq import Groq
from config import GROQ_API_KEY, MODEL, MAX_RETRIES
from memory import (get_all_tools, save_tool, update_tool_score,
                    log_interaction, get_weak_tools)
from memory_store import load_memory, save_memory, update_frequent_commands
from executor import run_code
import json
import os
import base64


client         = Groq(api_key=GROQ_API_KEY)
echo_memory  = load_memory()
stop_requested = False
conversation_history = []

BUILTIN_TOOLS = {
    "translator": {
        "keywords": ["translate", "in tamil", "in telugu", "in hindi",
                     "in japanese", "in arabic", "in french", "in spanish",
                     "in german", "in chinese", "in korean", "say in",
                     "how do you say", "in language"],
        "template": """
import sys
sys.stdout.reconfigure(encoding='utf-8')
from deep_translator import GoogleTranslator
result = GoogleTranslator(source='auto', target='{target_lang}').translate('{text}')
print(result)
"""
    },
    "app_opener": {
        "keywords": ["open", "launch", "start", "run"],
        "apps": {
            "chrome":    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox":   r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "notepad":   "notepad.exe",
            "calculator":"calc.exe",
            "explorer":  "explorer.exe",
            "cmd":       "cmd.exe",
            "vscode":    r"C:\Users\cherie berry\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "spotify":   r"C:\Users\cherie berry\AppData\Roaming\Spotify\Spotify.exe",
            "camera":    "start microsoft.windows.camera:",
        },
        "template": """
import subprocess
try:
    app_path = r'{app_path}'
    if app_path.startswith('start '):
        subprocess.Popen(app_path, shell=True)
    else:
        subprocess.Popen(app_path)
    print('{app_name} opened successfully')
except Exception as e:
    print('Failed to open {app_name}: ' + str(e))
"""
    },
    "file_manager": {
        "keywords": ["create file", "delete file", "rename file",
                     "move file", "copy file", "list files", "show files",
                     "make file", "remove file"],
        "template": """
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
action   = '{action}'
filepath = r'{filepath}'
dest     = r'{dest}'
if action == 'create':
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('{content}')
    print('File created: ' + filepath)
elif action == 'delete':
    if os.path.exists(filepath):
        os.remove(filepath)
        print('Deleted: ' + filepath)
    else:
        print('File not found: ' + filepath)
elif action == 'list':
    files = os.listdir(filepath)
    for i, f in enumerate(files, 1):
        print(str(i) + '. ' + f)
elif action == 'rename':
    os.rename(filepath, dest)
    print('Renamed to: ' + dest)
"""
    },
    "system_info": {
        "keywords": ["cpu usage", "ram usage", "check battery", "check disk",
                     "my ip", "computer name", "my username",
                     "running apps", "list apps", "show apps", "active apps",
                     "what apps are", "which apps are"],
        "template": """
import sys, psutil, socket, os
sys.stdout.reconfigure(encoding='utf-8')
info_type = '{info_type}'
if info_type == 'cpu':
    print('CPU Usage: ' + str(psutil.cpu_percent(interval=1)) + '%')
elif info_type == 'ram':
    ram = psutil.virtual_memory()
    print('RAM Total: ' + str(round(ram.total/1e9,1)) + 'GB')
    print('RAM Used:  ' + str(round(ram.used/1e9,1)) + 'GB')
    print('RAM Free:  ' + str(round(ram.available/1e9,1)) + 'GB')
elif info_type == 'battery':
    b = psutil.sensors_battery()
    if b:
        print('Battery: ' + str(round(b.percent)) + '% - ' + ('Charging' if b.power_plugged else 'Not charging'))
    else:
        print('No battery detected')
elif info_type == 'disk':
    d = psutil.disk_usage(os.getcwd())
    print('Disk Total: ' + str(round(d.total/1e9,1)) + 'GB')
    print('Disk Used:  ' + str(round(d.used/1e9,1)) + 'GB')
    print('Disk Free:  ' + str(round(d.free/1e9,1)) + 'GB')
elif info_type == 'ip':
    print('IP Address: ' + socket.gethostbyname(socket.gethostname()))
elif info_type == 'name':
    print('Computer: ' + socket.gethostname())
    print('User: ' + os.getlogin())
elif info_type == 'apps':
    seen = set()
    apps = []
    skip = ['svchost.exe','System','Registry','smss.exe','csrss.exe',
            'wininit.exe','services.exe','lsass.exe','fontdrvhost.exe',
            'dwm.exe','SearchIndexer.exe','WmiPrvSE.exe','spoolsv.exe',
            'RuntimeBroker.exe','sihost.exe','taskhostw.exe']
    for p in psutil.process_iter(['name','status']):
        try:
            name = p.info['name']
            if name and name not in seen and p.info['status'] == 'running':
                if name not in skip:
                    seen.add(name)
                    apps.append(name.replace('.exe',''))
        except: pass
    for i, a in enumerate(sorted(apps), 1):
        print(str(i) + '. ' + a)
"""
    },
    "project_creator": {
        "keywords": ["create a project", "make a project", "build a project",
                     "create project", "make project", "zip it", "zip and save",
                     "project with", "files and zip"],
    },
}

LANG_CODES = {
    "tamil":"ta","telugu":"te","hindi":"hi","japanese":"ja","arabic":"ar",
    "french":"fr","spanish":"es","german":"de","chinese":"zh-CN","korean":"ko",
    "russian":"ru","portuguese":"pt","italian":"it","dutch":"nl","turkish":"tr",
    "thai":"th","malay":"ms","kannada":"kn","malayalam":"ml","bengali":"bn",
    "urdu":"ur","punjabi":"pa","marathi":"mr","gujarati":"gu",
}

SKIP_BUILTIN_KEYWORDS = [
    "monitor","every","for 30","for 60","for 10","for 20","for 15",
    "over time","watch","track","keep checking","seconds","minutes",
    "interval","repeatedly","continuously"
]

def ask_groq(messages):
    response = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.2)
    return response.choices[0].message.content.strip()

def classify(user_input):
    response = ask_groq([{
        "role": "user",
        "content": f"""Classify this message as exactly one word.

Message: "{user_input}"

Reply CHAT if it is:
- greeting or farewell
- small talk or casual conversation
- asking about your personality, feelings, opinions, wishes
- asking you to explain a concept or idea
- follow up to a conversation like "tell me more", "any other", "yes", "no", "ok"
- general knowledge question not requiring computer action

Reply TASK if it is:
- requires running code or a script
- requires accessing files, folders, or the file system
- requires opening, closing, or controlling an app
- requires checking system info like cpu, ram, battery, disk, ip
- requires translating text to another language
- requires taking a screenshot or capturing screen
- requires monitoring system over time
- requires scanning wifi or checking internet speed
- requires creating a file, folder, or project
- requires searching the web or wikipedia
- requires sending an email or message
- requires setting a reminder or timer
- requires downloading or uploading anything
- anything that needs to actually DO something on the computer

Reply with ONE WORD ONLY. Either CHAT or TASK. Nothing else."""
    }])
    return "TASK" if "TASK" in response.upper() else "CHAT"

def analyze_screenshot(image_path):
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                {"type": "text", "text": "You are ECHO. Look at this screenshot and describe: 1. What apps are open 2. What content is visible 3. What the user is doing. Be sharp and concise."}
            ]}], max_tokens=500)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not analyze screenshot: {e}"

def format_output(user_input, raw_output):
    if not raw_output or raw_output.strip() == "":
        return "Done!"
    formatted = ask_groq([{"role": "user", "content": f"""The user asked: "{user_input}"
ECHO produced this output: "{raw_output}"
Format this output cleanly. Rules:
- Lists → numbered items one per line
- System info → clear labels and values
- Translation → Original: ... → Translation: ...
- App names → clean names no .exe no PIDs
- NEVER change or make up data — only format what is given
- Keep it short and sharp
Reply with ONLY the formatted output. Nothing else."""}])
    if not formatted or formatted.strip() == "":
        return raw_output
    return formatted.replace("```","").strip()

def create_project_code(user_input):
    response = ask_groq([{"role":"user","content":f"""The user said: "{user_input}"
Extract info and reply ONLY with JSON:
- project_name: snake_case name
- files: list of filenames
- save_path: where to save zip (default: C:\\Users\\cherie berry\\Desktop)
Reply ONLY JSON."""}])
    try:
        clean = response.replace("```json","").replace("```","").strip()
        info  = json.loads(clean)
    except:
        info  = {"project_name":"my_project","files":["main.py"],
                 "save_path":r"C:\Users\cherie berry\Desktop"}
    project_name = info.get("project_name","my_project")
    files        = info.get("files",["main.py"])
    save_path    = info.get("save_path",r"C:\Users\cherie berry\Desktop")
    file_contents = {}
    for fname in files:
        code = ask_groq([{"role":"user","content":f"Write basic starter Python code for '{fname}' in project '{project_name}'. Reply ONLY raw Python code."}])
        file_contents[fname] = code.replace("```python","").replace("```","").strip()
    contents_json = json.dumps(file_contents)
    return f"""
import sys,os,shutil,zipfile,json
sys.stdout.reconfigure(encoding='utf-8')
project_name='{project_name}'
save_path=r'{save_path}'
project_path=os.path.join(save_path,project_name)
zip_path=os.path.join(save_path,project_name+'.zip')
if os.path.exists(project_path): shutil.rmtree(project_path)
if os.path.exists(zip_path): os.remove(zip_path)
os.makedirs(project_path)
file_contents={contents_json}
print('Creating project files...')
for fname,content in file_contents.items():
    with open(os.path.join(project_path,fname),'w',encoding='utf-8') as f:
        f.write(content)
    print('  Created: '+fname)
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
    for fname in os.listdir(project_path):
        zf.write(os.path.join(project_path,fname),os.path.join(project_name,fname))
shutil.rmtree(project_path)
print('Done! Saved to: '+zip_path)
"""

def try_builtin_tool(user_input):
    lower = user_input.lower()
    if any(k in lower for k in SKIP_BUILTIN_KEYWORDS):
        return None
    tool = BUILTIN_TOOLS["project_creator"]
    if any(k in lower for k in tool["keywords"]):
        return create_project_code(user_input)
    tool = BUILTIN_TOOLS["translator"]
    if any(k in lower for k in tool["keywords"]):
        target_lang = None
        for lang, code in LANG_CODES.items():
            if lang in lower:
                target_lang = code
                break
        if target_lang:
            text = ask_groq([{"role":"user","content":f'User said: "{user_input}". Extract only the text to translate. Reply with just that text.'}])
            return tool["template"].replace("{target_lang}",target_lang).replace("{text}",text.strip())
    tool = BUILTIN_TOOLS["app_opener"]
    if any(k in lower for k in tool["keywords"]):
        for app_name, app_path in tool["apps"].items():
            if app_name in lower:
                return tool["template"].replace("{app_path}",app_path).replace("{app_name}",app_name)
    tool = BUILTIN_TOOLS["system_info"]
    if any(k in lower for k in tool["keywords"]):
        if any(k in lower for k in ["running apps","list apps","show apps","active apps","what apps","which apps"]):
            info_type = "apps"
        elif "cpu" in lower:     info_type = "cpu"
        elif "ram" in lower or "memory" in lower: info_type = "ram"
        elif "battery" in lower: info_type = "battery"
        elif "disk" in lower or "storage" in lower: info_type = "disk"
        elif "ip" in lower:      info_type = "ip"
        elif "name" in lower or "username" in lower: info_type = "name"
        else:                    info_type = "ram"
        return tool["template"].replace("{info_type}",info_type)
    tool = BUILTIN_TOOLS["file_manager"]
    if any(k in lower for k in tool["keywords"]):
        desktop = r"C:\Users\cherie berry\Desktop"
        if "list" in lower or "show files" in lower:
            return tool["template"].replace("{action}","list").replace("{filepath}",desktop).replace("{dest}","").replace("{content}","")
        elif "delete" in lower or "remove" in lower:
            fname = ask_groq([{"role":"user","content":f'User said: "{user_input}". Extract just the filename to delete. Reply only filename.'}]).strip()
            fpath = os.path.join(desktop,fname)
            return tool["template"].replace("{action}","delete").replace("{filepath}",fpath).replace("{dest}","").replace("{content}","")
        elif "create" in lower or "make" in lower:
            fname = ask_groq([{"role":"user","content":f'User said: "{user_input}". Extract just the filename to create. Reply only filename.'}]).strip()
            fpath = os.path.join(desktop,fname)
            return tool["template"].replace("{action}","create").replace("{filepath}",fpath).replace("{dest}","").replace("{content}","")
    return None

def pick_saved_tool(user_input, tools):
    if not tools: return None
    tool_list = "\n".join([f"- {t['name']}: {t['description']}" for t in tools.values()])
    answer = ask_groq([{"role":"user","content":f'User said: "{user_input}"\nSaved tools:\n{tool_list}\nDoes any saved tool EXACTLY match? Reply tool name or NONE.'}])
    return answer.strip() if answer.strip() in tools else None

def write_script(user_input, error_history=[]):
    error_context = ""
    if error_history:
        error_context = "\n\nPrevious errors:\n" + "\n".join(error_history) + "\nAvoid these."
    prompt = f"""You are ECHO writing a Python script for Windows.
The user wants: "{user_input}"
{error_context}

Always start with:
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

Critical rules:
- NEVER make up or fake any data. Always get REAL data from the system.
- If monitoring: use time.sleep() to actually wait between readings
- For wifi devices: use subprocess.run(['arp', '-a'], capture_output=True, text=True)
- For internet speed: use speedtest library
- For ping on Windows: use ping -n NOT ping -c
- For translation: use deep_translator NOT googletrans
- For zipping: use Python zipfile module NOT zip command
- Output must be clean — no PIDs, no .exe, numbered lists for multiple items
- If listing files: use os.listdir() or os.walk() for REAL file names
- If listing apps: use psutil.process_iter() for REAL process names
- If screenshot needed: save to desktop as echo_screen.png and print: SCREENSHOT_PATH:C:\\Users\\cherie berry\\Desktop\\echo_screen.png
Reply ONLY raw Python code. No markdown. No backticks. No explanation."""
    code = ask_groq([{"role":"user","content":prompt}])
    return code.replace("```python","").replace("```","").strip()

def name_and_describe_tool(user_input, code):
    response = ask_groq([{"role":"user","content":f'Request: "{user_input}"\nGive JSON with name (snake_case) and description (one sentence).\nReply ONLY: {{"name":"tool_name","description":"what it does"}}'}])
    try:
        clean = response.replace("```json","").replace("```","").strip()
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        data  = json.loads(clean[start:end])
        if "name" not in data or "description" not in data: raise ValueError()
        data["name"] = data["name"].replace(" ","_").replace("-","_").lower()
        return data
    except:
        safe = "_".join(user_input.lower().split()[:3]).replace("?","").replace("!","")
        return {"name": safe, "description": user_input[:100]}

def patch_weak_tools():
    weak = get_weak_tools()
    if not weak: return
    print(f"\n[ECHO] Patching {len(weak)} weak tools...")
    for tool in weak:
        new_code = write_script(tool["description"])
        success, output, error, _ = run_code(new_code)
        if success:
            save_tool(tool["name"], tool["description"], new_code)
        else:
            path = f"tools/{tool['name']}.json"
            if os.path.exists(path): os.remove(path)

def handle(user_input):
    global conversation_history, stop_requested

    user_input = user_input.lstrip(': -').strip()
    if not user_input:
        return "Yes?"

    if user_input.strip().lower() in ["stop","stop echo","cancel"]:
        stop_requested = True
        return "Stopping current task."
    stop_requested = False

    # let groq classify — CHAT or TASK
    msg_type = classify(user_input)

    if msg_type == "CHAT":
        conversation_history.append({"role":"user","content":user_input})
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        messages = [
            {"role":"system","content":"""You are ECHO, a powerful AI assistant running on Windows.
You can do almost anything on the computer — open apps, manage files, check system info,
translate languages, take screenshots, monitor system, scan wifi, create projects and much more.
You learn new skills automatically by writing Python scripts.
Reply in 1-2 sharp sentences for chat. Use numbered list for listing things.
Be witty and confident. Never make up capabilities you don't have.
Do not reference previous sessions."""}
        ] + conversation_history
        reply = ask_groq(messages)
        if not reply: reply = "Yes, how can I help?"
        conversation_history.append({"role":"assistant","content":reply})
        update_frequent_commands(echo_memory, user_input)
        save_memory(echo_memory)
        return reply

    # TASK — run a script
    # 1. builtin tools
    builtin_code = try_builtin_tool(user_input)
    if builtin_code:
        if stop_requested: return "Task stopped."
        success, output, error, _ = run_code(builtin_code)
        if success and output.strip():
            log_interaction(user_input, "builtin", True)
            update_frequent_commands(echo_memory, user_input)
            save_memory(echo_memory)
            return format_output(user_input, output)
        print(f"[ECHO] Built-in failed: {error}")

    # 2. saved tools
    tools     = get_all_tools()
    tool_name = pick_saved_tool(user_input, tools)
    if tool_name:
        if stop_requested: return "Task stopped."
        code = write_script(user_input)
        success, output, error, _ = run_code(code)
        update_tool_score(tool_name, success)
        log_interaction(user_input, tool_name, success, error)
        if success and output.strip():
            if "SCREENSHOT_PATH:" in output:
                img_path = output.split("SCREENSHOT_PATH:")[-1].strip()
                if os.path.exists(img_path):
                    return analyze_screenshot(img_path)
            save_tool(tool_name, tools[tool_name]["description"], code)
            update_frequent_commands(echo_memory, user_input)
            save_memory(echo_memory)
            return format_output(user_input, output)
        else:
            path = f"tools/{tool_name}.json"
            if os.path.exists(path): os.remove(path)

    # 3. write new script
    error_history = []
    for attempt in range(MAX_RETRIES):
        if stop_requested: return "Task stopped."
        print(f"[ECHO] Writing script... attempt {attempt + 1}")
        code = write_script(user_input, error_history)
        status, output, error, path = run_code(code)
        if status and output.strip():
            if "SCREENSHOT_PATH:" in output:
                img_path = output.split("SCREENSHOT_PATH:")[-1].strip()
                if os.path.exists(img_path):
                    return analyze_screenshot(img_path)
            meta = name_and_describe_tool(user_input, code)
            save_tool(meta["name"], meta["description"], code)
            log_interaction(user_input, meta["name"], True)
            update_frequent_commands(echo_memory, user_input)
            save_memory(echo_memory)
            return format_output(user_input, output)
        else:
            print(f"[ECHO] Failed: {error}")
            error_history.append(error)

    # 4. all 3 attempts failed — honest fallback
    log_interaction(user_input, "none", False)
    return "Couldn't complete that after 3 attempts. Try being more specific."
