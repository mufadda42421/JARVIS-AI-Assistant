
import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_NAME = "J.A.R.V.I.S."
USER_NAME = "Sir"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

AI_MODEL = "gemini-3.8-flash"

VOICE_RATE = 175
VOICE_VOLUME = 1.0

MIC_SAMPLE_RATE = 16000
MIC_DURATION = 5
