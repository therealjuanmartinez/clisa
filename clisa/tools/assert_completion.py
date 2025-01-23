import datetime
from clisa.tools.tool_base import ToolBase
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # This goes up two levels: from tools/assert_completion.py to clisa/

class AssertCompletion(ToolBase):
	def execute(self, args_json: str, role_variables: dict = {}) -> str:
		try:
			args = json.loads(args_json)
			if 'tasks' not in args:
				return json.dumps({"error": "Missing required parameter: tasks"})

			#for key, value in role_variables.items():
			#	print(f"{key}: {value}")

			#see if task_id is in role_variables and is set
			try:
				task_id = int(role_variables.get('task_id'))
				print("task_id: " + str(task_id))
			except:
				task_id = None
		
			tasks = args['tasks']
			if not isinstance(tasks, list):
				tasks = [tasks]

			results = []
			for task in tasks:
				if 'name' not in task or 'requirements' not in task or 'accomplishment' not in task:
					return json.dumps({"error": f"Invalid task structure: {task}"})
				
				results.append({
					"task_name": task['name'],
					"requirements_met": task['requirements'],
					"accomplishment": task['accomplishment'],
					"status": "completed"
				})
				try:
					results.append(
						{ "info": task['information'], }
					)
				except:
					pass
				#is it an int? if so, check existance of task_id in tasks table in tasks.db (sqlite3)
				if task_id:
					#check if task_id exists in tasks table
					#does file exist
					db_path = BASE_DIR/'tasks.db'
					if os.path.exists(db_path):
						#open file
						import sqlite3
						conn = sqlite3.connect(db_path)
						c = conn.cursor()
						c.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
						if c.fetchone() is None:
							print("Could not find id of " + str(task_id) + " in tasks table\n")
						else:
							print("Found id of " + str(task_id) + " in tasks table\n")
							#now update it with the accomplishment/requiremnets_met etc etc, and last_udpated to now
							#    id INTEGER PRIMARY KEY,
							#directive TEXT NOT NULL,
							#status BOOLEAN DEFAULT 0,
							#output TEXT DEFAULT ''
							#last_updated - should be YYYY-MM-DD HH:MM:SS
							now_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							c.execute('UPDATE tasks SET status=1, output=output || " - " || ?, last_updated=? WHERE id=?', (json.dumps(results), now_ts, task_id))
							conn.commit()
							# Check the number of rows affected
							if c.rowcount > 0:
								print(f"Successfully updated task with ID {task_id}.")
							else:
								print(f"No task found with ID {task_id}. No updates were made.")
							conn.close()
							#now end the entire python program, as in, from here, do it

							#ok so there may be a role_variables.get("pid") that is set, if so, we need to kill that process
							try:
								#kill like SIGTERM this process w/o specifying pid
								import signal
								os.kill(os.getpid(), signal.SIGTERM)	
							except:
								pass
						
						conn.close()
				else:
					try:
						#print all role_variables here
						print("all role vars")
						for key, value in role_variables.items():
							print(f"{key}: {value}")
						do_kill = (role_variables.get('die_on_assert'))
						if (do_kill):
							import signal
							os.kill(os.getpid(), signal.SIGTERM)	
						else:
							print("not dying on assert...")
					except:
						pass

			return 'Thank you for asserting completion. USER has not seen your tool calls nor any responses you have received. Please proceed to the next task'
		except json.JSONDecodeError:
			return json.dumps({"error": "Invalid JSON input"})
		except Exception as e:
			return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

	@staticmethod
	def function_info() -> str:
		function_info = [
			{
				"type": "function",
				"function": {
					"name": "assert_completion",
					"description": "Assert completion of one or more tasks, including requirements met and accomplishments",
					"parameters": {
						"type": "object",
						"properties": {
							"tasks": {
								"type": "array",
								"items": {
									"type": "object",
									"properties": {
										"name": {
											"type": "string",
											"description": "The name of the task"
										},
										"requirements": {
											"type": "array",
											"items": {
												"type": "string"
											},
											"description": "List of requirements that were met for this task"
										},
										"accomplishment": {
											"type": "string",
											"description": "Description of how the task was accomplished"
										},
										"information": {
											"type": "string",
											"description": "If any information was retrieved, please provide it all clearly and succinctly here"
										}
									},
									"required": ["name", "requirements", "accomplishment"]
								},
								"description": "List of tasks to assert completion for"
							}
						},
						"required": ["tasks"]
					}
				}
			}
		]
		return json.dumps(function_info)

	@staticmethod
	def file_location() -> str:
		return os.path.abspath(__file__)

	@classmethod
	def main(cls):
		if cls.validate_function_info():
			print("Function info validation successful.")

			tool = cls()

			# Test case for a single task
			single_task_args = json.dumps({
				"tasks": {
					"name": "Implement AssertCompletion tool",
					"requirements": ["Create execute method", "Create function_info method"],
					"accomplishment": "Implemented all required methods and tested functionality"
				}
			})

			# Test case for multiple tasks
			multiple_tasks_args = json.dumps({
				"tasks": [
					{
						"name": "Implement AssertCompletion tool",
						"requirements": ["Create execute method", "Create function_info method"],
						"accomplishment": "Implemented all required methods and tested functionality"
					},
					{
						"name": "Write documentation",
						"requirements": ["Explain usage", "Provide examples"],
						"accomplishment": "Created comprehensive README with usage instructions and examples"
					}
				]
			})

			print("Testing single task:")
			result_single = tool.execute(single_task_args)
			print(result_single)

			print("\nTesting multiple tasks:")
			result_multiple = tool.execute(multiple_tasks_args)
			print(result_multiple)

		else:
			print("Function info validation failed. Please check the schema.")

if __name__ == "__main__":
	AssertCompletion.main()
