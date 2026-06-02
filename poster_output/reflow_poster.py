"""Reflow BossAI_Poster_A1.pptx — fix text overflow & line placement."""

from pptx import Presentation
from pptx.util import Inches, Emu
import os, copy

SRC = os.path.join(os.path.dirname(__file__), "BossAI_Poster_A1.pptx")
OUT = os.path.join(os.path.dirname(__file__), "BossAI_Poster_A1_reflowed.pptx")

INCH = 914400  # 1 inch in EMU

# Column boundaries
LEFT_COL_MAX_X = 11.5 * INCH  # shapes with left < this → left column


def estimate_text_height(shape, col_width_inch=10.5):
    """Estimate needed height for a text box based on content."""
    if not shape.has_text_frame:
        return shape.height

    total_lines = 0
    max_font_pt = 10

    for para in shape.text_frame.paragraphs:
        # Get font size
        font_pt = 10
        if para.runs:
            for run in para.runs:
                if run.font.size:
                    font_pt = run.font.size.pt
                    break
        if font_pt > max_font_pt:
            max_font_pt = font_pt

        # Estimate chars per line (Korean chars are wider)
        text = para.text
        if not text.strip():
            total_lines += 0.3
            continue

        # Korean chars take ~1.8x width of latin chars
        effective_len = 0
        for ch in text:
            if ord(ch) > 0x1100:  # CJK range (rough)
                effective_len += 1.8
            else:
                effective_len += 1.0

        chars_per_inch = 72 / font_pt * 1.1  # rough estimate
        chars_per_line = col_width_inch * chars_per_inch
        lines_for_para = max(1, effective_len / chars_per_line)
        total_lines += lines_for_para

    line_height_inch = max_font_pt / 72 * 1.6  # 1.6 line spacing
    needed_inch = total_lines * line_height_inch + 0.25  # padding
    return max(int(needed_inch * INCH), shape.height)


def is_line(shape):
    """Check if shape is a separator line (very thin)."""
    return shape.height < 5000 and "AUTO_SHAPE" in str(shape.shape_type)


def is_banner(shape):
    """Check if shape is a section banner image (short picture)."""
    return ("PICTURE" in str(shape.shape_type) and
            shape.height < 0.6 * INCH and
            shape.width > 5 * INCH)


def is_figure(shape):
    """Check if shape is a content figure (tall picture)."""
    return ("PICTURE" in str(shape.shape_type) and
            shape.height > 0.6 * INCH)


def is_title_banner(shape):
    """Check if shape is the title banner (very tall picture at top)."""
    return ("PICTURE" in str(shape.shape_type) and
            shape.height > 2 * INCH and
            shape.top < 2 * INCH)


def reflow_column(shapes, start_y, bottom_limit):
    """Reposition shapes in a column sequentially."""
    y = start_y
    gap_after_line = int(0.08 * INCH)
    gap_after_banner = int(0.05 * INCH)
    gap_after_text = int(0.05 * INCH)
    gap_after_figure = int(0.05 * INCH)
    gap_before_line = int(0.08 * INCH)

    for i, shape in enumerate(shapes):
        shape.top = int(y)

        if is_line(shape):
            # Line: keep zero height, add gap before and after
            y += gap_after_line
        elif is_banner(shape):
            y += shape.height + gap_after_banner
        elif is_figure(shape):
            y += shape.height + gap_after_figure
        elif shape.has_text_frame:
            new_h = estimate_text_height(shape)
            shape.height = new_h
            y += new_h + gap_after_text
        elif "TABLE" in str(shape.shape_type):
            y += shape.height + gap_after_text
        else:
            y += shape.height + gap_after_text

        # Add extra gap before a line separator
        if i + 1 < len(shapes) and is_line(shapes[i + 1]):
            y += gap_before_line

    return y


def main():
    prs = Presentation(SRC)
    slide = prs.slides[0]

    # Separate shapes into left column, right column, and title
    left_shapes = []
    right_shapes = []
    title_shapes = []

    for shape in slide.shapes:
        if is_title_banner(shape):
            title_shapes.append(shape)
        elif shape.left < LEFT_COL_MAX_X:
            left_shapes.append(shape)
        else:
            right_shapes.append(shape)

    # Sort by top position
    left_shapes.sort(key=lambda s: s.top)
    right_shapes.sort(key=lambda s: s.top)

    # Title stays at its position
    # Content starts after title
    title_bottom = 1.0 * INCH  # default
    for s in title_shapes:
        b = s.top + s.height
        if b > title_bottom:
            title_bottom = b

    content_start = title_bottom + int(0.15 * INCH)

    # Reflow each column
    left_end = reflow_column(left_shapes, content_start, 33 * INCH)
    right_end = reflow_column(right_shapes, content_start, 33 * INCH)

    max_end = max(left_end, right_end)
    print(f"Left column ends at: {left_end/INCH:.1f} inches")
    print(f"Right column ends at: {right_end/INCH:.1f} inches")
    print(f"Page height: {prs.slide_height/INCH:.1f} inches")

    if max_end > prs.slide_height:
        overflow = (max_end - prs.slide_height) / INCH
        print(f"WARNING: Content overflows by {overflow:.1f} inches!")
        print("Consider reducing font sizes or figure heights.")

    prs.save(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
