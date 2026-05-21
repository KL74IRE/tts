"""
CS426 Podcast Generator
=======================
Converts the CS426 podcast script into MP3 audio files — one per episode.

Requirements:
    pip install edge-tts python-docx

Usage:
    1. Place this script in the same folder as CS426_Podcast_Script.docx
    2. Run:  python generate_cs426_podcast.py
    3. Five MP3 files will be created in an 'audio' subfolder.

Free — no API key required. Uses Microsoft Edge's neural TTS engine.
Requires an internet connection.
"""

import edge_tts
import asyncio
from docx import Document
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
DOCX_FILE  = "CS426_Podcast_Script.docx"   # must be in the same folder
OUTPUT_DIR = "audio"                        # folder where MP3s are saved

# Voice options — uncomment your preference:
VOICE = "en-IE-EmilyNeural"      # Irish female — most natural for Maynooth content
# VOICE = "en-IE-ConnorNeural"   # Irish male
# VOICE = "en-GB-SoniaNeural"    # British female
# VOICE = "en-US-AriaNeural"     # American female

# Episode output filenames
EPISODE_TITLES = [
    "CS426_Ep1_Rendering_Foundations",
    "CS426_Ep2_Geometry_and_Projection",
    "CS426_Ep3_Illumination_and_Colour",
    "CS426_Ep4_Rotation_and_Orientation",
    "CS426_Ep5_Simulation_ODEs_Fractals",
    "CS426_Ep6_Displays_and_Hardware",
    "CS426_Ep7_Code_Analysis",
]

# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean up the script text so it reads naturally through TTS.
    Handles mathematical notation, markers, and special formatting.
    """
    # Remove NOTE: prefix (notes are already phrased for speech)
    text = text.replace("NOTE: ", "Note. ")

    # Convert pause markers to natural pauses via ellipsis
    text = re.sub(r'\[\s*PAUSE\s*\]', '...', text, flags=re.IGNORECASE)

    # Mathematical notation → spoken form
    replacements = [
        # Greek letters
        ("theta",    "theta"),
        ("alpha",    "alpha"),
        ("beta",     "beta"),
        ("gamma",    "gamma"),
        ("lambda",   "lambda"),
        ("phi",      "phi"),
        ("delta",    "delta"),
        ("omega",    "omega"),

        # Subscripts and notation
        ("x_dot",    "x dot"),
        ("y_dot",    "y dot"),
        ("theta_dot","theta dot"),
        ("v_new",    "v new"),
        ("x_new",    "x new"),
        ("t_new",    "t new"),
        ("v_old",    "v old"),
        ("x_old",    "x old"),
        ("t_old",    "t old"),
        ("v_x",      "v x"),
        ("v_y",      "v y"),
        ("k_a",      "k a"),
        ("k_d",      "k d"),
        ("k_s",      "k s"),
        ("I_A",      "I A"),
        ("I_I",      "I I"),
        ("n_i",      "n i"),
        ("n_r",      "n r"),

        # Common maths symbols in text
        ("^2",       " squared"),
        ("^T",       " transpose"),
        ("^n",       " to the power n"),
        ("sqrt(",    "square root of "),
        ("×",        " times "),
        ("÷",        " divided by "),
        ("≈",        " approximately "),
        ("≠",        " not equal to "),
        ("≥",        " greater than or equal to "),
        ("≤",        " less than or equal to "),
        ("→",        " gives "),
        ("−",        " minus "),          # en-dash used in maths
        ("±",        " plus or minus "),

        # Matrix notation
        ("4×4",      "4 by 4"),
        ("3×3",      "3 by 3"),
        ("2×2",      "2 by 2"),
        ("3×1",      "3 by 1"),

        # OpenGL / code identifiers
        ("glutSwapBuffers",        "glut Swap Buffers"),
        ("glutMainLoop",           "glut Main Loop"),
        ("glutDisplayFunc",        "glut Display Func"),
        ("glutIdleFunc",           "glut Idle Func"),
        ("glutKeyboardFunc",       "glut Keyboard Func"),
        ("glutTimerFunc",          "glut Timer Func"),
        ("glutMouseFunc",          "glut Mouse Func"),
        ("glutReshapeFunc",        "glut Reshape Func"),
        ("glutPostRedisplay",      "glut Post Redisplay"),
        ("glutInitDisplayMode",    "glut Init Display Mode"),
        ("GLUT_DOUBLE",            "G-L-U-T double"),
        ("GLUT_SINGLE",            "G-L-U-T single"),
        ("GLUT_RGB",               "G-L-U-T R-G-B"),
        ("glEnable(GL_DEPTH_TEST)","g-l enable depth test"),
        ("glEnable(GL_CULL_FACE)", "g-l enable cull face"),
        ("glFrontFace(GL_CCW)",    "g-l front face C-C-W"),
        ("GL_DEPTH_BUFFER_BIT",    "depth buffer bit"),
        ("gl_Position",            "g-l position"),
        ("gluLookAt",              "g-l-u look at"),
        ("gluPerspective",         "g-l-u perspective"),
        ("gluOrtho",               "g-l-u ortho"),
        ("glm::",                  "G-L-M"),
        ("vec4",                   "vec 4"),
        ("vec3",                   "vec 3"),
        ("vec2",                   "vec 2"),
        ("mat4",                   "mat 4"),
        ("MVP",                    "M-V-P"),

        # File extensions
        (".docx",    " dot d-o-c-x"),
        (".mtl",     " dot m-t-l"),
        (".obj",     " dot o-b-j"),
        (".bmp",     " dot b-m-p"),
        (".mp3",     " dot m-p-3"),

        # Acronyms — add spaces so TTS spells them out
        ("NDC",   "N-D-C"),
        ("ITO",   "I-T-O"),
        ("TN",    "T-N"),
        ("AMOLED","A-M-O-L-E-D"),
        ("SLERP", "S-L-E-R-P"),
        ("IPS",   "I-P-S"),
        ("RTX",   "R-T-X"),
        ("CIE",   "C-I-E"),
        ("CMY",   "C-M-Y"),
        ("RGB",   "R-G-B"),
        ("CMYK",  "C-M-Y-K"),
        ("GLSL",  "G-L-S-L"),
        ("OBJ",   "O-B-J"),
        ("MTL",   "M-T-L"),
        ("XNA",   "X-N-A"),
        ("GPU",   "G-P-U"),
        ("CPU",   "C-P-U"),
        ("BVH",   "B-V-H"),
        ("SIMD",  "S-I-M-D"),
        ("FPS",   "F-P-S"),
        ("RMS",   "R-M-S"),
        ("AC",    "A-C"),
        ("DC",    "D-C"),
        ("IMU",   "I-M-U"),
        ("FOV",   "F-O-V"),

        # Clean up leftover artefacts
        ("  ",  " "),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    # Remove markdown-style formatting that might have crept in
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # bold
    text = re.sub(r'\*(.+?)\*',     r'\1', text)   # italic
    text = re.sub(r'`(.+?)`',       r'\1', text)   # code

    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


# ── Document parsing ──────────────────────────────────────────────────────────

def extract_episodes(docx_path: str):
    """
    Parse the Word document and split it into episodes.
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

        is_h1 = (para.style and
                 para.style.name == "Heading 1" and
                 text.upper().startswith("EPISODE"))

        if is_h1:
            if current_lines:
                episodes.append((current_title, "\n".join(current_lines)))
            current_title = text
            current_lines = [text]
        else:
            current_lines.append(text)

    if current_lines:
        episodes.append((current_title, "\n".join(current_lines)))

    return episodes


