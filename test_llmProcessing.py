import unittest
from unittest.mock import patch, MagicMock
from llm_processing import process_llm_queue

class TestLLMProcessor(unittest.TestCase):
    def setUp(self):
        # Simulate the output from the router
        self.audio_queue = [
            {"play_type": "DIRECT_PLAY", "id": "txt_0", "text": "This is the introduction."},
            {"play_type": "WAIT_FOR_LLM", "id": "pending_1", "text": None},
            {"play_type": "DIRECT_PLAY", "id": "txt_2", "text": "This is a following sentence."}
        ]
        
        self.llm_queue = [
            {
                "id": "pending_1",
                "type": "BULLET",
                "text": "High revenue.",
                "context_before": ["This is the introduction."],
                "context_after": ["This is a following sentence."]
            }
        ]

    # This decorator replaces the real OpenAI client with a fake one for this test
    @patch('llm_processor.client.chat.completions.create')
    def test_process_llm_queue(self, mock_openai_create):
        # 1. Setup the fake OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The company experienced highly increased revenue."
        mock_openai_create.return_value = mock_response

        # 2. Run the function
        updated_audio_queue = process_llm_queue(self.audio_queue, self.llm_queue)

        # 3. Verify the API was called
        mock_openai_create.assert_called_once()

        # 4. Verify the audio queue was updated correctly in-place
        self.assertEqual(len(updated_audio_queue), 3)
        
        # Check the specific item that was "WAIT_FOR_LLM"
        target_item = updated_audio_queue[1]
        self.assertEqual(target_item["id"], "pending_1")
        self.assertEqual(target_item["play_type"], "DIRECT_PLAY") # Status should change
        self.assertEqual(target_item["text"], "The company experienced highly increased revenue.") # Text should be inserted
        
        # Ensure order and other items remained untouched
        self.assertEqual(updated_audio_queue[0]["id"], "txt_0")
        self.assertEqual(updated_audio_queue[2]["id"], "txt_2")

if __name__ == '__main__':
    unittest.main()