
from google import genai
from google.genai import types

from config import GEMINI_API_KEY


# ==========================================
#          J.A.R.V.I.S. AI BRAIN
# ==========================================

MODEL_NAME = "gemini-3.1-flash-lite"

if not GEMINI_API_KEY:
    raise ValueError(
        "Gemini API key missing, Sir. Check your .env file."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==========================================
#          JARVIS PERSONALITY
# ==========================================

JARVIS_PERSONALITY = """
You are J.A.R.V.I.S.
(Just A Rather Very Intelligent System).

You are an advanced personal AI assistant
running locally on the user's Windows computer.

PERSONALITY:

- Intelligent, professional and confident.
- Address your user as Sir when appropriate.
- Be loyal, respectful and helpful.
- Have witty humor and occasional sarcasm.
- Speak naturally like a human assistant.
- Be futuristic but not overly robotic.
- Keep simple answers short.
- Explain complicated topics in detail.
- Help with coding, technology, science and productivity.

INTELLIGENCE:

- Understand natural language.
- Understand incomplete sentences and context.
- Interpret the user's actual intention.
- Handle spelling mistakes where the meaning is clear.
- Understand application names and common aliases.
- Ask concise questions when a request is ambiguous.
- Give practical and accurate answers.

COMPUTER CONTROL RULES:

You are connected to a Python-based local automation system.

However, you do NOT directly control Windows.

Python automation functions are responsible for:
- Opening applications.
- Opening folders.
- Managing files.
- Controlling approved system functions.
- Performing mouse and keyboard actions.

IMPORTANT:

- Never claim that you opened an application unless
  the Python automation system confirms it.
- Never pretend that an action was completed.
- If the user asks you to perform a computer action
  but no tool result is provided, explain that the
  local automation system must execute it.
- Never invent successful tool execution.
- Never claim to have inspected the user's screen
  or files without receiving actual data.
- Never reveal API keys, passwords or credentials.
- Ask for confirmation before dangerous actions.

CONVERSATION:

- Remember the context of the current conversation.
- Understand follow-up questions.
- Avoid unnecessarily repeating explanations.
- Keep responses natural and relevant.
- Do not say Sir in every sentence.

SPECIAL EXPRESSIONS:

- Certainly, Sir.
- Right away, Sir.
- At your service, Sir.
- An interesting question, Sir.
- Everything is running smoothly.

You are J.A.R.V.I.S., the user's personal AI assistant.
"""


# ==========================================
#          CHAT CONFIGURATION
# ==========================================

CHAT_CONFIG = types.GenerateContentConfig(
    system_instruction=JARVIS_PERSONALITY,
    temperature=0.7,
    max_output_tokens=1500
)


# ==========================================
#          CREATE CHAT SESSION
# ==========================================

def create_chat():

    return client.chats.create(
        model=MODEL_NAME,
        config=CHAT_CONFIG
    )


chat = create_chat()


# ==========================================
#          TALK TO JARVIS
# ==========================================

def ask_ai(question):

    global chat

    try:

        response = chat.send_message(
            message=question
        )

        answer = response.text

        if not answer:
            return "I have no response at the moment, Sir."

        return answer.strip()

    except Exception as error:

        print("\n========== JARVIS AI ERROR ==========")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))
        print("=====================================")

        return (
            "I'm experiencing a temporary interruption "
            "in my neural network, Sir."
        )


# ==========================================
#          RESET CONVERSATION
# ==========================================

def reset_chat():

    global chat

    try:

        chat = create_chat()

        return "Conversation reset successfully, Sir."

    except Exception as error:

        print("Chat reset error:", repr(error))

        return "I couldn't reset the conversation, Sir."


# ==========================================
#          CHECK AI STATUS
# ==========================================

def brain_status():

    return (
        f"J.A.R.V.I.S. AI initialized successfully "
        f"using {MODEL_NAME}."
    )


# ==========================================
#          SYSTEM INFORMATION
# ==========================================

if __name__ == "__main__":

    print("====================================")
    print("       J.A.R.V.I.S. AI BRAIN")
    print("====================================")

    print(brain_status())

    print("\nType 'exit' to shut down.\n")

    while True:

        try:

            question = input("You: ").strip()

            if question.lower() in ["exit", "quit"]:
                print("J.A.R.V.I.S.: Goodbye, Sir.")
                break

            if not question:
                continue

            answer = ask_ai(question)

            print("\nJ.A.R.V.I.S.:", answer)

        except KeyboardInterrupt:

            print("\nJ.A.R.V.I.S.: Goodbye, Sir.")
            break
