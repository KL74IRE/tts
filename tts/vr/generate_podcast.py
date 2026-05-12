"""
CS423 Podcast Generator
=======================
Converts the CS423_Podcast_Script.docx into MP3 audio files — one per episode.

Requirements:
    pip install edge-tts python-docx

Usage:
    1. Place this script in the same folder as CS423_Podcast_Script.docx
    2. Run:  py generate_podcast.py
    3. Five MP3 files will be created in an 'audio' subfolder.

Free — no API key required. Uses Microsoft Edge's neural TTS engine.
Requires internet connection.
"""

import edge_tts
import asyncio
from docx import Document
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
DOCX_FILE  = "CS423_Podcast_Script.docx"   # must be in the same folder
OUTPUT_DIR = "audio"                        # folder where MP3s are saved
VOICE      = "en-IE-EmilyNeural"           # Irish Female — change as needed

# Episode output filenames
EPISODE_TITLES = [
    "CS423_Episode1_VR_Definitions_History_Technology",
    "CS423_Episode2_Immersion_and_Presence",
    "CS423_Episode3_Wingrave_LaViola_Design_Issues",
    "CS423_Episode4_3D_Interaction_Selection_Navigation",
    "CS423_Episode5_Content_Creation_Level_Design_Exam_Strategy",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_text(text):
    """Clean up text so it reads naturally through TTS."""
    # Remove pause markers
    text = re.sub(r'\[\s*PAUSE\s*\]', '...', text)

    # Common abbreviations spoken naturally
    replacements = [
        ("VR",   "V R"),
        ("AR",   "A R"),
        ("MR",   "M R"),
        ("HMD",  "H M D"),
        ("DoF",  "degrees of freedom"),
        ("FoV",  "field of view"),
        ("WiM",  "world in miniature"),
        ("TTS",  "T T S"),
        ("HCI",  "H C I"),
        ("VE",   "V E"),
        ("VEs",  "V Es"),
        ("VEDI", "V E D I"),
        ("3D",   "3 D"),
        ("6DoF", "6 degrees of freedom"),
        ("3DoF", "3 degrees of freedom"),
        ("fps",  "frames per second"),
        ("SDK",  "S D K"),
        ("GPU",  "G P U"),
        ("FIVE", "five"),
        ("UE5",  "Unreal Engine 5"),
        ("WIM",  "world in miniature"),
        ("UI",   "U I"),
        ("UX",   "U X"),
        ("AI",   "A I"),
        ("API",  "A P I"),
        ("Q1",   "question 1"),
        ("Q2",   "question 2"),
        ("Q3",   "question 3"),
        ("Q4",   "question 4"),
        ("Q5",   "question 5"),
    ]
    for old, new in replacements:
        # Replace whole words only to avoid partial matches
        text = re.sub(r'\b' + re.escape(old) + r'\b', new, text)

    # Clean up multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def extract_episodes(docx_path):
    """
    Extract text from the Word doc and split into episodes.
    Episodes are separated by Heading 1 paragraphs starting with 'EPISODE'.
    Returns a list of (title, text) tuples.
    """
    doc = Document(docx_path)
    episodes = []
    current_lines = []
    current_title = "Intro"

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        is_heading = (para.style and
                      para.style.name and
                      "Heading 1" in para.style.name and
                      text.upper().startswith("EPISODE"))

        if is_heading:
            if current_lines:
                episodes.append((current_title, "\n".join(current_lines)))
            current_title = text
            current_lines = [text]
        else:
            current_lines.append(text)

    if current_lines:
        episodes.append((current_title, "\n".join(current_lines)))

    return episodes


async def _text_to_mp3_async(text, output_path):
    """Convert text to MP3 using edge-tts."""
    cleaned = clean_text(text)
    communicate = edge_tts.Communicate(text=cleaned, voice=VOICE)
    await communicate.save(output_path)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  Saved: {output_path}  ({size_kb} KB)")


def text_to_mp3(text, output_path, **kwargs):
    asyncio.run(_text_to_mp3_async(text, output_path))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DOCX_FILE):
        print(f"\nERROR: Could not find '{DOCX_FILE}'")
        print("Make sure this script is in the same folder as CS423_Podcast_Script.docx\n")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\nCS423 Podcast Generator")
    print(f"========================")
    print(f"Reading: {DOCX_FILE}")
    print(f"Voice:   {VOICE}")

    episodes = extract_episodes(DOCX_FILE)
    episode_blocks = [e for e in episodes if e[0].upper().startswith("EPISODE")]

    if not episode_blocks:
        print("ERROR: No EPISODE headings found in the document.")
        print("Check that the Word document uses 'Heading 1' style for episode titles.")
        return

    print(f"Found {len(episode_blocks)} episodes\n")

    for i, (title, text) in enumerate(episode_blocks):
        filename = EPISODE_TITLES[i] if i < len(EPISODE_TITLES) else f"CS423_Episode_{i+1}"
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")

        print(f"[{i+1}/{len(episode_blocks)}] Generating: {title[:60]}...")
        print(f"  Text length: {len(text):,} characters")

        try:
            text_to_mp3(text, output_path)
        except Exception as e:
            print(f"  ERROR generating episode {i+1}: {e}")
            print("  Check your internet connection — edge-tts requires internet access.")

    print(f"\nAll done! MP3 files saved to: ./{OUTPUT_DIR}/\n")
    print("Files generated:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.mp3'):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
            print(f"  {f}  ({size} KB)")
    print()


if __name__ == "__main__":
    main()