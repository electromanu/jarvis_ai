JARVIS - AI Agent That Builds Its Own Tools
============================================

SETUP:
1. Open config.py and replace "your_groq_api_key_here" with your actual Groq API key
2. Install dependencies:
   pip install -r requirements.txt
3. Run:
   python main.py

HOW IT WORKS:
- Talk to JARVIS naturally
- If it knows how to do something it runs it instantly
- If it doesn't know, it writes a Python script, tests it, saves it forever
- Gets smarter every time you use it

EXAMPLE COMMANDS:
- "what is my cpu usage"
- "list all files on my desktop"
- "what time is it"
- "open chrome"
- "show my ip address"
- "how much ram is free"

GET YOUR GROQ API KEY:
Visit https://console.groq.com and sign up for free


--------------------------------------------------------------------------------------
 IMAGES::
 -------------------------------------------------------------------------------------
<img width="1366" height="577" alt="jarvis" src="https://github.com/user-attachments/assets/173ca647-1cb9-4db4-95a2-964b729df2e8" />


## How It Works — Full Flow

### Step 1 — You type something
Example: *"open chrome"*

---

### Step 2 — `handle()` receives it
It's the **main function**. Everything passes through it.  
It first cleans your input (removes extra spaces/symbols).

---

### Step 3 — `classify()` decides
It asks the AI one question:
> *"Is this CHAT or TASK?"*

- *"how are you"* → **CHAT**
- *"open chrome"* → **TASK**

---

### Step 4A — If CHAT
Just sends your message to the AI and returns a reply. Simple conversation. Done.

---

### Step 4B — If TASK
Now it tries **3 methods in order:**

**Method 1 — Built-in tools** `try_builtin_tool()`
> Checks keywords. If you said "open" + "chrome" → it already has a template for that. Runs it immediately. Fast and reliable.

**If that fails or doesn't match → Method 2**

**Method 2 — Saved tools** `pick_saved_tool()`
> Checks if Jarvis has **learned this before**. If yes, reuses the saved script.

**If nothing saved → Method 3**

**Method 3 — Write new code** `write_script()`
> Asks the AI to **write a brand new Python script** on the spot.  
> Tries up to **3 times** if it fails.  
> Each retry passes the previous error so the AI doesn't repeat the same mistake.

---

### Step 5 — Run the code
`run_code()` actually **executes** whatever script was produced.

---

### Step 6 — Clean the output
`format_output()` takes the raw messy result and makes it readable.

---

### Step 7 — Save for next time
If a new script was written and it worked → **saves it to memory** so next time Method 2 catches it instantly.

---

## Flow Diagram

```
You type
   ↓
handle()
   ↓
classify()
   ↓
CHAT ————————————→ AI replies → Done
   ↓
TASK
   ↓
Method 1: Built-in template? → Yes → Run → Done
   ↓ No
Method 2: Seen this before?  → Yes → Run → Done
   ↓ No
Method 3: Write new code     → Run → Save → Done
   ↓ Failed 3 times
"Couldn't complete that"
```

---

## Function Summary

| Function | Purpose |
|---|---|
| `ask_groq()` | Talk to the AI |
| `classify()` | Decide CHAT or TASK |
| `analyze_screenshot()` | Describe what's on screen |
| `format_output()` | Make results look clean |
| `create_project_code()` | Build and zip a code project |
| `try_builtin_tool()` | Use pre-built templates |
| `pick_saved_tool()` | Check learned memory |
| `write_script()` | Generate new Python code |
| `name_and_describe_tool()` | Label new tools for saving |
| `patch_weak_tools()` | Fix or delete bad tools |
| `handle()` | Main brain — runs everything |






