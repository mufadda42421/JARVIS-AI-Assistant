
from voice import speak, listen
from assistant import process_command
from wake_word import wait_for_wake_word


def start_jarvis():

    print("""
    =========================================
          J.A.R.V.I.S. AI ASSISTANT
    =========================================

    [1] Voice Mode
    [2] Typing Mode
    [3] Exit

    """)

    speak("All systems online, Sir.")

    while True:

        try:

            choice = input(
                "\nSelect input mode (1/2/3): "
            ).strip()

            # =================================
            # VOICE MODE
            # =================================

            if choice == "1":

                speak("Voice mode activated, Sir.")

                while True:

                    print("\nWaiting for wake word...")

                    wait_for_wake_word()

                    speak("At your service, Sir.")

                    command = listen()

                    if not command:
                        print("No command recognized. Try again.")
                        continue

                    result = process_command(command)

                    if result is False:
                        return

            # =================================
            # TYPING MODE
            # =================================

            elif choice == "2":

                speak("Typing mode activated, Sir.")

                while True:

                    command = input(
                        "\nYou: "
                    ).strip()

                    if not command:
                        continue

                    result = process_command(command)

                    if result is False:
                        return

            # =================================
            # EXIT
            # =================================

            elif choice == "3":

                speak("Goodbye, Sir. Shutting down.")
                break

            else:

                print("Invalid selection. Choose 1, 2 or 3.")

        except KeyboardInterrupt:

            speak("Shutting down. Goodbye, Sir.")
            break

        except Exception as error:

            print("System Error:", error)
            speak("A minor system error occurred, Sir.")


if __name__ == "__main__":
    start_jarvis()
