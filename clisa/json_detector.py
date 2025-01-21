import json
import re


class JSONDetector:
    @staticmethod
    def could_be_json(s):
        s = s.strip()
        if not (s.startswith("{") or s.startswith("[")):
            return False

        stack = []
        in_string = False
        escaped = False

        for i, char in enumerate(s):
            if not in_string:
                if char in "{[":
                    stack.append(char)
                elif char in "]}":
                    if not stack or (stack[-1] + char) not in ["{}", "[]"]:
                        return False
                    stack.pop()
                elif char == '"':
                    in_string = True
            else:
                if char == '"' and not escaped:
                    in_string = False
                elif char == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False

            # If stack is empty and we're at the end of the string, check for trailing characters
            if not stack and i < len(s) - 1:
                remaining = s[i + 1 :].strip()
                if remaining:
                    return False

        # Make sure the stack is empty, indicating all braces/brackets closed properly
        return True

    @staticmethod
    def is_valid_json(s):
        try:
            result = json.loads(s)
            try:
                result = json.loads(result)
            except:
                if isinstance(result, (dict, list)):
                    return True
                return False

            # Check if the result is a dict or list (JSON object or array)
            if isinstance(result, (dict, list)):
                return True
            else:
                return False
        except json.JSONDecodeError:
            return False

    @staticmethod
    def could_be_multiple_sets_of_json(s: str) -> bool:
        # Remove leading whitespace
        s = s.lstrip()

        # Check if the string is empty after removing whitespace
        if not s:
            return False

        # Check if the string starts with '{' or '['
        if s[0] not in "{[":
            return False

        # Check for invalid characters before the first '{' or '['
        valid_start = re.match(r"^[\s\n]*[\{\[]", s)
        if not valid_start:
            return False

        return True

    @staticmethod
    def contains_valid_json_within_larger_string(s):
        for i in range(len(s)):
            for j in range(i + 1, len(s) + 1):
                if JSONDetector.is_valid_json(s[i:j]):
                    return True
        return False

    @staticmethod
    def extract_array_of_json_strings_from_larger_string(input_string):
        # This regex pattern will match most JSON objects and arrays in the string
        json_pattern = re.compile(r"({.*?}|[\[].*?[\]])", re.DOTALL)
        potential_json_strings = json_pattern.findall(input_string)

        json_strings = set()

        for potential_json in potential_json_strings:
            try:
                # Try to parse the potential JSON string
                parsed_json = json.loads(potential_json)
                # If successful, add the original string to the set
                json_strings.add(potential_json)
            except json.JSONDecodeError:
                # If parsing fails, it's not a valid JSON, so we skip it
                continue

        return list(json_strings)


def main():
    import sys

    input_data = sys.stdin.read().strip()

    detector = JSONDetector()

    if detector.is_valid_json(input_data):
        print("Valid JSON")
    elif detector.could_be_json(input_data):
        print("Potentially valid partial JSON")
    else:
        print("Not JSON")


if __name__ == "__main__":
    main()