# ── TTS conversion ────────────────────────────────────────────────────────────

async def _tts_async(text: str, output_path: str):
    """Convert text to MP3 using edge-tts (async)."""
    cleaned = clean_text(text)
    communicate = edge_tts.Communicate(text=cleaned, voice=VOICE)
    await communicate.save(output_path)


def tts(text: str, output_path: str):
    """Synchronous wrapper for the async TTS call."""
    asyncio.run(_tts_async(text, output_path))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DOCX_FILE):
        print(f"ERROR: Could not find '{DOCX_FILE}'")
        print("Make sure this script is in the same folder as CS426_Podcast_Script.docx")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Reading: {DOCX_FILE}")
    print(f"Voice:   {VOICE}")
    print(f"Output:  ./{OUTPUT_DIR}/\n")

    episodes = extract_episodes(DOCX_FILE)

    # Skip the intro block (cover text before Episode 1)
    episode_blocks = [e for e in episodes if e[0].upper().startswith("EPISODE")]

    if not episode_blocks:
        print("ERROR: No EPISODE headings found in the document.")
        print("Make sure the episode headings use Heading 1 style and start with 'EPISODE'.")
        return

    print(f"Found {len(episode_blocks)} episodes\n")

    total_chars = sum(len(t) for _, t in episode_blocks)
    print(f"Total script length: {total_chars:,} characters")
    estimated_minutes = total_chars / 900   # rough estimate: ~900 chars/min for spoken word
    print(f"Estimated audio duration: ~{estimated_minutes:.0f} minutes\n")

    for i, (title, text) in enumerate(episode_blocks):
        filename = EPISODE_TITLES[i] if i < len(EPISODE_TITLES) else f"CS426_Episode_{i+1}"
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")

        print(f"[{i+1}/{len(episode_blocks)}] Generating: {title}")
        print(f"     Text: {len(text):,} characters")

        try:
            tts(text, output_path)
            size_kb = os.path.getsize(output_path) // 1024
            print(f"     Saved: {output_path}  ({size_kb} KB)\n")
        except Exception as e:
            print(f"     ERROR: {e}")
            print("     Check your internet connection — edge-tts requires internet access.\n")
            continue

    print("=" * 60)
    print("Done! MP3 files saved:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".mp3"):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
            print(f"  {f}  ({size} KB)")

    print(f"\nTip: listen at 1.25x or 1.5x speed to cover all 5 episodes in one study session.")
    print("Return to the printed guide for diagrams and matrices.")


if __name__ == "__main__":
    main()
