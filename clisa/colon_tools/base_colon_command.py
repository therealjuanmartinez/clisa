from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Any, Optional

class Action(Enum):
	REFRESH_MESSAGES = 1
	REFRESH_COLON_FILES = 3
	NO_ACTION = 2
	SET_CONVERSATION_TITLE = 4  # New action for setting terminal title

class ActionResult:
	def __init__(self, action: Action, value: Any = None):
		self.action = action
		self.value = value

class BaseColonCommand(ABC):
	def __init__(self, command: str, text: str, messages: List[dict], cursor_location: int, max_messages: int):
		self.command = command
		self.text = text
		self.messages = messages
		self.cursor_location = cursor_location
		self.max_messages = max_messages  

	@staticmethod
	@abstractmethod
	def execute(command: str, text: str, messages: List[dict], cursor_location: int, max_messages: int) -> Tuple[List[dict], int, List[ActionResult]]:
		pass
	
	@staticmethod
	@abstractmethod
	def command_names() -> List[str]:
		pass
	
	@staticmethod
	@abstractmethod
	def descriptions() -> List[str]:
		pass

class CustomCommand(BaseColonCommand):
	@staticmethod
	def execute(command: str, text: str, messages: List[dict], cursor_location: int, max_messages: int) -> Tuple[List[dict], int, List[ActionResult]]:
		print(f"Executing command: {command} with text: {text}")
		actions = [ActionResult(Action.REFRESH_MESSAGES)]
		return messages, cursor_location, actions
	
	@staticmethod
	def command_names() -> List[str]:
		return ["mycommand", "mycommand2"]
	
	@staticmethod
	def descriptions() -> List[str]:
		return "This command does something useful with the provided text."

if __name__ == "__main__":
	messages = [{"role": "user", "content": "Hello!"}]
	cursor_location = 0
	max_messages = 5  

	updated_messages, updated_cursor, actions = CustomCommand.execute(":mycommand", "thing thing2", messages, cursor_location, max_messages)

	print("Updated Messages:", updated_messages)
	print("Updated Cursor Location:", updated_cursor)
	print("Actions to Perform:", actions)
	print("Command Description:", CustomCommand.description())
	print("Command Names:", CustomCommand.command_names()) 
