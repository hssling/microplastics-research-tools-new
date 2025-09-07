
"""
gene_expression_animation.py
Creates an animated video showing the "Gene Expression Clock Across Human Lifespan"
with narration in a female voice explaining each life stage.
Dependencies: moviepy, matplotlib, numpy, pyttsx3, pillow
Install with: pip install moviepy matplotlib numpy pyttsx3 pillow

Usage: python gene_expression_animation.py
Output: ./output/gene_expression_lifespan.mp4 (and narration .wav)
Notes:
 - pyttsx3 is used for offline TTS and attempts to pick a female voice.
 - If pyttsx3 is unavailable or voices are limited, the script will still
   produce the video but with silent audio (or you can substitute your own audio).
 - Modify FRAME_DURATION, FPS, and image sizes as needed for performance.
"""

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

# Try to import pyttsx3 for offline TTS
use_tts = True
try:
    import pyttsx3
except Exception as e:
    print("pyttsx3 not available; narration will be skipped. Error:", e)
    use_tts = False

# -----------------------------
# Data for the animation
# -----------------------------
stages = [
    ("Zygote", "0–1 day", "Maternal RNAs; early zygotic genome activation. Example: maternal RNAs, ZGA genes."),
    ("Blastocyst", "2–7 days", "Pluripotency maintained. Key genes: OCT4, SOX2, NANOG."),
    ("Implantation", "2–3 weeks", "Adhesion & immune tolerance genes. Examples: HLA-G, integrins."),
    ("Fetal Development", "4–40 weeks", "Organ-specific programs. HOX genes, hemoglobin switching."),
    ("Infancy", "0–2 years", "Rapid brain growth and immune priming. IGF1, BDNF active."),
    ("Childhood", "2–12 years", "Learning and immune maturation. FOXP2, immune receptor genes."),
    ("Adolescence", "12–20 years", "Hormone-driven change. GnRH, sex-hormone targets."),
    ("Adulthood", "20–50 years", "Stable homeostasis. CLOCK, TP53, metabolic genes."),
    ("Aging", "50–70 years", "Repair declines; oxidative stress rises. SIRT1, repair genes change."),
    ("Old Age", "70+ years", "Senescence and inflammaging: p16, inflammatory cytokines.")
]

# estimated active genes per stage (approx)
active_genes = [200, 1500, 5500, 11000, 13000, 11000, 12000, 9000, 7000, 5000]

# Influencers for each stage
influencers = [
    "Maternal Factors",
    "Epigenetic Reset",
    "Hormonal (Prog/Estrogen)",
    "Growth Factors / Nutrition",
    "Nutrition, Antibodies, Sleep",
    "Diet, Activity, Circadian Rhythm",
    "Sex Hormones, Stress",
    "Lifestyle, Cortisol, Circadian",
    "Oxidative Stress, Hormone Decline",
    "Epigenetic Drift, Chronic Disease"
]

# -----------------------------
# Output settings
# -----------------------------
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)
VIDEO_FILE = os.path.join(OUT_DIR, "gene_expression_lifespan.mp4")
NARRATION_WAV = os.path.join(OUT_DIR, "narration.wav")

# Visual settings
W, H = 1280, 720
FPS = 24
FRAME_DURATION = 2.0  # seconds per stage frame (you can increase for longer narration)
TRANSITION_FRAMES = int(FPS * 0.8)  # frames for crossfade between stages
FONT_PATH = None  # default PIL font; for better results, set path to a TTF file

# Local helper to get a font
def get_font(size=20):
    try:
        if FONT_PATH and os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, size)
    except:
        pass
    return ImageFont.load_default()

# -----------------------------
# Create narration using pyttsx3
# -----------------------------
def create_narration(text_lines, out_wav):
    """Use pyttsx3 to synthesize narration into a WAV file (mono)."""
    if not use_tts:
        return None
    engine = pyttsx3.init()
    # Attempt to pick a female voice
    voices = engine.getProperty('voices')
    female_voice = None
    for v in voices:
        name = getattr(v, 'name', '') or ''
        gender = getattr(v, 'gender', '') or ''
        if 'female' in name.lower() or 'female' in gender.lower():
            female_voice = v.id
            break
    # fallback: pick any voice that sounds suitable
    if female_voice is None and len(voices) > 0:
        # try to select a voice with 'zira', 'samantha', 'kate', or common female names (platform dependent)
        for v in voices:
            if any(n in v.name.lower() for n in ['zira', 'samantha', 'kate', 'female', 'anna']):
                female_voice = v.id
                break
    if female_voice:
        engine.setProperty('voice', female_voice)
    # set rate and volume
    engine.setProperty('rate', 150)  # words per minute
    engine.setProperty('volume', 1.0)
    # Save to file: pyttsx3 can save to file by using engine.save_to_file then run engine.runAndWait()
    combined_text = " ".join(text_lines)
    engine.save_to_file(combined_text, out_wav)
    engine.runAndWait()
    return out_wav

