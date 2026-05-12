"""
CS423 Episode 6 — Q&A Revision Podcast Generator
==================================================
Generates a single MP3 — a spoken Q&A revision session covering all
key concepts from Episodes 1 to 5.

Format:
    - Full spoken intro explaining what the podcast is
    - Question read aloud
    - 3-second silence (thinking gap)
    - Correct answer read twice
    - Short explanation of why it is correct
    - 1-second silence
    - Next question

Requirements:
    pip install edge-tts

Usage:
    python generate_podcast_ep6.py

Output:
    audio/CS423_Episode6_QnA_Revision.mp3

Notes:
    - Requires internet connection — edge-tts connects to Microsoft Speech servers
    - Uses Emily (en-IE-EmilyNeural) — Irish female neural voice
    - Run from any folder — the audio subfolder is created automatically
    - If you see an SSL error, run:
        pip install --upgrade certifi
      or on Windows open Python and run:
        import certifi; print(certifi.where())
      and ensure your system certificates are up to date
"""

import edge_tts
import asyncio
import os
import re
import struct
import wave
import io

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = "audio"
OUTPUT_FILE  = "CS423_Episode6_QnA_Revision.mp3"
VOICE        = "en-IE-EmilyNeural"

# ── Silence generator (raw PCM → WAV → writable bytes) ───────────────────────

def make_silence_mp3_bytes(seconds):
    """
    edge-tts produces MP3. We can't easily inject raw silence into MP3 mid-stream,
    so we generate a short silent WAV-like MP3 via a TTS whisper of blank space,
    OR we use a pre-built silent MP3 frame approach.
    Simplest reliable approach: generate silence as a spoken pause via SSML.
    We handle silence by splitting the script into segments and inserting
    silent audio files between them.
    """
    pass  # handled via SSML break tags in text below


# ── Content ───────────────────────────────────────────────────────────────────

INTRO = """
Welcome to the CS423 Designing for Virtual Environments Q and A Revision Podcast. 
This is Episode 6 — your exam preparation session.

This podcast covers all the key concepts from Episodes 1 through 5. 
It includes Virtual Reality definitions, the difference between AR, MR and VR, 
core technology, Slater's framework for Immersion and Presence, 
the Wingrave and LaViola paper on design issues in virtual environments, 
3D interaction techniques including selection and navigation, 
and content creation including low poly design and level design.

Here is how this session works. I will read a question. 
You will have 3 seconds to think of your answer. 
Then I will read the correct answer twice, followed by a short explanation of why it is correct. 
There will be a brief pause, then we move to the next question.

Try to answer out loud as if you are in the exam. 
This will help you recall the material under pressure.

There are 40 questions in total. 
If you can answer these confidently, you are well on your way to a first class result.

Let us begin.
"""

