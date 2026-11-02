
import datetime
import re

from voice import speak
from brain import ask_ai
from automation import execute_command, is_local_command
from memory import save_memory


# ==========================================
#          J.A.R.V.I.S. COMMAND ENGINE
# ==========================================

EXIT_COMMANDS = [
    "exit",
    "quit",
    "goodbye",
    "shutdown jarvis",
    "stop jarvis",
    "go offline",
]


def _save_response(command, response):
    try:
        save_memory(command, response)
    except Exception as error:
        print("Memory save warning:", error)


def _process_command(command, speak_response=True):
    """
    Shared command engine.

    Returns:
        (keep_running, response_text)
    """

    if not command or not command.strip():
        return True, ""

    original_command = command.strip()
    normalized = original_command.lower().strip()

    print(f"\nYou: {original_command}")

    # EXIT J.A.R.V.I.S.
    if normalized in EXIT_COMMANDS:
        response = "Goodbye, Sir. Shutting down."
        if speak_response:
            speak(response)
        return False, response

    # TIME
    if re.search(
        r"\b(what time is it|tell me the time|current time|time now)\b",
        normalized
    ) or normalized == "time":

        current_time = datetime.datetime.now().strftime("%I:%M %p")
        response = f"Sir, the time is {current_time}."

        print(f"J.A.R.V.I.S.: {response}")
        if speak_response:
            speak(response)

        _save_response(original_command, response)
        return True, response

    # DATE
    if re.search(
        r"\b(what is the date|what's the date|today's date|current date|tell me the date)\b",
        normalized
    ) or normalized == "date":

        today = datetime.datetime.now().strftime("%d %B %Y")
        response = f"Today is {today}, Sir."

        print(f"J.A.R.V.I.S.: {response}")
        if speak_response:
            speak(response)

        _save_response(original_command, response)
        return True, response

    # LOCAL COMPUTER AUTOMATION
    if is_local_command(original_command):
        try:
            result = execute_command(original_command)

            if result:
                response = str(result)
                print(f"J.A.R.V.I.S.: {response}")

                if speak_response:
                    speak(response)

                _save_response(original_command, response)
                return True, response

            response = "I couldn't complete that command, Sir."
            print(f"J.A.R.V.I.S.: {response}")

            if speak_response:
                speak(response)

            return True, response

        except Exception as error:
            print("Automation error:", repr(error))
            response = "I encountered an error while executing that command, Sir."

            if speak_response:
                speak(response)

            return True, response

    # GEMINI AI
    try:
        response = ask_ai(original_command)

        if not response:
            response = "I couldn't generate a response, Sir."

        response = str(response)
        print(f"J.A.R.V.I.S.: {response}")

        if speak_response:
            speak(response)

        _save_response(original_command, response)
        return True, response

    except Exception as error:
        print("AI processing error:", repr(error))
        response = "I'm having trouble processing that request, Sir."

        if speak_response:
            speak(response)

        return True, response


def process_command(command):
    """
    Original terminal interface.
    Keeps the existing True/False return behaviour.
    """
    keep_running, _ = _process_command(command, speak_response=True)
    return keep_running


def process_command_for_gui(command):
    """
    Desktop interface.
    Returns (keep_running, response_text).
    """
    return _process_command(command, speak_response=True)
