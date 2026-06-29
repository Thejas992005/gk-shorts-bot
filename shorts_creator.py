from moviepy.editor import ImageSequenceClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import textwrap

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# Category color themes
THEMES = {
    "GK":      {"top": (10,10,50),  "accent": (99,102,241), "pill": (50,50,130)},
    "Science": {"top": (5,30,20),   "accent": (16,185,129), "pill": (20,80,50)},
    "Math":    {"top": (40,10,10),  "accent": (239,68,68),  "pill": (100,30,30)},
}

OPT_COLORS = {
    "A": (79,70,229), "B": (16,185,129),
    "C": (245,158,11), "D": (239,68,68)
}
WHITE        = (255,255,255)
ANSWER_GREEN = (52,211,153)
WRONG_GRAY   = (50,55,80)

def get_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def get_font_reg(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def draw_gradient(img, top_color, bottom_color=(10,10,30)):
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = img.height
        ratio = y / r
        c = tuple(int(top_color[i] + (bottom_color[i]-top_color[i])*ratio) for i in range(3))
        draw.line([(0,y),(WIDTH,y)], fill=c)
    return ImageDraw.Draw(img)

def center_text(draw, text, font, y, color=WHITE):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    draw.text(((WIDTH-tw)//2, y), text, font=font, fill=color)

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def create_frame(qdata, phase="question", countdown=None):
    """
    phase = 'question' | 'countdown' | 'answer'
    """
    category = qdata.get("category", "GK")
    topic    = qdata.get("topic", "General Knowledge")
    theme    = THEMES.get(category, THEMES["GK"])
    accent   = theme["accent"]
    pill_c   = theme["pill"]

    img  = Image.new("RGB", (WIDTH, HEIGHT), theme["top"])
    draw = draw_gradient(img, theme["top"])

    # ── Category icons ────────────────────────────────────────────────
    icons = {"GK": "🌍", "Science": "🔬", "Math": "➕"}
    icon  = icons.get(category, "🧠")

    # ── Top bar ───────────────────────────────────────────────────────
    draw.rounded_rectangle([20,50,WIDTH-20,165], radius=22, fill=accent)
    font_top = get_font(48)
    center_text(draw, f"{icon}  GK QUIZ  {icon}", font_top, 78)

    # ── Topic pill ────────────────────────────────────────────────────
    font_topic = get_font(30)
    tbbox = draw.textbbox((0,0), topic, font=font_topic)
    tw = tbbox[2]-tbbox[0]
    px = (WIDTH-tw-50)//2
    draw.rounded_rectangle([px,185,px+tw+50,235], radius=16, fill=pill_c)
    draw.text((px+25,191), topic, font=font_topic, fill=(200,210,255))

    # ── Question box ──────────────────────────────────────────────────
    draw.rounded_rectangle([20,255,WIDTH-20,570], radius=24, fill=(20,20,60))
    font_q = get_font(42)
    lines  = wrap_text(draw, qdata["question"], font_q, WIDTH-100)
    q_y    = 275
    for line in lines[:5]:
        center_text(draw, line, font_q, q_y)
        q_y += 56

    # ── Comment prompt ────────────────────────────────────────────────
    font_p = get_font(32)
    center_text(draw, "💬 Comment A / B / C / D below!", font_p, 585, (180,180,255))

    # ── Options ───────────────────────────────────────────────────────
    opt_y   = 650
    opt_h   = 135
    opt_gap = 18
    font_o  = get_font(36)
    answer  = qdata["answer"]

    for key, val in qdata["options"].items():
        if phase == "answer":
            fill   = ANSWER_GREEN if key == answer else WRONG_GRAY
            text_c = (0,0,0) if key == answer else (100,110,140)
            if key == answer:
                draw.rounded_rectangle([16,opt_y-4,WIDTH-16,opt_y+opt_h+4],
                                      radius=22, fill=(20,120,80))
        else:
            fill   = OPT_COLORS.get(key,(80,80,120))
            text_c = WHITE

        draw.rounded_rectangle([20,opt_y,WIDTH-20,opt_y+opt_h],
                               radius=18, fill=fill)

        # Key badge
        draw.ellipse([32,opt_y+22,102,opt_y+92], fill=(0,0,0,60))
        font_k = get_font(34)
        draw.text((50, opt_y+30), key, font=font_k,
                 fill=WHITE if phase != "answer" else text_c)

        # Value text
        vlines = wrap_text(draw, val, font_o, WIDTH-160)
        for li, vl in enumerate(vlines[:2]):
            draw.text((115, opt_y+25+li*44), vl, font=font_o, fill=text_c)

        opt_y += opt_h + opt_gap

    # ── Countdown bar ─────────────────────────────────────────────────
    if phase == "countdown" and countdown is not None:
        bar_y = opt_y + 20
        pct   = countdown / 7
        bar_c = (52,211,153) if pct>0.5 else (251,191,36) if pct>0.25 else (239,68,68)
        draw.rounded_rectangle([60,bar_y,WIDTH-60,bar_y+28], radius=14, fill=(40,40,80))
        bw = int((WIDTH-120)*pct)
        if bw > 0:
            draw.rounded_rectangle([60,bar_y,60+bw,bar_y+28], radius=14, fill=bar_c)
        font_t = get_font(60)
        center_text(draw, str(countdown), font_t, bar_y+35, bar_c)

    # ── Answer reveal ─────────────────────────────────────────────────
    if phase == "answer":
        ans_y = opt_y + 15
        draw.rounded_rectangle([20,ans_y,WIDTH-20,ans_y+130], radius=18, fill=(6,60,45))
        font_a = get_font(40)
        center_text(draw, f"✅  Correct Answer: {answer}", font_a, ans_y+10, ANSWER_GREEN)
        exp    = qdata.get("explanation","")
        font_e = get_font_reg(28)
        elines = wrap_text(draw, exp, font_e, WIDTH-80)
        for li, el in enumerate(elines[:2]):
            center_text(draw, el, font_e, ans_y+68+li*34, (167,243,208))

    # ── Bottom bar ────────────────────────────────────────────────────
    draw.rectangle([0,HEIGHT-110,WIDTH,HEIGHT], fill=(10,10,40))
    font_b = get_font(30)
    center_text(draw, "👍 Like  🔔 Subscribe  💬 Comment!", font_b, HEIGHT-90, (180,180,255))

    return np.array(img)


def create_short(qdata, output_path="short.mp4"):
    """Create a 18-second vertical Short."""
    Q_SECS  = 5
    CD_SECS = 7
    AN_SECS = 6

    frames = []

    # Phase 1: Question
    f = create_frame(qdata, phase="question")
    frames += [f] * (Q_SECS * FPS)

    # Phase 2: Countdown
    for s in range(CD_SECS, 0, -1):
        f = create_frame(qdata, phase="countdown", countdown=s)
        frames += [f] * FPS

    # Phase 3: Answer
    f = create_frame(qdata, phase="answer")
    frames += [f] * (AN_SECS * FPS)

    print(f"🎞️  Rendering {len(frames)} frames...")
    clip = ImageSequenceClip(frames, fps=FPS)
    clip.write_videofile(output_path, codec="libx264",
                        audio=False, logger=None,
                        ffmpeg_params=["-crf","23"])
    print(f"✅ Short saved: {output_path}")
    return output_path


if __name__ == "__main__":
    sample = {
        "question": "What is the speed of light?",
        "options": {"A":"3×10⁸ m/s","B":"3×10⁶ m/s","C":"3×10¹⁰ m/s","D":"3×10⁴ m/s"},
        "answer": "A",
        "explanation": "Light travels at approximately 3×10⁸ metres per second in vacuum.",
        "topic": "Physics",
        "category": "Science"
    }
    create_short(sample, "test_short.mp4")
