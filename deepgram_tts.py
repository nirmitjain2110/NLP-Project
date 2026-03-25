import os
import time
import threading
import httpx
import subprocess
from dotenv import load_dotenv

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

llm_responses = {}

class DeepgramVoiceEngine:
    def __init__(self):
        # Using Aura-Asteria for a clear, professional female voice
        self.url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
        self.audio_cache = {}
        self.cache_lock = threading.Lock()

    def fetch_audio(self, text):
        """Fetches MP3 bytes from Deepgram."""
        if not text or not str(text).strip():
            return None
        
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}
        
        try:
            with httpx.Client() as client:
                # Deepgram is very fast, but we keep a healthy timeout
                resp = client.post(self.url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    return resp.content
                else:
                    print(f"❌ Deepgram Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"⚠️ Connection Error: {e}")
        return None

    def _pre_fetch_worker(self, item_id, text):
        """Background thread to download the next audio block."""
        audio_data = self.fetch_audio(text)
        if audio_data:
            with self.cache_lock:
                self.audio_cache[item_id] = audio_data

    def play_audio(self, audio_bytes):
        """Universal playback (Mac/Windows) via ffplay."""
        if not audio_bytes: return
        try:
            proc = subprocess.Popen(
                ['ffplay', '-nodisp', '-autoexit', '-hide_banner', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            )
            proc.stdin.write(audio_bytes)
            proc.stdin.close()
            proc.wait() 
        except Exception as e:
            print(f"Playback error: {e}. Ensure FFmpeg is installed.")

    def run_engine(self, audio_queue):
        print("\n⚡ [DEEPGRAM ENGINE] Online. Optimized for Speed.")
        
        for i, item in enumerate(audio_queue):
            current_id = item["id"]

            # 1. RESOLVE TEXT (Wait for LLM if needed)
            if item["play_type"] == "WAIT_FOR_LLM":
                print(f"⏳ Waiting for LLM: {current_id}")
                while current_id not in llm_responses:
                    time.sleep(0.1)
                text_to_speak = llm_responses[current_id]
            else:
                text_to_speak = item["text"]

            # 2. PRE-FETCH NEXT ITEM
            if i + 1 < len(audio_queue):
                next_item = audio_queue[i+1]
                if next_item["play_type"] == "DIRECT_PLAY" and next_item["id"] not in self.audio_cache:
                    threading.Thread(
                        target=self._pre_fetch_worker, 
                        args=(next_item["id"], next_item["text"]),
                        daemon=True
                    ).start()

            # 3. GET & PLAY AUDIO
            with self.cache_lock:
                audio_data = self.audio_cache.pop(current_id, None)
            
            if not audio_data:
                print(f"🐢 Cache miss: {current_id}")
                audio_data = self.fetch_audio(text_to_speak)

            if audio_data:
                print(f"▶️ Playing: {text_to_speak[:50]}...")
                self.play_audio(audio_data)

# --- THE TEST DATA ---
if __name__ == "__main__":
    # Simulate a heavy academic PDF input
    mock_audio_queue = [
        {
            "play_type": "DIRECT_PLAY", 
            "id": "intro_0", 
            "text": "Welcome to the Advanced Module on Neural Network Architectures and Optimization.", 
            "type": "TITLE"
        },
        {
            "play_type": "WAIT_FOR_LLM", 
            "id": "summary_1", 
            "text": None, 
            "type": "BULLET"
        },
        {
            "play_type": "DIRECT_PLAY", 
            "id": "heavy_block_2", 
            "text": (
                "The fundamental challenge in training deep neural networks lies in the optimization of high-dimensional, non-convex loss functions. "
                "At the heart of this process is the backpropagation algorithm, which utilizes the chain rule of calculus to compute gradients of the loss function with respect to each weight in the network. "
                "However, as networks grow deeper, they often encounter the vanishing gradient problem, where gradients become infinitesimally small as they are propagated back through the layers, effectively halting the learning process. "
                "To combat this, researchers have introduced architectural innovations such as Residual Connections and Batch Normalization. "
                "Residual Connections allow gradients to flow through 'shortcut' paths, bypassing one or more layers, which mitigates the degradation problem seen in very deep models. "
                "Batch Normalization, on the other hand, stabilizes the learning process by normalizing the inputs to each layer, reducing the internal covariate shift. "
                "Furthermore, modern optimization techniques like Adam and RMSprop adapt the learning rate for each parameter individually, allowing for faster convergence in complex landscapes. "
                "Understanding these mechanisms is crucial for designing robust AI systems that can generalize well to unseen data. "
                "In the following sections, we will explore the mathematical foundations of Stochastic Gradient Descent and its various momentum-based variants, providing a comprehensive overview of how state-of-the-art models are fine-tuned for peak performance in real-world applications ranging from natural language processing to computer vision."
            ), 
            "type": "PARAGRAPH"
        },
        {
            "play_type": "DIRECT_PLAY", 
            "id": "closing_3", 
            "text": "This concludes the theoretical overview. We will now move to the practical implementation in Python.", 
            "type": "SENTENCE"
        }
    ]

    # Mock LLM response for the summary
    def simulate_llm_worker():
        time.sleep(3) # Simulate the LLM "thinking"
        llm_responses["summary_1"] = "Summary: This module covers backpropagation, vanishing gradients, and optimization techniques like Adam."
        print("\n🧠 [LLM] Summary ready for summary_1")

    # Initialize Engine
    engine = DeepgramVoiceEngine()

    # Start LLM in background
    import threading
    threading.Thread(target=simulate_llm_worker, daemon=True).start()

    # Run the TTS
    try:
        engine.run_engine(mock_audio_queue)
    except KeyboardInterrupt:
        print("\nDemo stopped.")