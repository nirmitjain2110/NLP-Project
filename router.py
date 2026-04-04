import re

def get_context(blocks, current_index, window_size=2):
    """
    Extracts +/- window_size valid blocks around the current index.
    Skips HEADER_FOOTER and EMPTY blocks.
    """
    context_before = []
    context_after = []
    
    # Look backwards
    i = current_index - 1
    while i >= 0 and len(context_before) < window_size:
        b_type = blocks[i].get("type", "")
        if b_type not in ["HEADER_FOOTER", "EMPTY"]:
            context_before.insert(0, blocks[i].get("text", ""))
        i -= 1
        
    # Look forwards
    j = current_index + 1
    while j < len(blocks) and len(context_after) < window_size:
        b_type = blocks[j].get("type", "")
        if b_type not in ["HEADER_FOOTER", "EMPTY"]:
            context_after.append(blocks[j].get("text", ""))
        j += 1
        
    return context_before, context_after

def contains_main_verb(text):
    """
    Shallow parsing to check if the text contains a verb.
    """
    # 1. Check for explicit auxiliary / linking verbs
    aux_verbs = r'\b(is|are|was|were|am|be|been|being|has|have|had|does|do|did|will|would|shall|should|can|could|may|might|must)\b'
    if re.search(aux_verbs, text, re.IGNORECASE):
        return True
        
    # 2. Check for words ending in 'ed' (common past-tense verbs)
    # We exclude common words that end in 'ed' but aren't verbs (red, bed, etc.)
    if re.search(r'\b\w{3,}ed\b', text, re.IGNORECASE) and not re.search(r'\b(red|bed|need|seed|weed|feed|hundred)\b', text, re.IGNORECASE):
        return True

    # If it fails the shallow checks, assume it lacks a main verb
    return False

def nlp_based_router(document_blocks):
    audio_queue = []
    llm_queue = []
    
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
            
        # --- THE NEW LOGIC ---
        # Shallow parse to see if it's a complete thought
        if contains_main_verb(text):
            # It has a verb! It doesn't need summarization.
            audio_queue.append({"play_type": "DIRECT_PLAY", "id": f"txt_{i}", "text": text})
            
        else:
            # It lacks a verb! It's a fragment and needs context/expansion.
            pid = f"pending_{i}"            
            
            # keep order intact in main queue with a placeholder
            audio_queue.append({"play_type": "WAIT_FOR_LLM", "id": pid, "text": None})            
            
            # Extract the +/- 2 context window
            ctx_before, ctx_after = get_context(document_blocks, i, window_size=2)
            
            # send to llm for expansion
            llm_queue.append({
                "id": pid, 
                "type": b_type, 
                "text": text,
                "context_before": ctx_before,
                "context_after": ctx_after
            })
            
    return audio_queue, llm_queue