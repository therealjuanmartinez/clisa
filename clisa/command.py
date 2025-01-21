class Command:
	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super(Command, cls).__new__(cls)
		return cls._instance

	def __init__(self, name, description):
		if not hasattr(self, 'initialized'):  # Prevent reinitialization
			self.name = name
			self.description = description
			self.params = {}
			self.initialized = True
			self.state = {}

	def execute(self, messages, metadata):
		"""
		Process the command with the given messages and metadata.

		:param messages: List of message dictionaries.
		:param metadata: Additional information required for execution.
		:return: A tuple with (status, modified_messages, processed_text, remaining_text).
		"""
		raise NotImplementedError("Subclasses must implement this method.")

	def get_name(self):
		"""Return the name of the command."""
		return self.name

	def get_state(self):
		return self.state

	def set_state(self, state):
		self.state = state

	def clear_state(self):
		self.state.clear()
	
	def get_description(self):
		"""Return the description of the command."""
		return self.description

class InjectTextCommand(Command):
	def __init__(self, text_to_inject):
		super().__init__(name="inject_text", description="Injects specified text into the last user message.")
		self.text_to_inject = text_to_inject

	def execute(self, messages, metadata):
		if not messages or messages[-1]['role'] != 'user':
			return 'error', messages, '', self.text_to_inject

		messages[-1]['content'] += f" {self.text_to_inject}"
		return 'success', messages, self.text_to_inject, ''
