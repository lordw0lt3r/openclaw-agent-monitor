import os
from PIL import Image

# Ensure the assets directory exists
os.makedirs("assets", exist_ok=True)

# Color Palette (RGB)
PALETTE = {
    '.': (0, 0, 0, 0),          # Transparent
    'R': (230, 57, 70),         # Lobster Red
    'D': (157, 2, 8),           # Shadow Red
    'W': (255, 255, 255),       # White (Eyes)
    'B': (29, 53, 87),          # Dark Blue (Pupils)
    'G': (0, 245, 212),         # Cyan/Green Glow (Working)
    'S': (108, 117, 125),       # Sleep Gray
    'C': (73, 80, 87),          # Dark Sleep Gray
    'Z': (144, 224, 239)        # Zzz Light Blue
}

# 16x16 Pixel Art Matrices (Will be scaled up to 32x32)
WORKING_0 = [
    "....G...........",
    "..RR.......RR...",
    ".RRRR.....RRRR..",
    ".RDD.R...R.DDR..",
    "..RR.......RR...",
    "...RR.....RR....",
    "....RRRRRRR.....",
    "...RRRRRRRRR....",
    "..RRWBRRRWBRR...",
    "..RRRRRRRRRRR...",
    "..RRRRRRRRRRR...",
    "...RRRRRRRRR....",
    "....RRRRRRR.....",
    ".....RRRRR......",
    "......RRR.......",
    "................"
]

WORKING_1 = [
    ".......G........",
    ".RRR.......RRR..",
    ".R.RR.....RR.R..",
    "..DDR.....RDD...",
    "..RR.......RR...",
    "...RR.....RR....",
    "....RRRRRRR.....",
    "...RRRRRRRRR....",
    "..RRGGRRRGGRR...", # Glowing Cyan Eyes when working hard!
    "..RRRRRRRRRRR...",
    "..RRRRRRRRRRR...",
    "...RRRRRRRRR....",
    "....RRRRRRR.....",
    ".....RRRRR......",
    "......RRR.......",
    "................"
]

SLEEPING_0 = [
    "................",
    "..SS.......SS...",
    ".SSSS.....SSSS..",
    ".SCC.S...S.CCS..",
    "..SS.......SS...",
    "...SS.....SS....",
    "....SSSSSSS.....",
    "...SSSSSSSSS....",
    "..SSCCSSSCCSS...", # Closed eyes (Dark Gray)
    "..SSSSSSSSSSS...",
    "..SSSSSSSSSSS...",
    "...SSSSSSSSS....",
    "....SSSSSSS.....",
    ".....SSSSS......",
    "......SSS.......",
    "................"
]

SLEEPING_1 = [
    "............Z...", # Floating Z
    "..SS.......SS...",
    ".SSSS.....SSSS..",
    ".SCC.S...S.CCS..",
    "..SS.......SS.z.", # Tiny z
    "...SS.....SS....",
    "....SSSSSSS.....",
    "...SSSSSSSSS....",
    "..SSCCSSSCCSS...",
    "..SSSSSSSSSSS...",
    "..SSSSSSSSSSS...",
    "...SSSSSSSSS....",
    "....SSSSSSS.....",
    ".....SSSSS......",
    "......SSS.......",
    "................"
]

def save_pixel_art(matrix, filename):
    """Parses the string matrix, creates a 16x16 image, and scales it up to 32x32."""
    img = Image.new("RGBA", (16, 16))
    pixels = img.load()
    
    for y, row in enumerate(matrix):
        for x, char in enumerate(row):
            pixels[x, y] = PALETTE.get(char, (0, 0, 0, 0))
            
    # Scale 2x using Nearest Neighbor to keep the crisp pixel edges
    scaled_img = img.resize((32, 32), Image.Resampling.NEAREST)
    scaled_img.save(os.path.join("assets", filename))
    print(f"Generated: assets/{filename}")

if __name__ == "__main__":
    save_pixel_art(WORKING_0, "working_0.png")
    save_pixel_art(WORKING_1, "working_1.png")
    save_pixel_art(SLEEPING_0, "sleeping_0.png")
    save_pixel_art(SLEEPING_1, "sleeping_1.png")
    print("All OpenClaw agent frame assets generated successfully!")
