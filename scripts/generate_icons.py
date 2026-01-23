#!/usr/bin/env python3
"""
Generate placeholder PWA icons for the Selettore Inni application.
This creates simple colored icons with text until proper icons are designed.

Requirements: pip install Pillow
"""

import os

from PIL import Image, ImageDraw, ImageFont

# Icon sizes needed
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Colors (Church blue theme)
BACKGROUND_COLOR = (0, 63, 135)  # #003f87
TEXT_COLOR = (255, 255, 255)  # White

def create_icon(size, output_path):
    """Create a simple icon with the app initials."""
    # Create image with background color
    img = Image.new('RGB', (size, size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Calculate font size (roughly 40% of icon size)
    font_size = int(size * 0.4)
    
    # Try to use a system font, fallback to default
    try:
        # Try common system fonts
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            'C:\\Windows\\Fonts\\arial.ttf',  # Windows
        ]
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Text to display
    text = "LDS"  # Selettore Inni
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate position to center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Draw text
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)
    
    # Add a subtle border
    border_width = max(2, size // 64)
    draw.rectangle(
        [(border_width, border_width), (size - border_width, size - border_width)],
        outline=(255, 255, 255, 128),
        width=border_width
    )
    
    # Save image
    img.save(output_path, 'PNG')
    print(f"✓ Created {output_path}")

def main():
    """Generate all required icon sizes."""
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    icons_dir = os.path.join(project_root, 'static', 'icons')
    
    # Create icons directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    print("Generating PWA icons...")
    print(f"Output directory: {icons_dir}")
    print()
    
    # Generate each icon size
    for size in SIZES:
        filename = f"icon-{size}x{size}.png"
        output_path = os.path.join(icons_dir, filename)
        create_icon(size, output_path)
    
    print()
    print("✓ All icons generated successfully!")
    print()
    print("Note: These are placeholder icons with the 'SI' initials.")
    print("For production, replace these with professionally designed icons.")
    print("See static/icons/README.md for more information.")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("Error: Pillow library not found.")
        print("Install it with: pip install Pillow")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)