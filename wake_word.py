
import os
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "vosk-model-small-en-us-0.15"
)

SAMPLE_RATE = 16000

model = Model(MODEL_PATH)


def wait_for_wake_word():

    print("J.A.R.V.I.S is listening... Say Jarvis!")

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1
    ) as stream:

        while True:
            data, overflowed = stream.read(4000)

            if recognizer.AcceptWaveform(bytes(data)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()

                print("Heard:", text)

                if "jarvis" in text:
                    print("Wake word detected!")
                    return True
