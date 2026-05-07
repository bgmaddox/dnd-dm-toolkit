import os
from pathlib import Path
from PIL import Image

def generate_icons():
    # Paths
    root_dir = Path(__file__).parent.parent.resolve()
    input_png = root_dir / "tools" / "DnDIcon-Computer.png"
    output_ico = root_dir / "tools" / "app_icon.ico"
    
    if not input_png.exists():
        print(f"Error: {input_png} not found.")
        return

    print(f"Generating {output_ico.name} from {input_png.name}...")
    
    img = Image.open(input_png)
    
    # Standard ICO sizes
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico, sizes=icon_sizes)
    
    print(f"Success! Icon created at: {output_ico}")

if __name__ == "__main__":
    generate_icons()
