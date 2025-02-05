import abc
import json
import jsonschema
from jsonschema import validate
import os


class ToolBase(abc.ABC):
    @property
    def name(self):
        try:
            # Load the function info and validate it
            info = self.function_info()
            functions = json.loads(info)

            if isinstance(functions, list):
                return [func["function"]["name"] for func in functions]
            else:
                print("Error: function_info did not return a list.")
                return []  # Return an empty list if the format is incorrect
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error processing function_info: {e}")
            return []  # Return an empty list in case of an error

    @staticmethod
    def function_info_schema():
        FUNCTION_INFO_SCHEMA = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["function"]},
                    "function": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "enum": ["object"]},
                                    "properties": {"type": "object"},
                                    "required": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["type", "properties"]
                            }
                        },
                        "required": ["name", "description", "parameters"]
                    }
                },
                "required": ["type", "function"]
            }
        }
        return FUNCTION_INFO_SCHEMA

    @abc.abstractmethod
    def execute(self, args_json: str, role_variables={}) -> str:
        """Method to execute the tool with given JSON arguments"""
        pass

    @staticmethod
    @abc.abstractmethod
    def function_info() -> str:
        """Method to provide the function information in JSON format"""
        pass

    @staticmethod
    @abc.abstractmethod
    def file_location() -> str:
        """Method to return the full path and file of the script"""
        pass

    @classmethod
    def validate_function_info(cls):
        """Validate the function_info JSON against the schema"""
        try:
            function_info = json.loads(cls.function_info())
            jsonschema.validate(instance=function_info, schema=cls.function_info_schema())
            print(f"Function info for {cls.__name__} is valid.")
            return True
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in function_info for {cls.__name__}")
        except jsonschema.exceptions.ValidationError as e:
            print(f"Error: Invalid function_info schema for {cls.__name__}: {e}")
        return False

    @classmethod
    def main(cls):
        """Main method to execute the tool, testing a basic test case or two, depending on requirements."""
        if cls.validate_function_info():
            # Proceed with tool execution
            tool = cls()
            # Example test case (should be overridden by subclasses)
            test_case = json.dumps({"example": "test"})
            result = tool.execute(test_case)
            print(f"Test case result: {result}")
        else:
            print(f"Cannot proceed with {cls.__name__} due to invalid function_info.")

    @staticmethod
    def validate_json_format(json_data: str, schema: dict) -> str:
        """
        Validates the given JSON string against the provided schema.

        :param json_data: JSON string to validate.
        :param schema: JSON schema to validate against.
        :return: Error message if invalid, or success message if valid.
        """
        try:
            # Attempt to load the JSON data
            data = json.loads(json_data)

            # Validate against the schema
            validate(instance=data, schema=schema)
            return "Valid JSON format."
        except json.JSONDecodeError as e:
            return f"Invalid JSON format: {str(e)}"
        except jsonschema.exceptions.ValidationError as e:
            return f"JSON does not conform to schema: {str(e)}"

    @staticmethod
    def function_info_schema() -> dict:
        """
        Returns the schema for function info validation.
        This should be defined according to the expected structure of function info.
        """
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "function": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "action": {
                                        "type": "string",
                                        "enum": ["query", "get_amd_query_patterns"],
                                        "description": "Action to perform: query JIRA or get AMD query patterns"
                                    },
                                    "query": {"type": "string"},
                                    "url": {"type": "string"},
                                    "max_results": {"type": "integer"},
                                    "use_query_builder": {"type": "boolean"},
                                    "query_type": {"type": "string"},
                                    "program_code": {"type": "string"}
                                },
                                "required": ["action"]
                            }
                        },
                        "required": ["name", "description", "parameters"]
                    }
                },
                "required": ["type", "function"]
            }
        }
