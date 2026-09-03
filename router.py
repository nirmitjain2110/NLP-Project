import re
import spacy

nlp = spacy.load("en_core_web_sm")

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
    Dependency parsing to check if the text contains a ROOT token.
    In spaCy's dependency parse, the ROOT is the main verb (or head)
    of the sentence. If no ROOT is found, the text is a fragment.
    """
    doc = nlp(text)
    return any(token.dep_ == "ROOT" for token in doc)

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
            
        # --- DEPENDENCY PARSING LOGIC ---
        # Use spaCy to check if the text has a ROOT (main verb/head)
        if contains_main_verb(text):
            # It has a ROOT! It's a complete thought, no summarization needed.
            audio_queue.append({"play_type": "DIRECT_PLAY", "id": f"txt_{i}", "text": text})
            
        else:
            # No ROOT found — it's a fragment and needs context/expansion.
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