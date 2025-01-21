#!/usr/bin/env python3 
import json
import requests
#from unittest.util import _MAX_LENGTH
import os
import time,sys
#import openai as openai #not needed for gpt-4 / 'modern' API calls, seemingly
import datetime
import glob
import string
import subprocess
import shutil
import re
#from openai import OpenAI
import base64
import traceback
import threading
import termios
import tty
import signal
import select
import socket

#from assistant import (
#    Assistant,
#    DEFAULT_ASSISTANTS,
#    AssistantGlobalArgs,
#    init_assistant,
#)
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from clisa.json_detector import JSONDetector
from rich.table import Table

from rich.progress import SpinnerColumn, Progress, TextColumn
from rich.text import Text
from rich.panel import Panel

import uuid
import tempfile

from itertools import groupby
from operator import itemgetter

from clisa.colon_tools.base_colon_command import BaseColonCommand
from clisa.command import Command  # Import the base Command class

import importlib.util
import importlib
import inspect  
import yaml
from pathlib import Path

from clisa.streaming_socket_server import StreamingSocketServer

from clisa.jprinty import *

from clisa.custom_exceptions import (
    LLMOutputNotValidJSONError,
    LLMRepeatJSONTwiceError,
    LLMDotMessageError,
    LLMRepetitiveResponseError,
    LLMEndConversationError,
    ExitWithCodeException
)

from clisa.role import Role
from bs4 import BeautifulSoup, Comment
from PIL import Image
from colorama import Fore, Style
import curses

import yaml
import jsonschema
from jsonschema import validate

from clisa.role import Role  # Make sure this import is at the top of ai.py

#AI TODO we need to add the feature such that when we use new feature :XXXXX it also disables {{}}

BASE_DIR = Path(__file__).resolve().parent

TOOLS_TOP_DIR=BASE_DIR/"tools"
files_cursor = 0
tool_instances = []  # Global array to hold instances of tools
force_tools_flag = False  # Add this line here
#AI a good place to add globals

homedir = os.path.expanduser("~")
conversationDirectory = homedir + "/conversations/"

loaded_role = None

#AI feat when performing a mission, default to no blocking or hit enter to continue or something, maybe that is a mode that can be set....  i was thinking param to the command, but, that seems inappropriate

#AI this begins the list of in-line run-time commands with their descriptions
commands = [
    {"command": ":q!", "description": "hard quit"},
    {"command": ":vij", "description": "edit conversation (json)"},
    {"command": ":sr", "description": "speedread the response"},
    {"command": ":vi", "description": "vi mode for entering text"},
    {"command": ":s", "description": "search (usage :s [term]) first by [term].*.json in current directory and then by general JSON files collection content"},
    {"command": ":bash", "description": "drop to bash prompt for a moment"},
    {"command": ":add", "description": "erase last assistant message, append any text after ':add' to the end of the last user message, and re-send"},
    {"command": ":redo", "description": "erase last assistant message, edit previous message, and re-send. (or type text after ':redo' and that text becomes the new redo message. if you change your mind, exit editor w/o changes)"},
    {"command": ":r", "description": "respond to the response using same model, or specify model optionally to respond with"},
    {"command": ":multi", "description": "multiline mode for text entry, press CTRL+D when done"},
    {"command": ":wc", "description": "save last assistant message to colon file (provide colon name)"},
    {"command": ":wca", "description": "append last assistant message to colon file (provide colon name)"},
    {"command": ":wm", "description": "save last assistant message to file (provide filename)"},
    {"command": ":wma", "description": "append save last assistant message to file (provide filename)"},
    {"command": "genimage", "description": "Perform Dalle3 image generation based on last 4000 characters of the conversation and place in Windows clipboard"},
    {"command": ":?", "description": "display help menu, or :? [question] to ask the AI about these commands"},
    {"command": ":nopaste", "description": "turn off paste mode"},
    {"command": ":paste", "description": "turn on paste mode (from CLI, can paste w/o text getting mangled)"},
    {"command": ":x", "description": "only use last 'x' messages (provide #) to reduce context window"},
    {"command": ":w", "description": "Write current conversation to a file in JSON"},
    {"command": ":o", "description": "Write current conversation to a file in plain text"},
    {"command": ":m", "description": "Specify Model"},
    {"command": ":c", "description": "Copy to new file"},
    {"command": ":t", "description": "Specify temperature"},
    {"command": ":url", "description": "provide URL to convert to text as user input"},
    {"command": ":e", "description": "Erase last X messages"},
    {"command": ":tools", "description": "List Active Tools (can also specify # of tool to activate or deactivate)"},
    {"command": ":toolsall", "description": "Show all tools including disabled"}, #AI bug this doesnt work at all, but if i --tools google -p "get btc price" and after that THEN run this it works fine
    {"command": ":notools", "description": "Disable all tools"},
    {"command": ":first", "description": "Go to top of conversation"},
    {"command": ":savetools <filename>", "description": "Save active tools to the specified file"},
    {"command": ":loadtools <filename>", "description": "Load tools from the specified file"},
    {"command": ":toolsjust list of tools", "description": "Load tools exclusively"},
    {"command": ":last", "description": "Go to bottom of conversation"},
    {"command": ":remresp", "description": "permanently remove last tool response to save tokens"},
    {"command": ":alltools", "description": "Enable all tools"},
    {"command": ":onlytools", "description": "Enable only tools"},
    {"command": ":noonlytools", "description": "disEnable only tools"},
    {"command": ":system", "description": "View LLM system message"},
    {"command": ":sysedit", "description": "Edit LLM system message"},
    {"command": ":role", "description": "view role info or provide role name to load role"},
    {"command": ":rolesave", "description": "save current toolset to current role"},
    {"command": ":roleedit", "description": "edit currently loaded role file"},
    {"command": ":rolelist", "description": "list all roles"},
    {"command": ":nobash", "description": "disable {{[command]}} style bash command string replacement functionality"},
    {"command": ":yesbash", "description": "enable {{[command]}} style bash command string replacement functionality"},
    {"command": ":vars", "description": "list role variables, or provide key=value,key2=value2 list after command to set",},
    {"command": ":hint", "description": "with role loaded, you can use this command followed by text for your hint to append to that role",},
    {"command": ":scribe", "description": "Connect/reconnect to the transcription server, making this instance the sole consumer of the REC+SEND button in the Android app",},
    {"command": "image=", "description": "Deprecated? Uses image filename for vision prompt"},
    {"command": "images=", "description": "specify # of images along with prompt, will pull latest file(s) from /dev/shm/"},
]


#AI feat add command to rerun last tool call and heck maybe even with a old=new after the command to do replacements 

# Initialize content dictionary
content_dict = {}
colon_command_modules = []


def loadColonStrings():
    # Iterate through .colon files in the specified directory
    global content_dict
    content_dict = {}
    for filename in os.listdir(TOOLS_TOP_DIR):
        if filename.endswith('.colon'):
            command_name = f":{filename[:-6]}"  # Remove the .colon extension
            #description = f"insert {filename[:-6]} text before message that follows from user"
            description = f"insert {filename} text before message that follows from user"

            # Read the content of the file
            with open(os.path.join(BASE_DIR/"tools/", filename), 'r') as file:
                content = file.read()

            # Add the command to the commands array
            commands.append({"command": command_name, "description": description, "tool_color": "yellow", "desc_color" : "brown"}) #it totally is gray not brown

            # Store the content in the content dictionary
            content_dict[filename[:-6]] = content

def loadColonCommands():
    import inspect
    for filename in os.listdir(BASE_DIR/"colon_tools"):
        try:
            if filename.endswith('.py') and "base_colon_command" not in filename:
                #it is a class, load
                    unique_module_name = f"module_{uuid.uuid4().hex}"

                    # Load the module
                    #print("aobut to load full path is " + dirr + "/" + file)
                    spec = importlib.util.spec_from_file_location(unique_module_name, BASE_DIR/"colon_tools/" + filename)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # List all attributes of the module
                    attributes = dir(module)

                    # Filter out the classes
                    colclasses = [getattr(module, attr) for attr in attributes if isinstance(getattr(module, attr), type)]

                    # Filter out the abstract classes
                    colclasses = [cls for cls in colclasses if not inspect.isabstract(cls)]

                    if (len(colclasses) == 0):
                        pass

                    for myclass in colclasses:
                        #print("myclass is " + str(myclass))
                        try:
                            unique_module_name = f"module_{uuid.uuid4().hex}"
                            try:
                                #check for actual class type of myclass and does it have command_names
                                if hasattr(myclass, 'command_names'):
                                    colon_command_modules.append(myclass)

                                #if (myclass.command_names): #TODO check for actual class type dont rely on command_names
                                    colon_command_modules.append(myclass)
                            except Exception as e:
                                print(str(e))
                                pass
                            #print(myclass.file_location())
                        except Exception as e:
                            print(str(e))
                            pass
        except Exception as e:
            print(str(e))
            pass


#AI if loading a role we dont need to load tools first

global syscontent_dict
syscontent_dict = {}
def loadSysColons():
    # Iterate through .colon files in the specified directory
    text = ""
    for filename in os.listdir(BASE_DIR/"tools"):
        if filename.endswith('.syscolon'):
            command_name = f":{filename[:-9]}"  # Remove the .colon extension
            #description = f"append [{filename[:-9]}] text to system message"
            description = f"append {filename} text to system message"

            content = ""
            # Read the content of the file
            with open(os.path.join(BASE_DIR/"tools/", filename), 'r') as file:
                content = file.read()

            # Add the command to the commands array
            commands.append({"command": command_name, "description": description, "tool_color": "red", "desc_color" : "brown"})

            syscontent_dict[filename[:-9]] = content


def backupFile(filename):
    # Check if the file exists
    if not os.path.isfile(filename):
        return False  # File does not exist, backup cannot be performed

    # Define initial backup filename
    backup_filename = filename + ".1"

    # Check if backup files already exist and find the highest number
    i = 1
    while os.path.isfile(filename + f".{i}"):
        i += 1

    # Rename existing backups to shift them up
    for j in range(i - 1, 0, -1):
        if os.path.isfile(filename + f".{j}"):
            os.rename(filename + f".{j}", filename + f".{j + 1}")

    # Set the new backup filename to .1
    backup_filename = filename + ".1"

    # Perform the backup
    try:
        shutil.copy2(filename, backup_filename)  # Copy with metadata
        return True  # Backup successful
    except Exception as e:
        print(f"An error occurred during backup: {e}")
        return False  # Backup failed

# Directory containing he .txt files
syspdirectory = BASE_DIR/'tools/sysfile'
#AI this begins the parser.add_argument list
import argparse
parser = argparse.ArgumentParser(description='')
parser.add_argument('--sysfile', '-sf', type=str, help='Specify a system (prompt) file (e.g., whatever) to load from '+str(BASE_DIR/'sysfile/'))
parser.add_argument('--sysfile_list', action='store_true', help=f'List all available system prompts in {syspdirectory} and exit')
parser.add_argument('--sysfile_edit', '-sfe', type=str, help='edit a system file in vi')
parser.add_argument('-m', '--model', type=str, default="4m", help='[OPTIONAL DO NOT USE] Model to use, 3.5 or 4, or full name')
parser.add_argument('-r', '--role', type=str, help='Load Role by name')
parser.add_argument('-re', '--role_edit', type=str, help='Load Role by name')
parser.add_argument('--role_list', '-rl', action='store_true', help='List all available roles and exit')
parser.add_argument('--models', action='store_true', help='list models then exit')
parser.add_argument('-t', '--temperature', type=float, default=0.7, help='[DO NOT USE] Temperature, 0.0 to 2.0, higher is more random')
parser.add_argument('--system', "-sys", type=str, default="", help='Prompt to setup the nature of the AI - THIS GOES TO SYSTEM MESSAGE')
parser.add_argument('-p', '--prompt', type=str, default="", help='Prompt')
parser.add_argument('-o', '--oneshot', action='store_true', help='One Shot Mode, only one back/forth cycle and only prints AI response')
parser.add_argument('-u', '--url', type=str, default="", help='Include content from URL as part of prompt')
parser.add_argument('-s', '--searchterm', type=str, default=None, help='Search term to filter old conversations by (to use with -c option)')
parser.add_argument('-f', '--filename', type=str, default="", help='Filename to load conversation from')
parser.add_argument('-x', '--max', type=float, default=0, help='How many back/forth cycles back to go (always includes the setup prompt)')
parser.add_argument('-jo', type=str, default=None, help='Output JSON to file')
parser.add_argument('-jou', type=str, default=None, help='Output JSON to file and force last message to be from user (forces oneshot)')
parser.add_argument('-oc', '--outputcode', action='store_true', help='does a oneshot in command output mode and outputs to stdout')
parser.add_argument('-ocf', '--outputcodefile', type=str, help='does a oneshot in command output mode and outputs to specified file')
parser.add_argument('--socket', type=int, help='Start streaming tcpip server on specified port during each response')
parser.add_argument('--nc', action='store_true', help='NC Mode')
parser.add_argument('--identity', type=str, help='The identity of the agent (e.g., Harry, ClimateChangeActivist)')
parser.add_argument('--toolsfile', '-tf', type=str, help='Load Tools File, just a list of partial or whole tool names')
parser.add_argument('--onlytools', action='store_true', help='force tools only')
parser.add_argument('--default', action='store_true', help='Use Instructions from file "ai_default.txt"')
parser.add_argument('--usecomments', action='store_true', help='Use comments starting with # from stdin in the prompt')
#now one for generating an image, take in prompt from user
parser.add_argument('--image', type=str, default="" , help='Image Generation Mode, include prompt from user')
parser.add_argument('--size', type=int, default="1" , help='Image Size, 1=1024x1024, 2=1024x1792, 3=1792x1024')
parser.add_argument('-l', '--last_conversation', action='store_true', help='Open directly to last conversation, this can be used to pipe input from stdin as a new message in the last conversation')
parser.add_argument('--procimage', type=str, default="" , help='Process an image, include path to image')
parser.add_argument('--nostdinprint', action='store_true', help='when set, suppress printing of stdin before processing')
#do a tools arr tht takes multiple marams
parser.add_argument('--tools', nargs='+', help='list of one or more tool names (same as what would match when using :tools command in the program to search for available tools)')         
parser.add_argument('--notools', action='store_true', help='No tools will be loaded')
parser.add_argument('--nobash', action='store_true', help='No {{[command]}} bash command string replacement functionality')
parser.add_argument('--tlist', action='store_true', help='List all tools and exit')
parser.add_argument('-doa', '--die_on_assert', action='store_true', help='Kill process after assert_completion')
parser.add_argument('-rv', '--role_variables', type=str, help='Set role variables (key=value,key2=value2) - can use spaces in values if string is put in quotes')
parser.add_argument('--no_transcription', '-nt', action='store_true', help='Do not connect to transcription server')





def generate_remote_control_json():
    # Generate the JSON object for the remote control
    # so, we will have buttons and switches (and siwtches to have default values) so 
    # we will have a list of buttons, each button will have a name and a command
    # same for list of switches, then default to on or off for each
    # Also, some buttons will be for recording, and some will not, so that is a is_recording flag
    # 
    # For now, let's just have a is_recording=True button that says Rec+Send 
    #make json ojject
    remote_control = {
        "client_name" : "ai",
        "buttons": [
            {
                "name": "Rec+Send",
                "command": "rec_send",
                "is_recording": True
            },
            {
                "name": "Enter",
                "command": "{{enter}}",
                "is_recording": False
            },
        ],
        "switches": [ ]
    }
    #ok now return it as string
    return json.dumps(remote_control)




def print_yaml_pretty(data):
    data = data.replace("\n", "\n\t")
    data = "\t" + data
    print(data) #TODO

