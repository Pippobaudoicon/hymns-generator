# PWA Icons Guide

This directory contains the app icons for the Progressive Web App (PWA).

## Required Icon Sizes

The following icon sizes are needed for optimal PWA support:

- **72x72** - Android Chrome
- **96x96** - Android Chrome
- **128x128** - Android Chrome
- **144x144** - Android Chrome, Windows
- **152x152** - iOS Safari
- **192x192** - Android Chrome (standard)
- **384x384** - Android Chrome
- **512x512** - Android Chrome (high-res), splash screens

## How to Generate Icons

### Option 1: Using Online Tools (Easiest)

1. **PWA Asset Generator** (Recommended)
   - Visit: https://www.pwabuilder.com/imageGenerator
   - Upload a 512x512 PNG source image
   - Download the generated icon pack
   - Extract and place files in this directory

2. **RealFaviconGenerator**
   - Visit: https://realfavicongenerator.net/
   - Upload your source image
   - Configure settings for PWA
   - Download and extract to this directory

### Option 2: Using ImageMagick (Command Line)

If you have ImageMagick installed, you can generate all sizes from a single source image:

```bash
# Navigate to this directory
cd static/icons

# Place your source image (512x512 or larger) as source.png
# Then run these commands:

convert source.png -resize 72x72 icon-72x72.png
convert source.png -resize 96x96 icon-96x96.png
convert source.png -resize 128x128 icon-128x128.png
convert source.png -resize 144x144 icon-144x144.png
convert source.png -resize 152x152 icon-152x152.png
convert source.png -resize 192x192 icon-192x192.png
convert source.png -resize 384x384 icon-384x384.png
convert source.png -resize 512x512 icon-512x512.png
```

### Option 3: Using Python Script

Create a Python script to generate icons:

```python
from PIL import Image
import os

sizes = [72, 96, 128, 144, 152, 192, 384, 512]
source = "source.png"

img = Image.open(source)

for size in sizes:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(f"icon-{size}x{size}.png")
    print(f"Generated icon-{size}x{size}.png")
```

## Design Guidelines

### Source Image Requirements
- **Minimum size**: 512x512 pixels
- **Recommended size**: 1024x1024 pixels
- **Format**: PNG with transparency
- **Safe zone**: Keep important content within 80% of the canvas (avoid edges)
- **Background**: Use a solid color or transparent background

### Design Tips
1. **Simple and recognizable**: Icons should be clear at small sizes
2. **High contrast**: Ensure good visibility on various backgrounds
3. **Centered content**: Keep the main symbol centered
4. **Avoid text**: Small text becomes unreadable at smaller sizes
5. **Test on devices**: Check how icons look on actual devices

## Maskable Icons

For Android adaptive icons, consider creating maskable versions:
- Use the full 512x512 canvas
- Keep important content in the center 80% (safe zone)
- The outer 20% may be cropped on some devices

## Screenshots (Optional)

For better app store presentation, add screenshots:
- `screenshot-mobile.png` - 540x720 (portrait)
- `screenshot-desktop.png` - 1280x720 (landscape)

## Current Status

⚠️ **Icons need to be generated**

Please generate the required icons using one of the methods above and place them in this directory.

## Verification

After generating icons, verify they exist:

```bash
ls -la static/icons/
```

You should see:
- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

## Testing

1. **Local Testing**: Run your app and check browser DevTools > Application > Manifest
2. **Lighthouse**: Run a PWA audit in Chrome DevTools
3. **Mobile Testing**: Test installation on actual mobile devices