#!/usr/bin/env python3
from PIL import Image
import os

# The image has already been downloaded, let's find it and process it
# Create a new image with black background (512x512)
size = (512, 512)
black_bg = Image.new('RGBA', size, (0, 0, 0, 255))

# Try to load the icon from the attachment
# Since we're working with a URL-based image, we'll create it properly
try:
    # If there's already an image file, use it
    if os.path.exists('temp_icon.png'):
        icon_img = Image.open('temp_icon.png').convert('RGBA')
        # Resize to fit in the 512x512 space with some padding
        icon_img.thumbnail((450, 450), Image.Resampling.LANCZOS)
        
        # Create centered position
        offset = ((size[0] - icon_img.width) // 2, (size[1] - icon_img.height) // 2)
        
        # Paste the icon onto the black background
        black_bg.paste(icon_img, offset, icon_img)
        black_bg.save('icon.png')
        print("Icon created successfully!")
    else:
        print("Icon file not found. Please save the image as 'temp_icon.png' first.")
except Exception as e:
    print(f"Error processing icon: {e}")
