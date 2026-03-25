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
