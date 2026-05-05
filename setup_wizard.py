import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def validate_key(key, provider):
    """Basic validation for API keys."""
    if not key:
        return False
    key = key.strip()
    if provider == "anthropic":
        return key.startswith("sk-ant-") and len(key) > 40
    if provider == "gemini":
        return len(key) > 30
    return True

def _is_headless() -> bool:
    """True on Linux/Pi without a display (i.e., not macOS or Windows)."""
    if sys.platform in ("win32", "darwin"):
        return False
    return "DISPLAY" not in os.environ

def setup_wizard():
    """Checks for API keys and prompts the user via GUI if they are missing.
    Skips silently on headless environments (e.g. Raspberry Pi / server)."""
    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()

    load_dotenv(env_path)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if anthropic_key and gemini_key:
        return

    if _is_headless():
        if not anthropic_key:
            print("WARNING: ANTHROPIC_API_KEY not set. Please add it to your .env file.")
        return

    needs_anthropic = not anthropic_key
    needs_gemini = not gemini_key

    try:
        import tkinter as tk
        from tkinter import simpledialog, messagebox

        root = tk.Tk()
        root.withdraw()

        if needs_anthropic:
            messagebox.showinfo("Setup Required", "The DM Toolkit needs an Anthropic API Key for core AI features (Claude).\n\nIf you don't have one, you can skip, but AI features will be disabled.")
            a_key = simpledialog.askstring("Anthropic API Key", "Paste your Anthropic API Key (sk-ant-...):", show='*')
            if a_key and validate_key(a_key, "anthropic"):
                set_key(str(env_path), "ANTHROPIC_API_KEY", a_key.strip())
                os.environ["ANTHROPIC_API_KEY"] = a_key.strip()
            elif a_key:
                messagebox.showwarning("Invalid Key", "The Anthropic key provided doesn't look valid. It should start with 'sk-ant-'.")

        if needs_gemini:
            prompt_gemini = messagebox.askyesno("Optional Setup", "Would you like to add a Gemini API Key? (Optional, used for free-tier generation and image analysis)")
            if prompt_gemini:
                g_key = simpledialog.askstring("Gemini API Key", "Paste your Gemini API Key:", show='*')
                if g_key and validate_key(g_key, "gemini"):
                    set_key(str(env_path), "GEMINI_API_KEY", g_key.strip())
                    os.environ["GEMINI_API_KEY"] = g_key.strip()
                elif g_key:
                    messagebox.showwarning("Invalid Key", "The Gemini key provided seems too short to be valid.")

        root.destroy()
    except Exception as e:
        print(f"Could not open setup window: {e}")
        print("Please create a .env file manually with ANTHROPIC_API_KEY=your_key")

if __name__ == "__main__":
    setup_wizard()
