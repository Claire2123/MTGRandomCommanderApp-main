#!/usr/bin/env python3
from PIL import Image, ImageDraw
import math

# Create a 512x512 image with black background
size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

# Golden/bronze color
gold = (218, 165, 32, 255)

# Draw chalice/cup icon
center_x, center_y = size // 2, size // 2
margin = 50

# Draw the cup body (main chalice shape)
cup_width = 280
cup_height = 200
cup_top = 180
cup_left = center_x - cup_width // 2
cup_right = center_x + cup_width // 2

# Top rim of the chalice
rim_height = 40
draw.rectangle([cup_left - 20, cup_top - rim_height, cup_right + 20, cup_top], fill=gold)

# Cup body (trapezoid-like)
draw.polygon([
    (cup_left, cup_top),
    (cup_right, cup_top),
    (cup_right - 40, cup_top + cup_height),
    (cup_left + 40, cup_top + cup_height)
], fill=gold)

# Draw decorative slits/openings on the cup
slit_y_start = cup_top + 50
slit_y_end = cup_top + cup_height - 30
slit_width = 30

# Left slit
draw.rectangle([cup_left + 50, slit_y_start, cup_left + 50 + slit_width, slit_y_end], fill=(0, 0, 0, 255))

# Middle slit
draw.rectangle([center_x - slit_width // 2, slit_y_start, center_x + slit_width // 2, slit_y_end], fill=(0, 0, 0, 255))

# Right slit
draw.rectangle([cup_right - 50 - slit_width, slit_y_start, cup_right - 50, slit_y_end], fill=(0, 0, 0, 255))

# Draw cup base/stem
stem_width = 80
stem_height = 60
draw.rectangle([
    center_x - stem_width // 2,
    cup_top + cup_height,
    center_x + stem_width // 2,
    cup_top + cup_height + stem_height
], fill=gold)

# Draw base
base_width = 160
base_height = 30
draw.rectangle([
    center_x - base_width // 2,
    cup_top + cup_height + stem_height,
    center_x + base_width // 2,
    cup_top + cup_height + stem_height + base_height
], fill=gold)

# Save the icon
img.save('icon.png')
print("Icon created successfully: icon.png")
