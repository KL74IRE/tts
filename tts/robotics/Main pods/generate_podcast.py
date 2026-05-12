"""
CS427 Podcast Generator
=======================
Converts the CS427 podcast script into MP3 audio files — one per episode.

Requirements:
    pip install edge-tts python-docx

Usage:
    1. Place this script in the same folder as CS427_Podcast_Script.docx
    2. Run:  py generate_podcast.py
    3. Five MP3 files will be created in an 'audio' subfolder.

Free — no API key required. Uses Microsoft Edge's neural TTS engine.
"""

import edge_tts
import asyncio
from docx import Document
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
DOCX_FILE  = "CS427_Podcast_Script.docx"   # must be in the same folder
OUTPUT_DIR = "audio"                        # folder where MP3s are saved
VOICE      = "en-IE-EmilyNeural"           # Irish Female — change as needed

# Episode titles — used for output filenames
EPISODE_TITLES = [
    "CS427_Episode1_Kinematics",
    "CS427_Episode2_Localisation",
    "CS427_Episode3_Sensing",
    "CS427_Episode4_Vision",
    "CS427_Episode5_ROS2_and_Exam_Strategy",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_text(text):
    """Clean up text so it reads naturally through TTS."""
    # Remove note markers
    text = text.replace("📌 NOTE: ", "Note. ")

    # Remove pause markers — TTS handles natural pauses via punctuation
    text = re.sub(r'\[\s*PAUSE\s*\]', '...', text)

    # Speak common notation naturally
    replacements = [
        ("x_dot",       "x dot"),
        ("y_dot",       "y dot"),
        ("theta_dot",   "theta dot"),
        ("phi_dot",     "phi dot"),
        ("bel_bar",     "bel bar"),
        ("x_{t-1}",     "x t minus 1"),
        ("x_t",         "x t"),
        ("z_t",         "z t"),
        ("u_t",         "u t"),
        ("delta_m",     "delta m"),
        ("delta_s",     "delta s"),
        ("delta_M",     "delta M"),
        ("alpha",       "alpha"),
        ("beta",        "beta"),
        ("gamma",       "gamma"),
        ("theta",       "theta"),
        ("phi",         "phi"),
        ("r_sw",        "r sub sw"),
        ("t_i",         "t i"),
        ("n_id",        "n i d"),
        ("n_d",         "n d"),
        ("n_i",         "n i"),
        ("p_r",         "p r"),
        ("p_l",         "p l"),
        ("C1",          "C 1"),
        ("J1",          "J 1"),
        ("J2",          "J 2"),
        ("Pi_0",        "Pi zero"),
        ("T_wc",        "T w c"),
        ("u_l",         "u l"),
        ("u_r",         "u r"),
        ("fx",          "f x"),
        ("fy",          "f y"),
        ("u0",          "u zero"),
        ("v0",          "v zero"),
        ("SUM_ij",      "sum over i j"),
        ("SUM SUM",     "sum sum"),
        ("^2",          " squared"),
        ("^T",          " transpose"),
        ("*",           " times "),
        ("==>",         "implies"),
        ("->",          "gives"),
        ("!=",          "not equal to"),
        (">=",          "greater than or equal to"),
        ("<=",          "less than or equal to"),
        ("/",           " over "),
        ("~=",          "approximately equals"),
        ("sqrt(",       "square root of "),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    # Clean up multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def extract_episodes(docx_path):
    """
    Extract text from the Word doc and split into episodes.
    Episodes are separated by HEADING_1 paragraphs starting with 'EPISODE'.
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

        # Detect episode heading
        if para.style and para.style.name == "Heading 1" and text.upper().startswith("EPISODE"):
            if current_lines:
                episodes.append((current_title, "\n".join(current_lines)))
            current_title = text
            current_lines = [text]
        else:
            current_lines.append(text)

    # Don't forget the last episode
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
        print(f"ERROR: Could not find '{DOCX_FILE}'")
        print("Make sure the script is in the same folder as the Word document.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Reading: {DOCX_FILE}")
    print(f"Voice:   {VOICE}\n")
    episodes = extract_episodes(DOCX_FILE)

    # Skip the intro block (cover page text before Episode 1)
    episode_blocks = [e for e in episodes if e[0].upper().startswith("EPISODE")]

    print(f"Found {len(episode_blocks)} episodes\n")

    for i, (title, text) in enumerate(episode_blocks):
        filename = EPISODE_TITLES[i] if i < len(EPISODE_TITLES) else f"Episode_{i+1}"
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")

        print(f"Generating Episode {i+1}: {title}")
        print(f"  Text length: {len(text):,} characters")

        try:
            text_to_mp3(text, output_path)
        except Exception as e:
            print(f"  ERROR: {e}")
            print("  Check your internet connection — edge-tts requires internet access.")

    print(f"\nDone. MP3 files saved to: ./{OUTPUT_DIR}/")
    print("\nFiles generated:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.mp3'):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
            print(f"  {f}  ({size} KB)")


if __name__ == "__main__":
    main()