from PIL import Image
import sys

MAX_EXTRA_PIXELS = 6

def edge_score_rgba(pixel):
    r, g, b, a = pixel

    # Transparent pixels are safest to remove.
    if a == 0:
        return 0

    # Pure black frame pixels should be very expensive to remove.
    # Higher score = less desirable to trim.
    return a + r + g + b

def trim_transparent_to_size(input_file, output_file, target_w, target_h):
    img = Image.open(input_file).convert("RGBA")
    w, h = img.size

    if w < target_w or h < target_h:
        raise ValueError(f"Image is smaller than target: {w}x{h}, target {target_w}x{target_h}")

    left, top, right, bottom = 0, 0, w, h
    pixels = img.load()

    def col_is_fully_transparent(x):
        return all(pixels[x, y][3] == 0 for y in range(top, bottom))

    def row_is_fully_transparent(y):
        return all(pixels[x, y][3] == 0 for x in range(left, right))

    def col_score(x):
        return sum(edge_score_rgba(pixels[x, y]) for y in range(top, bottom))

    def row_score(y):
        return sum(edge_score_rgba(pixels[x, y]) for x in range(left, right))

    # First trim fully transparent edges.
    while right - left > target_w and col_is_fully_transparent(left):
        left += 1
    while right - left > target_w and col_is_fully_transparent(right - 1):
        right -= 1
    while bottom - top > target_h and row_is_fully_transparent(top):
        top += 1
    while bottom - top > target_h and row_is_fully_transparent(bottom - 1):
        bottom -= 1

    # If still slightly too large, trim the least-black / most-transparent edge.
    # If equal score, alternate sides
    last_edge_trimmed = ""
    if right - left <= target_w + MAX_EXTRA_PIXELS:
        while right - left > target_w:
            left_score = col_score(left)
            right_score = col_score(right - 1)

            if left_score < right_score or (left_score == right_score and last_edge_trimmed == "right"):
                left += 1
                last_edge_trimmed = "left"
            else:
                right -= 1
                last_edge_trimmed = "right"

    if bottom - top <= target_h + MAX_EXTRA_PIXELS:
        while bottom - top > target_h:
            top_score = row_score(top)
            bottom_score = row_score(bottom - 1)

            if top_score < bottom_score or (top_score == bottom_score and last_edge_trimmed == "bottom"):
                top += 1
                last_edge_trimmed = "top"
            else:
                bottom -= 1
                last_edge_trimmed = "bottom"

    cropped = img.crop((left, top, right, bottom))

    if cropped.size != (target_w, target_h):
        raise ValueError(f"Could not reach exact target size. Got {cropped.size}, target {(target_w, target_h)}")

    # retain same DPI as original, default to 300
    dpi = img.info.get("dpi", (300, 300))
    cropped.save(output_file, dpi=dpi)
    print(f"Saved {output_file}: {cropped.size[0]}x{cropped.size[1]}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python trim_to_size.py input.png output.png width height")
        sys.exit(1)

    trim_transparent_to_size(
        sys.argv[1],
        sys.argv[2],
        int(sys.argv[3]),
        int(sys.argv[4])
    )