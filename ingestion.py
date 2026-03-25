import pdfplumber
import re
import math

def classify_block(text, metadata, page_stats):
    text = text.strip()
    if not text:
        return "EMPTY"

    # Initialize scores
    scores = {
        "TITLE": 0.0,
        "PARAGRAPH": 0.0,
        "BULLET": 0.0,
        "SENTENCE": 0.0,
        "HEADER_FOOTER": 0.0,
        "INDEX": 0.0
    }

    # Extract metadata & stats
    y = metadata["y"]
    x0 = metadata["x0"]
    font_size = metadata["font_size"]
    page_width = metadata["page_width"]
    page_height = metadata["page_height"]
    
    mean_font = page_stats["mean_font"]
    std_font = page_stats["std_font"]

    # Derived metrics
    words = text.split()
    num_words = len(words)
    sentences = re.split(r'[.!?]\s+', text)
    y_pct = y / page_height if page_height > 0 else 0

    # Linguistic checks
    # Simple heuristic for verbs instead of importing heavy NLP libraries
    common_verbs = r'\b(is|are|was|were|has|have|had|does|do|did|will|can|could|should|would)\b'
    has_verb = bool(re.search(common_verbs, text, re.IGNORECASE))

    # SCORING

    # 1. HEADER / FOOTER RULES (Spatial)
    if y_pct < 0.10 or y_pct > 0.90:
        scores["HEADER_FOOTER"] += 0.8
        if num_words < 10:
            scores["HEADER_FOOTER"] += 0.2

    # 2. TITLE RULES (Typography & Spatial)
    # Uses statistical threshold instead of hardcoded font size
    if font_size > (mean_font + 1.2 * std_font):
        scores["TITLE"] += 0.6
    if num_words < 12 and y_pct < 0.30:
        scores["TITLE"] += 0.3
    if not has_verb:
        scores["TITLE"] += 0.1

    # 3. BULLET RULES (Pattern, Spatial, Linguistic)
    bullet_match = re.match(r"^(\•|\-|\*|\u2022|\d+\.|[a-zA-Z]\))", text)
    if bullet_match:
        scores["BULLET"] += 0.7
    if x0 > page_width * 0.12: # Indentation check
        scores["BULLET"] += 0.3
    if not has_verb and num_words < 15: # Noun phrase fragment
        scores["BULLET"] += 0.2

    # 4. PARAGRAPH & SENTENCE RULES (Structural & Linguistic)
    if len(sentences) > 1 and num_words > 12:
        scores["PARAGRAPH"] += 0.6
    
    if has_verb and num_words > 5:
        scores["SENTENCE"] += 0.5
        scores["PARAGRAPH"] += 0.2
    
    # 5. INDEX RULES (Pattern)
    if re.search(r'\.{4,}', text): # Dot leaders (.....)
        scores["INDEX"] += 0.8
    if re.search(r'\d+$', text.strip()): # Ends with a number
        scores["INDEX"] += 0.2

    # DECISION LOGIC 
    # Find the category with the highest score
    best_match = max(scores, key=scores.get)

    # Fallback if no rule triggered strongly
    if scores[best_match] < 0.4:
        return "SENTENCE"

    return best_match

def ingest_pdf(file_path):
    document_blocks = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_width = page.width
            page_height = page.height
            words = page.extract_words(use_text_flow=True)

            if not words:
                continue

            # PASS 1: Group lines by Y-coordinate and calculate Statistical Baseline
            lines = {}
            all_font_sizes = []
            
            for word in words:
                y = round(word["top"], 1)
                if y not in lines:
                    lines[y] = []
                lines[y].append(word)

                if "size" in word:
                    all_font_sizes.append(word["size"])

            if all_font_sizes:
                mean_font = sum(all_font_sizes) / len(all_font_sizes)
                variance = sum((x - mean_font) ** 2 for x in all_font_sizes) / len(all_font_sizes)
                std_font = math.sqrt(variance)
            else:
                mean_font, std_font = 12.0, 0.0

            page_stats = {
                "mean_font": mean_font,
                "std_font": std_font
            }

            # PASS 1.5: THE BLOCK MERGER (Your Period Logic + Spatial Proximity)
            merged_blocks = []
            current_block = None
            
            # Sort lines top-to-bottom
            sorted_y = sorted(lines.keys())

            for y in sorted_y:
                line_words = sorted(lines[y], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in line_words).strip()
                
                font_sizes = [w.get("size", mean_font) for w in line_words]
                avg_font_size = sum(font_sizes) / len(font_sizes)
                x0 = line_words[0]["x0"]

                if current_block is None:
                    current_block = {
                        "text": text, 
                        "y": y, 
                        "last_y": y, 
                        "x0": x0, 
                        "font_size": avg_font_size
                    }
                else:
                    # HEURISTIC 1: Is the vertical gap small enough to be standard line spacing?
                    # Generally, line spacing is < 2.5x the font size
                    is_vertically_close = (y - current_block["last_y"]) < (avg_font_size * 2.5)
                    
                    # HEURISTIC 2: Are the font sizes similar?
                    is_same_font = abs(avg_font_size - current_block["font_size"]) < 2.0
                    
                    # HEURISTIC 3 (Your Rule): Does the previous line lack terminal punctuation?
                    # If it doesn't end in . ! ? or a quote, it's highly likely a continuation.
                    needs_continuation = not re.search(r'[.!?\"\'”]$', current_block["text"].strip())

                    # If it's close, the same font, AND needs continuation, stitch them together!
                    if is_vertically_close and is_same_font and needs_continuation:
                        current_block["text"] += " " + text
                        current_block["last_y"] = y # Update the bottom edge of the block
                    else:
                        # The block is finished. Save it and start a new one.
                        merged_blocks.append(current_block)
                        current_block = {
                            "text": text, 
                            "y": y, 
                            "last_y": y, 
                            "x0": x0, 
                            "font_size": avg_font_size
                        }
            
            # Don't forget to append the very last block on the page
            if current_block:
                merged_blocks.append(current_block)


            # PASS 2: Classify the fully merged blocks
            for block in merged_blocks:
                metadata = {
                    "page": page_num,
                    "x0": block["x0"],
                    "y": block["y"],
                    "font_size": block["font_size"],
                    "page_width": page_width,
                    "page_height": page_height
                }

                # Now, classify_block is evaluating a whole paragraph at once!
                block_type = classify_block(block["text"], metadata, page_stats)

                document_blocks.append({
                    "text": block["text"],
                    "type": block_type,
                    "metadata": metadata
                })

    return document_blocks