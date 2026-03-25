import re
def nlp_based_router(document_blocks):
    audio_queue = []
    llm_queue = []
    sentence_count = 0
    for i, block in enumerate(document_blocks):
        text = block.get("text", "")
        b_type = block.get("type", "SENTENCE")
        # skip noise
        if b_type in ["HEADER_FOOTER", "EMPTY"]:
            continue
        # handle index/toc
        if re.search(r'\.{4,}\s*\d+$', text):
            audio_queue.append({"play_type": "DIRECT_PLAY", "id": f"idx_{i}", "text": text})
            continue
        if b_type == "SENTENCE":
            sentence_count += 1
        # route bullets and even sentences to llm queue
        if b_type == "BULLET" or (b_type == "SENTENCE" and sentence_count % 2 == 0):
            pid = f"pending_{i}"            
            # keep order intact in main queue
            audio_queue.append({"play_type": "WAIT_FOR_LLM", "id": pid, "text": None})            
            # send to llm for expansion
            llm_queue.append({"id": pid, "type": b_type, "text": text})
        # direct play for odd sentences, titles, etc
        elif b_type in ["TITLE", "PARAGRAPH", "SENTENCE"]:
            audio_queue.append({"play_type": "DIRECT_PLAY", "id": f"txt_{i}", "text": text})
    return audio_queue, llm_queue

if __name__ == "__main__":
    print("🚀 Starting Isolated Test for SmoothFlow NLP Router...\n")
    # Mock data simulating Nirmit's ingestion output (from GCP PDF)
    mock_document_blocks = [
        {"type": "HEADER_FOOTER", "text": "--- PAGE 2 ---"},
        {"type": "TITLE", "text": "Private Cloud in GCP"},
        {"type": "BULLET", "text": "Lecture 5"},
        {"type": "SENTENCE", "text": "In Google Cloud Platform (GCP), a Private Cloud generally refers to creating an isolated environment."},
        {"type": "SENTENCE", "text": "While GCP itself is a public cloud provider, it offers multiple services."},
        {"type": "BULLET", "text": "1. Private Cloud with VPC"},
        {"type": "SENTENCE", "text": "A Virtual Private Cloud is a logically isolated network."},
        {"type": "SENTENCE", "text": "With a VPC, you control IP address ranges."}
    ]
    # Calling the router module
    audio_queue, llm_queue = nlp_based_router(mock_document_blocks)
    # Printing the output to verify order and logic
    print("🎧 AUDIO QUEUE (Strict Order Maintained):")
    for item in audio_queue:
        print(f" -> [{item['play_type']}] {item['text']}")
    print("\n🧠 LLM GENERATION QUEUE (Sent to OpenAI API):")
    for item in llm_queue:
        print(f" -> Expand this {item['type']}: {item['text']}")
