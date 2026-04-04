import sys
import threading

from ingestion import ingest_pdf
from router import nlp_based_router
from llm_processing import process_llm_queue
from deepgram_tts import DeepgramVoiceEngine, llm_responses


def main(pdf_path):
    print("\n Starting Pipeline...\n")

    print(" Ingesting PDF...")
    document_blocks = ingest_pdf(pdf_path)
    print(f" Extracted {len(document_blocks)} blocks\n")

    
    print(" Routing blocks...")
    audio_queue, llm_queue = nlp_based_router(document_blocks)

    print(f" Audio Queue Size: {len(audio_queue)}")
    print(f" LLM Queue Size: {len(llm_queue)}\n")

   
    def run_llm():
        print(" Processing LLM queue...")
        updated_audio_queue = process_llm_queue(audio_queue, llm_queue)

        # CRITICAL: Populate shared llm_responses for Deepgram
        for item in updated_audio_queue:
            if item["text"]:
                llm_responses[item["id"]] = item["text"]

        print(" LLM Processing Done\n")

    # Run LLM in background
    llm_thread = threading.Thread(target=run_llm)
    llm_thread.start()

    print(" Starting Deepgram TTS Engine...\n")
    engine = DeepgramVoiceEngine()
    engine.run_engine(audio_queue)

    llm_thread.join()

    print("\n Pipeline Completed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(" Usage: python main.py <pdf_file_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    main(pdf_path)
