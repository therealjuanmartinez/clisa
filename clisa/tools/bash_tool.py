from clisa.base.tool_base import ToolBase
import json
import subprocess
import time
import shlex
import os
import re

class BashCommandTool(ToolBase):
	def execute(self, args_json: str, role_variables={}) -> str:
		args = json.loads(args_json)
		if 'function' in args:
			print("FUNCTION WAS IN ARGS AND IT IS " + args['function'])

		if 'command' not in args:
			return json.dumps({"error": "Missing required parameter: command"})

		for key, value in role_variables.items():
			print(f"{key}: {value}")

		command = args['command']
		timeout_limit = args.get('timeout_limit', 60)  # Default timeout limit is set to 60 seconds

		# Check for simple SSH command
		if re.match(r'^ssh\s+(\S+|\S+@\S+)$', command):
			return json.dumps({"error": "persistent SSH sessions not supported, this is a blocking command, no blocking commands, please."})

		# Check if the command requires sudo
		if command.startswith("sudo"):
			if not self.check_sudo():
				return json.dumps({"error": "Sudo command requires sudo to be available. Please run sudo locally."})

		try:
			process = subprocess.Popen(
				command,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				shell=True,
				text=True
			)

			start_time = time.time()
			stdout_lines = []
			while process.poll() is None:
				if time.time() - start_time > timeout_limit:
					process.kill()
					return json.dumps({"error": f"Command execution timed out after {timeout_limit} seconds"})
				time.sleep(0.1)

			stdout, stderr = process.communicate()

			execution_time = round(time.time() - start_time, 3)

			return json.dumps({
				"stdout": stdout,
				"stderr": stderr,
				"returncode": process.returncode,
				"execution_time": execution_time
			})

		except subprocess.SubprocessError as e:
			return json.dumps({"error": f"Command execution failed: {str(e)}"})
		except Exception as e:
			return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

	def check_sudo(self) -> bool:
		try:
			subprocess.run("sudo -v", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			return True
		except subprocess.CalledProcessError:
			return False

	@staticmethod
	def function_info() -> str:
		function_info = [
			{
				"type": "function",
				"function": {
					"name": "execute_bash_command",
					"description": "Local WSL2 Env - execute a Bash command and return its output - take care not to run anything with blocking UI input",
					"parameters": {
						"type": "object",
						"properties": {
							"command": {
								"type": "string",
								"description": "The Bash command to execute, including pipes and other shell features",
							},
							"timeout_limit": {
								"type": "integer",
								"description": "Timeout limit in seconds for command execution",
							},
						},
						"required": ["command"],
					},
				}}]
		return json.dumps(function_info)

	@staticmethod
	def file_location() -> str:
		return os.path.abspath(__file__)
