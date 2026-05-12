import asyncio
import edge_tts
import os

VOICES = [
    ("en-GB-SoniaNeural",   "British Female - Sonia"),
    ("en-GB-RyanNeural",    "British Male - Ryan"),
    ("en-GB-LibbyNeural",   "British Female - Libby"),
    ("en-US-AriaNeural",    "American Female - Aria"),
    ("en-US-GuyNeural",     "American Male - Guy"),
    ("en-US-JennyNeural",   "American Female - Jenny"),
    ("en-AU-NatashaNeural", "Australian Female - Natasha"),
    ("en-AU-WilliamNeural", "Australian Male - William"),
    ("en-IE-EmilyNeural",   "Irish Female - Emily"),
    ("en-IE-ConnorNeural",  "Irish Male - Connor"),
]

TEST_TEXT = (
    "Welcome to CS427. In this episode we'll be covering robot kinematics, "
    "localisation, and how to apply Bayes filters to estimate robot state."
)

async def generate(voice_name, label, output_dir):
    path = os.path.join(output_dir, f"{voice_name}.mp3")
    print(f"  Generating: {label} ({voice_name})")
    communicate = edge_tts.Communicate(text=TEST_TEXT, voice=voice_name)
    await communicate.save(path)
    print(f"  Saved: {path}")

async def main():
    output_dir = "voice_samples"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating {len(VOICES)} voice samples...\n")
    for voice_name, label in VOICES:
        await generate(voice_name, label, output_dir)
    print(f"\nDone! Check the '{output_dir}' folder.")

asyncio.run(main())