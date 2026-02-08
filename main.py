# JARVIS 2.0 — FINAL MAIN (v4.1)
# Phase 3: Continuous Conversation + Memory Brain
# Voice backend: SAPI or ElevenLabs (handled in core.voice)

import os, time, queue, threading, importlib
from typing import Optional

import speech_recognition as sr
from openai import OpenAI

from config import settings
from core.wake_word import WakeWordDetector
from core.voice import speak, set_language   # 🔥 ElevenLabs-ready
from core import memory, scheduler
from gui.hud import start_hud_thread, hud_log, hud_set_mode

# =========================
# OPENAI CONFIG
# =========================
client = OpenAI(api_key=settings.OPENAI_API_KEY)
OPENAI_MODEL = settings.OPENAI_MODEL

# =========================
# WAKE WORD CONFIG
# =========================
PICOVOICE_ACCESS_KEY = settings.PICOVOICE_ACCESS_KEY
KEYWORD_PATH = settings.KEYWORD_PATH

# =========================
# STT CONFIG
# =========================
recognizer = sr.Recognizer()
recognizer.energy_threshold = 250
recognizer.dynamic_energy_threshold = True

# =========================
# GLOBALS
# =========================
command_q = queue.Queue()
skill_modules = {}

# =========================
# SKILLS
# =========================
def load_skills():
    if skill_modules:
        return
    for f in os.listdir("skills"):
        if f.endswith(".py"):
            name = f[:-3]
            skill_modules[name] = importlib.import_module(f"skills.{name}")
            hud_log(f"[SKILL] Loaded {name}")

def run_skill(cmd: str) -> Optional[str]:
    load_skills()
    for m in skill_modules.values():
        if hasattr(m, "handle"):
            try:
                res = m.handle(cmd)
                if res:
                    return res
            except Exception as e:
                hud_log(f"[SKILL ERROR] {e}")
    return None

# =========================
# COMMAND NORMALIZER
# =========================
def normalize_command(text: str) -> str:
    t = text.lower().strip()
    FIXUPS = {
        "combat": "combat mode",
        "combat mo": "combat mode",
        "combat mod": "combat mode",
        "gaming": "gaming mode",
        "normal": "normal mode",
        "stealth": "stealth mode",
        "shut down": "shutdown computer",
        "switch to hindi": "switch to hindi",
        "hindi mein baat karo": "switch to hindi",
        "switch to english": "switch to english",
        "english mein baat karo": "switch to english",
    }
    if t in FIXUPS:
        return FIXUPS[t]
    for k, v in FIXUPS.items():
        if t.endswith(" " + k):
            return v
    return t

# =========================
# OPENAI (LAST RESORT ONLY)
# =========================
def think(prompt: str) -> str:
    try:
        sys_prompt = "You are JARVIS, concise and professional."
        if settings.LANGUAGE == "hi":
            sys_prompt = "You are JARVIS. Reply in Hindi (Devanagari script). Be concise and professional."

        res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=300
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        hud_log(f"[OPENAI ERROR] {e}")
        return "AI error, sir."

# =========================
# COMMAND PROCESSOR
# =========================
def command_processor():
    while True:
        cmd = command_q.get()
        if not cmd:
            continue

        cmd = normalize_command(cmd)
        hud_log(f"[CMD] {cmd}")

        # -------- MODES --------
        if cmd == "combat mode":
            hud_set_mode("combat")
            speak("Combat mode engaged, sir.")
            continue

        if cmd == "gaming mode":
            speak("Gaming mode activated, sir.")
            run_skill("gaming mode")
            continue

        if cmd == "normal mode":
            hud_set_mode("normal")
            speak("Normal mode restored, sir.")
            continue

        # -------- MEMORY --------
        if cmd.startswith("remember "):
            payload = cmd.replace("remember", "", 1).strip()
            if " is " in payload:
                k, v = payload.split(" is ", 1)
            elif " to " in payload:
                k, v = payload.split(" to ", 1)
            else:
                speak("Please tell me what to remember, sir.")
                continue
            memory.remember(k.strip(), v.strip())
            speak(f"I will remember {k.strip()}, sir.")
            continue

        if cmd.startswith("what is ") or cmd.startswith("who is "):
            key = cmd.split(" ", 2)[-1].strip()
            val = memory.recall(key)
            if val:
                speak(f"{key} is {val}, sir.")
                continue

        if cmd.startswith("forget "):
            key = cmd.replace("forget", "", 1).strip()
            if memory.forget(key):
                speak(f"I have forgotten {key}, sir.")
            else:
                speak(f"I have no memory of {key}, sir.")
            continue

        # -------- SKILLS --------
        res = run_skill(cmd)
        if res:
            speak(res)
            continue

        # -------- AI LAST --------
        speak(think(cmd))

# =========================
# VOICE LISTENER — CONTINUOUS
# =========================
def voice_listener(wake: WakeWordDetector):
    conversation_until = 0.0

    while True:
        now = time.time()

        if now < conversation_until:
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower().strip()
                except:
                    time.sleep(0.05)
                    continue

            hud_log(f"[VOICE] {text}")
            command_q.put(text)
            conversation_until = time.time() + 10
            continue

        if not wake.listen():
            time.sleep(0.05)
            continue

        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, phrase_time_limit=5)
                # Choose language based on settings
                lang_code = "hi-IN" if settings.LANGUAGE == "hi" else "en-US"
                text = recognizer.recognize_google(audio, language=lang_code).lower().strip()
            except:
                continue

        if text.startswith("jarvis"):
            text = text.replace("jarvis", "", 1).strip()

        if not text:
            continue

        hud_log(f"[VOICE] {text}")
        command_q.put(text)
        conversation_until = time.time() + 10

# =========================
# MAIN
# =========================
def main():
    start_hud_thread(command_q)
    load_skills()
    
    # Register scheduler callback to speak reminders
    scheduler.register_callback(lambda msg: speak(f"Reminder, sir: {msg}"))

    # Launch WhatsApp Bot (Daemon)
    # whatsapp_bot.launch() # Uncomment to enable (Requires Chrome)

    threading.Thread(target=command_processor, daemon=True).start()

    wake = WakeWordDetector(
        keyword_path=KEYWORD_PATH,
        access_key=PICOVOICE_ACCESS_KEY
    )

    threading.Thread(target=voice_listener, args=(wake,), daemon=True).start()

    speak("Jarvis online, sir.")
    hud_log("JARVIS ONLINE — ELEVENLABS READY")

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
