
import sounddevice as sd
import speech_recognition as sr
import pyttsx3
import numpy as np
import time

from config import VOICE_RATE, VOICE_VOLUME, MIC_SAMPLE_RATE

# ==========================================
#       J.A.R.V.I.S. VOICE ENGINE
# ==========================================

engine = pyttsx3.init()
engine.setProperty("rate", VOICE_RATE)
engine.setProperty("volume", VOICE_VOLUME)

recognizer = sr.Recognizer()

recognizer.pause_threshold = 0.9
recognizer.non_speaking_duration = 0.5
recognizer.dynamic_energy_threshold = True


def speak(text):
    print(f"J.A.R.V.I.S.: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():

    try:
        speak("I'm listening, Sir.")

        sample_rate = MIC_SAMPLE_RATE
        chunk_duration = 0.1
        chunk_size = int(sample_rate * chunk_duration)

        audio_chunks = []

        # Ambient noise calibration
        print("Calibrating microphone...")

        calibration = sd.rec(
            int(sample_rate * 0.7),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        noise_level = np.sqrt(
            np.mean(calibration.astype(np.float32) ** 2)
        )

        threshold = max(300, noise_level * 2.5)

        print("Listening...")

        started = False
        silence_time = 0
        start_time = time.time()

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        ) as stream:

            while True:

                audio, overflowed = stream.read(chunk_size)

                audio = audio.flatten()

                volume = np.sqrt(
                    np.mean(audio.astype(np.float32) ** 2)
                )

                if volume > threshold:
                    started = True
                    silence_time = 0

                elif started:
                    silence_time += chunk_duration

                if started:
                    audio_chunks.append(audio.copy())

                if started and silence_time >= 1.2:
                    break

                if not started and time.time() - start_time > 8:
                    print("No speech detected.")
                    return ""

                if started and time.time() - start_time > 20:
                    break

        if not audio_chunks:
            return ""

        audio_data = np.concatenate(audio_chunks)

        audio = sr.AudioData(
            audio_data.tobytes(),
            sample_rate,
            2
        )

        print("Recognizing speech...")

        command = recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        print(f"You: {command}")

        return command.lower().strip()

    except sr.UnknownValueError:
        speak("I couldn't understand that, Sir.")
        return ""

    except sr.RequestError as error:
        print("Recognition error:", error)
        speak("Speech recognition service is unavailable.")
        return ""

    except Exception as error:
        print("Microphone error:", error)
        return ""
