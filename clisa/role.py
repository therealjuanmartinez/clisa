class Task:
	def __init__(self, directive, description, tools, model=None, state="pending"):
		self.directive = directive
		self.description = description
		self.tools = tools
		self.model = model  # New attribute for specifying the model
		self.state = state  # e.g., "pending", "in-progress", "completed"

	def update_state(self, new_state):
		self.state = new_state

	def to_dict(self):
		return {
			"directive": self.directive,
			"description": self.description,
			"tools": self.tools,
			"model": self.model,
			"state": self.state
		}


class Mission:
	def __init__(self, name, description):
		self.name = name
		self.description = description
		self.tasks = []  # List of Task objects

	def add_task(self, directive, description, tools, model=None):
		task = Task(directive, description, tools, model)
		self.tasks.append(task)

	def get_task_by_directive(self, directive):
		for task in self.tasks:
			if task.directive == directive:
				return task
		return None

	def get_tasks(self):
		return self.tasks

	def to_dict(self):
		return {
			"name": self.name,
			"description": self.description,
			"tasks": [task.to_dict() for task in self.tasks]
		}


class Role:
	def __init__(self, name):
		self.name = name
		self.missions = []  # List of Mission objects
		self.system_prompt_collection = []
		self.system_prompt_texts = []
		self.tools = []
		self.initial_prompt = ""
		self.system_prompt = ""
		self.rolefile = ""
		self.current_mission_cursor = None  # New attribute for mission cursor
		self.current_task_cursor = None  # New attribute for task cursor
		self.variables = {} #this is a dictionary that will store the variables for the role

	def add_mission(self, name, description):
		mission = Mission(name, description)
		self.missions.append(mission)
		return mission

	def get_mission(self, name):
		for mission in self.missions:
			if mission.name == name:
				return mission
		return None

	def get_current_mission(self):
		for mission in self.missions:
			if get_current_mission_cursor() is not None and mission.name == get_current_mission_cursor():
				return mission
		return None
		

	def get_task(self, directive):
		for mission in self.missions:
			task = mission.get_task_by_directive(directive)
			if task:
				return task
		return None

	def load_from_yaml(self, yaml_data, role_file):
		self.name = yaml_data['name']
		self.system_prompt_collection = yaml_data.get('system_prompt_collection', [])
		self.system_prompt_texts = yaml_data.get('system_prompt_texts', [])
		self.tools = yaml_data.get('tools', [])
		self.initial_prompt = yaml_data.get('initial_prompt', "")
		self.system_prompt = yaml_data.get('system_prompt', "")
		self.rolefile = role_file

		for mission_data in yaml_data.get('missions', []):
			mission = self.add_mission(mission_data['name'], mission_data['description'])
			for task_data in mission_data.get('tasks', []):
				mission.add_task(
					task_data['directive'],
					task_data['description'],
					task_data.get('tools', []),
					task_data.get('model')  # New parameter for model
				)

	def set_current_mission_cursor(self, mission_name):
		if mission_name is None:
			self.current_mission_cursor = None
			return
		mission = self.get_mission(mission_name)
		if mission is not None:
			self.current_mission_cursor = mission_name
		else:
			raise ValueError("Mission name does not match any existing missions.")

	def set_current_task_cursor(self, task_index):
		if (task_index == -1):
			self.current_task_cursor = task_index
		elif (task_index is None):
			self.current_task_cursor = None
		elif self.current_mission_cursor is not None:
			mission = self.get_mission(self.current_mission_cursor)
			#if -1 <= task_index < len(self.missions[self.current_mission_cursor].tasks):
			if -1 <= task_index < len(mission.tasks):
				self.current_task_cursor = task_index
			else:
				raise IndexError("Task index out of range for the current mission's tasks.")
		else:
			raise RuntimeError("Set mission cursor before setting task cursor.")

	def get_current_mission_cursor(self):
		return self.current_mission_cursor

	def get_current_task_cursor(self):
		return self.current_task_cursor

	def to_dict(self):
		return {
			"name": self.name,
			"system_prompt_collection": self.system_prompt_collection,
			"system_prompt_texts": self.system_prompt_texts,
			"tools": self.tools,
			"initial_prompt": self.initial_prompt,
			"initial_prompt": self.system_prompt,
			"rolefile": self.rolefile,
			"missions": [mission.to_dict() for mission in self.missions],
			"current_mission_cursor": self.current_mission_cursor,  # Include mission cursor in dict
			"current_task_cursor": self.current_task_cursor  # Include task cursor in dict
		}