QNA = [
    # ── EPISODE 1: VR, AR, MR, Core Technology ──
    {
        "q": "Question 1. How does Merriam-Webster define Virtual Reality?",
        "a": "An artificial environment experienced through sensory stimuli provided by a computer, in which the user's actions partially determine what happens.",
        "why": "This is the exact definition used in the Week 2 lecture. The key phrase is that the user's actions partially determine what happens — this distinguishes VR from passive media like film."
    },
    {
        "q": "Question 2. Who coined the term Virtual Reality, and approximately when?",
        "a": "Jaron Lanier coined the term Virtual Reality around 1990.",
        "why": "Lanier founded VPL Research and is credited with popularising the term. He described VR as the inverse of Artificial Intelligence and as hope for a medium that could convey dreaming."
    },
    {
        "q": "Question 3. What are the three core technological ingredients of VR that create the VR Effect?",
        "a": "Stereoscopic view, head tracking, and positional room tracking.",
        "why": "These three ingredients are covered in Week 2 as the foundation of immersive VR. Stereoscopic view creates depth, head tracking updates the view on rotation, and positional tracking adds movement through space."
    },
    {
        "q": "Question 4. What is the difference between 3 degrees of freedom and 6 degrees of freedom tracking?",
        "a": "3 degrees of freedom tracks rotation only — pitch, yaw, and roll. 6 degrees of freedom adds positional tracking — movement along the X, Y, and Z axes.",
        "why": "3 DoF is what a basic smartphone gyroscope provides. 6 DoF is what makes you feel like you are physically inside a space rather than just looking into one."
    },
    {
        "q": "Question 5. What is the difference between inside-out and outside-in tracking?",
        "a": "Outside-in tracking uses external base stations to track the headset, like the HTC Vive Lighthouse system. Inside-out tracking uses cameras mounted on the headset itself to map the environment, like the Meta Quest.",
        "why": "This distinction is important for understanding VR hardware. Inside-out requires no room setup and is portable. Outside-in is typically more precise but requires fixed base stations."
    },
    {
        "q": "Question 6. Where does Mixed Reality sit on the Reality-Virtuality Continuum?",
        "a": "Mixed Reality sits between Augmented Reality and full Virtual Reality on the Reality-Virtuality Continuum.",
        "why": "The continuum runs from the real environment at one end to a fully virtual environment at the other. MR is where virtual content interacts with and is anchored to the real world, making it closer to reality than full VR."
    },
    {
        "q": "Question 7. Name one benefit and one shortcoming of VR compared to Mixed Reality.",
        "a": "Benefit: total immersion and full control of the environment. Shortcoming: complete disconnection from the real world, which can cause cybersickness and raises safety concerns.",
        "why": "MR keeps the real world visible, which is safer and more practical for working environments. VR's disconnection is both its strength for immersion and its weakness for safety."
    },
    {
        "q": "Question 8. What did Ivan Sutherland describe in his 1965 paper The Ultimate Display?",
        "a": "A room in which the computer can control the existence of matter — where a chair would be good enough to sit in and a bullet would be deadly.",
        "why": "Sutherland's Ultimate Display is the theoretical endpoint of VR technology. It is still cited as the North Star of VR research and was referenced in the Week 2 lecture."
    },

    # ── EPISODE 2: Immersion and Presence ──
    {
        "q": "Question 9. In one sentence, what is the key difference between immersion and presence?",
        "a": "Immersion is objective and describes what the technology can deliver. Presence is subjective and describes what the user feels.",
        "why": "This distinction is the foundation of Slater's framework from the FIVE paper published in 1997. Immersion is technical, presence is psychological. They are related but not the same."
    },
    {
        "q": "Question 10. Who wrote the FIVE paper on immersion and presence, and when was it published?",
        "a": "Mel Slater and Sylvia Wilbur. It was published in 1997 in the journal Presence: Teleoperators and Virtual Environments.",
        "why": "The full title is A Framework for Immersive Virtual Environments — speculations on the role of presence in virtual environments. You should cite it as Slater and Wilbur, 1997 in your exam answers."
    },
    {
        "q": "Question 11. Name all six dimensions of immersion from Slater and Wilbur's FIVE framework.",
        "a": "Extensive, Matching, Surrounding, Vivid, Interactable, and Plot.",
        "why": "These six dimensions describe how a system creates stimuli for the user. Extensive is range of senses, Matching is congruence between senses, Surrounding is panoramic coverage, Vivid is simulation quality, Interactable is ability to change the world, and Plot is the narrative."
    },
    {
        "q": "Question 12. What does the Surrounding dimension of immersion refer to?",
        "a": "The extent to which sensory cues are panoramic — including the width of the field of view, whether tracking is 360 degrees, and whether audio is spatial.",
        "why": "A system with a narrow field of view or limited tracking angles scores low on surroundness. A CAVE system with screens on all walls scores very high."
    },
    {
        "q": "Question 13. What is the ISPR definition of presence, and what year was it published?",
        "a": "Presence is a psychological state or subjective perception in which even though an individual's experience is generated by technology, their perception fails to accurately acknowledge the role of the technology. Published in 2000 by the International Society for Presence Research.",
        "why": "This definition is shown directly in the Week 11 lecture slides. It traces back to Minsky's concept of Telepresence from 1980. You should reference it as ISPR, 2000."
    },
    {
        "q": "Question 14. What is the formula linking immersion and presence from the lecture?",
        "a": "Immersion multiplied by the User equals Presence.",
        "why": "This formula from the Week 11 lecture captures that presence is not guaranteed by immersion alone. The user's psychology, susceptibility, and engagement all determine how much presence is generated from a given level of immersion."
    },
    {
        "q": "Question 15. Who introduced the concept of Telepresence, and when?",
        "a": "Marvin Minsky introduced Telepresence in 1980 in Omni Magazine.",
        "why": "Minsky proposed remote-controlled mechanical hands for working in hazardous environments. The sense of being there he identified is exactly what modern VR research still pursues. The word presence in VR derives directly from his term."
    },
    {
        "q": "Question 16. Name the three types of presence identified by Heeter in 1992.",
        "a": "Personal Presence, Social Presence, and Environmental Presence.",
        "why": "Heeter's 1992 paper Being There defined these three types. Personal is how much you feel part of the VE, Social is how much others feel present, and Environmental is how much the environment reacts to you."
    },
    {
        "q": "Question 17. What VR experience is used in the Week 11 lecture to demonstrate high presence?",
        "a": "Richie's Plank Experience — a VR experience where users walk a narrow plank at great height.",
        "why": "The lecture uses it to illustrate that people afraid of heights in real life show genuine fear responses in VR. This is a direct demonstration of presence — the body responds as if the virtual environment is real."
    },
    {
        "q": "Question 18. Name the four components of presence as illusion described by Jarald in The VR Book, 2015.",
        "a": "Place Illusion, Body Ownership Illusion, Physical Interaction, and Social Communication.",
        "why": "These four components describe how presence manifests experientially. Place Illusion is feeling you are somewhere. Body Ownership is the virtual body feeling like yours. Physical Interaction is tactile feedback. Social Communication is responsive characters."
    },
    {
        "q": "Question 19. Who created the Presence Questionnaire and what are its four categories?",
        "a": "Witmer and Singer created it in 1998. The four categories are Control, Sensory, Realism, and Distraction.",
        "why": "The questionnaire has 32 items rated on a Likert scale from 1 to 7. It is the most cited tool for measuring presence and is referenced in the Week 11 lecture slides."
    },

    # ── EPISODE 3: Wingrave and LaViola ──
    {
        "q": "Question 20. What is the full title of the Wingrave and LaViola paper, and when was it published?",
        "a": "Reflecting on the Design and Implementation Issues of Virtual Environments. Published in 2010.",
        "why": "This paper appears in Question 2 of both exam papers you have seen. Always cite it as Wingrave and LaViola, 2010. The paper took a candid look at why building VR systems remains so difficult despite advances in hardware."
    },
    {
        "q": "Question 21. How many issues did Wingrave and LaViola identify, and how were they organised?",
        "a": "67 issues, clustered into 11 themes, with 5 research challenges proposed.",
        "why": "The number 67 is specific and frequently tested. Knowing the structure — 67 issues, 11 themes, 5 challenges — shows you have read the paper rather than just heard about it."
    },
    {
        "q": "Question 22. Name any five of the eleven themes from the Wingrave and LaViola paper.",
        "a": "Multiple Varied Skills, Human Experience and Perception, Content, Design Knowledge, Iterative Prototyping, Models and Reuse, Complex and Chaotic, Real-Time Operation, Callbacks and Events, Hardware, and Tools and Community.",
        "why": "The exam typically asks you to name and briefly describe themes. Multiple Varied Skills, Real-Time Operation, Hardware, and Content are the most commonly cited in exam answers."
    },
    {
        "q": "Question 23. Name two issues from Wingrave and LaViola that are still relevant today.",
        "a": "The lack of a standard hardware platform — Quest, Vive, and Pico all have different SDKs. And human factors such as cybersickness and individual differences in spatial ability remain hard to predict.",
        "why": "The exam asks for issues still relevant versus resolved. These two remain genuinely unsolved. Hardware fragmentation has arguably got worse since the paper was written, not better."
    },
    {
        "q": "Question 24. Name two issues from Wingrave and LaViola that have largely been resolved.",
        "a": "Cable encumbrance has been solved by wireless headsets like the Meta Quest. Basic locomotion and teleportation are now built into standard engine templates so they no longer need to be built from scratch.",
        "why": "Showing you can distinguish resolved from still-relevant issues demonstrates critical engagement with the paper rather than just memorisation."
    },
    {
        "q": "Question 25. What does the Real-Time Operation theme in Wingrave and LaViola refer to?",
        "a": "VR requires extremely fast frame rates — typically 90 frames per second or higher — to avoid nausea and maintain presence. This conflicts with the computational demands of realistic environments.",
        "why": "This is one of the most technically important themes. Below around 72 frames per second, users experience motion sickness. Higher fidelity graphics demand more computation, creating a fundamental tension."
    },
    {
        "q": "Question 26. What does the Callbacks and Events theme in Wingrave and LaViola refer to?",
        "a": "The dominant event-based callback architecture used in VR systems is poorly suited for actions that unfold over time, leading to code that is hard to maintain and extend.",
        "why": "This is a software engineering issue specific to VR. Discrete events work well for button presses but not for continuous interactions like holding and moving an object."
    },

    # ── EPISODE 4: 3D Interaction ──
    {
        "q": "Question 27. What is the equation for navigation in VR?",
        "a": "Navigation equals Wayfinding plus Travel.",
        "why": "This equation is fundamental and directly testable. Wayfinding is the cognitive component — knowing where you are and where you want to go. Travel is the motor component — physically moving through the environment."
    },
    {
        "q": "Question 28. What are the two components of navigation and what does each mean?",
        "a": "Wayfinding is the cognitive component — building a mental map, knowing where you are and where you can go. Travel is the motor component — physically moving from one place to another in the virtual environment.",
        "why": "Travel without wayfinding is just wandering. Wayfinding without travel is just knowing. Navigation requires both together."
    },
    {
        "q": "Question 29. Name three travel metaphors used in VR.",
        "a": "Real walking, teleportation, and redirected walking.",
        "why": "Real walking is most natural but limited by physical space. Teleportation avoids motion sickness but breaks spatial continuity. Redirected walking creates the illusion of unlimited space by subtly warping the view as the user walks in a circle."
    },
    {
        "q": "Question 30. What is redirected walking and what is its main advantage?",
        "a": "Redirected walking is a technique where the system subtly warps the virtual view so the user feels they are walking straight while actually walking in a physical circle, extending a small physical space into a large virtual one.",
        "why": "Its main advantage is that it allows exploration of large virtual environments within a small physical space without teleportation, preserving spatial continuity and the sense of physical presence."
    },
    {
        "q": "Question 31. Name three selection metaphors used in VR.",
        "a": "Ray-casting, the Go-Go technique, and World in Miniature.",
        "why": "Ray-casting uses a virtual ray from the hand. The Go-Go technique extends the virtual arm beyond physical reach for distant objects. World in Miniature places a miniature copy of the scene in your hand for selection."
    },
    {
        "q": "Question 32. What is the HOMER technique?",
        "a": "Hand-Centred Object Manipulation Extending Ray-casting. It combines ray-casting for selection with direct hand manipulation for control — the object attaches to the hand as if being held once selected at a distance.",
        "why": "HOMER solves the problem of selecting distant objects precisely and then manipulating them naturally. It is a hybrid technique combining the reach of ray-casting with the naturalness of direct manipulation."
    },
    {
        "q": "Question 33. What is a non-isomorphic interaction technique and what is one advantage and one shortcoming?",
        "a": "A non-isomorphic technique maps physical movements to virtual movements at a different scale or ratio. Advantage: superhuman capability — small movements can produce large virtual effects. Shortcoming: reduced naturalness and higher error rates because physical memory and proprioception do not match the virtual result.",
        "why": "Non-isomorphic techniques are powerful but break the natural correspondence between body and virtual action. They are tested in Question 5 of the exam."
    },
    {
        "q": "Question 34. Name five wayfinding support techniques used in VR.",
        "a": "Landmarks, maps, path following, breadcrumbs, and compass.",
        "why": "Landmarks are distinct non-mobile objects visible from multiple locations. Maps can be ego-centric or exo-centric. Path following uses coloured lines on floors. Breadcrumbs show where you have been. A compass gives directional orientation."
    },
    {
        "q": "Question 35. Name Kevin Lynch's five elements of city imageability.",
        "a": "Paths, Edges, Districts, Nodes, and Landmarks.",
        "why": "Lynch's framework from urban planning is applied to VR environment design in the lecture. Well-designed VR environments use the same spatial grammar to help users build cognitive maps."
    },

    # ── EPISODE 5: Content Creation, Low-Poly, Level Design ──
    {
        "q": "Question 36. What is white-boxing or grey-boxing in level design, and name one advantage and one disadvantage?",
        "a": "White-boxing is prototyping an environment using only primitive 3D shapes before adding any art assets. Advantage: quickly test spatial layout, proportions, flow, and scale. Disadvantage: cannot test visual mood or emotional tone.",
        "why": "White-boxing is a standard industry technique referenced in the Week 10 lecture. It lets designers iterate on space before investing in expensive art assets."
    },
    {
        "q": "Question 37. What are the four steps to making low-poly look good, from the Week 10 lecture?",
        "a": "Step 1 is Modelling — silhouette and polygon count per unit. Step 2 is Materials — flat colours and limiting textures. Step 3 is Lighting — the most important part, using a skydome with indirect and specular light. Step 4 is Post-processing — depth haze, colour correction, and depth of field.",
        "why": "These four steps are a direct framework from the lecture slides, drawing on the SundaySundae reference. Lighting is explicitly called the most important part in the lecture."
    },
    {
        "q": "Question 38. Who wrote the Aladdin VR paper, when was it published, and what was the main finding about content versus technology?",
        "a": "Randy Pausch and colleagues published it in 1996. The main finding was that people are not impressed by technology alone — content matters. Guests wanted something to do, not just something to look at.",
        "why": "The Pausch Aladdin paper is a key reading referenced in the lecture. Over 45,000 guests experienced the attraction. It also found that 60 frames per second and high-quality textures were required to achieve suspension of disbelief."
    },
    {
        "q": "Question 39. What does the Heider and Simmel 1944 experiment demonstrate about human perception and VR content design?",
        "a": "34 participants watched geometric shapes — triangles and a circle — moving on screen and almost all invented a coherent story about a bully, a hero, and a victim. This demonstrates that people are meaning generators — simple cues produce consistent interpretations.",
        "why": "The lecture uses this experiment to support the principle that you do not need photorealistic graphics to create compelling VR experiences. People fill gaps with imagination. Suggestion is often enough."
    },
    {
        "q": "Question 40. What does the rule of thumb for polygon count per unit state in low-poly design?",
        "a": "If you are halving the size of an object, halve its subdivisions as well. This creates visual uniformity in terms of detail and resolution across all objects in the scene.",
        "why": "This rule is from the Week 10 lecture drawing on the SundaySundae reference. Giving a small object the same polygon count as a large one creates an inconsistent resolution that breaks the visual cohesion of a low-poly scene."
    },
]

