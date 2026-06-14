"""
Entry point for the JavaScript interpreter.

Usage:
  python main.py              - Start interactive REPL
  python main.py file.js      - Execute a JavaScript file

Dependencies are auto-installed on first run.
"""
import sys
import os
import subprocess

# ─── Auto-install dependencies BEFORE any other imports ──────────────
REQUIRED_PACKAGES = ["esprima"]

def _ensure_dependencies():
    """Check and auto-install any missing required packages."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    print(f"Installing missing dependencies: {', '.join(missing)}")

    install_commands = [
        [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
        [sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages"] + missing,
    ]

    for cmd in install_commands:
        try:
            subprocess.check_call(cmd)
            print("Dependencies installed successfully.\n")
            return
        except subprocess.CalledProcessError:
            continue

    print("Failed to auto-install dependencies.", file=sys.stderr)
    print("Please install manually: pip install " + " ".join(missing), file=sys.stderr)
    sys.exit(1)

_ensure_dependencies()

# ─── Now safe to import everything ────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import esprima
from interpreter import Interpreter, ReturnException, BreakException, ContinueException
from js_types import UNDEFINED, js_format_output, js_to_string


BANNER = """
╔══════════════════════════════════════════════════════╗
║     Thunder JS Interpreter v1.0                     ║
║     Tree-Walking JavaScript Runtime in Python       ║
║     Type 'exit' or Ctrl+C to quit                  ║
║     Type 'clear' to clear the screen               ║
╚══════════════════════════════════════════════════════╝
"""

PROMPT = "js> "
CONTINUE_PROMPT = "... "


def run_file(filepath):
    """Execute a JavaScript file."""
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        code = f.read()

    interp = Interpreter()
    try:
        interp.execute(code)
    except Exception as e:
        error_msg = str(e)
        if not error_msg.startswith("SyntaxError") and not error_msg.startswith("ReferenceError") and not error_msg.startswith("TypeError"):
            error_msg = f"Error: {error_msg}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def clear_screen():
    """Clear the terminal screen (works on Linux, Mac, Windows, Colab)."""
    print("\033[2J\033[H", end="", flush=True)


def collect_input():
    """
    Collect potentially multi-line input by tracking unmatched delimiters.
    
    Keeps reading lines as long as there are unmatched { }, ( ), or [ ],
    then returns the complete input.
    """
    lines = []
    prompt = PROMPT
    open_braces = 0
    open_parens = 0
    open_brackets = 0
    in_string = False
    string_char = None
    escaped = False

    while True:
        try:
            line = input(prompt)
        except EOFError:
            if lines:
                return "\n".join(lines)
            raise

        lines.append(line)

        # Track delimiters, respecting strings
        for ch in line:
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if in_string:
                if ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                continue
            if ch == '{':
                open_braces += 1
            elif ch == '}':
                open_braces -= 1
            elif ch == '(':
                open_parens += 1
            elif ch == ')':
                open_parens -= 1
            elif ch == '[':
                open_brackets += 1
            elif ch == ']':
                open_brackets -= 1

        # If there are unmatched delimiters, keep reading
        if open_braces > 0 or open_parens > 0 or open_brackets > 0:
            prompt = CONTINUE_PROMPT
        else:
            break

    return "\n".join(lines)


def run_repl():
    """Start an interactive REPL."""
    print(BANNER)
    interp = Interpreter()

    while True:
        try:
            code = collect_input()
            if code is None:
                continue

            stripped = code.strip()

            # Built-in REPL commands
            if stripped in ("exit", "exit()", "quit", "quit()"):
                print("Goodbye!")
                break
            if stripped in ("clear", "cls", ".clear", ".cls"):
                clear_screen()
                continue
            if stripped == "help":
                print("Commands: exit, clear, help")
                print("Enter JavaScript expressions or statements to evaluate.")
                continue

            # Try to execute
            try:
                result = interp.execute_repl(code, interp.global_env)
                if result is not UNDEFINED:
                    print(js_format_output(result))
            except Exception as e:
                error_msg = str(e)
                print(error_msg)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        run_file(filepath)
    else:
        run_repl()


if __name__ == "__main__":
    main()
