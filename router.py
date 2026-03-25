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