OUTRO = """
That is the end of your CS423 Q and A revision session.

You have covered 40 questions across all five topics — 
Virtual Reality foundations, Immersion and Presence, 
the Wingrave and LaViola design issues paper, 
3D interaction and navigation techniques, 
and content creation with low poly design.

Key papers to remember for your exam are:
Slater and Wilbur, 1997, the FIVE framework.
Wingrave and LaViola, 2010, 67 issues, 11 themes.
Minsky, 1980, Telepresence.
Sutherland, 1965, The Ultimate Display.
Heeter, 1992, three types of presence.
Witmer and Singer, 1998, the Presence Questionnaire.
Pausch, 1996, the Aladdin VR paper.
Sadowski, 2002, guidelines for presence.
International Society for Presence Research, 2000, definition of presence.

Good luck in your exam. You have done the work. Now go prove it.
"""

# ── TTS helpers ───────────────────────────────────────────────────────────────

def clean(text):
    text = re.sub(r'  +', ' ', text)
    return text.strip()


async def speak_to_file(text, path):
    communicate = edge_tts.Communicate(text=clean(text), voice=VOICE)
    await communicate.save(path)


def silence_to_file(seconds, path):
    """Generate a true silent audio file using pure Python — no API call needed."""
    import wave, struct
    sample_rate = 44100
    num_samples = int(sample_rate * seconds)
    wav_path = path.replace('.mp3', '.wav')
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack('<' + 'h' * num_samples, *([0] * num_samples)))
    os.rename(wav_path, path)


