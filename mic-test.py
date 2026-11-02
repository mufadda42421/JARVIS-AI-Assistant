
import sounddevice as sd

print("Available audio devices:\n")
print(sd.query_devices())

print("\nJARVIS: Listening for 5 seconds, Sir.")

audio = sd.rec(
    int(5 * 16000),
    samplerate=16000,
    channels=1
)

sd.wait()

print("JARVIS: Audio recording completed, Sir!")
