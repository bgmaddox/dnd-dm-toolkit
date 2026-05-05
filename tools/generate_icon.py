from PIL import Image, ImageDraw

def create_icon(output_path, size=(512, 512)):
    # Create a transparent image
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a stylized D20 (hexagon)
    padding = 40
    points = [
        (size[0] // 2, padding),
        (size[0] - padding, size[1] // 3),
        (size[0] - padding, 2 * size[1] // 3),
        (size[0] // 2, size[1] - padding),
        (padding, 2 * size[1] // 3),
        (padding, size[1] // 3)
    ]
    
    # Fill with a deep red
    draw.polygon(points, fill=(150, 0, 0, 255), outline=(255, 255, 255, 255), width=10)
    
    # Draw internal lines for the D20 look
    center = (size[0] // 2, size[1] // 2)
    for p in [points[0], points[2], points[4]]:
        draw.line([center, p], fill=(255, 255, 255, 255), width=5)
    
    # Save as PNG
    image.save(output_path)
    print(f"Icon saved to {output_path}")

    # Also save as .ico for Windows
    if output_path.endswith(".png"):
        ico_path = output_path.replace(".png", ".ico")
        # ICO usually contains multiple sizes
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        image.save(ico_path, format="ICO", sizes=icon_sizes)
        print(f"Windows icon saved to {ico_path}")

if __name__ == "__main__":
    import os
    os.makedirs("tools", exist_ok=True)
    create_icon("tools/app_icon.png")
