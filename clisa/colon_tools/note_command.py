from clisa.colon_tools.base_colon_command import BaseColonCommand, Action
import requests
from typing import List, Tuple
import json
from clisa.jprinty import printGrey

class NoteCommand(BaseColonCommand):
    ADD_ENDPOINT_URL = "https://cave.keychaotic.com:7878/add_transcription"

    @staticmethod
    def execute(command: str, text: str, messages: List[dict], cursor_location: int, max_messages: int) -> Tuple[List[dict], int, List[Action]]:
        # Find the last assistant message, ensuring cursor_location is taken into account
        last_assistant_message = None
        for message in reversed(messages[:cursor_location]):
            if message["role"] == "assistant":
                last_assistant_message = message["content"]
                break
        
        if last_assistant_message is None:
            print("No assistant message found to note")
            print("messages is " + str(messages))
            return messages, cursor_location, [Action.NO_ACTION]

        if not text.strip():
            print("Please provide a headline for the note")
            return messages, cursor_location, [Action.NO_ACTION]

        try:
            payload = {
                "comment_text": text.strip(),
                "transcription_text": last_assistant_message
            }
            
            response = requests.post(
                NoteCommand.ADD_ENDPOINT_URL, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Get the URL and ID from response
            child_id = response_data.get('child_id', '')
            url = f"https://cave.keychaotic.com:7878/transcriptionmd/{child_id}"
            
            printGrey("Note saved successfully!")
            printGrey(f"URL: {url}")
            printGrey(f"Created: {response_data.get('date_created', 'unknown date')}")
            print()


        except requests.exceptions.RequestException as e:
            print(f"Error saving note: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        return messages, cursor_location, [Action.NO_ACTION]

    @staticmethod
    def command_names() -> List[str]:
        return ["note"]
    
    @staticmethod
    def descriptions() -> List[str]:
        return ["Save last AI response as a note with headline (:note Your Headline Here)"] 