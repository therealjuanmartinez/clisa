from clisa.base.base_colon_command import BaseColonCommand, Action
import requests
from typing import List, Tuple
import json
import os
from clisa.jprinty import printGrey
from pathlib import Path

class NoteCommand(BaseColonCommand):
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "note_config.json")
    
    @staticmethod
    def load_config():
        if os.path.exists(NoteCommand.CONFIG_FILE):
            try:
                with open(NoteCommand.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def save_config(config):
        with open(NoteCommand.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def validate_server_connection(server, port, protocol):
        try:
            url = f"{protocol}://{server}:{port}/add_transcription"
            response = requests.options(url, timeout=5)
            return response.status_code == 200 or response.status_code == 405
        except:
            return False

    @staticmethod
    def execute(command: str, text: str, messages: List[dict], cursor_location: int, max_messages: int) -> Tuple[List[dict], int, List[Action]]:
        config = NoteCommand.load_config()
        
        # First-time setup or if config file doesn't exist
        if config is None:
            print("\nFirst-time setup for note command:")
            print("Please enter your note server configuration:")
            config = {}
            config["server"] = input("Server address: ").strip()
            config["port"] = input("Port: ").strip()
            config["protocol"] = input("Protocol (http/https): ").strip()
            
            if not all([config["server"], config["port"], config["protocol"]]):
                print("\nError: All configuration values must be provided")
                return messages, cursor_location, [Action.NO_ACTION]
            
            if not NoteCommand.validate_server_connection(config["server"], config["port"], config["protocol"]):
                print(f"\nError: Could not connect to {config['protocol']}://{config['server']}:{config['port']}")
                print("Please check your settings and try again.")
                return messages, cursor_location, [Action.NO_ACTION]
            
            NoteCommand.save_config(config)
            print("\nConfiguration saved successfully!")

        # Find the last assistant message
        last_assistant_message = None
        for message in reversed(messages[:cursor_location]):
            if message["role"] == "assistant":
                last_assistant_message = message["content"]
                break
        
        if last_assistant_message is None:
            print("No assistant message found to note")
            return messages, cursor_location, [Action.NO_ACTION]

        if not text.strip():
            print("Please provide a headline for the note")
            return messages, cursor_location, [Action.NO_ACTION]

        try:
            base_url = f"{config['protocol']}://{config['server']}:{config['port']}"
            payload = {
                "comment_text": text.strip(),
                "transcription_text": last_assistant_message
            }
            
            response = requests.post(
                f"{base_url}/add_transcription", 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Get the URL and ID from response
            child_id = response_data.get('child_id', '')
            url = f"{base_url}/transcriptionmd/{child_id}"
            
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
