import openai
import os
from dotenv import load_dotenv

# This looks for the .env file and loads the variables into your environment
load_dotenv()

# Now the OpenAI client will automatically find the key from your environment
client = openai.OpenAI()

def process_llm_queue(audio_queue, llm_queue):
    """
    Processes items that need LLM expansion and updates the audio_queue in place,
    guaranteeing that the original document order is preserved.
    """
    for item in llm_queue:
        target_text = item["text"]
        ctx_before = " ".join(item["context_before"])
        ctx_after = " ".join(item["context_after"])
        
        # Construct a prompt that clearly separates context from the target
        prompt = f"""
            You are an assistant preparing text for a text-to-speech audio reader.
            Your task is to take a text fragment that lacks a main verb (such as a heading, label, or short bullet point) and turn it into a smooth, complete, and conversational sentence.

            Previous Context: "{ctx_before}"
            Target Fragment to Expand: "{target_text}"
            Following Context: "{ctx_after}"

            Generate ONLY the expanded, complete sentence for the 'Target Fragment'. 
            Ensure it fits seamlessly between the Previous and Following context. Do not repeat the context.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are a helpful text-to-speech script editor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            expanded_text = response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error processing item {item['id']}: {e}")
            # Fallback to the original text if the API fails
            expanded_text = target_text 

        # Find the placeholder in the audio_queue and update it
        for audio_item in audio_queue:
            if audio_item.get("id") == item["id"]:
                audio_item["text"] = expanded_text
                audio_item["play_type"] = "DIRECT_PLAY" # Ready for audio generation
                break
                
    return audio_queue