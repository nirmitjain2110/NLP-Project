import threading
import time
from ingestion import ingest_pdf
from router import nlp_based_router
from deepgram_tts import DeepgramVoiceEngine, llm_responses

# --- SIMULATED LLM WORKER ---
# In your final project, replace this with your teammate's actual OpenAI/Gemini call
def llm_processor_worker(llm_queue):
    """
    Simulates the background processing of bullets and complex sentences.
    Updates the shared 'llm_responses' dictionary in deepgram_tts.py.
    """
    for item in llm_queue:
        # Simulate processing delay (network/generation time)
        time.sleep(3) 
        
        # Example expansion logic
        if item["type"] == "BULLET":
            summary = f"Expanding on the point: {item['text']}. This is a key detail for the lecture."
        else:
            summary = f"Summary of the concept: {item['text']}"
            
        # Update shared state so TTS can proceed
        llm_responses[item["id"]] = summary
        print(f"\n🧠 [LLM WORKER] Finished processing {item['id']}")

# --- MAIN EXECUTION FLOW ---
def run_project(pdf_path):
    print("🎬 Starting SmoothFlow PDF Voice Assistant...")
    
    # 1. INGESTION (Nirmit's part)
    print("📄 Ingesting PDF and classifying blocks...")
    document_blocks = ingest_pdf(pdf_path)
    
    # 2. ROUTING (Teammate's part)
    print("🚦 Routing blocks to appropriate queues...")
    audio_queue, llm_queue = nlp_based_router(document_blocks)
    
    print(f"📊 Stats: {len(audio_queue)} Audio Items | {len(llm_queue)} LLM Tasks")

    # 3. INITIALIZE TTS ENGINE (Your part)
    engine = DeepgramVoiceEngine()

    # 4. START LLM THREAD
    # This runs in parallel so we don't block the start of the audio
    llm_thread = threading.Thread(target=llm_processor_worker, args=(llm_queue,), daemon=True)
    llm_thread.start()

    # 5. START TTS CONSUMER
    # This will play DIRECT_PLAY items instantly and WAIT for the LLM thread for others
    try:
        engine.run_engine(audio_queue)
    except KeyboardInterrupt:
        print("\n👋 User stopped playback. Exiting...")

if __name__ == "__main__":
    # Path to your test PDF
    PDF_FILE = "test_lecture.pdf" 
    
    # Check if file exists before running
    import os
    if os.path.exists(PDF_FILE):
        run_project(PDF_FILE)
    else:
        print(f"❌ File not found: {PDF_FILE}. Please place a PDF in the directory.")