"""Small Pillow renderer; no GUI, matplotlib, or video encoder required."""
from pathlib import Path

from PIL import Image, ImageDraw


def draw_frame(observation, candidates, selected=None, scale=9):
    width, height = observation.width, observation.height
    image = Image.new("RGB", (width * scale, height * scale + 52), "#243341")
    draw = ImageDraw.Draw(image)
    for points, color in ((observation.observed_free, "#c7e6de"),
                          (observation.observed_walls, "#101a24")):
        for x, y in points:
            draw.rectangle((x*scale, y*scale, (x+1)*scale-1, (y+1)*scale-1), fill=color)
    for x, y in candidates:
        draw.rectangle((x*scale+1, y*scale+1, (x+1)*scale-2, (y+1)*scale-2), outline="#e69026", width=2)
    for i, (x, y) in enumerate(observation.agent_positions):
        draw.ellipse((x*scale+1, y*scale+1, (x+1)*scale-1, (y+1)*scale-1),
                     fill="#e36472" if i == 0 else "#2865ad")
    if selected is not None:
        x, y = selected
        draw.ellipse((x*scale-2, y*scale-2, (x+1)*scale+2, (y+1)*scale+2), outline="#ffbc42", width=2)
    draw.text((8, height*scale+7), f"Step {observation.step} | {len(observation.agent_positions)} agents incl. depot | {len(candidates)} eligible", fill="white")
    draw.text((8, height*scale+27), "Teal: observed | dark: unknown/walls | gold: candidates", fill="white")
    return image


def save_frames(frames, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frames[-1].save(output / "final.png")
    if len(frames) > 1:
        frames[0].save(output / "exploration.gif", save_all=True,
                       append_images=frames[1:], duration=650, loop=0)
