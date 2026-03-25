import pdfplumber
import re

def classify_block(text, avg_font_size, x0, page_width):
    text = text.strip()

    # Rule 1: TITLE
    if avg_font_size > 18 and (0.3 * page_width < x0 < 0.7 * page_width):
        return "TITLE"

    # Rule 2: BULLET
    bullet_patterns = r"^(\•|\-|\*|\d+\.)"
    if re.match(bullet_patterns, text) and x0 > 50:
        return "BULLET"

    # Rule 3: PARAGRAPH
    sentences = re.split(r'[.!?]', text)
    if len(sentences) > 3:
        return "PARAGRAPH"

    return "SENTENCE"


# -----------------------------
# MAIN INGESTION FUNCTION
# -----------------------------
def ingest_pdf(file_path):
    document_blocks = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_width = page.width

            # Extract words with metadata
            words = page.extract_words(use_text_flow=True)

            # Group words into lines (simple heuristic: same y)
            lines = {}
            for word in words:
                y = round(word["top"], 1)  # group by Y position
                if y not in lines:
                    lines[y] = []
                lines[y].append(word)

            # Process each line
            for y, line_words in lines.items():
                # Sort words left to right
                line_words = sorted(line_words, key=lambda w: w["x0"])

                text = " ".join(w["text"] for w in line_words)

                # Approx font size (if available)
                font_sizes = [w.get("size", 12) for w in line_words]
                avg_font_size = sum(font_sizes) / len(font_sizes)

                x0 = line_words[0]["x0"]

                block_type = classify_block(
                    text,
                    avg_font_size,
                    x0,
                    page_width
                )

                block = {
                    "text": text,
                    "type": block_type,
                    "metadata": {
                        "page": page_num,
                        "x0": x0,
                        "y": y,
                        "font_size": avg_font_size
                    }
                }

                document_blocks.append(block)

    return document_blocks
