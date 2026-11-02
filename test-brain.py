
from brain import ask_ai

print("J.A.R.V.I.S. AI SYSTEM ONLINE")

while True:

    question = input("\nYou: ")

    if question.lower() == "exit":
        print("JARVIS: Goodbye, Sir.")
        break

    answer = ask_ai(question)

    print("\nJARVIS:", answer)