def printRoleInfo():
    # Get a list of all filenames in tools/roles/ but no extension and order it by last modified
    roles_directory = BASE_DIR/'tools/roles/'
    filenames = sorted([f[:-5] for f in os.listdir(roles_directory) if f.endswith('.yaml')],
                       key=lambda x: os.path.getmtime(os.path.join(roles_directory, x + '.yaml')),
                       reverse=True)

    # Print roles from the YAML directory
    print()
    printRed("Roles ".ljust(30) + "Last Modified")
    printYellow("------------------------------------------------------------")
    for filename in filenames:
        last_modified_timestamp = os.path.getmtime(os.path.join(roles_directory, filename + '.yaml'))
        last_modified_time = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%A, %Y-%m-%d %H:%M:%S')
        printPeach(f"{filename}".ljust(30) + f"{last_modified_time}")

    # Connect to the SQLite database
    import sqlite3
    conn = sqlite3.connect(BASE_DIR/'roles.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.name, r.description, GROUP_CONCAT(t.name) AS tool_names
        FROM roles r
        LEFT JOIN roles_tools rt ON r.id = rt.role_id
        LEFT JOIN tools t ON rt.tool_id = t.id
        GROUP BY r.id
        ORDER BY r.usage_count desc, r.rowid desc
    """)

    roles = cursor.fetchall()

    # Print roles from the database
    print()
    printRed("Roles (from DB)".ljust(30) + "Description".ljust(45) + "Associated Tools")
    printYellow("--------------------------------------------------------------------------------------------------------")
    for role in roles:
        role_name = role[0]
        try:
            role_description = role[1][:40]  # First 40 characters of description
            if (len(role[1]) > 40):
                role_description += "..."
        except:
            role_description = "None"
        tool_names = role[2] if role[2] else ""
        printPeach(f"{role_name}".ljust(30) + f"{role_description}".ljust(45) + f"{tool_names}")

    # Close the database connection
    conn.close()

    if (args.role is not None):
        printYellow(f"\n  Role is '{args.role}'\n")
        #get the filepath to it

        #rolefile = " + args.role + ".yaml"
        #try:
        #    rolefiletxt = ""
        #    with open(rolefile, 'r') as file:
        #        rolefiletxt = file.read()
        #    print_yaml_pretty(rolefiletxt)
        #except:
        #    print("Error printing file " + rolefile)


# Function to display the help menu using rich
def display_help():
    console = Console()
    table = Table(title="Help Menu")

    # Define columns with their default styles
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="")

    for cmd in commands:
        # Determine command style from tool_color
        if 'tool_color' in cmd:
            command_style = cmd['tool_color']
        else:
            command_style = 'cyan'  # Default command color

        # Determine description style from desc_color
        if 'desc_color' in cmd:
            description_style = cmd['desc_color']
        else:
            description_style = 'brown'  # Default description color (brown shows up as grey)

        # Add the row with the respective styles for command and description
        table.add_row(
            f"[{command_style}]{cmd['command']}[/]",
            f"[{description_style}]{cmd['description']}[/]"
        )

    console.print(table)
    print()

def get_display_help_as_txt():
    help_txt = ""
    for cmd in commands:
        help_txt += f"{cmd['command']}\n"
        help_txt += f"{cmd['description']}\n"
    return help_txt


#AI feature if there is a command entered but not matched, like :toosl, then maybe pass that to a specialized AI thing that can evaluate that against supported commands in realtime, then ask the user if did they mean ???? and then the user can be all 'yeah!'.  This points to the need to be able to 'hand things off' and ideally with the same local engine that is already instantiated so that we dont have to be standing up libraries every time we do a handoff. 
#AI feat teh role should be preserved with each open converasation and then role loads maybe 
#AI feat the tools loaded by a role should remain with that instantiated role... staefully that is. taller order I get it. probably do it the way VSTs save their settings... there will need to be something like JSON serialization or some such, perhaps

    
#a method that will recei ve a string, look for {{ cat myfile.txt}} or like {{ echo `date` }} or {{echo "my name is $name and date is `date`"}} and run those bash commands and replace them with the output of those commands. allow for extra or less whitespace
def replace_bash_commands(input_string):

    if args.nobash:
        return input_string

    import re
    import subprocess
    pattern = re.compile(r'{{\s*(.*?)\s*}}')

    def replace_match(match):
        command = match.group(1)
        #does command start with #
        if (command.strip().startswith('#')):
            #ok, we know this is a special plea to get the role_variable identified
            if loaded_role is not None and isinstance(loaded_role, Role):
                try:
                    role_variable_value = loaded_role.variables[command[1:]].strip()
                    return role_variable_value
                except:
                    return ""
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
            return result.stdout.strip()

    try:
        return pattern.sub(replace_match, str(input_string))
    except KeyboardInterrupt:
       return "KeyboardInterrupt"
        

def getPreProcessedSystemMessage():
    setuptxt = ""

    #check for --sysfile
    if (args.sysfile is not None): #it may be multiple files
        for sysfile in args.sysfile.split(","):
            #now add .txt
            sysfile = sysfile + ".txt"
            if (os.path.exists(BASE_DIR/"tools/sysfile/" + sysfile)):
                with open(BASE_DIR/"tools/sysfile/" + sysfile, 'r') as file:
                    setuptxt += file.read()
                    first = False
    if (args.sysfile_edit is not None): #it may be multiple files
        for sysfile in args.sysfile_edit.split(","):
            sysfile = sysfile + ".txt"
            if (os.path.exists(BASE_DIR/"tools/sysfile/" + sysfile)):
                #edit it in vi
                os.system("vi " + BASE_DIR/"tools/sysfile/" + sysfile)
        sys.exit(0)

    if (args.system != ""):
        first = False
        setuptxt = setuptxt + args.system

    if (args.outputcode == True or args.outputcodefile is not None):
        first = False
        setuptxt += "Please output the requested command/script with zero markup or additional commentary (other than code comments) as your response is being directed to stdout or file. (Tabs instead of spaces for any Python). NO ``` markup"
  
    setuptxt = setuptxt.strip()
    return setuptxt



def refreshSystemPrompt(messages, args):
    setuptxt = getPreProcessedSystemMessage()
    system_prompt_exists = False

    setuptxt = replace_bash_commands(setuptxt)

    #Insert system message
    for message in messages:
        if message["role"] == "system":
            message["content"] = setuptxt
            system_prompt_exists = True
            break

    if not system_prompt_exists:
        messages.insert(0, {
            "role": "system",
            "content": setuptxt
        })


    return messages


#TODO
# create ABC for OpenAI API (or 2)
# abstract the prompt options
# add ESC to switch between command and input mode

#this will decide whether a tag's text is visible or not, this is for html parsing for the --url option
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, type(Comment)):
        return False
    return True

def url_to_text(url):
    print("URL is " + url)

    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an exception for unsuccessful requests

        soup = BeautifulSoup(response.content, "html.parser")
        texts = soup.find_all(string=True)

        visible_texts = filter(tag_visible, texts)

        output = []
        for t in visible_texts:
            if t.parent.name == 'div':
                output.append(t.strip() + '\n')
            else:
                output.append(t.strip() + ' ')

        return ''.join(output)

    except requests.exceptions.RequestException as e:
        print("Error occurred while fetching the URL:", str(e))
        return ""

def printFileInformationLine(filename):
    try:
        file_size = getFileSizeInBytes(filename)
        last_modified_timestamp = os.path.getmtime(filename)
        last_modified_time = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%A, %Y-%m-%d %H:%M:%S')

        # Calculate the time difference
        current_time = datetime.datetime.now()
        last_modified_time_dt = datetime.datetime.fromtimestamp(last_modified_timestamp)
        time_difference = current_time - last_modified_time_dt

        # Determine if we should print minutes, hours, or days
        print()
        if time_difference.total_seconds() < 60:  # Less than 1 minute
            printGrey(f"{filename} - {file_size} bytes - {last_modified_time} - Modified just now.")
        elif time_difference.total_seconds() < 2 * 3600:  # Less than 2 hours
            minutes_since_modified = time_difference.total_seconds() / 60
            printGrey(f"{filename} - {file_size} bytes - {last_modified_time} - Modified {int(minutes_since_modified)} minutes ago.")
        elif time_difference.total_seconds() < 48 * 3600:  # Less than 48 hours
            hours_since_modified = time_difference.total_seconds() / 3600
            printGrey(f"{filename} - {file_size} bytes - {last_modified_time} - Modified {int(hours_since_modified)} hours ago.")
        else:  # 48 hours or more
            days_since_modified = time_difference.days
            printGrey(f"{filename} - {file_size} bytes - {last_modified_time} - Modified {days_since_modified} days ago.")
        print()

    except Exception as e:
        print(f"An error occurred: {e}")  # Optionally print the error
    
    
#AI performance why is left/rigth arrow kinda slow ?
    

def file_to_json_string(filename):
    # Check if the file exists
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Error: The file '{filename}' does not exist.")

    try:
        # Open and read the file
        with open(filename, 'r') as file:
            content = file.read()

        # Attempt to parse the content as JSON
        json_data = json.loads(content)

        # Convert the parsed JSON back to a JSON string
        #json_string = json.dumps(json_data)

        #return json_string
        return json_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Error: The file '{filename}' does not contain valid JSON. Details: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while processing the file '{filename}'. Details: {str(e)}")



def getAllToolsFromDirectory(dirs = []): #Similar to refreshTools, but this one only returns an array of tools and does not affect args
#is args tools just called out but no value given

    from clisa.tools.tool_base import ToolBase
    import importlib.util
    import inspect
    global args
    
    tools_array = []
    for dirr in dirs:
        files = os.listdir(dirr)
        for file in files:
            json_objects = []
            if file.endswith(".py"):
                #import the class, we will use the following code: https://stackoverflow.com/a/67692
                #get the name of the class
                #call the function_info() method on the class
                # Generate a unique module name
                unique_module_name = f"module_{uuid.uuid4().hex}"

                # Load the module
                #print("aobut to load full path is " + dirr + "/" + file)
                spec = importlib.util.spec_from_file_location(unique_module_name, dirr + "/" + file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # List all attributes of the module
                attributes = dir(module)

                # Filter out the classes
                classes = [getattr(module, attr) for attr in attributes if isinstance(getattr(module, attr), type)]

                # Filter out the abstract classes
                classes = [cls for cls in classes if not inspect.isabstract(cls)]

                if (len(classes) == 0):
                    #print("No classes found in " + file)
                    pass

                for myclass in classes:
                    #print("myclass is " + str(myclass))
                    try:
                        json_objects.append(myclass.function_info())
                    except:
                        pass
                
                #convert string to json object till it works using json.loads, and break if fail
                for json_obj in json_objects:
                    while type(json_obj) == str:
                        try:
                            json_obj = json.loads(json_obj)
                        except:
                            raise ValueError(file + "' provides invalid JSON.")

                    # Ensure json_obj is always a list of dictionaries
                    if isinstance(json_obj, dict):
                        json_obj = [json_obj]
                    elif not isinstance(json_obj, list):
                        raise ValueError(f"JSON object at index {i} is neither a dict nor a list.")

                    #take all the immeidate children of each of the json_objects and combine them together into one legal JSON object
                    for obj in json_obj:
                        #add the file name to the object
                        obj["file"] = dirr + "/" + file
                        obj["last_modified"] = os.path.getmtime(dirr + "/" + file)
                        tools_array.append(obj)
        tools_array = sorted(tools_array, key=lambda x: x["last_modified"], reverse=False)
        return tools_array

#AI feat need a better tools output for listing all available tools


def setToolActivation(tool_py_files_full_path=[], active=False):
    global args
    for tool_py_file in tool_py_files_full_path:
        for tool in args.tools_array:
            if (tool["file"] == tool_py_file):
                tool["active"] = active

def getDeactivatedCanonicalNamesFromFile():
    filename = BASE_DIR/"tools/deactivated_tools.txt"
    # If the file does not exist, create it
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("")  # create an empty file
    deactivated_tools = []
    with open(filename, 'r') as f:
        for line in f:
            deactivated_tools.append(line.strip())
    return deactivated_tools


def writeActiveCanonicalNamesToFile(filename=BASE_DIR/"tools/active_tools.txt"):
    #empty it
    open(filename, 'w').close()
    global args
    for tool in args.tools_array:
        if (tool["active"]):
            with open(filename, 'a') as f:
                f.write(tool["canonical_name"] + "\n")
                f.close()

def getCanonicalToolsNamesFromFile(filename=BASE_DIR/"tools/active_tools.txt"):
    #if no exist create
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("")
            f.close()
    active_tools = []
    with open(filename, 'r') as f:
        for line in f:
            active_tools.append(line.strip())
    return active_tools     

def getActiveTools():
    global args
    active_tools = []
    for tool in args.tools_array:
        #clone it to new object
        try:
            if (tool["active"]):
                active_tools.append(tool)
        except Exception as e:
            print("Error loading tool " + str(tool))
            
    return active_tools

def deactivateAllToolsInArgsToolsArray():
    global args
    for tool in args.tools_array:
        tool["active"] = False

def deactivateTools():
    writeActiveCanonicalNamesToFile(BASE_DIR/"tools/deactivated_tools.txt")
    deactivateAllToolsInArgsToolsArray()
    writeActiveCanonicalNamesToFile()

def setToolsArray(myarray):
    global args
    args.tools_array = myarray

def refreshToolsRecursive(dirs=[TOOLS_TOP_DIR], force_to_active=False): #AI TODO, i think the need for this function is slightly overblown and we should remove/reduce it at some point. we are keeping instances of tools in tool_instances and this doesn't do much once those instances are created

    try:
        from tools.tool_base import ToolBase
    except:
        return
    import importlib.util
    import inspect
    global args

    #AI if we ever need to truly refresh thte tools, i.e. de-intantiate them, we need to clear out tool_instances array

    active_tool_files = []
    for tool in args.tools_array:
        active = tool["active"]
        if (active):
            active_tool_files.append(tool["file"])

    args.tools_array = []
    #for all dirs in dirr
    for dirr in dirs:
        #get all descendent files of this dirr into an array
        all_descendent_py_files_of_this_dirr = []
        for root, dirs, files in os.walk(dirr):
            for file in files:
                if file.endswith(".py"):
                    all_descendent_py_files_of_this_dirr.append(os.path.join(root, file))
            
        for file in all_descendent_py_files_of_this_dirr:
            json_objects = []
            if file.endswith(".py"):
                unique_module_name = f"module_{uuid.uuid4().hex}"
                # Load the module
                try:
                    spec = importlib.util.spec_from_file_location(unique_module_name, file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    print("Exception when loading from " + file + ": " + str(e))
                    continue

                # List all attributes of the module
                attributes = dir(module)

                # Filter out the classes
                classes = [getattr(module, attr) for attr in attributes if isinstance(getattr(module, attr), type)]

                # Filter out the abstract classes
                classes = [cls for cls in classes if not inspect.isabstract(cls)]

                if (len(classes) == 0):
                    #print("No classes found in " + file)
                    pass

                for myclass in classes:
                    #print("myclass is " + str(myclass))
                    try:
                        #print("myclass is " + str(myclass))
                        #print("\t- myclass.function_info() is " + str(myclass.function_info()))
                        json_objects.append(myclass.function_info())
                        #print(myclass.file_location())
                        #print("\t -json_objects is " + str(json_objects))
                    except:
                        pass
                
                #convert string to json object till it works using json.loads, and break if fail
                for json_obj in json_objects:
                    while type(json_obj) == str:
                        try:
                            json_obj = json.loads(json_obj)
                        except:
                            raise ValueError(file + "' provides invalid JSON.")

                    # Ensure json_obj is always a list of dictionaries
                    if isinstance(json_obj, dict):
                        json_obj = [json_obj]
                    elif not isinstance(json_obj, list):
                        raise ValueError(f"JSON object at index {i} is neither a dict nor a list.")

                    #take all the immeidate children of each of the json_objects and combine them together into one legal JSON object
                    for obj in json_obj:
                        #add the file name to the object
                        obj["file"] = file
                        #ok so at this point there is this file, it is some level from [basedir]/tools. That woudl be the parent directory. anyway, 
                        #if in parent directory and filename is thingy_tool.py, then i want there to be a new key called canonical_name that is just thingy_tool
                        #say we were in [basedir/jira, then i would want the canonical_name to be jira.thingy_tool
                        #so keep in mind, if we are in tools, there is no prepending, just thingy_tool. only if we go down 1 or more levels do we prepend

                        #is file in parent directory?
                        if (os.path.dirname(file) == dirr):
                            canonical_name = os.path.splitext(os.path.basename(file))[0]
                        else:
                            #be sure to get full path of file, all subdirs should be part of prepending
                            canonical_name = os.path.relpath(file, dirr)
                            #remove the .py extension
                            canonical_name = os.path.splitext(canonical_name)[0]
                            #replace / with .
                            canonical_name = canonical_name.replace("/", ".")

                        obj["canonical_name"] = canonical_name + "." + obj["function"]["name"]
                        #set to active
                        obj["active"] = force_to_active or obj["file"] in active_tool_files
                        #ok also add the last modified timestamp to it
                        obj["last_modified"] = os.path.getmtime(file)
                        args.tools_array.append(obj)
                        #for key in obj:
                        #    args.tools.append(obj[key])    

    #ok now order the array both by subdirectory name and then by modified
    setToolsArray(sort_tools_array(args.tools_array))

def sort_tools_array(tools_array):
    # Goal: Sort the tools_array by subdirectory and last modified date
    # The result will have subdirectories grouped together, with the most recently modified subdirectory at the bottom
    # Within each subdirectory group, files are sorted by last modified date, with the most recent at the bottom
    # Step 1: Group by subdirectory
    sorted_array = sorted(tools_array, key=lambda x: os.path.dirname(x['file']))
    grouped = []
    for key, group in groupby(sorted_array, key=lambda x: os.path.dirname(x['file'])):
        group_list = list(group)

        # Step 2: Sort each group by last_modified (oldest first)
        group_list.sort(key=itemgetter('last_modified'))

        # Store the group with its most recent modification time
        most_recent = max(item['last_modified'] for item in group_list)
        grouped.append((key, most_recent, group_list))

    # Step 3: Sort the groups based on their most recent file (oldest first)
    grouped.sort(key=lambda x: x[1])

    # Step 4: Flatten the list of lists
    return [item for _, _, group in grouped for item in group]


def activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(terms=[], no_print=False):
    refreshToolsRecursive()
    global args

    tools_to_switch = set()
    for term in terms:
        index = -1
        try:
            index = int(term)
        except:
            pass

        if index != -1:  # If it's an integer, activate/deactivate the tool at that index
            if index < len(args.tools_array):
                tools_to_switch.add(args.tools_array[index])
        else:  # Go by text
            for tool in args.tools_array:
                try:
                    if term in tool["canonical_name"]:
                        tools_to_switch.add(json.dumps(tool))  # Dumping to remove duplicates
                except:
                    if term['name'] in tool["canonical_name"]:
                        tools_to_switch.add(json.dumps(tool))  # Dumping to remove duplicates
    
    jo_tools_to_switch = []
    for tool in tools_to_switch:
        tool = json.loads(tool)
        jo_tools_to_switch.append(tool)
    jo_tools_to_switch = sorted(jo_tools_to_switch, key=lambda x: x["canonical_name"])

    # Activate or deactivate tools
    for tool in jo_tools_to_switch:
        tool["active"] = not tool["active"]
        for tool2 in args.tools_array:
            if tool2["canonical_name"] == tool["canonical_name"]:
                tool2["active"] = tool["active"]

    writeActiveCanonicalNamesToFile()

    # Call the print function to display the results
    if not (args.oneshot) and not no_print:
        printToolStatus(jo_tools_to_switch)
        print()

def printActiveTools():
    #get active_tools = [tool for tool in args.tools_array if tool["active"]]
    active_tools = [tool for tool in args.tools_array if tool["active"]]
    printToolStatus(active_tools)

def modalOfActiveTools(): #THIS IS A WORK IN PROGRESS IT DOES NOT WORK PROPERLY AT ALL
    # Get active tools from args.tools_array
    active_tools = [tool for tool in args.tools_array if tool.get("active")]

    def display_modal(stdscr):
        # Clear the screen
        stdscr.clear()

        # Get the height and width of the window
        height, width = stdscr.getmaxyx()

        # Ensure the modal is not too large for the terminal
        modal_height = min(len(active_tools) + 4, height - 2)  # Leave space for borders
        modal_width = min(width // 2, 40)  # Limit width to a reasonable size
        start_y = (height // 2) - (modal_height // 2)
        start_x = (width // 2) - (modal_width // 2)

        # Create a new window for modal
        modal_win = curses.newwin(modal_height, modal_width, start_y, start_x)

        # Draw the modal box
        modal_win.box()

        # Display the tools
        for i, tool in enumerate(active_tools):
            tool_name = tool.get("name", "Unnamed Tool")  # Use a default name if 'name' key is missing
            modal_win.addstr(i + 1, 1, tool_name)

        modal_win.addstr(len(active_tools) + 2, 1, "Press ESC to exit")

        # Refresh the modal window
        modal_win.refresh()

        # Wait for the user to press ESC
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC key
                break

    # Initialize curses and start the modal display
    curses.wrapper(display_modal)



#AI TODO feature add new command :tag x y z and then i can tag the conversation with tags and when this happens it writes the tags to a json file or something along with the conversation maybe the tags are just filename to be easy at first
    

def printToolStatus(tools):
    colors = []
    last_canonical_name = None

    for tool in tools:
        status = "activated" if tool["active"] else "deactivated"

        # Color flipping logic
        parts = tool["canonical_name"].split('.')
        if last_canonical_name is None:
            colors = ['A'] * len(parts)
        else:
            last_parts = last_canonical_name.split('.')
            for i in range(len(parts)):
                if i >= len(colors):
                    colors.append('A')
                elif parts[i] != last_parts[i]:
                    colors[i] = 'A' if colors[i] == 'B' else 'B'
                    colors = colors[:i + 1]  # Reset subsequent colors

        # Print with alternating colors
        print(Style.BRIGHT, end='')
        for i, part in enumerate(parts):
            if i > 0:
                print('.', end='')
            color = Fore.YELLOW if colors[i] == 'A' else Fore.WHITE
            print(f"{color}{part}", end='')

        print(Fore.WHITE + " is now ", end="")
        if tool["active"]:
            print(Fore.GREEN + status)
        else:
            print(Fore.RED + status)
        print(Style.RESET_ALL, end="")

        last_canonical_name = tool["canonical_name"]

    
#if not args.toolsfile and (not args.notools and not ocf) and (args.tools is None or args.tools == []) and not args.role:
#    print()
#    terms = getCanonicalToolsNamesFromFile()
#    terms = list(set(terms))
#    terms.sort()
#    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(terms)


def refreshTools(force_to_active=False):
    refreshToolsRecursive([TOOLS_TOP_DIR], force_to_active)
    pass


def loadRole(name, role_files=[], prompt_files=[]):
    #iterate through prompt_files and append each one to same string
    prompt = ""
    for prompt_file in prompt_files:
        with open(prompt_file, 'r') as file:
            prompt += file.read()
            file.close()

    refreshToolsRecursive()

    for file in prompt_files:
        for tool in args.tools_array:
            if (tool["file"] == file):
                tool["active"] = True
            else:
                tool["active"] = False
            canonical_name = tool["canonical_name"]
            printYellow(canonical_name + " loaded")


#AI :remresp has a bug somehow, it's eating up lower-array messages with up/down arrow after using it


def validate_yaml_string(role_data) -> bool: #TODO this allows too much, true like for anything almost
    # Hardcoded path to the role template YAML file
    template_file = BASE_DIR/'tools/role_template.yaml'

    # Load the schema from the template YAML file
    with open(template_file, 'r') as file:
        template_schema = yaml.safe_load(file)

    # Check if role_data is a string or a dictionary
    if isinstance(role_data, str):
        # If it's a string, load it as a dictionary
        try:
            yaml_data = yaml.safe_load(role_data)
        except yaml.YAMLError as e:
            print("Error loading YAML:", e)
            return False
    elif isinstance(role_data, dict):
        # If it's already a dictionary, use it directly
        yaml_data = role_data
    else:
        print("Invalid input type. Expected a YAML string or dictionary.")
        return False

    # Validate the YAML data against the schema from the template
    try:
        validate(instance=yaml_data, schema=template_schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print("Validation error:", e.message)
        return False

def appendUserMessage(user_message, no_bash_replacement=False):
    if not no_bash_replacement:
        user_message = replace_bash_commands(user_message)

    messages.append({
        "role": "user",
        "content": user_message
    })



def get_role_file(role_name):
    # Construct the path to the role YAML file
    role_file = os.path.join(BASE_DIR/'tools/roles/', f'{role_name}.yaml')

    if os.path.isfile(role_file): #in case we are passed a full path...
        return (role_file)
    elif os.path.isfile(role_name):
        return (role_name)
    else:
        #check if there is a partial match in the roles directory to role_name
        filenames = [f for f in os.listdir(BASE_DIR/'tools/roles') if os.path.isfile(os.path.join(BASE_DIR/'tools/roles', f))]
        #if only one filename return it
        if len(filenames) == 1:
            return os.path.join(BASE_DIR/'tools/roles', filenames[0])
        else:
            #print that multiple matches were foun.d list the matches.
            printRed("Multiple role files found:")
            for filename in filenames:
                printRed(" - " + filename)

        return None

def edit_role(role_name):
        thfile = get_role_file(role_name)
        current_time = datetime.datetime.now().timestamp()
        os.system('vi ' + thfile)
        last_modified = os.path.getmtime(thfile)

        if last_modified < current_time:
            printYellow('\nRole not modified.\n')
            return False
        else:
            printYellow('\nRole modified.\n')
            return True

def is_role_in_db(role_name):
    #OK so we are going to check roles.db for the role_name, in the roles table
    #if it is there, return True, otherwise return False
    import sqlite3
    conn = sqlite3.connect(BASE_DIR/'roles.db')
    c = conn.cursor()
    c.execute("SELECT * FROM roles WHERE name=?", (role_name,))
    if c.fetchone():
        conn.close()
        return True
    else:
        conn.close()
        return False



def validate_role_data(role):
    return True

def edit_role_in_db(role_id):
    script_path = BASE_DIR/'edit_roles.py'

    # Execute the script with the database path as an argument
    result = subprocess.run(['python3', script_path, BASE_DIR/'roles.db'], capture_output=True, text=True)

    # Check if the script executed successfully
    if result.returncode == 0:
        return True
    else:
        return False


def load_role_from_db(role_name):
    global loaded_role
    global args
    global messages

    db_path = BASE_DIR/'roles.db'
    import sqlite3

    args.system = ""

    if not os.path.isfile(db_path):
        printRed(f"Error: Database file {db_path} not found.\n")
        args.role = None
        return None
        

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch role data
        cursor.execute("SELECT id, name, system_prompt, conversation_file FROM roles WHERE name = ?", (role_name,))
        role_row = cursor.fetchone()

        if not role_row:
            printRed(f"Could not load role '{role_name}': Role not found in the database.\n")
            args.role = None
            conn.close()
            return None

        role_id, name, system_prompt, conversation_file = role_row

        # Create Role object
        role = Role(name)
        role.id = role_id
        role.system_prompt = system_prompt
        role.conversation_file = conversation_file

        cursor.execute("SELECT name FROM role_variables WHERE role_id = ?", (role_id,))
        thevars = cursor.fetchall()
        #role.variables is a {}
        for thevar in thevars:
            role.variables[thevar[0]] = ""

        if args.die_on_assert:
            role.variables["die_on_assert"] = "True"

        if args.role_variables:
            vars_string = args.role_variables

            # Use regex to split on commas not within quotes
            var_key_value_pairs = re.findall(r'(\S+?)=(.*?)(?=,\s*|\s*$)', vars_string)

            for key, value in var_key_value_pairs:
                key = key.strip()
                #remove any leading ,
                if key[0] == ",":
                    key = key[1:]
                value = value.strip()

                # Store or update the variable in the loaded role's variables
                role.variables[key] = value
            
            role.variables["pid"] = str(os.getpid())


            #print("Variables set for loaded role:")
            #for key, value in loaded_role.variables.items():
            #    print(f"{key}: {value}")

        # Fetch hints associated with the role
        cursor.execute("SELECT text FROM hints WHERE role_id = ?", (role_id,))
        hints = cursor.fetchall()
        hints_texts = [hint[0] + "\n" for hint in hints]  # Extract texts from tuples

    
        # Consolidate system prompt with hints
        if hints_texts: 
            try:
                role.system_prompt += "\n" + "\n".join(hints_texts)
            except:
                role.system_prompt_texts = hints_texts

        # Fetch associated missions
        cursor.execute("SELECT id, name, description FROM missions WHERE role_id = ?", (role_id,))
        missions = cursor.fetchall()

        for mission in missions:
            mission_id, mission_name, mission_description = mission
            mission_obj = role.add_mission(mission_name, mission_description)

            # Fetch tasks for each mission
            cursor.execute("SELECT id, description, directive, model FROM tasks WHERE mission_id = ?", (mission_id,))
            tasks = cursor.fetchall()

            for task in tasks:
                task_id, task_description, task_directive, task_model = task
                mission_obj.add_task(
                    directive=task_directive,
                    description=task_description,
                    tools=[],  # We'll populate this next
                    model=task_model
                )

                # Fetch tools for each task
                cursor.execute("""
                    SELECT tools.id, tools.name, tools.description
                    FROM tools
                    JOIN tasks_tools ON tools.id = tasks_tools.tool_id
                    WHERE tasks_tools.task_id = ?
                """, (task_id,))
                tools = cursor.fetchall()

                task_obj = mission_obj.get_task_by_directive(task_directive)
                if task_obj:
                    for tool in tools:
                        tool_id, tool_name, tool_description = tool
                        tool_dict = {
                            'id': tool_id,
                            'name': tool_name,
                            'description': tool_description
                        }
                        task_obj.tools.append(tool_dict)  # Assuming tools are stored as dictionaries
        
        # Fetch tools directly associated with the role
        cursor.execute("""
            SELECT tools.id, tools.name, tools.description
            FROM tools
            JOIN roles_tools ON tools.id = roles_tools.tool_id
            WHERE roles_tools.role_id = ?
        """, (role_id,))
        role_tools = cursor.fetchall()

        for tool in role_tools:
            tool_id, tool_name, tool_description = tool
            role.tools.append({
                'id': tool_id,
                'name': tool_name,
                'description': tool_description
            })

        conn.close()

        # Validate role data
        validated = validate_role_data(role)
        if not validated:
            printRed(f"Error: Role '{role_name}' data does not match the expected schema.\n")
            return None

    except Exception as e:
        print(str(e))
        #now stacktrace
        traceback.print_exc()
        response = input("The role didn't load, would you like to edit the role in the database? (y/n): ")
        if response.lower() == 'y':
            # Implement a function to edit the role in the database
            changed = edit_role_in_db(role_id)
            if changed:
                return load_role_from_db(role_name)  # Removed recursion_count as it wasn't defined

        printRed(f"Could not load role '{role_name}': {str(e)}\n")
        args.role = None
        return None

    # Handle tools
    deactivateAllToolsInArgsToolsArray()
    if args.tools is not None and not args.notools and len(args.tools) > 0:
        role_tool_names = [tool['name'] for tool in role.tools]
        launch_tool_names = [tool for tool in args.tools]
        #combine the two lists
        role_tool_names.extend(launch_tool_names)
        role.tools = list(set(role_tool_names))  # Remove duplicates
    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(role.tools)

    # Handle system prompts
    role.system_prompt_collection = []  # Assuming you have a way to collect system prompts
    if system_prompt:
        role.system_prompt_collection.append(system_prompt)

    args.sysfile = '\n'.join(role.system_prompt_collection)
    temp_file_path = BASE_DIR/'tools/sysfile/temp.txt'
    with open(temp_file_path, 'w') as temp_file:
        if hasattr(role, 'system_prompt_texts'):
            for text in role.system_prompt_texts:
                temp_file.write(text + '\n')

    args.system += '\n' + ','.join(role.system_prompt_texts) if hasattr(role, 'system_prompt_texts') else ''
    args.sysfile = args.sysfile.strip()

    messages = refreshSystemPrompt(messages, args)

    if hasattr(role, 'initial_prompt') and role.initial_prompt:
        appendUserMessage(role.initial_prompt)
        initprompt = replace_bash_commands(role.initial_prompt)
        #print("\n" + initprompt)

    if role.name:
        role.name = replace_bash_commands(role.name)
    if role.system_prompt:
        role.system_prompt = replace_bash_commands(role.system_prompt)
        args.system += role.system_prompt
        #print("System Prompt is: " + role.system_prompt)

    printGrey(f'\nLoaded Role: {role.name}\n')

    loaded_role = role
    return role


def load_role(role_name, recursion_count=0):
    global loaded_role

    if is_role_in_db(role_name):
        return load_role_from_db(role_name)

    import yaml
    import os

    role_file = get_role_file(role_name)
    if role_file is None:
        printRed(f"Could not load role {role_name}\n")
        args.role = None
        return None

    if not os.path.isfile(role_file):
        printRed(f'Error: Role file {role_file} not found.\n')
        args.role = None
        return None

    try:
        with open(role_file, 'r') as file:
            printYellow(f"Loading {role_file}\n")
            role_data = yaml.safe_load(file)

        validated = validate_yaml_string(role_data)
        if not validated:
            printRed(f"Error: Role file {role_file} does not match the expected schema.\n")
            return None

        role = Role(role_data['name'])
        role.load_from_yaml(role_data, role_file)

    except Exception as e:
        if recursion_count < 1:
            response = input("The role didn't load, would you like to edit the role YAML? (y/n): ")
            if response.lower() == 'y':
                changed = edit_role(role_file)
                if changed:
                    return load_role(role_name, recursion_count + 1)
        
        printRed(f"Could not load role {role_name}: {str(e)}\n")
        args.role = None
        return None

    # Handle tools
    deactivateAllToolsInArgsToolsArray()
    if args.tools is not None and not args.notools and len(args.tools) > 0:
        role.tools.extend(args.tools)
        role.tools = list(set(role.tools))  # remove duplicates
    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(role.tools)

    # Handle system prompts
    args.sysfile = ','.join(role.system_prompt_collection)
    with open(BASE_DIR/'tools/sysfile/temp.txt', 'w') as temp_file:
        for text in role.system_prompt_texts:
            temp_file.write(text + '\n')
    args.system += '\n' + ','.join(role.system_prompt_texts)
    args.sysfile = args.sysfile.strip()

    global messages  # TODO refactor
    messages = refreshSystemPrompt(messages, args)

    # Print loaded system prompts
    #for system_prompt_item in role.system_prompt_collection:
    #    printYellow(f"Loaded system prompt item: {system_prompt_item}")
    #for system_prompt_text in role.system_prompt_texts:
    #    printYellow(f"Loaded system prompt text: {system_prompt_text[:40]}")

    if role.initial_prompt:
        appendUserMessage(role.initial_prompt)
        initprompt = replace_bash_commands(role.initial_prompt)
        print("\n" + initprompt)

    if role.name:
        role.name = replace_bash_commands(role.name)
    if role.system_prompt:
        role.system_prompt = replace_bash_commands(role.system_prompt)
        args.system += (role.system_prompt)
        print("System Prompt is: " + role.system_prompt)

    printGrey(f'\nLoaded Role: {role.name}\n')

    loaded_role = role
    return role


def save_role():
    global loaded_role
    if not isinstance(loaded_role, Role):
        print("No role is currently loaded or the loaded role is not of the correct type.")
        return

    """Save the current role state to a YAML file."""
    import yaml
    import os

    # Construct the path to the role YAML file
    role_file = os.path.join(BASE_DIR/'tools/roles/', f'{loaded_role.name}.yaml')

    # Get currently loaded tools and update the role's tools
    loaded_role.tools = getActiveTools()

    # Convert the Role object to a dictionary
    role_dict = loaded_role.to_dict()

    # Save the role dictionary to a YAML file
    with open(role_file, 'w') as file:
        yaml.dump(role_dict, file)

    print(f'Role saved to {role_file}.\n')



#AI feature we need to have a role_edit as well as a role_sys_edit (edit all system files associated with role) know what i mean?


#AI - this would be a good place to drop some new methods, for example, during refactoring

#def get_tool_instance(tool_name):
def get_tool_instance(tool_name, myclass):
    global tool_instances
    for instance in tool_instances:
        jobj = json.loads(instance.function_info())
        for key in jobj:
            if key['function']['name'] == tool_name:  # Assuming tool_instance has an attribute `tool_name`
                #print("not creating new instance of " + tool_name)
                return instance
    # Create a new instance if not found
    new_instance = myclass()  # Replace with appropriate class initialization
    tool_instances.append(new_instance)
    #print("creating new instance of " + tool_name)
    return new_instance


def init_assistantt():
    from gptcli.assistant import ( #TODO all these imports shouldn't be in so many places for this specific one thing
    #from cloudassistant import (
        Assistant,
        DEFAULT_ASSISTANTS,
        AssistantGlobalArgs,
        init_assistant,
    )
    global args
    if True:
        """
        Initialize the assistant
        """
        if True:
            args.stream = True
            #get model 
            if (args.model == "3.5"):
                #model='gpt-3.5-turbo'
                #args.model='gpt-3.5-turbo-16k'
                args.model='gpt-3.5-turbo'
            elif (args.model == "4oo"):
                args.model='gpt-4-0314'
            elif (args.model == "4"):
                #args.model='gpt-4-1106-preview'
                #args.model='gpt-4-turbo-2024-04-09'
                args.model='gpt-4o'
            elif (args.model == "4m"):
                args.model='gpt-4o-mini'
            elif (args.model == "4v"):
                args.model='gpt-4-vision-preview'
            elif (args.model == "4o"):
                args.model='gpt-4o-2024-11-20'
            elif (args.model[0:2] == "o1"):
                args.model='o1-mini'
                args.temperature = 1
                args.stream = False
            elif (args.model == 'claude'):
                args.model='claude-3-opus-20240229'
            elif (args.model == 'sonnet'):
                #args.model='claude-3-sonnet-20240229'
                args.model='claude-3-5-sonnet-20240620'
            elif (args.model == 'haiku'):
                args.model='claude-3-haiku-20240307'
            elif (args.model == 'gemini') or (args.model == 'g'):
                #args.model='gemini-1.0-pro'
                args.model='gemini-1.5-pro'
            elif (args.model == 'gv'):
                args.model='gemini-1.0-pro-vision'
            elif (args.model == 'dolphin'):
                args.model='dolphin'
        
            
        global config
        config = {
            "model": args.model,  # Specify the model here
            "temperature": args.temperature, 
            "top_p": 1.0,
            "stream": args.stream,
            #"messages": [],
        }

        global assistantt
        assistantt = Assistant(config)
        args.init_assistant = True


#spin off a thread to lazy load the assistant
#assistant = None
def lazy_load_assistant():
    #global assistant
    #assistant = init_assistant(args)
    #assistant.load()
    from gptcli.assistant import (
    #from cloudassistant import (
        Assistant,
        DEFAULT_ASSISTANTS,
        AssistantGlobalArgs,
        init_assistant,
    )
    


def print_models():
    #for model in client.models.list():
    #    print(model)
    #print models.txt 
    with open(os.path.dirname(os.path.realpath(__file__)) + "/models.txt", "r") as f:
        print(f.read())

# list engines
#engines = openai.Engine.list()

def delay_10us():
    """
    Delay for 10 microseconds, used to slow down printing of characters
    when using old models that do not support the stream parameter,
    which is of course superior
    """
    for aaa in range (0,330000):
        pass


def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def interrupt_handler(signum, frame):
    """Signal handler that sets the interrupt_requested event."""
    interrupt_requested.set()
    print("\nInterrupt requested in getch.")



def check_for_interrupt(force=False):
    """Thread that listens for incoming messages from the server and checks for interrupts."""

    if args.no_transcription and not force:
        return

    global latest_message
    import struct

    # Attempt to set up the socket connection
    host = "cave.keychaotic.com"
    port = 65433  # Specified port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Define metadata
    METADATA = generate_remote_control_json()

    try:
        sock.connect((host, port))
        printYellowStderr(f"Connected to {host}:{port}")

        # Send metadata to the server
        metadata_bytes = METADATA.encode('utf-8')
        metadata_length = len(metadata_bytes)
        packed_length = struct.pack('!I', metadata_length)  # Network byte order (big-endian)

        # Send the length followed by the metadata
        sock.sendall(packed_length + metadata_bytes)

        while True and killThread == False:
            # Use select to wait for incoming messages
            ready_to_read, _, _ = select.select([sock], [], [], 0.1)

            if ready_to_read:
                # Read the message length first
                length_bytes = sock.recv(4)  # Read the first 4 bytes for message length
                if not length_bytes:
                    break  # Connection closed by the server

                # Unpack the length (network byte order)
                message_length = struct.unpack('!I', length_bytes)[0]

                # Now read the actual message based on the length
                message = sock.recv(message_length)  # Receive the message of the specified length
                if message:
                    # Check if the message is a single x00 null byte
                    if message == b'\x00':
                        latest_message = ""
                    else:
                        latest_message += message.decode('utf-8').strip() + " "

                    # Set the interrupt to allow getch to return the message
                    interrupt_requested.set()

            # Check if the interrupt was requested while the socket is active
            if getch_active and interrupt_requested.is_set():
                interrupt_handled.set()
                # No further action needed here; getch will handle the return

    except (socket.error, ConnectionRefusedError):
        # If connection fails, do not print anything
        pass

    finally:
        sock.close()  # Ensure the socket is closed when done
        # No need to print anything on socket closure

def getch():
    """Get a single character from standard input, handling special keys and interrupts."""
    global original_sigint_handler, getch_active, latest_message
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    # Set up the custom interrupt handler
    signal.signal(signal.SIGINT, interrupt_handler)

    try:
        tty.setraw(fd)
        global getch_active
        getch_active = True  # Set the flag indicating getch is active

        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                c = os.read(sys.stdin.fileno(), 1)

                if c == b'\x1b':  # ESC key
                    next_c = os.read(sys.stdin.fileno(), 1)
                    if next_c == b'[':
                        key = os.read(sys.stdin.fileno(), 1)
                        if key == b'A':
                            return 'up'
                        elif key == b'B':
                            return 'down'
                        elif key == b'C':
                            return 'right'
                        elif key == b'D':
                            return 'left'
                        else:
                            return 'unknown'
                    else:
                        return 'esc'
                elif c == b'\x18':  # Capture ctrl-x key
                    return 'ctrlx'
                elif c == b'\x09':  # Capture ctrl-i key
                    return 'ctrli'
                elif c == b'\x14':  # Capture ctrl-t key
                    return 'ctrlt'
                elif c == b'\x0e':  # Capture ctrl-n key
                    return 'ctrln'
                elif c == b'\x7f':  # Backspace key
                    return 'backspace'
                elif c == b'\x0d' or c == b'\n':  # Enter key
                    return '\n'
                else:
                    return c.decode('utf-8')  # Return regular character as string

            if interrupt_requested.is_set():
                interrupt_requested.clear()
                interrupt_handled.set()
                mymsg = latest_message
                if mymsg is not None and len(mymsg.strip()) == 0: #it was all whitespace
                    mymsg = ""
                latest_message = ""
                return mymsg  # Return the latest message received from the server

    finally:
        getch_active = False  # Clear the flag indicating getch is no longer active
        # Restore the original terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        # Restore the original SIGINT handler
        signal.signal(signal.SIGINT, original_sigint_handler)







#Begin section for terminal control, this is a bit of a mess
#but it is here to allow for the terminal to be controlled, 
#mainly to erase characters once it's clear that the AI is
#outputting code, so that the code can be output in a more
#colorful manner

def terminal_backspace(charcount = 1):
    for aaa in range (0,charcount): 
        sys.stdout.write(f"\033[D") #this one is a move left?
        sys.stdout.flush()
        sys.stdout.write(f"\033[X") #this one is a delete?
        sys.stdout.flush()

def terminal_move_back_a_space():
    sys.stdout.write(f"\033[D") #this one is a move left?
    sys.stdout.flush()

def terminal_move_up_a_line():
    sys.stdout.write(f"\033[A") #this one is a move up?
    sys.stdout.flush()

def terminal_move_right(spacesTotal):
    sys.stdout.write(f"\033[{spacesTotal}C") #move right
    sys.stdout.flush()

def get_code_type(codestring):
    #the codestring will start with ``` and immediately thereafter on that line will be the language, capture that`
    language = codestring.split("\n")[0].replace("```","").strip()
    return language

def erase_chars(num_chars_from_end, string_to_erase):
    # Move the cursor back by the specified number of spaces

    while (num_chars_from_end > 0):
        sys.stdout.write(f"\033[D")
        sys.stdout.flush()
        num_chars_from_end -= 1

    #split string_to_erase by newlines
    lines = string_to_erase.split("\n") 

    charCount = 0
    #iterate through the lines backwards
    start = True
    for line in reversed(lines):
        #itarte thru chars
        newline = True
        if (len(line) == 0):
            terminal_move_up_a_line()
        for char in reversed(line): #obviously won't include the newline
            #is it a newline
            charCount += 1
            if (newline and not start):
                terminal_move_up_a_line()
                terminal_move_right(len(line))
                newline = False
            #else:
            terminal_backspace()
            if (charCount > len(string_to_erase)):
                break
        start = False

def move_forward_chars(spaces_forward):
    # Move the cursor forward by the specified number of spaces
    sys.stdout.write(f"\033[{spaces_forward}C")
    sys.stdout.flush()

# END terminal control section


def get_files_collection(searchterm = None, do_not_insert_new_conversation = True):
    #get all files in ~/conversations that end in json, order by age
    #optionally filter by searchterm
    myfiles = []
    #combine conversationDirectory and "*.json"
    myfiles = glob.glob(os.path.join(conversationDirectory, "*.json"))
    #now sort such that first item is the newest
    myfiles.sort(key=os.path.getmtime, reverse=True)

    if (searchterm is not None and searchterm.strip() != ""):
        #now filter out files that don't contain the searchterm, case insensitive
        myfiles = [file for file in myfiles if searchterm.lower() in open(file).read().lower()]
        myfiles.sort(key=os.path.getmtime, reverse=True)
        #ok and now append a filename that exists in /dev/shm that is something like convo.temp.$pid, 
        if (not do_not_insert_new_conversation or len(myfiles) == 0):
            myfiles.insert(0, "/dev/shm/convo.temp." + str(os.getpid()))
    elif not do_not_insert_new_conversation:
        myfiles.insert(0, "/dev/shm/convo.temp." + str(os.getpid())) #only insert a new one if not searching
        
    return myfiles

def outputConversationToFile(file=None, unprocessedUserMessage=None, print_file_info=False):
    """
    Output the conversation to a file, optionally appending the user's message. JSON format.
    """
    messagesCopy = []
    for message in messages:
        messagesCopy.append(message)
    if (unprocessedUserMessage is not None and unprocessedUserMessage.strip() != ""):
        messagesCopy.append({
            "role": "user",
            "content": unprocessedUserMessage
        })
    if not os.path.exists(conversationDirectory):
        os.mkdir(conversationDirectory)
    filename = file
    if filename is None or len(filename.strip()) == 0:
        filename = datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + ".json"
    convoString = json.dumps(messagesCopy, indent=4)
    if file is None:
        directory=conversationDirectory
    else:
        directory=""
        #the file may already have a directory in it. but if not, we need to get current directory
        if (not "/" in file):
            directory = os.getcwd() + "/"
    with open(directory+filename, "w") as f:
        #convert messages to a json string with nice newlines and all
        f.write(convoString + "\n")
    
    if print_file_info:
        printGrey("\nWrote conversation to file: " + directory+filename + "\n")
        #print entire stack trace 
        #printGrey("Stack trace: " + ''.join(traceback.format_stack()))
    
    return filename

def outputMessagesToFile(file, total_messages_to_write):
    """
    Output messages to a file, NOT JSON. Meant for later human consumption
    """
    #no messages?
    if (len(messages) == 0):
        print("no messages to output")
        return
    
    #does the file exist?
    #if os.path.exists(file):
    #    print("file "+str(file)+" already exists, not overwriting")
    #    return
    
    #ok, we have messages, let's output them to the file
    count = 0
    with open(file, "a") as f:
        if (total_messages_to_write > len(messages)):
            total_messages_to_write = len(messages)
        #iterate over last 'count' messages
        for message in messages[-total_messages_to_write:]:
            if (count > 0):
                f.write("\n")
            f.write(message['content'] + "\n")
            count += 1
    printGrey("Wrote "+str(count)+" messages to file: " + str(file))


def detect_code(response_content):
    """
    Detects if the response_content is a code block, and if so, returns the language
    """
    lastCharIsNewline = response_content[-1] == "\n" #-1 is the last char in the string

    if lastCharIsNewline:
        lines = response_content.split("\n") #as of now we assume that included is the last line which is empty
        lastLine = lines[-2] #the last line is empty, so we want the second to last line

        #now we need to determine if the last line, stripped, begins with "```" and if so, get the word to the right of that
        lastLine = lastLine.strip()
        if lastLine.startswith("```"):
            #get the word to the right of that
            language = lastLine.replace("```", "").strip()
            return language
    return None

def detect_end_of_code(response_content):
    """
    Detects whether we've reached the end of the code block, based on ``` being the last line
    """
    lastCharIsNewline = response_content[-1] == "\n" #-1 is the last char in the string
    if lastCharIsNewline:
        lines = response_content.split("\n") #as of now we assume that included is the last line which is empty
        lastLine = lines[-2] #the last line is empty, so we want the second to last line

        lastLine = lastLine.strip()
        if lastLine.startswith("```"):
            return True
    return False

def detect_ansi_colors(response_content): #UNUSED, UNTESTED
    """
    Detects whether we've passed a string containing ANSI color codes
    Returns the number of characters affected by the ANSI codes, or -1 if not found
    """
    #Is the last char an ANSI code?
    lastCharIsAnsiCode = response_content[-5:] == "\033[0m" or \
        response_content[-6:] == "\033[0m\n" or \
        response_content[-6:] == "\033[0m\r\n" or \
        response_content[-4:] == "\033[0m " or \
        response_content[-4:] == "\033[0m." or \
        response_content[-4:] == "\033[0m,"

    if lastCharIsAnsiCode:
        #split string into lines and let's examine the last line
        lines = response_content.split("\n")
        lastLine = lines[-1:][0]
        indexOfLastCode = lastLine.rfind("\033[0m")
        #now find first "\033[" that happens before indexOfLastCode
        indexOfPenultimateCode = lastLine.rfind("\033[", 0, indexOfLastCode) #if not there, returns -1

        if indexOfPenultimateCode != -1:
            #we have an ANSI color code block
            return len("\033[0m") + indexOfLastCode - indexOfPenultimateCode + len("\033[0m")
    return -1

def detect_single_quoted_text(response_content):
    """
    Detects whether we've passed a single quoted text block
    Returns the number of characters in the single quoted text block, or -1 if not found
    """
    #Is the last char a "`" or similar
    lastCharIsSingleQuote = response_content[-2:] == "` " or response_content[-2:] == "`." or response_content[-2:] == "`,"

    if lastCharIsSingleQuote:
        #split string into lines and let's examine the last line
        lines = response_content.split("\n")
        lastLine = lines[-1:][0] 
        indexOfLastQuote = lastLine.rfind("`")
        #now find first " '" that happens before indexOfLastQuote
        indexOfPenultimateQuote = lastLine.rfind(" `", 0, indexOfLastQuote) #if not there, returns -1

        if indexOfPenultimateQuote != -1:
            #we have a single quoted string
            return len("` ") + indexOfLastQuote - indexOfPenultimateQuote + len("`")
    return -1


def extract_response_text_from_partial_json(partial_json):
    # Remove leading and trailing whitespace
    partial_json = partial_json.strip()

    # More flexible regex to match "respond" key with variable whitespace
    match = re.match(r'^\s*{\s*"respond"\s*:\s*(.*)$', partial_json, re.DOTALL)
    if not match:
        return partial_json  # Return the original input if no match

    # Extract content after the colon
    content = match.group(1).lstrip()

    # If the content starts with a quote, it's a JSON string
    if content.startswith('"'):
        # Find the position of the last unescaped quote
        last_quote = -1
        escape = False
        for i, char in enumerate(content[1:], 1):
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                last_quote = i

        # Extract the content within the quotes
        if last_quote != -1:
            return content[1:last_quote]
        else:
            return content[1:]  # Return everything after the first quote if no closing quote

    # Try to parse as JSON
    try:
        parsed = json.loads(f'{{{content}}}')
        if 'respond' in parsed and isinstance(parsed['respond'], str):
            return parsed['respond']
        else:
            return content  # Return the content if 'respond' key is not found or not a string
    except json.JSONDecodeError:
        return content  # Return the content if JSON parsing fails



def printAiContent(content, noprint=False, noJsonCheck=False):
    response = ""
    console = Console()
    jsoncommand = ""
    json_objects = []  # NEW: List to store multiple JSON objects

    global args
    sserver = None
    if args.socket:
        sserver = StreamingSocketServer(args.socket) #the port
        sserver.start()
        
        
    try:
        if (not noprint):
            with Live(console=console, auto_refresh=False) as live:
            #with Live(console=console, refresh_per_second=3) as live:

                #if content is a stirng, print it here in green
                if isinstance(content, str):
                    printGreen("content is a string: " + content)

                firstBlankLine = False


                #print(str(args.tools_array))
                for chunk in content: #AI is force_to_active yes or no here?

                    commandflag = False
                    if isinstance(chunk, tuple):
                        value, commandflag = chunk
                        chunk = value
                    
                    if (commandflag):
                        jsoncommand += chunk
                        #print("jc:" + jsoncommand)

                    if (firstBlankLine == False):
                        #print('23 - ')
                        print()
                        firstBlankLine = True

                    if not commandflag:
                        try:
                            response += chunk
                        except:
                            response += str(chunk)

                    if sserver is not None:
                        sserver.send_data(chunk)

                    looksLikeResponseToUser = (len(response) > 10 and "respo" in response.lower())

                    if commandflag or JSONDetector.could_be_json(response) or JSONDetector.could_be_multiple_sets_of_json(response) or JSONDetector.is_valid_json(response): #TODO REFACTOR
                        #now do that again but first response in green then jsoncommand in yellow
                        if (commandflag):

                            # Create styled Text objects for more control
                            text1 = Text(response, style="green")
                            text2 = Text(jsoncommand, style="yellow")

                            # Combine the texts into a single Panel for display
                            combined_text = (text1 + "\n" + text2)

                            live.update(combined_text)
                            #live.update(Markdown(response, style="green"), Markdown(jsoncommand, style="yellow"))
                        else:
                            live.update(Markdown(response, style="yellow"))
                        live.refresh()

                    else:
                        if (True):
                            try:
                                live.update(Markdown(response, style="green", code_theme="rrt", code_padding=0))
                            except:
                                live.update(Markdown(response, style="green", code_theme="rrt"))
                            live.refresh()
                    if interrupt_requested.is_set():
                        #interrupt_requested.clear()
                        raise KeyboardInterrupt() #ultimately, getch should handle the interrupt fully since we're not resetting anything here
        else:
            # Handling when noprint is True
            for chunk in content:
                response += chunk

    except KeyboardInterrupt:
        # Handling keyboard interrupts
        print()

        #we need to know if we have just interrupted a tool call. if we have, we probably don't want tools to remain active, 
        #so let's disable tools here provided that the last message was a user message containing "RESPONSE:" followed by an indeterminate amount of whitespace and then followed by valid JSON.
        if (len(messages) > 0 and messages[-1]['role'] == "user" and "RESPONSE:" in messages[-1]['content']):
            #get the last message
            lastMessage = messages[-1]['content']
            #get the content after RESPONSE: and strip whitespace
            lastMessage = lastMessage.split("RESPONSE:")[1].strip()
            #now check if it is valid JSON
            if (JSONDetector.is_valid_json(lastMessage)):
                #ok, it is valid JSON, so let's disable tools
                #deactivateTools()
                #printYellow("Deactivated all tools. (you're welcome)")
                pass

        live.update(Markdown(response, style="green", code_theme="rrt", code_padding=0))
        live.refresh()
        if interrupt_handled.is_set():
            interrupt_handled.clear()
            printYellow("[interrupt]")

    except LLMOutputNotValidJSONError as e:
        #The thought is that the response has triggered an error, as in, an LLM response error
        #so, the LLM needs to see what it did wrong :) and the error handling flow won't normally
        #add this message in. The error message will be seen, but some 
        messages.append({
            "role": "assistant",
            "content": response
        })
        raise e
    except Exception as e:
        print("ERROR: " + str(e))
        traceback.print_exc()
        #AI bug this is being called from someone somewhere and it's just giving up kinda, no retry.
        raise e
    finally:
        if sserver is not None:
            sserver.stop()


    return ((json_objects if json_objects else response), jsoncommand)

# NEW: Helper function to find the end of a JSON object
def find_json_end(s):
    """
    Finds the end index of a JSON object in a string.

    Args:
    s (str): The string to search for a JSON object.

    Returns:
    int: The index of the closing brace of the JSON object, or -1 if not found.
    """
    stack = []
    in_string = False
    for i, c in enumerate(s):
        if c == '"' and (i == 0 or s[i-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if c == '{':
                stack.append(c)
            elif c == '}':
                if not stack:
                    return -1
                stack.pop()
                if not stack:
                    return i
    return -1


#AI feat should make a otol athat makes code get selected in vscode in realtime
#AI feat that drops you in a temporary bash prompt that you can exit out of, much like :!sh from VI (maybe just we call it that here too)
#AI feat a bar across the bottom of the screen, status bar, you might call it, to show current role maybe color code it
#AI feat color code conversation to indicate speaker
#AI feat open bottom horizontal section of terminal for additional actions that are happening in realtime 
#AI tmux to SUTs (this is for OEM work)




def printMessagesToScreen(printLastMessageIfUser=True, limitByTerminalSize=False, appendString=""):
    """
    Print the messages to the screen, optionally printing the last message if it is a user message
    """
    global messages

    #can we get the # of lines in the terminal?
    if (len(mystdin) == 0):
        #lines_in_terminal = int(subprocess.check_output(['stty', 'size']).split()[0]) #TODO understand and/or fix these couple lines
        lines_in_terminal = 0 #TODO why is this line here?
        limitByTerminalSize = False

    messagesCopy = []

    if (limitByTerminalSize):
        #iterate over messages in reverse order, and count the number of lines
        lineCount = 0
        for item in reversed(messages):
            if item['role'] == "user" or item['role'] == "assistant":
                lineCount += len(item['content'].split("\n")) + 1
            #add item to top of messagesCopy
            messagesCopy.insert(0, item)
            try:
                lines_in_terminal = int(subprocess.check_output(['stty', 'size']).split()[0]) #TODO does this line break anything?
            except:
                lines_in_terminal = 20
            if (lineCount > lines_in_terminal * 1.2): #TODO sometimes lines_in_terminal is not defined
                break
    else:
        messagesCopy = messages

    if (len(messagesCopy) > 0):
        #iterate over messages and print
        #iterate over all but the last message
        unprocessedUserMessage=""
        for item in messagesCopy[:-1]:
            if item['role'] == "user":
                #print('9 -')
                if not args.nostdinprint:
                    print()
                    content = item['content']
                    if "TOOL RESPONSE:" in content:
                        content = content.split("TOOL RESPONSE:")
                        printYellow(str(content[0]))
                        printGrey("aTOOL RESPONSE: " + str(content[1]))
                    else:
                        #print the user message
                        printGrey(str(content), end="")
                        pass
                else:
                    args.nostdinprint = False
            if item['role'] == "assistant":
                resp = printAiContent([item['content']], False, True) #needs to be a collection
                #AI TODO seems we could probably refactor this with the above 
        
        #process final message
        if messagesCopy[-1]['role'] == "assistant":
            resp = printAiContent([messages[-1]['content']], False, True) #needs to be a collection
        elif messagesCopy[-1]['role'] == "user": 
            if not args.nostdinprint:
                if (printLastMessageIfUser):
                    content = messagesCopy[-1]['content']
                    if "TOOL RESPONSE:" in content:
                        content = content.split("TOOL RESPONSE:")
                        printYellow(str(content[0])) #TODO refactor with above, similar lines
                        printGrey("bTOOL RESPONSE: " + str(content[1]))
                    else:
                        #print the user message
                        printGrey(str(content))
            else:
                args.nostdinprint = False
            unprocessedUserMessage = messagesCopy[-1]['content']
        
        if (appendString != ""):
            print()
            print(appendString)
        
        return unprocessedUserMessage



def getMessagesAsText():
    text = ""
    if (args.max and args.max > 0):
        #get the last args.max messages
        for item in messages[-int(args.max):]: 
            if item['role'] == "system":
                text += "Instructions to AI: " + item['content'] + "\n"
            if item['role'] == "user":
                text += "Human: " + item['content'] + "\n"
            if item['role'] == "assistant":
                text += "AI: " + item['content'] + "\n"
    else:
        for item in messages:
            if item['role'] == "system":
                text += "Instructions to AI: " + item['content'] + "\n"
            if item['role'] == "user":
                text += "Human: " + item['content'] + "\n"
            if item['role'] == "assistant":
                text += "AI: " + item['content'] + "\n"
    return text


#start of code block
def detect_code(response_content):
    lastCharIsNewline = response_content[-1] == "\n" #-1 is the last char in the string

    if lastCharIsNewline:
        lines = response_content.split("\n") #as of now we assume that included is the last line which is empty
        lastLine = lines[-2] #the last line is empty, so we want the second to last line

        #now we need to determine if the last line, stripped, begins with "```" and if so, get the word to the right of that
        lastLine = lastLine.strip()
        if lastLine.startswith("```"):
            #get the word to the right of that
            language = lastLine.replace("```", "").strip()
            return language
    return None

#this detects when we've reached the end of the code block, based on ``` being the last line
def detect_end_of_code(response_content):
    lastCharIsNewline = response_content[-1] == "\n" #-1 is the last char in the string
    if lastCharIsNewline:
        lines = response_content.split("\n") #as of now we assume that included is the last line which is empty
        lastLine = lines[-2] #the last line is empty, so we want the second to last line

        lastLine = lastLine.strip()
        if lastLine.startswith("```"):
            return True
    return False

#did we pass an inline code block?
def detect_single_quoted_text(response_content):
    #OK so, is hte last char a '
    lastCharIsSingleQuote = response_content[-2:] == "` " or response_content[-2:] == "`." or response_content[-2:] == "`,"

    if lastCharIsSingleQuote:
        #split string into lines and let's examine the last line
        lines = response_content.split("\n")
        #get last line
        #print("here1")
        lastLine = lines[-1:][0] #this is the last line
        #print("h343, last line is: " + str(lastLine))

        indexOfLastQuote = lastLine.rfind("`")
        #print("here2")
        #now find first " '" that happens before indexOfLastQuote
        indexOfPenultimateQuote = lastLine.rfind(" `", 0, indexOfLastQuote) #if not there, returns -1
        #print("here3")

        if indexOfPenultimateQuote != -1:
            #we have a single quoted string
            return len("` ") + indexOfLastQuote - indexOfPenultimateQuote + len("`")
    return -1


#styles = ['rrt', 'default', 'colorful', 'autumn', 'manni', 'fruity', 'tango', 'murphy', 'vs', 'xcode', 'igor', 'paraiso-dark', 'paraiso-light', 'dracula', 'algol', 'lovelace', 'rrt', 'borland', 'bw', 'emacs', 'friendly', 'vim', 'pastie', 'perldoc', 'native', 'borland', 'trac', 'rainbow_dash', 'solarized-dark', 'solarized-light', 'zenburn', 'abap', 'algol_nu', 'arduino', 'rainbow', 'github', 'sas', 'stata', 'stata-light', 'stata-dark']

def getFileSizeInBytes(filename):
    try:
        # Get the size of the file in bytes
        size = os.path.getsize(filename)
        return size
    except OSError as e:
        # Handle the error if the file does not exist or is inaccessible
        print(f"eError: {e}")
        return None

def getMessagesFromFile(filename):
    #does the file exist?
    thesemessages = []
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            text = f.read()
            #print("OK, we read the file, now we're going to parse the json and print the messages to the screen")
            #print("text is " + text  )
            thesemessages = json.loads(text)
            #if len(setuptxt) > 0: #replace the system-role message in the messages collection with the new setuptxt
            #    thesemessages[0]['content'] = setuptxt
            thesemessages = refreshSystemPrompt(thesemessages, args)
            f.close()
            return thesemessages
    else:
        return thesemessages

def download_image(image_url, image_path):
    response = requests.get(image_url)
    response.raise_for_status()

    with open(image_path, 'wb') as image_file:
        image_file.write(response.content)
    return image_path

# Function to copy the image to the Windows clipboard using PowerShell
def copy_image_to_clipboard(image_path):
    # Convert the WSL2 path to the corresponding Windows path
    windows_path = subprocess.check_output(['wslpath', '-w', image_path]).decode().strip()

    # PowerShell command to copy the image to the clipboard
    ps_command = f"Add-Type -AssemblyName System.Windows.Forms; " \
                 f"[System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{windows_path}'))"

    # Execute the PowerShell command from WSL2
    subprocess.run(['powershell.exe', '-command', ps_command], check=True)
    #now delete the file

def weAreOnWSL():
    #check if we're on WSL
    if (os.path.exists("/mnt/c/Windows")):
        return True
    else:
        return False # this is 



def sendDalle3APIRequest(prompt, size="1024x1024", quality="standard", printToScreen=True):
    raise NotImplementedError("This function sending DALL-E 3 API requests is not yet implemented.")

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url
    #now get text also
    #make filename be jpg but some unique name with pid
    pid = str(os.getpid())
    filename = "/dev/shm/" + pid + ".jpg"
    download_image(image_url, filename)
    print("Image URL: " + image_url)
    if (weAreOnWSL()):
        #copy to clipboard
        copy_image_to_clipboard(filename)
        os.remove(filename)
        if (printToScreen):
            printGreen("Image copied to clipboard: " + response.data[0].revised_prompt)
    else:
        if (printToScreen):
            printGreen("Image File: " + filename)
    return response.data[0].revised_prompt


def cleanDotMessages(themessages):                                                                                                              
    # Create a duplicate of the original messages                                                                                               
    cleanedMessages = themessages[:]                                                                                                            
                                                                                                                                                
    # Find the last assistant message                                                                                                           
    lastAssistantIndex = -1                                                                                                                     
    for i in range(len(cleanedMessages)-1, -1, -1):                                                                                             
        if cleanedMessages[i]['role'] == "assistant":                                                                                           
            lastAssistantIndex = i                                                                                                              
            break                                                                                                                               
                                                                                                                                                
    try:                                                                                            
        #is cleanedMessages[lastAssistantIndex]['content'] a dict?
        if isinstance(cleanedMessages[lastAssistantIndex]['content'], dict):
            #convert that value in the dict to a string, it's json, just convert to a string. This was needed when parsing string that happens to be a JSON object in the LLM response itself like {"respond": "some json"}
            cleanedMessages[lastAssistantIndex]['content'] = json.dumps(cleanedMessages[lastAssistantIndex]['content'])

        # If no assistant message or last assistant message isn't a dot, return the original messages                                               
        if lastAssistantIndex == -1 or cleanedMessages[lastAssistantIndex]['content'].strip() != ".":                                               
            return themessages                                                                                                                      
    except:
        for key, value in cleanedMessages[lastAssistantIndex]['content']:
            print(f"{key}:{value}")
                                                                                                                                                    
    # Count preceding assistant dot messages, skipping user messages                                                                            
    dotCount = 1  # Start with the last dot message already found                                                                               
    dotIndices = [lastAssistantIndex]                                                                                                           
    for i in range(lastAssistantIndex - 1, -1, -1):                                                                                             
        if cleanedMessages[i]['role'] == "assistant" and cleanedMessages[i]['content'].strip() == ".":                                          
            dotCount += 1                                                                                                                       
            dotIndices.append(i)                                                                                                                
        elif cleanedMessages[i]['role'] == "user":                                                                                              
            continue                                                                                                                            
        else:                                                                                                                                   
            break  # Stop if we encounter an assistant message that is not a dot                                                                
                                                                                                                                                
    # If there are less than 2 preceding dot messages, return the original messages                                                             
    if dotCount < 3:                                                                                                                            
        return themessages                                                                                                                      
                                                                                                                                                
    # Gather the first and most recent user messages                                                                                            
    firstUserMessageIndex = next((i for i, msg in enumerate(cleanedMessages) if msg['role'] == "user"), None)                                   
    lastUserMessageIndex = next((i for i, msg in reversed(list(enumerate(cleanedMessages))) if msg['role'] == "user"), None)                    
                                                                                                                                                
    # Create a set of indices to keep                                                                                                           
    indicesToKeep = set()                                                                                                                       
    if firstUserMessageIndex is not None:                                                                                                       
        indicesToKeep.add(firstUserMessageIndex)                                                                                                
    if lastUserMessageIndex is not None:                                                                                                        
        indicesToKeep.add(lastUserMessageIndex)                                                                                                 
                                                                                                                                                
    # Keep the first and last dot messages                                                                                                      
    indicesToKeep.add(dotIndices[-1])  # First dot message in the series                                                                        
    indicesToKeep.add(dotIndices[0])   # Last dot message in the series                                                                         
                                                                                                                                                
    # Create the final list of cleaned messages                                                                                                 
    finalMessages = []                                                                                                                          
    ignoredMessages = []                                                                                                                        
    for i, msg in enumerate(cleanedMessages):                                                                                                   
        if i in indicesToKeep:                                                                                                                  
            finalMessages.append(msg)                                                                                                           
        else:                                                                                                                                   
            ignoredMessages.append(msg)                                                                                                         
                                                                                                                                                
    # Debug output for ignored messages                                                                                                         
    print("Ignored Messages:")                                                                                                                  
    for msg in ignoredMessages:                                                                                                                 
        print(msg)                                                                                                                              
                                                                                                                                                
    return finalMessages   



def sendRequest(no_std_out=False):

    global assistantt
    global config
    from gptcli.assistant import (
    #from cloudassistant import (
        Assistant,
        DEFAULT_ASSISTANTS,
        AssistantGlobalArgs,
        init_assistant,
    )
    init_assistantt()
    assistantt = Assistant(config)

    #url = 'https://api.openai.com/v1/chat/completions'

    from clisa.tools.tool_base import ToolBase

    global messages
    global finalMessages

    #check first message that is either user or assistant. If it's assistant, we need to insert an empty user message
    #above it 
    #so first, find index of first user or assistant message
    firstUserOrAssistantIndex = -1
    for i in range(len(messages)):
        if messages[i]['role'] == "user" or messages[i]['role'] == "assistant":
            firstUserOrAssistantIndex = i
            break
    #if it's an assistant message, insert an empty user message above it
    #check if it's greater than -1 and then do it
    if (firstUserOrAssistantIndex > -1 and messages[firstUserOrAssistantIndex]['role'] == "assistant"):
        messages.insert(firstUserOrAssistantIndex, {
            "role": "user",
            "content": "." #. because it can't be empty per some models
        })
    #if it's an empty assistant message, remove it entirely
    if (firstUserOrAssistantIndex > -1 and messages[firstUserOrAssistantIndex]['role'] == "assistant" and messages[firstUserOrAssistantIndex]['content'].strip() == ""):
        messages.pop(firstUserOrAssistantIndex)

    #if there are concurrent user messages, we need to insert empty assistant messages between them
    while True:
        found = False
        for i in range(len(messages)-1):
            if messages[i]['role'] == "user" and messages[i+1]['role'] == "user":
                messages.insert(i+1, {
                    "role": "assistant",
                    "content": "."
                })
                found = True
                break
        if not found:
            break

    #AI random idea just had, what if there are prompts that can be in role files that can be injected at will, you know? or task commands, that sort of thing maybe 

    messages = cleanDotMessages(messages) #todo is it needed

    if (not no_std_out):
        count = 0
        while (True):
            jsoncommand = ""
            global force_tools_flag
            try:
                #print tempmessages, which is a dict
                
                #printGreen("HERE IT IS")
                #print(tempmessages)
                #TODO: refactor this 4 lines
                tempmessages = messages

                #check if first message is system and model starts with o1

                if (args.max and args.max > 0):
                    tempmessages = messages[-int(args.max):] #fix this for o1
                    args.max = args.max + 1
                tempmessages = refreshSystemPrompt(tempmessages, args) #HORSE (look for HORSE in comments for some refacor wishes TODO)
                if args.model[0:2] == "o1":
                    if tempmessages[0]['role'] == "system":
                        tempmessages.pop(0)
                
                if args.tools_array is None or (len(args.tools_array) == 0):
                    ret, jsoncommand = printAiContent(assistantt.complete_chat(tempmessages), {}, args.stream)
                else:
                    ret, jsoncommand = printAiContent(assistantt.complete_chat(tempmessages, {}, args.stream, getActiveTools(), force_tools_flag))
                break


            except LLMRepeatJSONTwiceError:
                messages.append({'role': 'user', 'content': 'SYSTEM MESSAGE: You repeated a command - please stop repeating or explain the issue to the user.'})

                #TODO: refactor this 4 lines
                tempmessages = messages
                if (args.max and args.max > 0):
                    tempmessages = messages[-int(args.max):]
                    args.max = args.max + 1

            except LLMOutputNotValidJSONError as e: #we should therefore be in a mode that requires JSON, so we need to ask the model to retry. Refactor this, feels like printAiContent shouldn't be in charge of generating this error from args rather than being passed those args to the function call
                #why si it saying LLMOutputNotValidJSONError is not defined? I defined it above in its own class!
                # well, I think I need to import it, that should be done at the top of the file
                # which is wierd given that the class is already defined so why the need for an import?
                # well, I think it's because I'm trying to catch the exception, so I need to import it

                #we need to ask the model to retry
                #printGreen("appending user message, asking model to retry, as it did not output valid JSON")

                message = 'SYSTEM: ERROR '+str(e)+' Use { "respond": "..." } to address the human user for advice if this is happening a lot.'
                messages.append({'role': 'user', 'content': message})

                #TODO: refactor this 4 lines
                tempmessages = messages
                if (args.max and args.max > 0):
                    tempmessages = messages[-int(args.max):]
                    args.max = args.max + 1

            except LLMDotMessageError:
                #messages = cleanDotMessages(messages)
                #printGreen("here appending user message, asking model to retry, as it did not output valid JSON")
                messages.append({'role': 'user', 'content': 'SYSTEM MESSAGE: This was not a valid response, please try again.'})

                #TODO: refactor this 4 lines
                tempmessages = messages
                if (args.max and args.max > 0):
                    tempmessages = messages[-int(args.max):]
                    args.max = args.max + 1

            count += 1
            if count > 9:
                print("Error: Too many attempts to retry, exiting.")
                sys.exit()

        console = Console()

        import json

        if not isinstance(ret, list):
            mystr = ""
            if (len(ret) > 0):
                mystr += str(ret)

            ret = [ret]

        jo = None
        try:
            jo = json.loads(jsoncommand)
            continue_processing = True
        except:
            continue_processing = False

        max_iterations = 20  # Add a maximum number of iterations as a safeguard
        count = 0
        while continue_processing and count < max_iterations:
            pres = ""
            if (args.identity):
                pres = args.identity + ": "
            toolCallString = ""
            if (len(jsoncommand) > 0):
                jo = json.loads(jsoncommand)
                #get tool_call name
                first = False
                for j in jo:
                    if 'tool_call' in j: 
                        toolName = str(j['tool_call'])
                        arguments = json.dumps(j['arguments'])
                        if first:
                            toolCallString += ", "
                        toolCallString += toolName + ": " + arguments
                        first = True
            #if (toolCallString != ""):
            #    toolCallString = "LLM Called Tool(s): " + toolCallString 




            if not hasattr(args, 'last_tool_call_string') or (args.last_tool_call_string == "" and toolCallString != ""):
                args.last_tool_call_string = toolCallString
            elif hasattr(args, 'last_tool_call_string') and args.last_tool_call_string != "" and toolCallString != "":
                #they shoudln't match that's erroneous but let's see
                match =  args.last_tool_call_string == toolCallString
                if match:
                    if not hasattr(args, 'last_tool_call_screen_repeat_count'):
                        args.last_tool_call_screen_repeat_count = 1
                    else:
                        args.last_tool_call_screen_repeat_count += 1
                else:
                    args.last_tool_call_screen_repeat_count = 0
                args.last_tool_call_string = toolCallString

            #do last tool call timestamp
            if not hasattr(args, 'last_tool_call_timestamp'):
                args.last_tool_call_timestamp = datetime.datetime.now()

            #is it set, the repeat countyer
            if hasattr(args, 'last_tool_call_screen_repeat_count') and args.last_tool_call_screen_repeat_count > 1:
                toolCallString += " (command repeated " + str(args.last_tool_call_screen_repeat_count) + " times)"
            elif hasattr(args, 'last_tool_call_screen_repeat_count') and args.last_tool_call_screen_repeat_count == 1:
                toolCallString += " (command repeated once)"

            #now if it's 5 we need to throw an error
            if hasattr(args, 'last_tool_call_screen_repeat_count') and args.last_tool_call_screen_repeat_count > 2:
                if hasattr(args, 'last_tool_call_timestamp'):
                    if False:#(datetime.datetime.now() - args.last_tool_call_timestamp).total_seconds() > 60:
                        args.last_tool_call_screen_repeat_count = 0
                    else:
                        raise LLMRepetitiveResponseError("LLM has ended the conversation because the tool call was repeated too many times in quick succession.")

            retString = ""
            for r in ret:
                retString += str(r) + " "

            #messages.append({"role": "assistant", "content": (pres + retString.strip() + " " + toolCallString).strip()}) 
            messages.append({"role": "assistant", "content": (".")})
            
            vdRet = ""
            for retitem in ret:
                try:
                    retitem = json.dumps(retitem)
                except:
                    pass
                if JSONDetector.is_valid_json(retitem) or JSONDetector.is_valid_json(jsoncommand):
                    try:
              
                        #check if tool_call is element in 
                        jco = json.loads(jsoncommand)
                        for j in jco:
                            if 'tool_call' in j:
                                if j['tool_call'] == "assert_completion":  #AI right now this is a very hard-coded method to assert completion
                                    try:
                                        #check if loaded_role is assigned and is a Role
                                        if loaded_role is not None and isinstance(loaded_role, Role):
                                            directive = process_mission()
                                            #now add the directive as an assistant message
                                            if directive.strip() != "":
                                                messages.append({"role": "user", "content": directive})
                                            else:
                                                messages.append({"role": "user", "content": "."}) #AI dwe may not want this
                                            if loaded_role.get_current_task_cursor() is None:
                                                force_tools_flag = False
                                    except:
                                        pass
                                if j['tool_call'] == "conversation_control":
                                    try:
                                        action = "None"
                                        user_message = ""

                                        if 'action' in j['arguments']:
                                            action = j['arguments']['action']

                                        origmessage = ""

                                        if 'message' in j['arguments']:
                                            origmessage = j['arguments']['message']
                                            user_message = j['arguments']['message']
                                            message_combined = "LLM Called Tool(s): " + toolCallString + "\nLLM Ended Conversation using action "+action+" as part of conversation_control tool with message: " + user_message
                                        else:
                                            origmessage = "LLM Called Tool(s): " + toolCallString + "\nLLM Ended Conversation using action "+action+" as part of conversation_control tool"
                                            user_message = origmessage

                                        printSunsetOrange(origmessage+"\n")

                                        # If the latest message in messages is an assistant message where content is blank, put the combined message in that message now
                                        if (len(messages) > 0 and messages[-1]['role'] == "assistant" and (messages[-1]['content'].strip() == "" or messages[-1]['content'].strip() == "['']")):
                                            messages[-1]['content'] = message_combined
                                        else:
                                            # Is the latest message assistant or user
                                            if (len(messages) > 0 and messages[-1]['role'] == "assistant"):
                                                # Add blank user message to keep order correct
                                                messages.append({"role": "user", "content": ""})
                                            messages.append({"role": "assistant", "content": message_combined})

                                        if action == "end":
                                            continue_processing = False
                                            break
                                        elif action == "hangup":
                                            sys.exit(123)

                                    except LLMEndConversationError as e:
                                        raise e
                                    except Exception as e:
                                        raise LLMEndConversationError("LLM has ended the conversation with no message " + str(e))
                                        
                                    continue_processing = False
                                    break
                            else:
                                continue_processing = False
                                break
                    except LLMEndConversationError as e:
                        raise e
                    except Exception as e:
                        pass

                    # with Progress(SpinnerColumn('dots'), user_message + "\n", console=console) as progress:
                   #     task = progress.add_task("Querying...", start=True)
                   #     try:
                   #         vdRet += vd.process_json_command(retitem)
                   #     except Exception as e:
                   #         print(f"Error processing JSON command (are you adding markup?): {str(e)}")
                   #         continue_processing = False
                            #break
                        #progress.remove_task(task)

                    #AI there is a bug with :sysedit it doesn't seem to be working i.e. {{date}} but the AI isn't seeing it

                    #AI role structure ok so, a thought. each tool can have dynamic params, that is, they get specified in the yaml and each param will be defined as a name + a description, optional/required. all tools will allow for this. they may not process it, but it will certainly be possible to, at runtime, add dynamic input parameters to any tool.  

                    
                    #AI feat add way to fully de-instantiate tools - kill the tool instance and reinstantiate 

                    #next steps on mission development, we need to make sure the execution isn't halted for user input as it is today b/c that's an issue - that user input isn't even processed 

                    #AI feat add it so when you ctrl-c it says do it again to exit, because what's happening is i'm trying to interrupt the LLM but sometimes he beats me to the punch and the program exits
                    
                    resp=""
                    error = False
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        TextColumn("{task.fields[user_message]}"),
                        console=console
                    ) as progress:

                        try: #TODO should be a better way to do this, that is, to check if it's a json string with a tool_call key
                            #is retitem a json string and if so load it to an object

                            if JSONDetector.is_valid_json(retitem): 
                                jo = json.loads(retitem)
                            elif len(jsoncommand) > 0 and JSONDetector.is_valid_json(jsoncommand):
                                jo = json.loads(jsoncommand)

                            jcount = 0
                            resp += "["
                            if (True): #AI refactor this by just removing this statement and fix subsequent indent
                                while isinstance(jo, str):
                                    try:
                                        jo = json.loads(jo)
                                    except:
                                        break
                                for j in jo:
                                    if 'tool_call' in j: #AI this is the start of the loop to process an indivitual tool_call
                                        
                                        toolName = j['tool_call']
                                        
                                        found = False

                                        #AI bug when the role has a message and you also do a -l from CLI, it clobbers the message array a bit

                                        #files = os.listdir(args.tools)
                                        #ok we need to actually get a list of files from the 
                                        #file element in the json object
                                        tfiles = []
                                        for tool in getActiveTools(): #TODO surely refactor this and the next 10s of lines
                                            file = tool["file"]
                                            #tool.pop("file", None)
                                            if (file not in tfiles):
                                                tfiles.insert(0, file)

                                        for file in tfiles:
                                            if (found):
                                                break
                                            json_objects = []
                                            if file.endswith(".py"):
                                                import importlib.util
                                                import inspect
                                                #import the class, we will use the following code: https://stackoverflow.com/a/67692
                                                # Generate a unique module name
                                                unique_module_name = f"module_{uuid.uuid4().hex}"

                                                # Load the module
                                                spec = importlib.util.spec_from_file_location(unique_module_name, file)
                                                module = importlib.util.module_from_spec(spec)
                                                spec.loader.exec_module(module)

                                                # List all attributes of the module
                                                attributes = dir(module)

                                                # Filter out the classes
                                                loaded_classes = [getattr(module, attr) for attr in attributes if isinstance(getattr(module, attr), type)]

                                                # Filter out the abstract classes
                                                loaded_classes = [cls for cls in loaded_classes if not inspect.isabstract(cls)]

                                                #determine if classes has been set and if not set it
                                                classes = loaded_classes

                                                for myclass in classes:

                                                    if issubclass(myclass, ToolBase):

                                                        try:
                                                            inst = myclass()

                                                            # Assuming myclass is the dynamically loaded object
                                                            name_property = getattr(myclass, 'name', None)
                                                            if isinstance(name_property, property):
                                                                name_value = name_property.fget(inst)  # Call the getter method #AI this line is BROOOKEN....
                                                            else:
                                                                name_value = name_property  # Just get the attribute value
                                                            
                                                            if isinstance(name_value, str):
                                                                # If it's a string, check for equality
                                                                good = name_value == toolName
                                                            elif isinstance(name_value, list):
                                                                # If it's a list, check if tool_name is in the list
                                                                good = toolName in name_value

                                                            if good:

                                                                try:
                                                                    if hasattr(myclass, 'function_info'):
                                                                        for function in json.loads(myclass.function_info()):
                                                                            function_name = function['function']['name']
                                                                            #we need to make sure toolName i.e. role_manager is in the function_info
                                                                            
                                                                            #is_correct_tool_name = toolName == j['tool_call'] #j is wrong place... must come from myclass
                                                                            is_correct_tool_name = toolName == function_name
                                                                            if is_correct_tool_name:

                                                                                j['arguments']['function_name'] = function_name
                                                                                instance = get_tool_instance(toolName, myclass)  # Use the function to get the instance
                                                                                #AI OK so I guess we now have an instantiated tool class
                                                                                try:
                                                                                    if (jcount > 0):
                                                                                        resp += ","
                                                                                    #is loaded_role set and a Role
                                                                                    if loaded_role is not None and isinstance(loaded_role, Role):
                                                                                        resp += instance.execute(json.dumps(j['arguments']), loaded_role.variables) #AI this is where tools are actually executed
                                                                                    else:
                                                                                        resp += instance.execute(json.dumps(j['arguments'])) #AI this is where tools are actually executed
                                                                                    
                                                                                    if "{\"stdout\": null, \"stderr\": null, \"returncode\": -15}" in resp:
                                                                                        #kill this process
                                                                                        print("Exiting ai.py process")
                                                                                        os.kill(os.getpid(), signal.SIGKILL)
                                                                                        
                                                                                    jcount = jcount + 1
                                                                                    found = True #TODO refactor this, it's not needed probably
                                                                                    #print("done and resp is " + resp)
                                                                                except KeyboardInterrupt:
                                                                                    print("interrupted....")
                                                                                    raise KeyboardInterrupt
                                                                                except Exception as e:
                                                                                    print(str(e))
                                                                                    print('Debug: Executing instance with execute method...')
                                                                                    print(f"Exception occurred: {e}")
                                                                                    print(f"Type of exception: {type(e)}")
                                                                                    print(f"Arguments: {e.args}")
                                                                                    print(f"Traceback: {traceback.format_exc()}")

                                                                                try:
                                                                                    if j['tool_call'] == "role_creator":
                                                                                        # Load JSON data
                                                                                        data = j['arguments']
                                                                                        # Assign to variables
                                                                                        role_name = data['role_name']
                                                                                        prompt_files = []
                                                                                        tool_files = []
                                                                                        try:
                                                                                            prompt_files = data['prompt_files']
                                                                                        except:
                                                                                            pass
                                                                                        try:
                                                                                            tool_files = data['tool_files']
                                                                                        except:
                                                                                            pass
                                                                                        loadRole(role_name, tool_files, prompt_files)
                                                                                except:
                                                                                    pass

                                                                                break
                                                                except Exception as e:
                                                                    print("Error: " + str(e)) #AI refactor this should be going to the messages array not printed here.
                                                                    resp += str(e)
                                                        except Exception as e:
                                                            print("Error: " + str(e)) #AI refactor this should be going to the messages array not printed here. REFACTOR OMG
                                                            resp += str(e)

                                        if not found:
                                            resp += ("[ERROR COULD NOT FIND/LOAD TOOL] - Tool called: " + j['tool_call'] + " with the arguments: " + str(j['arguments']))
                                            error = True
                                    
                                    else:
                                        pass

                            resp += "]"
                        except:
                            #we assume we did not get an openai-style tool_call response  #TODO should be a better way to do this 
                            continue_processing = False


                    #vdRet += "\nSYSTEMe ("+str(count+1)+" of "+str(len(ret))+") JSON Command Complete!\nRESPONSE: " + resp
                    #if count == 0:

                if not error:
                    got_stdout = False
                    got_non = False
                    try:
                        joo = json.loads(resp)

                        if isinstance(joo, dict):
                            # Handle single JSON object
                            required_keys = {'stdout', 'stderr', 'returncode', 'execution_time'}
                            if required_keys.issubset(joo):
                                stdout_white_color = "\033[0;37m" + joo['stdout'] + "\033[0m"
                                stderr_red_color = "\033[0;31m" + joo['stderr'] + "\033[0m"
                                vdRet += (
                                    "\n\nSTDOUT:\n" + stdout_white_color +
                                    "\n\nSTDERR:\n" + stderr_red_color +
                                    "\n\nRETURN CODE: " + str(joo['returncode']) +
                                    "\n\nEXECUTION TIME: " + str(joo['execution_time']) + " seconds"
                                )
                                got_stdout = True
                            else:
                                # Missing required keys; treat as a generic TOOL RESPONSE
                                vdRet += "\n\n\nnTOOL RESPONSE: " + resp

                        elif isinstance(joo, list):
                            # Handle list of JSON objects
                            for item in joo:
                                if isinstance(item, dict):
                                    required_keys = {'stdout', 'stderr', 'returncode', 'execution_time'}
                                    if required_keys.issubset(item):
                                        stdout_white_color = "\033[0;37m" + item['stdout'] + "\033[0m"
                                        stderr_red_color = "\033[0;31m" + item['stderr'] + "\033[0m"
                                        vdRet += (
                                            "\n\nSTDOUT:\n" + stdout_white_color +
                                            "\n\nSTDERR:\n" + stderr_red_color +
                                            "\n\nRETURN CODE: " + str(item['returncode']) +
                                            "\n\nEXECUTION TIME: " + str(item['execution_time']) + " seconds"
                                        )
                                        got_stdout = True
                                    else:
                                        # Missing required keys; append generic TOOL RESPONSE
                                        vdRet += "\n\n\nxTOOL RESPONSE: " + json.dumps(item)
                                        got_non = True
                                else:
                                    # Item is not a dict; append generic TOOL RESPONSE
                                    vdRet += "\n\n\nxTOOL RESPONSE: " + str(item)
                                    got_non = True
                        else:
                            # JSON is neither dict nor list; append generic TOOL RESPONSE
                            vdRet += "\n\n\nnTOOL RESPONSE: " + resp

                    except json.JSONDecodeError:
                        # JSON parsing failed
                        got_non = True
                        vdRet += "\n\n\nrTOOL RESPONSE: " + resp
                    except Exception as e:
                        # Other exceptions
                        vdRet += f"\n\n\nERROR PROCESSING RESPONSE: {str(e)}"

                    # If neither stdout nor non-stdout content was processed
                    if not got_stdout and not got_non:
                        vdRet += "\n\n\nnTOOL RESPONSE: " + resp

                else:
                    vdRet += "ERROR: " + resp

                printGrey(vdRet + "\n")

                # Optional: Sleep for a short duration
                try:
                    time.sleep(0.5)  # Consider if this delay is necessary
                except KeyboardInterrupt:
                    print("ELEPHANT")
                    pass


            if continue_processing:
                
                #messages.append({'role': 'user', 'content': vdRet.strip()})
                messages.append({'role': 'user', 'content': "TOOL CALL: " + toolCallString.strip() + "\n\n" + vdRet.strip()})
                #TODO: refactor this 4 lines
                tempmessages = messages
                if (args.max and args.max > 0):
                    tempmessages = messages[-int(args.max):]
                    args.max = args.max + 1
                tempmessages = refreshSystemPrompt(tempmessages, args) #TODO refactor this together with the code around the line that says HORSE 

                try:
                    if (len(args.tools_array) == 0):
                        retitem, jsoncommand = printAiContent(assistantt.complete_chat(tempmessages, {}, args.stream))
                    else:
                        retitem, jsoncommand = printAiContent(assistantt.complete_chat(tempmessages, {}, args.stream, getActiveTools(), force_tools_flag))
                    if isinstance(retitem, list) and len(retitem) > 0:
                        ret = [retitem[0]]  # Take only the first item if it's a list
                    else:
                        ret = [retitem]
                    count = 0

                    if "respond" in json.dumps(ret[0]):
                        continue_processing = False
                    elif len(jsoncommand) > 0:
                        continue_processing = True
                    elif not JSONDetector.is_valid_json(json.dumps(ret[0])):
                        #print("No valid JSON command received. Ending processing.")
                        continue_processing = False
                except Exception as e:
                    print(f"Error in AI chat completion: {str(e)}")
                    vdRet = 'SYSTEM: ERROR ' + str(e)
                    continue_processing = False

            count += 1

        if count >= max_iterations:
            print("Maximum number of iterations reached. Ending processing.")


        
        #TODO: refactor this 4 lines 
        tempmessages = messages
        if (args.max and args.max > 0):
            tempmessages = messages[-int(args.max):]
            args.max = args.max + 1

        init_assistantt() #this is here only to reset the model in case a :r command has requested its reset after a response
        try:
            return retitem
        except:
            try:
                return ret[0]
            except:
                return ""


    else: #it is NOT stdout
        #TODO: refactor this 4 lines 
        tempmessages = messages
        if args.model[0:2] == "o1":
            if tempmessages[0]['role'] == "system":
                tempmessages.pop(0)
        if (args.max and args.max > 0):
            tempmessages = messages[-int(args.max):]
            args.max = args.max + 1
        return printAiContent(assistantt.complete_chat(tempmessages, {}, args.stream), True)

def clear_terminal():
    print("\033[2J\033[1;1H")  # Clear screen
    return
    #if os.name == 'nt':  # If the OS is Windows
    #    os.system('cls')
    #else:  # If the OS is Unix-like (macOS, Linux)
    #    os.system('clear')

def load_conversation(arrayLoc):
    """
    Load messages from the specified files array index pointing to the conversation file and update the state.
    """
    global messages #TODO refactor
    try:
        messages = getMessagesFromFile(files[arrayLoc])
        #messagesCopy = []
        #for item in messages:
        #    messagesCopy.append(item)

        #hasSystemMessage = (len(messages) > 0 and messages[0]['role'] == "system")
        clear_terminal()
        printMessagesToScreen(True)

        #messages = messagesCopy

        return messages  # Return the loaded messages

    except Exception as e:
        print("Exception in loading conversation (or file is empty): " + str(e))
        return []  # Return None if loading fails

def add_new_conversation():
    global files, files_cursor, currFileName, messages
    #at this point the code that captured ctrln should have saved the conversation

    # Create a new conversation file
    new_convo_file = f"/dev/shm/convo.temp.{os.getpid()}"  # Unique file for the new conversation

    #if new_convo_file exists, take the pid number and add a .1 behind it. if that exists, then do a .2. and so on. so then new_convo_file will be a unqiue filename eventually
    if os.path.exists(new_convo_file):
        i = 1
        while os.path.exists(f"/dev/shm/convo.temp.{os.getpid()}." + str(i)):
            i += 1
        new_convo_file = f"/dev/shm/convo.temp.{os.getpid()}." + str(i)

    # Write empty content to the new conversation file
    with open(new_convo_file, "w") as f:
        f.write("")  # You can initialize with some default content if needed

    # Append the new conversation file to the files list
    files.insert(0,new_convo_file)

    # Move to the newly created conversation
    files_cursor = 0

    messages = load_conversation(files_cursor) #AI refactor global use of messages, maybe a singleton
    currFileName = files[files_cursor]
    #printMessagesToScreen()
    clear_terminal()
    printGrey(f"\nNew conversation created: {new_convo_file}\n")
        

def invertMessages(messages=[]):
    inverted_messages = []
    for message in messages:
        if message['role'] == "assistant":
            inverted_messages.append({"role": "user", "content": message['content']})
        elif message['role'] == "user":
            inverted_messages.append({"role": "assistant", "content": message['content']})
        else:
            inverted_messages.append(message)
    return inverted_messages


def outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages(file="", print_file_info=True):
    if (file != ""):
        try:
            compareMessages = getMessagesFromFile(file)
            #are the messages from messages and compareMessages the same?
            if (len(messages) == len(compareMessages)):
                #check each message
                match = True
                for i in range(len(messages)):
                    if (messages[i]['content'] != compareMessages[i]['content']):
                        #there was a mismatch between messages and compareMessages, meaning there was an update, so write the file")
                        outputConversationToFile("", None, print_file_info)
                        return 
                #dlog("there was no mismatch between messages and compareMessages, meaning there was no update, so don't write the file")
                return 
        except:
            #dlog("we did not write to a file...")
            pass

    for message in messages:
        if (message['role'] != "system"):
            #there is at least one NON-system message, therefore we SHOULD save the conversation
            if (file != ""):
                outputConversationToFile(file, None, print_file_info)
            else:
                outputConversationToFile("", None, print_file_info)
            return
    #dlog("there were no non-system messages, so we did not write a file")


#AI eureeka moment, there needs to be a generic 'tool' tand one or more get created/instantiated when a role is loaded. The tool would be used to guide the role'd LLM through a set of tasks defined in the role itself. the role, as I see it, will need to have tasks that imply a certain set of steps and a certain set of tools for each step. i guess each task will need some description of what is required. in this way, a task can have certain baseline tools but then also tools that effectively guide the LLM through the process of completing a multi-step task and limit the tools at each step, and the tools themselves will be instantiated as needed (the ones guiding the process)

#AI unrelated to last note, we need to talk about a 'handoff' method to hand things off between different roles or whatever

def load_commands(directory="./commands"):
    
    if False:
        """
        Load all command classes from Python files in the specified directory.

        :param directory: The directory to scan for command Python files.
        """
        global loaded_commands
        global commands  # Ensure commands is treated as global
        commands = commands if commands else []  # Only initialize if not defined

        command_details = []  # Temporary list to hold command details for appending

        for filename in os.listdir(directory):
            if filename.endswith(".py"):
                file_path = os.path.join(directory, filename)
                module_name = filename[:-3]

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and issubclass(attr, Command) and attr is not Command:
                        command_instance = attr()  # Get the singleton instance
                        command_name = command_instance.get_name()  # Get the command name
                        command_description = command_instance.get_description()  # Get the command description

                        # Append command details to the command_details list
                        command_details.append({
                            "command": command_name,
                            "description": command_description,
                            "tool_color": "brown",  # Example color
                            "desc_color": "green"   # Example color
                        })

                        # Store the command instance in the loaded commands dictionary
                        commands[command_name] = command_instance

        # Append all collected command details to the commands array
        for detail in command_details:
            commands.append(detail)

        loaded_commands = commands
    


def load_colon_commands(directory, commands_array):
    """
    Load colon commands from .colon files in the specified directory.

    :param directory: The directory to scan for .colon files.
    :param commands_array: The array to append commands to.
    """
    global content_dict
    content_dict = {}

    for filename in os.listdir(directory):
        if filename.endswith('.colon'):
            command_name = f":{filename[:-6]}"  # Remove the .colon extension
            description = f"Insert {filename} text before the message that follows from user."

            # Read the content of the file
            with open(os.path.join(directory, filename), 'r') as file:
                content = file.read()

            # Append to the commands array
            commands_array.append({
                "command": command_name,
                "description": description,
                "tool_color": "orange",  # New color scheme for colon commands
                "desc_color": "purple"    # New color scheme for descriptions
            })

            # Store the content in the content dictionary
            content_dict[filename[:-6]] = content
    
    
def process_commands(myinput):
    pattern = r':([a-z0-9_]+)([^:]*?)(?=:(?![a-z0-9])|$)'
    result = []
    global force_tools_flag

    # Loop through the input to find all matches
    while True:
        match = re.search(pattern, myinput)
        if match:
            # Add to result
            mystr = match.string[match.start(1):match.end()]  # Get the command without the colon
            if mystr not in result:
                result.append(mystr)
            myinput = myinput[:match.start()] + myinput[match.end():]  # Remove processed command from myinput
        else:
            break

    unmatched = []
    matched = []
    global loaded_role
    if isinstance(loaded_role, Role):
        for name in result:
            mission = loaded_role.get_mission(name)
            if mission:
                matched.append(name)

                # Add both description and directive to myinput
                myinput += f" {mission.description} - {mission.name}: "
                for task in mission.tasks:
                    myinput += f"   - {task.directive}\n"
                    myinput += f"     - {task.description}\n"
                    # Load the tools needed for this task
                    if task.tools:
                        loaded_role.set_current_mission_cursor(mission.name)
                        loaded_role.set_current_task_cursor(-1)
                    break #just need the 1st one

            else:
                unmatched.append(name)
    else:
        # If no loaded_role or not a Role instance, treat all results as unmatched
        unmatched.extend(result)

    # Reconstruct the input string with unmatched commands
    bak = " ".join(f":{cmd}" for cmd in unmatched)
    if myinput.strip():
        bak += " " + myinput.strip()

    return bak.strip()  # Return the modified input string

def process_mission():
    global loaded_role
    global force_tools_flag 

    # Initialize an empty string to hold task details
    task_details = ""

    if loaded_role is None:
        return ""

    # Check if loaded role is valid and cursors are set
    if isinstance(loaded_role, Role) and loaded_role.get_current_mission_cursor() is not None and loaded_role.get_current_task_cursor() is not None:
        force_tools_flag = True  # Set the flag to force tools activation
        current_mission = loaded_role.get_mission(loaded_role.get_current_mission_cursor())
        
        # Advance the task cursor first
        task_index = loaded_role.get_current_task_cursor()
        if task_index < len(current_mission.get_tasks()) - 1:
            loaded_role.set_current_task_cursor(loaded_role.get_current_task_cursor() + 1)  # Move to next task
        else:
            loaded_role.set_current_task_cursor(None)  # No more tasks, reset cursor
            loaded_role.set_current_mission_cursor(None)
            printYellow("All tasks appear completed for this mission.")
            return ""

        # Get the current task after advancing the cursor
        current_task = current_mission.get_tasks()[loaded_role.get_current_task_cursor()]

        try:
            # Logic to handle the current task
            # Get task description and directive for the details string
            task_details += f"Task Description: {current_task.description}\n"
            task_details += f"Task Directive: {current_task.directive}\n"

            printPeach(task_details)

            # Load the tools needed for this task
            if current_task.tools:
                printYellow("Loading tools for the next task...")
                deactivateTools()
                activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(current_task.tools)
                printActiveTools()  # Print active tools after loading them

        except Exception as e:
            # If any error occurs, reset cursors to None
            print(f"Error occurred while processing task: {e}")
            loaded_role.set_current_mission_cursor(None)
            loaded_role.set_current_task_cursor(None)
            return ""

    else:
        # If cursors are None, do nothing
        #print("No active mission or task cursor is set.")
        pass

    # Return the task details string
    return task_details.strip()

def refreshUI(thefiles=[], show_file_info=False):
    """
    Refreshes the UI with the content of messages from the last file in thefiles
    TODO: probably refactor this out - it seems to only be used the first time
          files that match the search term are gathered
    """
    #make files == what's in thefiles
    global files
    global messages
    files = thefiles
    messages = getMessagesFromFile(files[0])
    currFileName = files[0]
    print("\033[2J\033[1;1H") #clear screen
    printMessagesToScreen(True)
    if (show_file_info):
        print('7 refresh ui')
        printFileInformationLine(files[0])

#AI bug :remresp isn't always working or the command isn't getting hit

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

        
def main():
    global args, force_tools_flag  # Add force_tools_flag here
    args = parser.parse_args()
    loadColonStrings()
    loadColonCommands()
    loadSysColons()

    args.tools_array = []
    
    force_tools_flag = False
    if (args.onlytools):
        force_tools_flag = True

    if (args.sysfile_list):
        print()
        # Get the list of .txt files in the specified directory, ordered by alphabetical order
        txt_files = [f[:-4] for f in os.listdir(syspdirectory) if f.endswith('.txt')]
        txt_files.sort()

        #now get a new array where it's sorted by most recent down to least
        txt_files_chron = sorted(txt_files, key=lambda x: os.path.getmtime(syspdirectory + "/" + x + ".txt"), reverse=True)
        
        #iterate over both arrays make 2 colums and give them labels and make it yellow
        printRed("System Prompt Files (alphabetial)".ljust(30) + "Last Modified")
        printYellow("------------------------------------------------------------")
        for i in range(len(txt_files)):
            #first a header
            printPeach(f"{txt_files[i]}".ljust(30) + f"{txt_files_chron[i]}")

        print()
        print("You can use the --sysfile or --sysfile_edit option to load a system prompt from the list above.\n")
        sys.exit(0)

    if (args.role_list):
        printRoleInfo()
        print()
        print("You can use the --role option to load a role from the list above.\n")
        sys.exit(0)

    if args.sysfile and ("git" in args.sysfile.split(" ")):
        args.usecomments = True

    ocf = False
    try:
        if len(args.ocf) > 0:
            ocf = True
    except:
        pass

    if (args.toolsfile is not None and len(args.toolsfile) > 0 and not args.notools):
        print()
        terms = getCanonicalToolsNamesFromFile(args.toolsfile)
        terms = list(set(terms))
        terms.sort()
        activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(terms)

    refreshTools()


    if args.tlist:
        for tool in args.tools_array:
            print(tool['canonical_name'])
        #exit program
        sys.exit(0)
                    

    if args.tools is not None and not args.notools and len(args.tools) > 0 and not args.role:  #if role, then tools are loaded when the role is
        activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(args.tools)


    if args.role_edit: #open role file, allow editing, then exit
        rfile = get_role_file(args.role_edit)
        os.system('vi ' + rfile)
        sys.exit(0)


    if (args.outputcode):
        args.oneshot = True
    if (args.outputcodefile):
        args.oneshot = True

    if (args.jou is not None):
        if (args.jo is None) or (args.jo is not None and len(args.jo) > len(args.jou)):
            args.jo = args.jou

    if (args.jo is not None or args.jou is not None):
        args.oneshot = True

    threading.Thread
    thread = threading.Thread(target=lazy_load_assistant)
    thread.start()

    if args.models:
        print_models()
        sys.exit(0)

    args.init_assistant = False

    global mystdin
    mystdin = ""

    #global variables for interrupt handling
    global interrupt_requested
    interrupt_requested = threading.Event()
    global interrupt_handled
    interrupt_handled = threading.Event()
    global original_sigint_handler
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    global getch_active
    getch_active = False  # Flag to indicate if getch is active
    global latest_message
    latest_message = ""  # Global variable to store the latest message

    # Start the interrupt checking thread
    global killThread
    killThread = False
    interrupt_thread = threading.Thread(target=check_for_interrupt, daemon=True)
    interrupt_thread.start()

    global messages
    files = []
    messages = []
    currFileName= ""
            

    if (args.image):
        if args.size:
            #case 1,2,3
            if args.size == 2:
                size = "1024x1792"
            if args.size == 3:
                size = "1792x1024"
            else:
                size = "1024x1024"
            sendDalle3APIRequest(args.image, size)
        else:
            sendDalle3APIRequest(args.image)
        os._exit(0)


    messages = refreshSystemPrompt(messages, args)

    if (len(args.url) > 0):
        #error out if no url specified
        if (args.url == ""):
            print("Error: -u/--url requires a url")
            sys.exit(1)
        args.prompt = url_to_text(args.url) + "\n\n" + args.prompt
        

    lostinput = ""


    if (args.filename != ""):
        #identify newest .json file in the ./conversation directory and put it in filename

        if (args.filename != ""):
            filename = args.filename
            #if (".json" not in args.filename):

                #filename = filename+".json"
        else:
            filename = ""
        files = []
        files.insert(0,filename)


        #open filename and read json into messages
        with open(filename, "r") as f:
            text = f.read()
            #print("OK, we read the file, now we're going to parse the json and print the messages to the screen")
            #print("text is " + text  )
            messages = json.loads(text)
            print("Warning: any arguments that affect prompting are ignored when reading from files")
            #refreshSystemPrompt(messages, args)
            #if setuptxt and len(setuptxt) > 0: #replace the system-role message in the messages collection with the new setuptxt
            #    messages[0]['content'] = setuptxt
            f.close()
        #print("OK, we parsed the json, now we're going to print the messages to the screen")
        lostinput = printMessagesToScreen()
    elif (os.path.exists(os.path.join(conversationDirectory, "flag"))):
        with open(os.path.join(conversationDirectory,"flag"), "r") as fff:
            filename = fff.read().strip()
            fff.close()
            with open(os.path.join(conversationDirectory,filename), "r") as ffff:
                text = ffff.read()
                print("Continuing conversation...\n")
                ffff.close()
            
            #text is 'messages' json, so parse and add to messages
            messages = json.loads(text)
            #print(messages)
            #os._exit(1)
            lostinput = printMessagesToScreen()
            os.remove(os.path.join(conversationDirectory,"flag"))
    elif not (args.oneshot) or (args.oneshot and args.last_conversation):
        # Check for files matching the search term in the current directory
        search_pattern = f"{args.searchterm}.*.json"
        matching_files = sorted(glob.glob(search_pattern), reverse=True)
        search_pattern = f"{args.searchterm}.json"
        matching_files += sorted(glob.glob(search_pattern), reverse=True)
        search_pattern = f"{args.searchterm}.json.*"
        matching_files += sorted(glob.glob(search_pattern), reverse=True)

        
        #now sort by date, oldest first
        matching_files.sort(key=os.path.getmtime)

        files = []

        # Iterate through matching files to check for valid JSON with 'role'
        for file in matching_files:
            try:
                with open(file, "r") as f:
                    text = f.read()
                    messages = json.loads(text)

                    # Check if 'messages' contains an array with elements including 'role'
                    if isinstance(messages, list) and any('role' in item for item in messages):
                        files.insert(0,file)
            except (json.JSONDecodeError, FileNotFoundError):  # Handle JSON decoding errors or file not found
                continue

        # If no valid files were found, execute the existing logic to get the files array
        if not files:
            files = get_files_collection(args.searchterm, False)

        currFileName = files[0]  # Get the most recent file

        try:
            with open(currFileName, "r") as f:
                text = f.read()
                messages = json.loads(text)#AI this is frequently the first time messages is set to values in a file
        except (json.JSONDecodeError, FileNotFoundError):  # Handle potential empty/new dev/shm file
            pass



    #remove last element of messages array if it is a user message, we don't want to force a response on first load 
    try:
        if (len(messages) > 0 and messages[len(messages)-1]['role'] == "user" and args.prompt == ""):
            messages.pop()
    except: #shouldn't happen
        pass

    messages_cursor=0

    paste = False
    #gotAnyRequestResult = False

    files_cursor = 0 
    if (args.last_conversation) and not args.oneshot:
        messages = getMessagesFromFile(files[files_cursor])
    elif args.last_conversation and args.oneshot:
        messages = getMessagesFromFile(files[files_cursor])
        

    #add prompt
    if (args.prompt != "" and not args.procimage):
        messages.append({
            "role": "user",
            "content": args.prompt
        })


    if (args.procimage and not args.prompt):
        print("You must enter a prompt with an image to process.")
        os._exit(1)


    if (args.procimage and args.prompt):
        try:
            #if the file is not a jpg, convert it
            if (args.procimage[-4:] != ".jpg"):
                im = Image.open(args.procimage)
                im.save(args.procimage + ".jpg")
                args.procimage = args.procimage + ".jpg"
        except Exception as e:
            print("vError: " + str(e))
            os._exit(1)
        try:
            with open(args.procimage, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_file.close()
                doImage = True
        except Exception as e:
            print("wError: " + str(e))
            os._exit(1)
        new_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": args.prompt
                }
            ]
        }
        new_message['content'].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{encoded_string}"
            }
        })
        messages.append(new_message)


    if not (args.oneshot):
        printMessagesToScreen() 
        #printGrey("348") 
        print() #TODO we want this to go away or be moved or whatever - refactor deal
        if (args.filename != ""):
            printFileInformationLine(args.filename)
        print(Fore.WHITE, end='')
        

    dontProcessInputYet = False
    generatedImage = False


    # Load commands at the start of the program
    load_commands()

    if args.role: #AI Todo we need to figure out if this should prevent other execution above or elsewhere
        # Load the role
        load_role(args.role)

    myinput = ""

    while True:  #AI this is the main conversation loop - takes in input and sends it to the API, and over and over

        #is the last msg from a user? make sure the content is not just whitespace or blank or escape characters, like \x03
        if (len(messages) > 0 and messages[-1]['role'] == "user" and not args.procimage):
            foundPrintableChar = False
            try:
                mystr = messages[-1]['content'].strip()
            except Exception as e:
                print("Hmm... this is not a string or what?" + str(e) + " " + str(messages[-1]['content']))
            for char in (str(messages[-1]['content']).strip()):
                if char not in string.printable:
                    pass
                else:
                    foundPrintableChar = True
                    break
            if not foundPrintableChar:
                messages.pop() #that user message is garbage, remove it

                
        #AI IDEA what if the mission metadata could be in the system message of the whatever

        #only capture user input if last message was not from user (this accommodates predefined prompts)
        if not (len(messages) > 0 and messages[-1]['role'] == "user"): #AI it is in here that we capture user input (this calls getch())

            if (not paste): 
                messagesCopy = []
                for item in messages:
                    messagesCopy.append(item)
                try:
                    hasSystemMessage = (messages[0]['role'] == "system")
                except:
                    hasSystemMessage = False
                if (dontProcessInputYet == False) or (generatedImage == True):
                    if (args.searchterm):    #assuming this is the 1st run of this loop since this gets None'd out
                        printFileInformationLine(files[0]) #making an unsafe assumption that files is populated
                        print()
                        args.searchterm = None #ensure next loop we dont assume it's the first loop (i don't love this)
                    print("vInput>>", end='')
                    generatedImage = False
                else:
                    dontProcessInputYet = False
                sys.stdout.flush()

                #check whether loaded_role is set and has a current mission and task cursor set 
                on_a_mission = False
                global loaded_role
                if isinstance(loaded_role, Role) and loaded_role.get_current_mission_cursor() is not None and loaded_role.get_current_task_cursor() is not None:
                    printYellow("Current mission and task cursor are set.")
                    printYellow("Processing task...")
                    task_details = process_mission() #this loads the tools and progresses the role/mission cursors 
                    if task_details:
                        printYellow(task_details)
                        myinput = task_details
                        on_a_mission = True
                        #do a 7 second countdown
                        for i in range(7, 0, -1):
                            print(f"\rContinuing in {i} seconds...", end='')
                            time.sleep(1)
                        
                while True and not on_a_mission: #This is the main user input loop
                    """
                    #AI look at the next 10 lines or so for main input loop info
                    This is the user input loop, it handles input text, arrow keys, enter key, etc.

                    The main limitation is that pasting works badly. Therefore typing 'paste' puts you in 
                    paste mode, where pasting works as expected, but you can't use arrow keys or CTRL-I, CTRL-X
                    until you get back to the input prompt or enter 'nopaste' to exit paste mode.

                    Paste works badly probably because of the speed of entry, the elements that capture
                    arrow keys and such seem to mangle pasted text. There's probably a better fix to this
                    or implementation.
                    """
                    #AI where we read keyboard entry for main loop

                    c=''
                    if True:
                        try:
                            c = getch() #read a key
                        except KeyboardInterrupt as e:
                            raise e

                        #AI begin processing individual key presses for special cases like up arrow eshtc 

                        if c == 'up': #UP ARROW
                            """
                            Go up in history of this conversation, 
                            it's like a stack, so we can go back down again with down arrow.
                            Purpose is to allow user to 'redo' a previous response and continue
                            the conversation from there.
                            """
                            minMessages = 3 if hasSystemMessage else 2
                            if (len(messages) + messages_cursor > minMessages): #AI bug at this point, messageCopy should be opuplated but it's really not, other than system message, when having left-arrowed to a historical file
                                messages_cursor -= 2
                                messages.pop()
                                messages.pop()
                                print("\033[2J\033[1;1H") #clear screen
                                printMessagesToScreen(False, True)
                                print()
                                print("kInput>>" , end='', flush=True)

                        elif c == 'down': #DOWN ARROW
                            if (messages_cursor < 0):
                                # take the next 2 messages from messagesCopy and append to bottom of messages
                                messages_cursor += 2
                                if (messages_cursor == 0):
                                    #make messages == messagesCopy
                                    messages = []
                                    for item in messagesCopy:
                                        messages.append(item)
                                else:
                                    messages.append(messagesCopy[len(messagesCopy)+messages_cursor-2])
                                    messages.append(messagesCopy[len(messagesCopy)+messages_cursor-1])
                                print("\033[2J\033[1;1H") #clear the screen
                                printMessagesToScreen(False, True)
                                print()
                                print("iInput>>" , end='', flush=True)
                        
                        elif c == 'ctrlt': #AI ctrl+t here and we need to do something important, need to add where a modal pops up and shows us what tools we have available -  tool in args.tools_array:
                            modalOfActiveTools()

                        elif c == 'ctrln': #AI ctrl+t here and we need to do something important, need to add where a modal pops up and shows us what tools we have available -  tool in args.tools_array:
                            #AI the below is also in the right-arrow code... this shoudl be refactored somehow probably, probably also in the left-arrow code
                            if (myinput.strip() != "" and currFileName != ""):  # Save current input if necessary
                                outputConversationToFile(currFileName, myinput.strip())
                            else:
                                outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages(currFileName)
                            add_new_conversation()
                            print("wInput>>" , end='', flush=True)

                        elif c == 'ctrl_up':  # CTRL-UP ARROW
                            # Get the last user message
                            lastUserMessage = ""
                            for i in range(len(messages) - 1, -1, -1):
                                if messages[i]['role'] == "user":
                                    lastUserMessage = messages[i]['content']
                                    break
                            
                            #command_index

                            # Clear the last printed line (if any)
                            print("\033[F\033[K", end='')  # Move the cursor up one line and clear that line

                            # Print the last user message
                            print(lastUserMessage)  # Print the last user message

                            # Print "NOT IMPLEMENTED" on a new line
                            print("NOT IMPLEMENTED")

                            # Prepare the input line again
                            print("\r>> ", end='')  # Bring the cursor back to the start of the line and show the prompt
                            myinput = ""  # Reset myinput for new input

                        elif c == 'ctrli': #CTRL-I
                            """
                            vi mode, but in this case it lets you edit what you've already typed in the input line.
                            Upon saving and exiting the vi session, the contents of that vi session are written to /dev/shm/convo.input
                            and then read back into myinput

                            TODO: Refactor/combine this with "vi" command logic, which is basically the same, with the exception that this
                            one will pass the already-input text to vi
                            """
                            #if the file exists, remove it
                            if os.path.exists("/dev/shm/convo.input"):
                                os.remove("/dev/shm/convo.input")
                            #is the last message in messages a user message
                                #write content of last message (from user) to /dev/shm/convo.input
                            with open("/dev/shm/convo.input", "w") as f:
                                f.write(myinput)
                                myinput = ""
                            if (messages[len(messages)-1]['role'] == "user"):
                                messages.pop()
                            os.system('vi {}'.format("/dev/shm/convo.input"))
                            #attempt to read /dev/shm/convo.input into myinput
                            try:
                                with open("/dev/shm/convo.input", "r") as f:
                                    myinput = f.read()
                                    #remove single endline from end of myinput if it exists
                                    if (myinput[-1] == "\n"):
                                        myinput = myinput[:-1]
                                    #clear screen
                                    print("\033[2J\033[1;1H")
                                    #print messages
                                    printMessagesToScreen()
                                    print("jInput>>" + myinput, end='', flush=True)
                                    dontProcessInputYet = True
                                    if (len(myinput.strip()) == 0):
                                        #dlog("myinput is blank, not appending to messages")
                                        #dontAppendToMessages = True
                                        continue
                                    break
                            except:
                                myinput = ""
                                #dontAppendToMessages = True
                                continue

                        
                        elif c == 'ctrlx':  #CTRL-X
                            """
                            delete the conversation file we're currently viewing then find a spot to move to
                            if there is only one file in the array, do nothing.
                            clear messages, clear messagesCopy, delete file
                            """
                            messages = []
                            messagesCopy = []
                            #does it exist
                            if (os.path.isfile(files[files_cursor-1])):
                                os.remove(files[files_cursor-1])
                                #dlog("deleted file "+files[files_cursor-1])
                            #remove that element from arrayLoc
                            if (files_cursor != 0):
                                files.pop(files_cursor-1)
                            #does the file files[file_cursor-1] exist? 
                            if (True):#(os.path.isfile(files[files_cursor])): #bit of a smoke test
                                message_cursor = 0
                                print("\033[2J\033[1;1H") #clear screen
                                if (files_cursor == 0):
                                    #we're on the temp file
                                    #clear out all messages that are not system messages
                                    for message in messages:
                                        #is it a system message
                                        if (message['role'] == "system"):
                                            messagesCopy.append(message)
                                            break
                                    messages = messagesCopy
                                else:
                                    while (True): #this not failing is predicated on the idea that we will never be allowed to delete the last file in the array
                                        try:
                                            messages = getMessagesFromFile(files[files_cursor])
                                            currFileName = files[files_cursor]
                                            #dlog("Files cursor is " + str(files_cursor) + " and files[files_cursor] is " + files[files_cursor])
                                            files_cursor += 1
                                            printMessagesToScreen()
                                            break
                                        except:
                                            files_cursor -= 1
                                            pass
                                print("jkInput>>", end='', flush=True)

                        elif c == 'left': #LEFT ARROW
                            """
                            Go to the previous conversation 
                            """
                            #AI PROFILING i want to profile from this line until we get back to getch()
                            if (files_cursor == 0): #we may be moving away from the 'live' session, so it needs to be saved 
                                #ok write the messages to a file, the /dev/shm file we created in the beginning
                                #is this file located in /dev/shm? (might not be, if we ran a search term)
                                if ("/dev/shm" in files[0]):
                                    if (myinput.strip() != ""):
                                        outputConversationToFile(files[0], myinput.strip())
                                    else:
                                        outputConversationToFile(files[0]) 
                            else: #this has no bad outcome but ideally it should be changed to not happen when we're at the end 
                                if (myinput.strip() != "" and currFileName != ""): #yeah, let's write this to a file
                                    #dlog("writing to file " + currFileName + " due to the unprocessed input " + myinput.strip())
                                    outputConversationToFile(currFileName, myinput.strip())
                                else:
                                    outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages(currFileName)
                            while (True): #loop until find a file that works or give up
                                #make sure abs(files_cursor) is less than len(files) - 1
                                if (files_cursor < len(files) - 1): #AI todo make sure shouldn't be files-2?
                                    files_cursor += 1
                                    try:
                                        messages = getMessagesFromFile(files[files_cursor])
                                        messagesCopy = []
                                        for item in messages:
                                            messagesCopy.append(item)
                                        #dlog("LM: files_cursor is now" + str(files_cursor) + "file: " + files[arrayLoc])
                                        hasSystemMessage = (messages[0]['role'] == "system")
                                        print("\033[2J\033[1;1H") #clear screen
                                        printMessagesToScreen(True)
                                        myinput = ""
                                        if (len(messages) > 1):
                                            printFileInformationLine(files[files_cursor])
                                        print("mInput>>", end='', flush=True) #TODO this input when used seems to ignore commands?
                                        #gotAnyRequestResult = False
                                        currFileName = files[files_cursor] #AI hey, refactor, high priority, remove currFileName entirely and just use files[files_cursor] although are there times where... currFileName is not yet in files?
                                        #print("File: " + files[arrayLoc] + " and cursor is " + str(arrayLoc))
                                        break
                                    except Exception as e:
                                        print("Exception in left move: " + str(e))
                                        pass
                                else:
                                    break
                        elif c == 'right': #RIGHT ARROW
                            """
                            Go to the next conversation
                            """
                            if (myinput.strip() != "" and currFileName != ""): #yeah, let's write this to a file
                                #dlog("writing to file " + currFileName + " due to the unprocessed input " + myinput.strip())
                                outputConversationToFile(currFileName, myinput.strip())
                            else:
                                outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages(currFileName)
                            while (True): #loop until find a file that works or give up
                                if (files_cursor > 0):
                                    files_cursor -= 1
                                    try:
                                        messages = getMessagesFromFile(files[files_cursor])
                                        messagesCopy = []
                                        for item in messages:
                                            messagesCopy.append(item)
                                        #dlog("RM: files_cursor is now" + str(files_cursor) + "file: " + files[arrayLoc])
                                        hasSystemMessage = (len(messages) > 0 and messages[0]['role'] == "system")
                                        clear_terminal()
                                        printMessagesToScreen(True)
                                        myinput = ""
                                        if (len(messages) > 1):
                                            printFileInformationLine(files[files_cursor])
                                        print("nInput>>", end='', flush=True)
                                        currFileName = files[files_cursor]
                                        #print("File: " + files[arrayLoc] + " and cursor is " + str(arrayLoc))
                                        break
                                    except Exception as e:
                                        print("Exception in right move: " + str(e))
                                        pass
                                else:
                                    break
                        elif c == '\x03': #CTRL-C
                            """
                            Exit the program but save file first 
                            """
                            print()
                            #TODO refactor this to not be duplicated as it is currently in the RIGHT ARROW code block
                            if (myinput.strip() != "" and currFileName != ""): #yeah, let's write this to a file
                                #dlog("writing to file " + currFileName + " due to the unprocessed input " + myinput.strip())
                                outputConversationToFile(None, myinput.strip())
                            else:
                                outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages()
                            os._exit(0) 

                        elif c == '\n' or c.strip() == "{{enter}}": #ENTER KEY 
                            """
                            If no input has been entered, then the program saves the conversation and exits.
                            Otherwise, this results in the input being processed (if a command) or sent to the AI (if not a command)
                            """
                            if c.strip() != "{{enter}}" or len(myinput.strip()) > 0:
                                print()
                                break
                            else: #prevent accidental exit from this script when hitting enter in android app when no input has been entered
                                pass

                        elif c == '\x7f' or c  == 'backspace': #BACKSPACE
                            if len(myinput) > 0:
                                myinput = myinput[:-1]
                                print("\b \b", end="", flush=True)
                        # Append the entered character to mystring
                        #elif c == '':
                            #this means we got possibly an 'interrupt' from an external process
                    #     break
                        elif c not in ('up', 'down', 'ctrlx', 'ctrli',  None): 
                            try:
                                myinput += c.decode('utf-8')
                            except:
                                try:
                                    myinput += c
                                except:
                                    pass
                            try:
                                print(c.decode('utf-8'), end="", flush=True)
                            except:
                                print(str(c), end="", flush=True)
                        #is last character a \n
                        elif myinput[-1] == "\n":
                            myinput = myinput[:-1]
                            print(myinput, flush=True)
                            break

                        
            #AI end user input loop

            #AI bug/feat need to make it so if after breaking a tool loop it still does it, like, the attempt to break the loop 'provide a different responmce 

            else: #paste, no arrow functionality
                myinput = input("aInput>>").strip() #here's the user's prompt

            if (len(myinput)) < 1:

                if (currFileName != "" and "/dev/shm" in currFileName):
                    currFileName = None
                #print("currFileName is " + str(currFileName))
                outputConversationToFileIfAtLeastOneNonSystemMessageAndIfProvidedFileHasAnyMismatchFromMessages(currFileName, True)
                os._exit(0)

            #COLON COMMANDS CAPTURING BEGINS HERE
            for module in colon_command_modules:
                try:
                    #TODO maybe we just do all the .py file loading herE? i dunno. probably not. 
                    # List all attributes of the module
                    attributes = dir(module)

                    # Filter out the classes
                    cclasses = [getattr(module, attr) for attr in attributes if isinstance(getattr(module, attr), type)]

                    # Filter out the abstract classes
                    cclasses = [cls for cls in cclasses if not inspect.isabstract(cls)]

                    if (len(cclasses) == 0):
                        #print("No classes found in " + file)
                        pass
                    else:
                        modcommands = module.command_names() #runt
                        descriptions = module.descriptions()
                    pass
                except:
                    pass

            #we have to parse the commands. there may be more than one, and there may be text in between. know what i mean? OK.
            #:comm1 stuff for commanad one :comm2 stufff for command 2 :comm3 :comm4 stuff
            #this should result in 
            # - comm1 with "stuff for command one"
            # - comm2 with "stuff for command 2"
            # - comm3 with "" or None
            # - comm4 with "stuff"
            
            if False: #AI ignore this segment for now 
                #we are starting with a string called myinput
                import re #TODO elsewhere please, probably

                #myinput = "#we have to parse the commands. there may be more than one, and there may be text in between. know what i mean? OK. #:command1 some text
                #:anothercommand here are some words :command3 :command4 more stuff"

                # Regular expression to match the commands and their associated text
                pattern = r':([a-z0-9]+)([^:]*?)(?=:(?![a-z0-9])|$)'

                # Prepare the result
                result = {}

                # Loop through the input to find all matches
                temp_myinput = myinput
                while myinput:
                    match = re.search(pattern, myinput)
                    if match:
                        cmd = match.group(1)
                        text = match.group(2).strip() if match.group(2) else ''
                        result[cmd] = text
                        #print("text is " + text + " and match is " + str(match) + " and match end is " + str(match.end()))
                        # Remove the matched portion from the input string
                        #myinput = myinput[match.end():]
                        myinput = myinput[:match.start()]
                        print("myinput is now" + myinput)
                    else:
                        break

                # Output the result
                for command, text in result.items():
                    print(f"- {command} with '{text}'")

                #TODO at this point we want to see that all the colon command files have been 
                #read in adn parsed and etc etc if that makes sense.
                #What has happend up to this point should be a model for changes that we want to see. 


                myinput = temp_myinput #eventually not needed
            
            myinput = process_commands(myinput) 
            missionstr = process_mission() #AI yes this resets myinput entirely,  if has value

            if missionstr is not None and (len(missionstr) > 0):
                myinput = missionstr



            if myinput == "": 
                print()

            
            #AI begin processing inline commands that all start with a ":" so like :q! works, :vij works, :savetools, etc

            if (myinput.strip() == ":q!"):
                os._exit(0)

            #vij - this part has to happen early, because it's a special case that modifies the input/messages
            if (myinput.strip() == ":vij"):
                """
                Open the JSON representation of the conversation in vi
                Allows the user to modify the conversation, 
                save it and exit like a normal vi user would,
                and then the conversation will be reloaded and continue
                """
                myinput = ""
                outputConversationToFile("/dev/shm/convo.json")
                os.system('vi {}'.format("/dev/shm/convo.json"))
                try:
                    messages = getMessagesFromFile("/dev/shm/convo.json")
                    #is last message from user
                    #if not (messages[-1]['role'] == "user"):
                    #    dontAppendToMessages = True
                    os.system("clear")
                except:
                    print("\033[31m")
                    print("Could not parse JSON")
                    #is the last message in messages a user message
                    if (messages[len(messages)-1]['role'] == "user"):
                        print("Last message in saved conversation is from user - it will be printed here but not be processed:")
                    print("\033[0m")
                    if (messages[len(messages)-1]['role'] == "user"):
                        #print content of last message (from user)
                        print("User Message: " + messages[len(messages)-1]['content'] + "\n")
                        messages.pop()
                    #dontAppendToMessages = True
                    continue
                finally: 
                    os.remove("/dev/shm/convo.json") 
                os.system("clear")
                printMessagesToScreen()
                if (messages[-1]['role'] == "user" or messages[-1]['role'] == "system"):
                    #if it's user
                    if messages[-1]['role'] == "user":
                        myinput = messages[-1]['content']
                        #dontAppendToMessages = True
                    pass
                else:
                    continue

            #TODO this would be a great candidate for refactor into separate file/class
            #sr - speedread. experimental.
            #output last message to /dev/shm/sr.txt and nothing more
            if (myinput.strip() == ":sr"):
                myinput = ""
                if (len(messages) > 0):
                    with open("/dev/shm/sr.txt", "w") as f:
                        f.write(messages[-1]['content'])
                    command = "cat /dev/shm/sr.txt | " + home + "/speedread/speedread -w 800"

                    #running speedread in such a way that user can ctrl-c and it doesn't also kill ai.py 
                    p = subprocess.Popen(command, shell=True)
                    try:
                        p.wait()
                    except KeyboardInterrupt:
                        print("FAFAFA")
                        p.terminate()

                    #clear screen
                    print("\033[2J\033[1;1H")
                    #print messages
                    printMessagesToScreen()
                    #print("Input>>", end='', flush=True)
                else:
                    print("No messages to speedread")
                    print("oInput>>", end='', flush=True)
                continue

            #vi - this edits just the input only
            if (myinput.strip() == ":vi"): 
                #if the file exists, remove it
                if os.path.exists("/dev/shm/convo.input"):
                    os.remove("/dev/shm/convo.input")
                    #if exists "/dev/shm/vi.prompt." + str(os.getpid())
                #Pull stdin into VI mode
                if os.path.exists("/dev/shm/vi.prompt." + str(os.getpid())): 
                    #overwrite /dev/shm/convo.input with stdin from /dev/shm/vi.prompt." + str(os.getpid()) 
                    #as in copy the file /dev/shm/vi.prompt." + str(os.getpid()) to /dev/shm/convo.input
                    os.system("cp /dev/shm/vi.prompt." + str(os.getpid()) + " /dev/shm/convo.input")
                elif (messages[len(messages)-1]['role'] == "user"): #is the last message in messages a user message
                    #write content of last message (from user) to /dev/shm/convo.input
                    with open("/dev/shm/convo.input", "w") as f:
                        f.write(messages[len(messages)-1]['content'])
                    messages.pop()
                os.system('vi {}'.format("/dev/shm/convo.input"))
                #attempt to read /dev/shm/convo.input into myinput
                os.system('reset')
                try:
                    with open("/dev/shm/convo.input", "r") as f:
                        myinput = f.read()#.strip()
                        #remove single endline from end of myinput if it exists (vi seems to add one)
                        if (myinput[-1] == "\n"):
                            myinput = myinput[:-1]
                        #clear screen
                        print("\033[2J\033[1;1H")
                        #print messages
                        printMessagesToScreen()
                        print("pInput>>", end='', flush=True)
                        print(myinput, end='', flush=True)
                        dontProcessInputYet = True
                        if (len(myinput.strip()) == 0):
                            #dontAppendToMessages = True
                            continue 
                except:
                    myinput = ""
                    #dontAppendToMessages = True
                    continue

            if myinput.strip().startswith(":hint"):
                if isinstance(loaded_role, Role):
                    loaded_role.id
                    import sqlite3
                    hint_text = replace_bash_commands(myinput.strip()[6:])
                    conn = sqlite3.connect(BASE_DIR/'roles.db')
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO hints (text, role_id) VALUES (?, ?)', (hint_text, int(loaded_role.id)))
                    conn.commit()
                    printGrey("Inserted hint for role " + str(loaded_role.id) + "\n")
                    conn.close()
                else:
                    print("Error: no role loaded")
                myinput = ""
                continue

            if myinput.strip().startswith(":scribe"):
                #check for interrupt_thread is alive or existing
                if interrupt_thread.is_alive():
                    killThread = True
                    interrupt_thread.join()
                    
                # Start the interrupt checking thread
                #interrupt_thread = threading.Thread(target=check_for_interrupt, daemon=True)
                #start interrupt thread where we force it to connect to transcription service
                #by passing True to the force value that is accepted by the ccheck_for_interrupt function
                
                interrupt_thread = threading.Thread(target=check_for_interrupt, args=(True,), daemon=True)
                interrupt_thread.start()

                myinput = ""
                continue

            if myinput.strip().startswith(":vars"):
                if myinput.strip() == ":vars":
                    # Do we have a loaded role?
                    if isinstance(loaded_role, Role):
                        print("Variables for loaded role:")
                        for key, value in loaded_role.variables.items():
                            print(f"{key}: {value}")
                    myinput = ""
                    continue
                else:
                    vars_string = myinput.strip()[6:]  # Extract the variable part after ":vars"

                    # Use regex to split on commas not within quotes
                    var_key_value_pairs = re.findall(r'(\S+?)=(.*?)(?=,\s*|\s*$)', vars_string)

                    for key, value in var_key_value_pairs:
                        key = key.strip()
                        value = value.strip()

                        # Store or update the variable in the loaded role's variables
                        if loaded_role is not None and isinstance(loaded_role, Role):
                            loaded_role.variables[key] = value
                        else:
                            print("Could not load variable definitions b/c no role is loaded")

                    print("Variables updated for loaded role:")
                    for key, value in loaded_role.variables.items():
                        print(f"{key}: {value}")

                    myinput = ""  # Clear input after processing
                continue


                
            if myinput.strip() == ":bash" or myinput.strip() == ":!sh":
                #drop to bash
                print()
                #get new PS1 so we know visually we're in a sub-bash session
                
                # Define the new PS1 setting
                new_ps1_setting = 'PS1="\\[\\033[01;31m\\]\\u@\\h:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ "\n'

                # Read the existing .bashrc content
                with open(os.path.expanduser('~/.bashrc'), 'r') as bashrc_file:
                    existing_content = bashrc_file.read()

                # Create a temporary file to hold the new content
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    # Write the existing content to the temporary file
                    temp_file.write(existing_content.encode('utf-8'))

                    # Append the new PS1 setting
                    temp_file.write(new_ps1_setting.encode('utf-8'))

                    temp_file_name = temp_file.name

                # Replace the original .bashrc with the modified one
                os.rename(temp_file_name, os.path.expanduser('~/.bashrc'))

                # Start a new bash session to reflect changes
                os.system("bash --rcfile ~/.bashrc")
                print()
                myinput = ""
                continue



            #is myinput == nopaste
            if (myinput == ":nopaste"):
                print("Paste mode disabled")
                paste = False
                myinput = ""
                continue

            #is myinput == paste
            if (myinput == ":paste"):
                print("Paste mode enabled - (disables audio transcription)")
                paste = True
                myinput = ""
                continue

            # :?
            if (len(myinput.strip()) == 2 and myinput[0] == ":" and (myinput[1] == "?")):
                display_help()
                myinput = ""
                continue

            if (len(myinput.strip()) > 2 and myinput[0] == ":" and (myinput[1] == "?")):
                #this means there was more than just :?, so lets ask the AI to help
                helptxt = get_display_help_as_txt()
                query = myinput[2:].strip()
                myinput = helptxt + "\n" + query + "Above is the user help text followed by a query from the user - can you please respond? This is to help them use the program they are currently using to communicate with (you)"

            
            # :s
            if (len(myinput.strip()) > 3 and myinput[0] == ":" and myinput[1] == "s" and myinput[2] == " "):
                """
                Search for conversations matching the string after :s
                """
                # What we want to do here is take any text after :s and pull files etc
                # If myinput[2:] is surrounded by quotes, then we want to match the exact string but remove quotes first
                #dlog("searching for files matching " + myinput[2:].strip())
                if (myinput[2] == '"' and myinput[-1] == '"'):
                    matchedfiles = get_files_collection(myinput[3:-1].strip())
                else:
                    matchedfiles = get_files_collection(myinput[2:].strip())
                #dlog("found a total of " + str(len(matchedfiles)-1) + " files matching " + myinput[2:])
                refreshUI(matchedfiles, True)
                # Make terminal print yellow
                files_cursor = 0
                printYellow("Found " + str(len(matchedfiles)) + " files matching '" + myinput[2:].strip() + "'\n")

                #dontAppendToMessages = True
                myinput = ""
                continue 

            # :x [num] for max
            if (len(myinput) > 3 and myinput[:3] == ":x "):
                """
                This limits the number of messages that are sent to the AI. i.e. last 10 messages
                user types :x 4 to only ever send last 4 messages
                """
                try:
                    max_messages = int(myinput[3:].strip())
                    if (max_messages < 1):
                        raise ValueError
                    args.max = max_messages
                except ValueError:
                    print("Invalid max message memory\n")
                    myinput = ""
                    continue
                print("Set max message memory to: " + str(max_messages))
                myinput = ""
                #get message that is the first message in the conversation, per the args.max
                if (len(messages) > args.max):
                    printYellow(messages[len(messages)-args.max]['content'])  #print oldest message to be sent to AI based on args.max
                continue

            if myinput.strip() == ":x": #just :x no value
                #do awawy with args.max
                args.max = None
                printYellow("Max message memory removed - total of " + str(len(messages)) + " messages\n")
                myinput = ""
                continue


            # :w
            if (len(myinput.strip()) > 2 and myinput[0] == ":" and myinput[1] == "w" and myinput[2] == " "):
                #get what comes after :w and strip it
                file = myinput[2:].strip()
                #does the file exist
                try:
                    if os.path.exists(file):
                        backupFile(file)
                        #now write the conversation to the file
                        outputConversationToFile(file)
                        print()
                    else: #write it
                        outputConversationToFile(file)
                    printGrey("Wrote conversation to " + file) #todo why don't we see the output of this during usage?
                        
                except Exception as e:
                    print("Error writing to file: " + str(e))
                    pass
                print()
                myinput = ""
                continue
            elif (len(myinput.strip()) == 2 and myinput[0] == ":" and myinput[1] == "w"):
                #write the conversation to the current file
                outputConversationToFile(files[files_cursor])
                printGrey("Wrote conversation to " + str(files[files_cursor]) + "\n") #todo refactor this method against using currFileName like :o does
                myinput = ""
                continue


            #:o 
            if (myinput.strip() == ":o"):
                """
                This writes the current conversation to a file, in plain text, not JSON
                """
                #the user may just type :o in which case we write the convo to the current file
                #the user may type :o filename.json in which case we write the convo to filename.json
                #the user may type :o filename.json and then a number to indicate how many messages back to write, in which case, do not use JSON

                #convert myinput any multiple spaces to a single space
                myinput = re.sub(' +', ' ', myinput)
                #split myinput on spaces
                words = myinput.split(" ")
                myinput = ""

                #if there is only one word, then we just write to the current file
                if (len(words) == 1):
                    #write the conversation to the current file
                    outputConversationToFile(currFileName)
                    continue

                #if there are two words, then we write to the file specified
                if (len(words) == 2):
                    #write the conversation to the file specified
                    outputConversationToFile(words[1])
                    continue

                if (len(words) == 3):
                    #write the conversation to the file specified, but only the last n messages
                    try:
                        num = int(words[2])
                        outputMessagesToFile(words[1], num)
                        continue
                    except: 
                        print("Invalid number of messages to write") 

            # :m [model]
            if (len(myinput) > 3 and myinput[:3] == ":m "):
                print("Model changed from "+args.model+" to: " + myinput[3:].strip())
                args.model = myinput[3:].strip()
                init_assistantt()  # Assuming this function initializes the assistant with the new model
                myinput = ""
                continue
            elif (len(myinput) >= 2 and myinput[:2] == ":m"):
                print_models()
                myinput = ""
                continue

            # :c
            if (myinput == ":c"):
                f = outputConversationToFile()  # Assuming this function outputs the conversation to a file
                print("Copied conversation to new file " + str(f))
                myinput = ""
                continue

            # :t [temperature]
            if (len(myinput) > 3 and myinput[:3] == ":t "):
                """
                This sets the temperature for the AI
                """
                try:
                    temp = float(myinput[3:].strip())
                    if (temp > 2.0 or temp < 0.0):
                        print("Invalid temperature")
                    else:
                        args.temperature = temp
                        print("Temperature changed to: " + str(args.temperature))
                except ValueError:
                    print("Invalid temperature")
                myinput = ""
                continue

            if myinput.strip() == ":system":
                for message in messages:
                    if (message['role'] == 'system'):
                        printYellow("\n" + message['content'] + "\n")
                        break
                myinput = ""
                continue

            if myinput.strip() == ":first" or myinput.strip() == ":last":
                print("Not yet implemented.\n")
                myinput = ""
                continue

            if myinput.strip() == ":sysedit":
                msg = getPreProcessedSystemMessage()

                with open("/dev/shm/delme", "w") as f:
                    msg = replace_bash_commands(msg).strip()
                    f.write(msg)
                os.system('vi {}'.format("/dev/shm/delme"))
                #attempt to read /dev/shm/convo.input into myinput
                try:
                    with open("/dev/shm/delme", "r") as f:
                        msg = f.read()
                    args.system = msg
                    #msg = replace_bash_commands(msg).strip()
                    hasSystemMessage = False
                    for message in messages:
                        if message["role"] == "system":
                            message["content"] = msg
                            hasSystemMessage = True
                            break
                    if not hasSystemMessage:
                        #append to top of array
                        messages.insert(0, {"role": "system", "content": msg})

                except:
                    pass
                print("loaded system message\n")
                myinput = ""
                continue

            #:add 
            if (len(myinput) == 4 and myinput[:4] == ":add") or (len(myinput) > 5 and myinput[:5] == ":add "):
                #if the last message is an assistant message, remove it from messages
                if (len(messages) > 0 and messages[-1]['role'] == "assistant"):
                    messages.pop()
                
                #is the last message a user message?
                if not (len(messages) > 0 and messages[-1]['role'] == "user"):
                    print("No user message to rerun")
                    myinput = ""
                    continue
                else:
                    str_after_command = myinput[5:].strip()
                    #now append to content of last message
                    messages[-1]['content'] += " " + str_after_command
                    myinput = messages[-1]['content']
                    #now remove that message from messages array since we're rerunning
                    messages.pop()
                #now rewrite messages to screen
                #print("\033[2J\033[1;1H") #clear screen
                printMessagesToScreen(True, False, "Input>>" + myinput)



            if myinput.startswith(":redo"):
                # Check if there's a user message to rerun
                if not (len(messages) > 1 and messages[-2]['role'] == "user"):
                    print("No user message to rerun")
                    myinput = ""
                    continue

                # Last message must be assistant
                if len(messages) > 0 and messages[-1]['role'] == "assistant":
                    str_after_command = myinput[6:].strip()
                    filetext = ""

                    if str_after_command == "":
                        # Write the last user message to /dev/shm/lusertemp
                        with open("/dev/shm/lusertemp", "w", encoding='utf-8') as f:
                            f.write(messages[-2]['content'])

                        # Open vi (consider using subprocess for better handling)
                        os.system('vi /dev/shm/lusertemp')

                        # Read the file back into myinput
                        with open("/dev/shm/lusertemp", "r", encoding='utf-8') as f:
                            filetext = f.read()

                        # Check if the message has changed
                        if filetext.strip() == messages[-2]['content'].strip():
                            print("No changes made to user message\n")
                            myinput = ""
                            continue
                        myinput = filetext
                    else:
                        myinput = messages[-2]['content'] + " " + str_after_command
                        

                    # Remove the last assistant message
                    if len(messages) > 0 and messages[-1]['role'] == "assistant":
                        messages.pop()

                    # Remove the user message from messages array since we're rerunning
                    messages.pop()

                # Print messages to screen
                printMessagesToScreen(True, False, "Input>>" + myinput)


            #:redo (same as :add but doesn't append to last user message, overwrites it)
            if False and (len(myinput) == 5 and myinput[:5] == ":redo") or (len(myinput) > 6 and myinput[:6] == ":redo "): #TODO can we simplify this if staetemtn
                #if the last message is an assistant message, remove it from messages
                
                #is the last message a user message?
                if not (len(messages) > 1 and messages[-2]['role'] == "user"):
                    print("No user message to rerun")
                    myinput = ""
                    continue
                elif (len(messages) > 0 and messages[-1]['role'] == "assistant"):
                    str_after_command = myinput[6:].strip()
                    #is it empty?
                    filetext = ""
                    if (str_after_command == ""):
                        #write the last user message to /dev/shm/lusertemp
                        with open("/dev/shm/lusertemp", "w") as f:
                            f.write(messages[-2]['content'])
                        #open vi
                        os.system('vi {}'.format("/dev/shm/lusertemp"))
                        #read the file back into myinput
                        with open("/dev/shm/lusertemp", "r") as f:
                            filetext = f.read()

                        #wait but is filetext the same as the original message?
                        if (filetext.strip() == messages[-2]['content'].strip()):
                            print("No changes made to user message\n")
                            myinput = ""
                            continue
                        myinput = filetext

                    if (len(messages) > 0 and messages[-1]['role'] == "assistant"):
                        messages.pop()
                        
                    #now remove that user message from messages array since we're rerunning
                    messages.pop()
                else:
                    #TODO this really should handle the case for if the last message is a user message... it's unlikely
                    #but there's realy no reason not to and it should really be refactored with the previous elif
                    pass
                #now rewrite messages to screen
                printMessagesToScreen(True, False, "Input>>" + myinput)
                
                
            if myinput.strip() == ":remresp": 
                #remove the JSON after "RESPONSE: " in the previous user message (which is actually tool output)
                #but if no such pattern/message exists then just output that there was nothing to remove
                #and if the message is in fact there, then remove it and output that it was removed, and in the 
                #message from which it was removed, output that it was removed in place of the content that was removed

                last_user_message_index = len(messages) - 1
                #now, starting from last_user_message_index, go backwards until you find a user message
                while last_user_message_index >= 0 and messages[last_user_message_index]['role'] != "user":
                    last_user_message_index -= 1
                #if last_user_message_index is less than 0, then there are no user messages to remove the response from
                if last_user_message_index < 0:
                    print("No user messages to remove responses from")
                else:
                    #messages[last_user_message_index]['content'] = messages[last_user_message_index]['content'].split("RESPONSE: ")[0] + "RESPONSE: [removed by user for effiency]"
                    #first see if RESPONSE: is in the message
                    #remove everything after the last 'RESPONSE: ' and replace it with 'RESPONSE: [removed by user for effiency]'
                    if "RESPONSE: " in messages[last_user_message_index]['content']:
                        #get first 64 chars of string to remove
                        first_64_chars = messages[last_user_message_index]['content'].split("RESPONSE: ")[0][:64]
                        messages[last_user_message_index]['content'] = messages[last_user_message_index]['content'].split("RESPONSE: ")[0] + "RESPONSE: [removed by user for effiency]"
                        print("Removed response from previous user message, which began with 'RESPONSE: '" + first_64_chars) 
                    else:
                        print("No response to remove from previous user message.")
                print()
                myinput = ""
                continue

            #:rolelist
            if myinput.strip() == (":rolelist"):
                printRoleInfo()
                print()

            if myinput.strip() == ":nobash":
                #global args
                args.nobash = True
                printGrey("Diable {{}} processing")
                continue

            if myinput.strip() == ":yesbash":
                #global args
                args.nobash = False
                printGrey("Enable {{}} processing")
                continue

            #:roleedit
            if myinput.strip() == ":roleedit":
                try:
                    if not isinstance(loaded_role, Role):
                        printYellow("No role currently loaded or the loaded role is not of the correct type.\n")
                    else:
                        thfile = loaded_role.rolefile
                        if thfile:
                            edit_role(thfile)
                            # Optionally, reload the role after editing
                            reloaded_role = load_role(loaded_role.name)
                            if reloaded_role:
                                loaded_role = reloaded_role
                                printGreen(f"Role '{loaded_role.name}' has been reloaded after editing.\n")
                            else:
                                printRed(f"Failed to reload role '{loaded_role.name}' after editing.\n")
                        else:
                            printYellow("The current role doesn't have an associated file, attempting DB\n")
                            edit_role_in_db(loaded_role.name)
                except Exception as e:
                    printRed(f"Error: {str(e)}\n")
                myinput = ""
                continue
                            
            #:role
            if myinput.strip() == ":role":
                printRoleInfo()
                myinput = ""
                continue
        
            if myinput.strip().startswith(":role "):
                first_word_after = myinput.strip().split(" ")[1].strip()
                if len(first_word_after) > 0:
                    load_role(first_word_after)
                myinput = ""
                continue
        
            if myinput.strip() == ":rolesave":
                save_role()
                myinput = ""
                continue
            

            if myinput.strip() == ":alltools":
                refreshTools(True)
                myinput = ""
                continue

            if myinput.strip() == ":savetools": 
                # Save active tools to the specified filename
                try:
                    filename = myinput[11:].strip()  # Get filename after ":savetools "
                    writeActiveCanonicalNamesToFile(fBASE_DIR/'tools/collections/{filename}')
                    print(f"Tools saved to "+BASE_DIR/"tools/collections/{filename}\n")
                except Exception as e:
                    print(f"Error saving tools: {e}")
                myinput = ""
                continue

            if myinput.strip() == ":loadtools":
                # Load tools from the specified filename
                try:
                    filename = myinput[11:].strip()  # Get filename after ":loadtools "
                    deactivateAllToolsInArgsToolsArray() #TODO refactor to use the other deactivateTools method
                    tools = getCanonicalToolsNamesFromFile(fBASE_DIR/'tools/collections/{filename}')
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print(f"\nTools loaded from "+BASE_DIR/"tools/collections/{filename}\n")
                except Exception as e:
                    print(f"Error loading tools: {e}")
                myinput = ""
                continue

            if myinput.strip() == ":notools":
                deactivateTools()
                printYellow("Deactivated tools\n")
                force_tools_flag = False
                myinput = ""
                continue

            if myinput.strip() == ":onlytools":
                print("Only tools\n")
                force_tools_flag = True
                myinput = ""
                continue

            if myinput.strip() == ":noonlytools":
                print("No only tools\n")
                force_tools_flag = False
                myinput = ""
                continue

            if ":toolsjust " in myinput.strip() and myinput.startswith(":toolsjust"):
                #get an array of the items passed after :tools which will be numbers only and it should throw an error if any number is greater than the length of the tools array
                tools = myinput.strip()[11:].split(" ")
                if len(tools) > 0 and ":toolsjust " in myinput.strip():
                    print(myinput.strip())
                    print()
                    deactivateAllToolsInArgsToolsArray()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print()
                    with open(BASE_DIR/'tools/deactivated_tools.txt', 'r+') as file:
                        file.truncate(0)
                myinput = ""
                continue
            
            if ":tools" in myinput.strip() and myinput.startswith(":tools"):
                #get an array of the items passed after :tools which will be numbers only and it should throw an error if any number is greater than the length of the tools array
                tools = myinput.strip()[7:].split(" ")
                if len(tools) > 0 and ":tools " in myinput.strip():
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print()
                else:
                    # Load the tools from the deactivated tools file
                    deactivated_tools = getDeactivatedCanonicalNamesFromFile()
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(deactivated_tools, True)
                    printActiveTools()
                    print()
                    #writeActiveCanonicalNamesToFile()
                    with open(BASE_DIR/'tools/deactivated_tools.txt', 'r+') as file:
                        file.truncate(0)
                myinput = ""
                continue

            #AI ultimately for a handoff to occur bewtween 2 roles, there needs to be an even greater/broader definition given to the 'state' of that role to include tools (including instantiated classes if any), conversation state, and I can't think of anything else but if you have ideas let me know

            
            #AI syscolon files i think may fall by the wayside (below this)
            #deal with syscolon files
            #if myinput.startswith(":"):
                    
            #:role
            if myinput.strip() == ":role":
                printRoleInfo()
                myinput = ""
                continue
        
            if myinput.strip().startswith(":role "):
                first_word_after = myinput.strip().split(" ")[1].strip()
                if len(first_word_after) > 0:
                    load_role(first_word_after)
                myinput = ""
                continue
        
            if myinput.strip() == ":rolesave":
                save_role()
                myinput = ""
                continue
            

            if myinput.strip() == ":alltools":
                refreshTools(True)
                myinput = ""
                continue

            if ":savetools" in myinput and myinput.startswith(":savetools"):
                # Save active tools to the specified filename
                try:
                    filename = myinput[11:].strip()  # Get filename after ":savetools "
                    writeActiveCanonicalNamesToFile(fBASE_DIR/'tools/collections/{filename}')
                    print(f"Tools saved to "+BASE_DIR/"tools/collections/{filename}\n")
                except Exception as e:
                    print(f"Error saving tools: {e}")
                myinput = ""
                continue

            if ":loadtools" in myinput and myinput.startswith(":loadtools"):
                # Load tools from the specified filename
                try:
                    filename = myinput[11:].strip()  # Get filename after ":loadtools "
                    deactivateAllToolsInArgsToolsArray() #TODO refactor to use the other deactivateTools method
                    tools = getCanonicalToolsNamesFromFile(BASE_DIR/'tools/collections/{filename}')
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print(f"\nTools loaded from "+BASE_DIR/"tools/collections/{filename}\n")
                except Exception as e:
                    print(f"Error loading tools: {e}")
                myinput = ""
                continue

            if myinput.strip() == ":notools":
                deactivateTools()
                printYellow("Deactivated tools\n")
                force_tools_flag = False
                myinput = ""
                continue

            if myinput.strip() == ":onlytools":
                print("Only tools\n")
                force_tools_flag = True
                myinput = ""
                continue

            if myinput.strip() == ":noonlytools":
                print("No only tools\n")
                force_tools_flag = False
                myinput = ""
                continue

            if ":toolsjust" in myinput.strip() and myinput.startswith(":toolsjust"):
                #get an array of the items passed after :tools which will be numbers only and it should throw an error if any number is greater than the length of the tools array
                tools = myinput.strip()[11:].split(" ")
                if len(tools) > 0 and ":toolsjust " in myinput.strip():
                    print(myinput.strip())
                    print()
                    deactivateAllToolsInArgsToolsArray()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print()
                    with open(BASE_DIR/'tools/deactivated_tools.txt', 'r+') as file:
                        file.truncate(0)
                myinput = ""
                continue
            
            if ":tools" in myinput.strip() and myinput.startswith(":tools"):
                #get an array of the items passed after :tools which will be numbers only and it should throw an error if any number is greater than the length of the tools array
                tools = myinput.strip()[7:].split(" ")
                if len(tools) > 0 and ":tools " in myinput.strip():
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(tools)
                    print()
                else:
                    # Load the tools from the deactivated tools file
                    deactivated_tools = getDeactivatedCanonicalNamesFromFile()
                    print()
                    activateOrDeactivateToolsInToolsArrayBasedOnIndexOrName(deactivated_tools, True)
                    printActiveTools()
                    print()
                    #writeActiveCanonicalNamesToFile()
                    with open(BASE_DIR/'tools/deactivated_tools.txt', 'r+') as file:
                        file.truncate(0)
                myinput = ""
                continue

            
            #AI syscolon files i think may fall by the wayside (below this)
            #deal with syscolon files
            if myinput.startswith(":"):
                # Split the input into command and the rest of the message
                command_and_message = myinput[1:].strip().split(" ", 1)
                command = command_and_message[0]  # This will be 'thing' in the example
                message = command_and_message[1] if len(command_and_message) > 1 else ""  # The rest of the message

                # Check if command (fne) exists in content_dict
                if command in syscontent_dict:
                    content = f"{syscontent_dict[command]} {message}"
                    if not messages:
                        # If messages is empty, add a new system message
                        messages.append({'role': 'system', 'content': content})
                    elif messages[0]['role'] == 'system':
                        # If the first message is system, append to it
                        messages[0]['content'] = f"{messages[0]['content']}\n{content}"
                    else:
                        # If the first message is not system, insert a new system message
                        messages.insert(0, {'role': 'system', 'content': content})
                    print("Added " + command + " content to system message\n")

                    myinput = ""
                    continue
                else:
                    pass

            #deal with colon files
            if myinput.startswith(":"):
                # Split the input into command and the rest of the message
                command_and_message = myinput[1:].strip().split(" ", 1)
                command = command_and_message[0]  # This will be 'thing' in the example
                message = command_and_message[1] if len(command_and_message) > 1 else ""  # The rest of the message

                # Check if command (fne) exists in content_dict
                if command in syscontent_dict:
                    # Prepend the content from the corresponding file to the message
                    myinput = f"{syscontent_dict[command]} {message}" #TODO i tihnk this is supposed to be system message...
                elif command in content_dict:
                    # Prepend the content from the corresponding file to the message
                    myinput = f"{content_dict[command]} {message}"
                    pass

            if ":toolslist" == myinput.strip():
                refreshTools()
                console = Console()
                table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
                table.add_column("Canonical Name", style="bold", ratio=1.5)
                table.add_column("Description", ratio=2)
                table.add_column("Parameters", ratio=1.5)
                for tool in args.tools_array: #AI this is a great example below of how to approach tools_array, which holds the tools passed to the LLM
                    name_color = "yellow" if tool["active"] else "grey"
                    desc_color = "bright_white" if args.tools_array.index(tool) % 2 == 0 else "white"
                    params = ", ".join(tool['function']['parameters']['properties'].keys())
                    table.add_row(
                        Text(tool['canonical_name'], style=name_color),
                        Text(tool['function']['description'], style=desc_color, overflow="ellipsis"),
                        Text(params, style=desc_color, overflow="ellipsis")
                    )
                console.print(table)
                myinput = ""
                continue

                            
            showtools = False
            showinactivetools = False
            if (myinput.strip() == ":toolsall") or (myinput.strip() == ":tools"):
                print("HIHIHIHI")
                showtools = True
                if myinput.strip() == ":toolsall":
                    refreshTools(args.tools)
                    showinactivetools = True
            if showtools:
                console = Console()
                table = Table(title="Available Tools", show_header=True, header_style="bold green")

                #do that aghain but make it all % of like terminal width pelase
                try:
                    terminal_width = shutil.get_terminal_size().columns
                    name_width = int(terminal_width * 0.3)
                    desc_width = int(terminal_width * 0.5)
                    param_width = int(terminal_width * 0.2)
                except:
                    name_width = 32
                    desc_width = 80
                    param_width = 50

                table.add_column("Name", style="white", width=name_width)
                table.add_column("Description", width=desc_width)
                table.add_column("Parameters", width=param_width)

                index = 0

                for index, tool in enumerate(args.tools_array):
                    function = tool['function']
                    name = function['name']
                    canonical_name = tool['canonical_name']
                    description = function['description']
                    params = function['parameters']['properties']
                    param_details = ", ".join([f"{k}: {v['description']}" for k, v in params.items()])

                    # Alternate brightness for description and parameters
                    description_style = "grey" if index % 2 == 0 else "white"
                    param_style = "grey" if index % 2 == 0 else "white"

                

                    #add a row but this time with the active status as per the args.tools_array[index]["active"]
                    if showinactivetools: #do the flow where we DO show an index b/c that's the index we'd want them to do activate/deactivate on
                        if args.tools_array[index]["active"]:
                            table.add_row(
                                f"{str(index)}. [green]{canonical_name}[/green]",
                                f"[{description_style}]{description}[/{description_style}]",
                                f"[{param_style}]{param_details}[/{param_style}]"
                            )
                        else:
                            table.add_row(
                                f"{str(index)}. [red]{canonical_name}[/red]",
                                f"[{description_style}]{description}[/{description_style}]",
                                f"[{param_style}]{param_details}[/{param_style}]"
                            )
                    else:
                        if args.tools_array[index]["active"]:
                            table.add_row(
                                f"[yellow]{canonical_name}[/yellow]",
                                f"[{description_style}]{description}[/{description_style}]",
                                f"[{param_style}]{param_details}[/{param_style}]"
                            )

                    index += 1
                console.print(table)
                myinput = ""
                continue

            if myinput.strip() == ":noimages":
                modified = False
                new_messages = []
                
                for message in messages:
                    new_message = message.copy()
                    
                    if message.get('content') and isinstance(message['content'], list):
                        new_content = []
                        for content_item in message['content']:
                            if isinstance(content_item, dict) and content_item.get('type') == 'image_url':
                                new_content.append({'type': 'text', 'text': '[Image removed from conversation history to save context]'})
                                modified = True
                            else:
                                new_content.append(content_item)
                        new_message['content'] = new_content
                    
                    new_messages.append(new_message)
                
                messages[:] = new_messages
                
                if modified:
                    print("Removed image data from conversation history\n") 
                else:
                    print("No image data found in conversation history\n")
                myinput = ""
                continue



            # :url [URL]
            if (len(myinput) > 5 and myinput[:5] == ":url "):
                url = myinput[5:].strip()
                urltext = url_to_text(url)  # Assuming this function fetches and returns the text from the URL
                # Now save that urltext to a file in /dev/shm
                with open("/dev/shm/url.txt", "w") as f:
                    f.write(urltext)

                # If the file exists, remove it
                if os.path.exists("/dev/shm/convo.input"):
                    os.remove("/dev/shm/convo.input")

                # Is the last message in messages a user message
                if (messages and messages[-1]['role'] == "user"):
                    # Write content of last message (from user) to /dev/shm/convo.input
                    with open("/dev/shm/convo.input", "w") as f:
                        f.write(messages[-1]['content'])
                    messages.pop()
                elif urltext is not None:
                    # Remove excessive blank lines from urltext
                    urltext = re.sub(r'\n\s*\n', '\n\n', urltext)
                    with open("/dev/shm/convo.input", "w") as f:
                        f.write(urltext)
                else:
                    print("Could not retrieve URL")
                    continue

                #amit praveen kumar has moved to another project.  akshata is coming in 

                os.system('vi /dev/shm/convo.input')
                # Attempt to read /dev/shm/convo.input into myinput
                try:
                    with open("/dev/shm/convo.input", "r") as f:
                        myinput = f.read().rstrip("\n")  # Removes trailing newline characters
                        # Clear screen
                        print("\033[2J\033[1;1H")
                        # Print messages
                        printMessagesToScreen()  # Assuming this function prints messages to the screen
                        print("IInput>>", end='', flush=True)
                        print(myinput, end='', flush=True)
                        dontProcessInputYet = True  # Assuming this flag is used elsewhere to control input processing
                        paste = False  # Assuming this flag is used elsewhere to control 'paste' behavior
                        if not myinput.strip():
                            continue
                except Exception as e:
                    print(f"Failed to read file: {e}")
                    myinput = ""
                    continue

            #is myinput == nopaste
            if (myinput == ":nopaste"):
                print("Paste mode disabled")
                paste = False
                myinput = ""
                continue

            #is myinput == paste
            if (myinput == ":paste"):
                print("Paste mode enabled")
                paste = True
                myinput = ""
                continue

            # :e 
            if (len(myinput) > 3 and myinput[0] == ":" and myinput[1] == "e" and myinput[2] == " "):
                try:
                    # Parse the number after the :e command
                    erasect = int(myinput[3:].strip())
                except ValueError:
                    print("Invalid erase parameter")
                    continue

                print("Removing last " + str(erasect) + " messages")
                myinput = ""

                # Delete last erasect messages
                for i in range(erasect):
                    if messages:
                        messages.pop()

                print("New Last Message:")
                # Get last message
                if messages:
                    lastMessageItem = messages[-1]  # Simplified way to get the last item
                    # Check if user or system
                    if lastMessageItem['role'] == "user":
                        print(lastMessageItem['content'])
                    elif lastMessageItem['role'] == "assistant":
                        printGreen(lastMessageItem['content'], True)
                continue


            if (":multi" == myinput.strip()):
                print("Enter Multiple Lines, then CTRL+D when done")
                contents = []
                while True:
                    try:
                        line = input()
                    except EOFError:
                        break
                    contents.append(line)
                mystr = '\n'.join([line.strip() for line in contents])
                myinput = mystr
            #print(mystr)

            #does myinput contain "genimage" 
            if (myinput.strip() == "genimage"):
                #first, get the conversation
                convo = ""
                for message in messages:
                    if (message['role'] == "user"):
                        convo += "User: " + message['content'] + "\n"
                    if (message['role'] == "assistant"):
                        convo += "AI: " + message['content'] + "\n"
                #now make convo only the last 4000 characters of the convo
                convo = convo[-4000:] 
                resp = sendDalle3APIRequest(convo, printToScreen=False)
                resp = "Copied the image to Windows clipboard: " + resp
                #now add resp as a message from the AI
                pres = ""
                if (args.identity):
                    pres = args.identity + ": "
                messages.append({
                    "role": "assistant",
                    "content": pres + resp
                })
                printGreen(resp)
                myinput = ""
                dontProcessInputYet = True
                generatedImage = True

            #does myinput contain "image=[anything]"
            doImage = False
            restOfMessage=""
            encoded_strings = []
            #make sure image= is at least the first 6 characters of myinput
            while (len(myinput) > 6 and myinput[0:6] == "image="):
                imageFilename = myinput.split("image=")[1].strip().split(" ")[0].strip()
                #make restOfMessage be everything except for the FIRST instance of "image=" + imageFilename, as if you took ONLY the first instance of "image=" + imageFilename and replaced it with nothing 
                restOfMessage = re.sub("image=" + imageFilename, "", myinput, 1).strip()
                
                #get base64
                try:
                    with open(imageFilename, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        encoded_strings.append(encoded_string)
                        image_file.close()
                        doImage = True
                    myinput = restOfMessage
                except Exception as e:
                    print("xError: " + str(e))
                    pass

            # New code snippet that processes "images="
            if myinput.startswith("images="):
                try:
                    # Extract the number of images to process
                    number_of_images = int(myinput.split("images=")[1].split()[0])
                    # Get a list of all .jpg files in the /dev/shm directory sorted by modification time (newest first)
                    jpg_files = sorted(glob.glob("/dev/shm/*.jpg"), key=os.path.getmtime, reverse=True)
                    # Take the most recent 'number_of_images' files
                    recent_jpg_files = jpg_files[:number_of_images]

                    if len(recent_jpg_files) < number_of_images:
                        print()

                    for filename in recent_jpg_files:
                        # Encode each image to base64 and add it to the list
                        with open(filename, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            encoded_strings.append(encoded_string)
                            doImage = True

                    # Update restOfMessage to remove the "images=" part
                    restOfMessage = re.sub("images=\d+", "", myinput, 1).strip()

                except ValueError:
                    print("Error: The number of images should be an integer.")
                except Exception as e:
                    print("yError: " + str(e))


            # :r [response model] [return model]
            if (len(myinput.strip()) >= 2 and (myinput[0] == ":" and myinput[1] == "r")): 
                parts = myinput.split()
                response_model = parts[1] if len(parts) > 1 else None
                return_model = parts[2] if len(parts) > 2 else None

                # Save the current model
                original_model = args.model

                # Invert the conversation roles
                messages = invertMessages(messages)

                if response_model:
                    # Switch to the response model
                    args.model = response_model
                    init_assistantt()
                if return_model:
                    # later Switch to the return model
                    args.model = return_model
                else:
                    # later Revert to the original model if no return model specified
                    args.model = original_model
                myinput = ""
                continue

            #AI end : command processing


            if not dontProcessInputYet and not doImage:
                #AI BIG DEAL why is messages sometimes NONE here?
                if (len(messages) == 0 or messages[-1]['role'] != "user" or myinput.strip() != messages[-1]['content'].strip()):
                    myinput = replace_bash_commands(myinput) #TODO this is a trial.... not sure if we'll keep it but i bet we do boy howdy
                    messages.append({
                        "role": "user",
                        "content": myinput.strip()
                    })
                    myinput = ""
            
            #now do one that processes multiple miamges from encoded_stirngs
            if not dontProcessInputYet and doImage:
                if (len(messages) == 0 or messages[-1]['role'] != "user" or restOfMessage.strip() != messages[-1]['content'].strip()):
                    new_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": restOfMessage.strip()
                            }
                        ]
                    }
                    for encoded_string in encoded_strings:
                        new_message['content'].append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_string}"
                            }
                        })
                messages.append(new_message)
                myinput = ""

        if dontProcessInputYet:
            continue

        #is the last message a user message?
        if (len(messages) > 0 and messages[len(messages)-1]['role'] == "user"):
            ok = False
            retryCount = 0
            while (not ok and retryCount < 8): #AI here is the loop that calls sendRequest() (loop in case of failure)
                try:
                    #is args.codeoutputfile set?
                    if args.outputcodefile is not None:
                        completion, ignore = sendRequest(True) #THIS IS WHERE WE CALL THE API, messages is global, and this also prints the response, IIRC
                        #anus
                        try:
                            if isinstance(completion, list):
                                completion = completion[0]
                        except:
                            pass
                        #now write completion to a file specified by args.codeoutputfile
                        backupFile(args.outputcodefile)
                        with open(args.outputcodefile, 'w') as f:
                            f.write(str(completion) + "\n")
                        #now change file to +x if it ends in .sh
                        if args.outputcodefile.endswith(".sh"):
                            os.system("chmod +x " + args.outputcodefile)
                        os._exit(0)
                    else:
                        completion = sendRequest() #THIS IS WHERE WE CALL THE API, messages is global, and this also prints the response, IIRC
                        try:
                            if isinstance(completion, list):
                                completion = completion[0]
                        except:
                            pass
                    if args.oneshot:
                        pres = ""
                        if (args.identity):
                            pres = args.identity + ": "
                        messages.append({
                            "role": "assistant",
                            "content": pres + completion
                        })
                        if args.jo is not None:
                            if (args.jou is not None):
                                messages = invertMessages(messages)
                            outputConversationToFile(args.jo)
                        os._exit(0)
                    print()
                    #gotAnyRequestResult = True
                    ok = True
                    if currFileName != None and currFileName != "" and not args.oneshot:
                        outputConversationToFile(currFileName)
                    elif not args.oneshot:
                        currFileName = outputConversationToFile()
                except LLMRepetitiveResponseError:
                    print("The LLM provided a repetitive response. Attempting to break the loop...")
                    messages.append({
                        "role": "user",
                        "content": "You seem to be repeating yourself. Please provide a different response or explain why you're repeating."
                    })
                except LLMEndConversationError as e:

                    if currFileName != None and currFileName != "" and not args.oneshot:
                        outputConversationToFile(currFileName)
                    elif not args.oneshot:
                        currFileName = outputConversationToFile()
                    #empty all messages, except the setup message
                    messages = [messages[0]]
                    pass
                except Exception as e:
                    print("mmmError: " + str(e))
                    stack = traceback.format_exc()
                    print(stack)
                    #we need here to reestablish the connection

                    #AI commenting the below ~10 lines may fix the 'stack trace in the messages array' bug
                    #check if latest message is a user message and if so, append stack trace to it or if not, append it to a new user message
                    #if (len(messages) > 0 and messages[-1]['role'] == "user"):
                    #    messages[-1]['content'] += "\n\nStack Trace:\n" + stack
                    #else:
                    #    messages.append({
                    #        "role": "user",
                    #        "content": stack
                    #    })

                    global assistantt
                    global config
                    init_assistantt()
                    from gptcli.assistant import (
                    #from cloudassistant import (
                        Assistant,
                        DEFAULT_ASSISTANTS,
                        AssistantGlobalArgs,
                        init_assistant,
                    )
                    assistant = Assistant(config)
                    print("Retrying...\n")
                retryCount += 1

            if (not ok):
                print("Too many errors, exiting...")
                if not (args.oneshot or args.outputcodefile is not None):
                    outfile = outputConversationToFile()
                    print("Conversation saved to: " + outfile)
                os._exit(1)

            pres = ""
            if (args.identity):
                pres = args.identity + ": "
            messages.append({
                "role": "assistant",
                "content": pres + completion
            })

            messages_cursor = 0 #this means the end, our cursors start at the end and go negative to go inward

        response = ""

        #check if oneshot was set
        if (args.oneshot):
            sys.stdout.flush()
            if args.jo is not None:
                outputConversationToFile(args.jo)
            os._exit(0)

    #AI note, when creating roles, the yaml, the strings, they need to be in a '' encapsulated in quotes so need to add that somewhere as a directive

    #AI bug i tihnk when too many tools are loaded we are still getting some sort of cnoflict or inability to find tools
    #AI FEAT add :inject so one can silently inject a user message above the latest message from the AI.  In this way anything importnat can be added to the conversation without requiring a response from the LLM
    #AI feat add :redraw command for those times you need the conversation to be reshown but like, you're at the 1st repsonse and can't just up/down arrow to refresh
    #AI BUG -l no longer seems to be working, instead just ignoring that to some extent



    #AI there needs to be a better system of printing to the screen. there are 2 key issues. One, output live is always better than re-output. The colors are right, you don't see those 'filler' assistant messages where they just have a '.' when they were making a tool call, the tool call which goes into the response 'user' message that's actually from the tool execution.  Anyway, that's one thing. There's another thing that is very painful that needs to be addressed, and that is the use of Console from the rich library in order to do markup printing, which to be fair is good stuff, you know? but here's the issue. When it's streaming new content back from the LLM, and updating the console, a coupl ethings about that really sucks.  One, there is a lot of flicker and it was cool for a while but now it's just annooying (flicker happens when the mssage is updating) and 2nd issue with it is that once it gets to the bottom of the terminal it just does this '...' thing at the bottom and then i can no longer see what it's writing because it's just writing under the '...' and i can't scroll down and it's STILL flickering and so it's just... you know?
    #AI another major thorn in my side is that getch() operates too slowly, for example, I can't paste text (and therefore, can't use a speech-to-text transcription engine) to talk to the LLM.  (I can paste using {{p}} or whatever but that is differetn, sometimes you need to paste multiple things to a single message, you know? there is after all only one clipboard. vi is a good option the program offers but simple ability to paste would be amazing. I dont want to have to hit ESC to go to 'doesn't mess up when you paste text here' mode because that really should be easy in 2024 even on WSL2.

    #AI singleton state machine instead of all these global vars?

    #AI refactor this ai.py file that we are in right here, it should itself be a class that can be imported by another script

    #AI FEATURE BIG BIG BIG There's been all this talk about how to handle the buttons in the UI for that thing. but what if instead of doing that, we like, allow the services that consume the transcription data to self-advertise and the buttons in the UI are a direct result of that. So for example if my computer has a nice little monster that lives in the taskbar that consumes from the service, it would advertise some name and then that button/entity would reveal itself in the android UI. so that is an idea..   This could play into multiple chatbots with conversational context and everything

    
if __name__ == "__main__":
    main()