def concat_mp3s(paths, output_path):
    """Concatenate MP3 files by binary concatenation."""
    with open(output_path, 'wb') as out:
        for p in paths:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                with open(p, 'rb') as f:
                    out.write(f.read())


async def generate_question_block(i, item, tmp_dir):
    """Generate all 4 audio segments for one question simultaneously."""
    def tmp(name):
        return os.path.join(tmp_dir, name)

    q_path   = tmp(f"q{i+1:03d}_a_question.mp3")
    a1_path  = tmp(f"q{i+1:03d}_b_answer1.mp3")
    a2_path  = tmp(f"q{i+1:03d}_c_answer2.mp3")
    why_path = tmp(f"q{i+1:03d}_d_why.mp3")

    # Fire all 4 TTS calls at the same time
    await asyncio.gather(
        speak_to_file(item["q"], q_path),
        speak_to_file("The answer is. " + item["a"], a1_path),
        speak_to_file("Again. " + item["a"], a2_path),
        speak_to_file(item["why"], why_path),
    )
    return q_path, a1_path, a2_path, why_path


async def build_episode():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tmp_dir = os.path.join(OUTPUT_DIR, "_tmp_ep6")
    os.makedirs(tmp_dir, exist_ok=True)

    def tmp(name):
        return os.path.join(tmp_dir, name)

    # ── Step 1: Silence, intro and outro all at once ──────────────────────────
    print("Step 1/3 — Generating silence, intro and outro in parallel...")
    gap3    = tmp("_silence_3s.mp3")
    gap1    = tmp("_silence_1s.mp3")
    intro_p = tmp("0000_intro.mp3")
    outro_p = tmp("9999_outro.mp3")

    # Silence is generated locally — no API call needed
    silence_to_file(3, gap3)
    silence_to_file(1, gap1)
    # Intro and outro in parallel
    await asyncio.gather(
        speak_to_file(INTRO, intro_p),
        speak_to_file(OUTRO, outro_p),
    )
    print("  Done.\n")

    # ── Step 2: All 40 questions in parallel batches of 10 ───────────────────
    BATCH_SIZE = 10
    all_results = []

    print(f"Step 2/3 — Generating {len(QNA)} questions in batches of {BATCH_SIZE}...")
    for batch_start in range(0, len(QNA), BATCH_SIZE):
        batch     = QNA[batch_start:batch_start + BATCH_SIZE]
        batch_end = min(batch_start + BATCH_SIZE, len(QNA))
        print(f"  Questions {batch_start+1} to {batch_end}...")

        results = await asyncio.gather(*[
            generate_question_block(batch_start + j, item, tmp_dir)
            for j, item in enumerate(batch)
        ])
        all_results.extend(results)

    print("  Done.\n")

    # ── Step 3: Assemble in order and concatenate ─────────────────────────────
    print("Step 3/3 — Assembling and concatenating...")
    segments = [intro_p, gap1]

    for q_path, a1_path, a2_path, why_path in all_results:
        segments.append(q_path)    # Question
        segments.append(gap3)      # 3 second thinking gap (reused)
        segments.append(a1_path)   # Answer first time
        segments.append(a2_path)   # Answer second time
        segments.append(why_path)  # Explanation
        segments.append(gap1)      # 1 second gap (reused)

    segments.append(outro_p)

    final = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    concat_mp3s(segments, final)

    size_mb = os.path.getsize(final) / (1024 * 1024)
    print(f"\nDone. Saved: {final}  ({size_mb:.1f} MB)")

    # Clean up temp files
    for f in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)
    print("Temp files cleaned up.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\nCS423 Episode 6 — Q&A Podcast Generator")
    print("==========================================")
    print(f"Voice:      {VOICE}")
    print(f"Questions:  {len(QNA)}")
    print(f"Output:     {OUTPUT_DIR}/{OUTPUT_FILE}\n")
    asyncio.run(build_episode())


if __name__ == "__main__":
    main()
