import os
from PIL import Image, ImageDraw


def create_app_icon(output_dir="assets"):
    """Generate high-quality modern eye icon for system tray and executable."""
    os.makedirs(output_dir, exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer background circle
    draw.ellipse([8, 8, size - 8, size - 8], fill=(18, 24, 38, 255))

    # Outer Eye Shape (glowing cyan chord)
    draw.chord([28, 40, size - 28, 216], start=190, end=350, fill=(0, 210, 255, 230))
    # Inner eye cutout
    draw.chord([36, 52, size - 36, 204], start=190, end=350, fill=(18, 24, 38, 255))

    # Iris (Vibrant Teal / Cyan)
    iris_center = (size // 2, size // 2 + 10)
    iris_radius = 56
    draw.ellipse(
        [iris_center[0] - iris_radius, iris_center[1] - iris_radius,
         iris_center[0] + iris_radius, iris_center[1] + iris_radius],
        fill=(0, 180, 216, 255)
    )

    # Pupil (Dark Deep Navy)
    pupil_radius = 28
    draw.ellipse(
        [iris_center[0] - pupil_radius, iris_center[1] - pupil_radius,
         iris_center[0] + pupil_radius, iris_center[1] + pupil_radius],
        fill=(10, 15, 26, 255)
    )

    # Light Reflection Glint
    glint_radius = 10
    draw.ellipse(
        [iris_center[0] - 18, iris_center[1] - 18,
         iris_center[0] - 18 + glint_radius * 2, iris_center[1] - 18 + glint_radius * 2],
        fill=(255, 255, 255, 240)
    )

    # Save PNG and ICO
    png_path = os.path.join(output_dir, "icon.png")
    ico_path = os.path.join(output_dir, "icon.ico")

    img.save(png_path, format="PNG")
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Generated icons: {png_path}, {ico_path}")
    return png_path, ico_path


if __name__ == "__main__":
    create_app_icon()