# -----------------------------
# Create frames for each stage
# -----------------------------
def create_stage_image(stage_idx, stage_label, subtitle, genes_count, influencer, info_text):
    """Return a PIL Image for a given life stage index."""
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Background bar showing gene activity
    max_genes = max(active_genes) * 1.1
    bar_w = int(W * 0.7)
    bar_h = 40
    bar_x = int((W - bar_w) / 2)
    bar_y = int(H * 0.25)
    # filled length
    filled = int((genes_count / max_genes) * bar_w)
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=(0,0,0), width=2)
    draw.rectangle([bar_x, bar_y, bar_x + filled, bar_y + bar_h], fill=(135,206,250))

    # Title
    title_font = get_font(28)
    draw.text((W//2, 20), "Gene Expression Clock Across Human Lifespan", anchor="ms", font=title_font, fill=(20,20,20))

    # Stage big label
    stage_font = get_font(36)
    draw.text((W//2, bar_y - 60), f"{stage_label} ({subtitle})", anchor="ms", font=stage_font, fill=(10,10,60))

    # Genes count text
    draw.text((W//2, bar_y + bar_h + 20), f"Estimated active genes this stage: {genes_count:,}", anchor="ms", font=get_font(22), fill=(0,60,0))

    # Influencer box
    infl_font = get_font(18)
    draw.rectangle([W*0.08, H*0.55, W*0.92, H*0.9], outline=(0,0,0), width=2)
    draw.text((W*0.1+10, H*0.55+10), f"Main influencers: {influencer}", font=infl_font, fill=(80,0,0))
    draw.text((W*0.1+10, H*0.55+40), f"Key genes / notes: {info_text}", font=get_font(16), fill=(0,0,0))

    # footer / progress
    footer_font = get_font(14)
    draw.text((W-10, H-10), f"Stage {stage_idx+1} of {len(stages)}", anchor="rs", font=footer_font, fill=(100,100,100))

    return img

# -----------------------------
# Produce images and narration lines
# -----------------------------
def build_assets():
    images = []
    narration_lines = []
    for i, ((label, subtitle, info), genes, infl) in enumerate(zip(stages, active_genes, influencers)):
        img = create_stage_image(i, label, subtitle, genes, infl, info)
        img_path = os.path.join(OUT_DIR, f"frame_{i:02d}.png")
        img.save(img_path)
        images.append(img_path)
        # narration line for this stage
        narration_lines.append(f"Stage {i+1}, {label}, {subtitle}. {info} Influenced mainly by {infl}.")
    return images, narration_lines

# -----------------------------
# Assemble video with moviepy
# -----------------------------
def assemble_video(image_paths, narration_wav=None):
    # Each image will last FRAME_DURATION seconds; optionally create short fade transitions
    clips = []
    for img_path in image_paths:
        clip = ImageSequenceClip([img_path], fps=1/FRAME_DURATION)  # single image clip with duration
        clips.append(clip)

    # Concatenate clips; Note: using ImageSequenceClip with single images might be suboptimal for transitions;
    # for a production version, generate multiple frames per image or animate properties.
    video = concatenate_videoclips(clips, method="compose")
    # Resize to desired resolution (moviepy uses width first)
    video = video.set_fps(FPS).resize((W, H))

    # Attach audio if available
    if narration_wav and os.path.exists(narration_wav):
        audio = AudioFileClip(narration_wav)
        # Loop or set audio duration to video duration
        audio = audio.set_duration(video.duration)
        video = video.set_audio(audio)

    # Write the final video
    video.write_videofile(VIDEO_FILE, codec="libx264", audio_codec="aac", fps=FPS)
    return VIDEO_FILE

# -----------------------------
# Main flow
# -----------------------------
def main():
    print("Building visual frames and narration text...")
    images, narration_lines = build_assets()
    print(f"Created {len(images)} stage images in {OUT_DIR}")

    if use_tts:
        print("Creating narration (this may take a moment)...")
        wav = create_narration(narration_lines, NARRATION_WAV)
        if wav:
            print("Narration saved to:", wav)
        else:
            print("Narration not created. Proceeding without audio.")
            wav = None
    else:
        wav = None

    print("Assembling video (this may take some time)...")
    video_path = assemble_video(images, narration_wav=wav)
    print("Video created at:", video_path)
    print("Done. You can play the video with any MP4-capable player.")

if __name__ == "__main__":
    main()
