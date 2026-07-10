import os
from PIL import Image, ImageDraw

def create_rect(name, size, color):
    img = Image.new("RGBA", size, color)
    img.save(name)
    print(f"Created {name}")

out_dir = "design/themes/grub/theonix"
os.makedirs(out_dir, exist_ok=True)
os.chdir(out_dir)

# Menu Box (Translucent Dark Gray)
box_color = (30, 30, 30, 180)
for part in ['nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se']:
    create_rect(f"menu_box_{part}.png", (16, 16), box_color)

# Terminal Box (Translucent Black)
term_color = (0, 0, 0, 200)
for part in ['nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se']:
    create_rect(f"terminal_box_{part}.png", (16, 16), term_color)

# Scrollbar
create_rect("scrollbar_thumb_c.png", (10, 10), (108, 99, 255, 255)) # #6C63FF
create_rect("scrollbar_thumb_n.png", (10, 10), (108, 99, 255, 255))
create_rect("scrollbar_thumb_s.png", (10, 10), (108, 99, 255, 255))

# Progress
create_rect("progress_center.png", (32, 32), (0, 0, 0, 0)) # transparent
create_rect("progress_tick.png", (16, 16), (108, 99, 255, 255))

print("Done generating GRUB theme assets.")
