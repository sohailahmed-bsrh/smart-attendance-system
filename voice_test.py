import pyttsx3

engine = pyttsx3.init()

engine.setProperty("rate", 170)
engine.setProperty("volume", 1)

voices = engine.getProperty("voices")

print(voices)

engine.say("Hello Sohail. Voice is working.")
engine.runAndWait()

print("Done")