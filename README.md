# AI Assistant

## Overview

This program is a sophisticated AI assistant that integrates with various models to process and respond to user inputs. It can handle text, URLs, and images, providing responses based on the context or a set of predefined rules.

THIS DOCUMENTATION IS AI GENERATED ONLY FROM AI.PY AND IS NOT IN ANY WAY COMPLETE

## Features

- **Model Selection**: Users can specify the model to use via command-line arguments, allowing flexibility in responses depending on the model's capabilities.
- **Input Modes**: Supports text and URL inputs. URLs are fetched, and their text content is extracted and used as input.
- **Oneshot Mode**: Executes a single query and exits, useful for scripting or when only a single response is needed.
- **File Operations**: Conversations can be saved to or loaded from files, allowing persistent states or reviewing past interactions.
- **Image Processing**: Can handle image inputs by encoding them in base64, allowing the model to process visual information.
- **Custom Commands**: Includes several custom commands (e.g., changing models, setting parameters) which can be triggered via specific command-line inputs.
- **Error Handling**: Basic error handling for requests, with retries and error logging.

## Usage

1. **Installation and Setup**:
   - Ensure Python 3.x is installed.
   - Install required packages: `requests`, `bs4`, `PIL`, `readchar`, `rich`.

2. **Command-Line Arguments**:
   - `-h, --help`: GET FULL LIST OF ARGUMENTS SINCE GPT-4 DECIDED TO PROVIDE A REDUX VERSION IN THIS FILE
   - `-m, --model`: Specify the model version.
   - `-u, --url`: Fetch text from a URL to use as input.
   - `-o, --oneshot`: Perform a single interaction and exit.
   - `-f, --filename`: Specify a file to load the conversation from.
   - Other flags for specific functionalities (refer to the source code for all options).

3. **Running the Program**:
   - Run the script from the command line with desired arguments.
   - Follow on-screen prompts to interact with the AI.

4. **Interacting with the AI**:
   - Input text directly or use commands like `:url [URL]` to fetch content from a URL.
   - Use `:m [model_name]` to switch models on the fly.
   - Save outputs or sessions using the `:o [filename]` command.

## Configuration

The `config` section in the script can be modified to change default settings like default model, temperature settings, etc.

## Extending Functionality

- **Adding New Models**: Integrate additional models by updating the `init_assistant()` function.
- **Custom Commands**: Extend or modify custom command handling in the `while True:` loop of the main program.

## Limitations

- Dependent on external services for model responses.
- Handles basic text and image inputs but might need updates to handle more complex scenarios or newer data formats.

## License

Specify the license under which the code is released, ensuring users know their rights regarding the use, modification, and distribution of the software.
