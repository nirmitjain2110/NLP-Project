import os
from ingestion import ingest_pdf   # your existing function
from router import nlp_based_router  # your router file

def test_router_on_pdf():
    """
    End-to-end test:
    PDF → ingestion → routing → inspect queues
    """

    # Path to your PDF (same repo)
    pdf_path = os.path.join(os.path.dirname(__file__), "generic_test_document.pdf")

    print("\nLoading PDF:", pdf_path)

    # Step 1: Ingest PDF
    document_blocks = ingest_pdf(pdf_path)

    print(f"\n Total Blocks Extracted: {len(document_blocks)}")

    # Debug: show block types
    print("\n--- Extracted Blocks ---")
    for i, block in enumerate(document_blocks):
        print(f"[{i}] ({block['type']}) -> {block['text'][:80]}")

    # Step 2: Route blocks
    audio_queue, llm_queue = nlp_based_router(document_blocks)

    # Step 3: Output results
    print("\n AUDIO QUEUE")
    print("-" * 40)
    for item in audio_queue:
        print(item)

    print("\n LLM QUEUE")
    print("-" * 40)
    for item in llm_queue:
        print(item)

    # Step 4: Basic Assertions (sanity checks)
    assert len(audio_queue) > 0, "Audio queue should not be empty"
    
    # Ensure index lines go directly to audio
    index_items = [x for x in audio_queue if x["play_type"] == "DIRECT_PLAY" and "...." in (x["text"] or "")]
    assert len(index_items) > 0, "Index lines should be directly played"

    # Ensure fragments go to LLM
    llm_items = [x for x in audio_queue if x["play_type"] == "WAIT_FOR_LLM"]
    assert len(llm_items) == len(llm_queue), "Mismatch between placeholders and LLM queue"

    print("\n TEST PASSED: Routing logic behaves as expected")


if __name__ == "__main__":
    test_router_on_pdf()
