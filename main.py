import os
import sys
import getpass
import json
import shutil
import colorama
from colorama import Fore, Back, Style
from urllib.parse import unquote, urlparse
import datetime as dt
colorama.init()


def printWithColor(message: str, foreground_color: Fore=Fore.RESET, background_color: Back=Back.BLACK, end: str='\n'):
    """Prints colored text if colorama is installed

    Args:
        message (str): The thing you want to print
        foreground_color (Fore): Foreground color of the text. Defaults to Fore.RESET.
        background_color (Back): Background coor of the text. Defaults to Back.BLACK.
        end (str, optional): end paramater of the print. Defaults to '\n'.
    """
    
    print(foreground_color + background_color + message + Style.RESET_ALL, end=end)


class Folder:
    def __init__(self, path: str, workspace_exists: bool, is_old: bool, sizeinbytes: int) -> None:
        self.path: str = path
        self.workspace_exists: bool = workspace_exists
        self.is_old = is_old
        self.sizeinbytes: int = sizeinbytes

    def __repr__(self) -> str:
        return f'(path: {self.path}, workspace_exists: {self.workspace_exists}, sizeinbytes: {self.sizeinbytes})'


def format_size(size_bytes: int) -> str:
    """Converts size as bytes to human readable format

    Args:
        size_bytes (int): Size to convert

    Returns:
        str: Human readable size in str format
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    elif size_bytes < 1024 ** 4:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    return f"{size_bytes / (1024 ** 4):.2f} TB"

def getDefaultWSSFolderPath() -> str:
    """Returns default workspaceStorage path based on operating system that the script ran on

    Returns:
        str: Path of workspaceStorage folder
    """
    username = getpass.getuser()
    
    if sys.platform in ('linux', 'linux2'):
        return f"/home/{username}/.config/Code/User/workspaceStorage/" 
    elif sys.platform == 'darwin':
        return f'/home/{username}/Library/Application Support/Code/User/workspaceStorage/'
    elif sys.platform in ('win32', 'win64'):
        return f'C:/Users/{username}/AppData/Roaming/Code/User/workspaceStorage/'

    return ''

def isValidWSSPath(path: str) -> bool:
    """Checks if the given folder path is a valid workspaceStorage folder

    Args:
        path (str): Path to check

    Returns:
        bool: True if given folder path is a valid workspaceStorage folder
    """
    if not os.path.exists(path):
        return False
    
    folders = os.listdir(path)
    for folder in folders:
        full_path = os.path.join(path, folder)
        if not os.path.exists(os.path.join(full_path, 'workspace.json')):
            return False
    return True

def askForValidWSSPath() -> str:
    """Continuously asks user for a valid workspaceStorage path

    Returns:
        str: A valid workspaceStorage path
    """
    while True:
        path = input("Please enter a valid workspaceStorage path: ")
        if isValidWSSPath(path):
            return path

def askYesNoQuestion(questionBody: str, yes_patterns: list[str]=['y', 'yes'], no_patterns: list[str]=['n', 'no']) -> bool:
    """Asks user a yes/no question. 

    Args:
        questionBody (str): Body of the question
        yes_patterns (list[str], optional): Strings that are considered yes. User input is lowered by default so no need to put both lower and upper versions of the same string. Defaults to ['y', 'yes'].
        no_patterns (list[str], optional): Strings that are considered no. User input is lowered by default so no need to put both lower and upper versions of the same string.. Defaults to ['n', 'no'].

    Returns:
        bool: Returns true if lowered input is in yes_patterns, false if lowered input is in no_patterns
    """
    while True:
        print(questionBody, end='')
        printWithColor(' (', Fore.MAGENTA, end='')
        printWithColor('y', Fore.GREEN, end='')
        printWithColor('/', Fore.MAGENTA, end='')
        printWithColor('n', Fore.RED, end='')
        printWithColor(')', Fore.MAGENTA, end='')
        inp = input(': ')
        if inp.lower() in yes_patterns:
            return True
        elif inp.lower() in no_patterns:
            return False
        
        printWithColor("Please provide a valid answer...", Fore.RED)

def getSizeOfFolder(path: str) -> int:
    """Calculates a foldersize recursively

    Args:
        path (str): Path to calculate size of

    Returns:
        int: Total size in bytes
    """

    total_size = 0
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path):
            total_size += os.path.getsize(full_path)
        elif os.path.isdir(full_path):
            total_size += getSizeOfFolder(full_path)
    return total_size

def parseWSSFolder(path: str) -> list[Folder]:
    """Parses workspaceStorage folder

    Args:
        path (str): workspaceStorage path

    Returns:
        list[Folder]: List of folders
    """
    
    result_list: list[Folder] = []
    for folder in os.listdir(path):
        full_path = os.path.join(path, folder)
        json_text = ''
        
        with open(os.path.join(full_path, "workspace.json"), 'r') as file:
            json_text = file.read()
        data = json.loads(json_text)
        
        if 'folder' not in data.keys():
            continue
        
        target_folder_name: str = data['folder']
        target_folder_name = unquote(urlparse(target_folder_name).path)
        
        # Consider a folder "old" if it isn't modified in the last 30 days
        lastmodified = dt.datetime.fromtimestamp(os.path.getmtime(full_path))
        now = dt.datetime.now()
        delta = now - lastmodified
        is_old = delta.days > 30
        
        result_list.append(Folder(
            full_path,
            os.path.exists(target_folder_name),
            is_old,
            getSizeOfFolder(full_path),
        ))
    
    return result_list

def main():
    printWithColor("Looking for workspaceFolder path...", Fore.BLUE)
    wss_path = getDefaultWSSFolderPath()
    
    if not wss_path:
        printWithColor("This OS is not supported.", Fore.RED)
        return
    
    if not isValidWSSPath(wss_path):
        printWithColor("Script couldn't find workspaceStorage folder.", Fore.YELLOW)
        askForValidWSSPath()
    else:
        printWithColor(f"Found workspaceStorage folder in {wss_path}", Fore.GREEN)
        if askYesNoQuestion("Do you want to provide an alternative path?"):
            askForValidWSSPath()
        
    folders = parseWSSFolder(wss_path)
    # Mark old and/or unused workspaces as unwanted
    unwanted_folders = [x for x in folders if x.is_old or not x.workspace_exists]
    unwanted_size = sum([x.sizeinbytes for x in unwanted_folders])
    unwanted_size_formatted = format_size(unwanted_size)
    total_size = getSizeOfFolder(wss_path)
    total_size_formatted = format_size(total_size)
    
    if len(unwanted_folders) == 0:
        printWithColor("No unwanted workspaceStorage folder found!", Fore.GREEN)
        return
    
    percentage = round(100 * unwanted_size/total_size, 2)
    
    printWithColor("Found ", end='')
    printWithColor(str(len(unwanted_folders)), Fore.CYAN, end='')
    printWithColor(f" folder{'s' if len(unwanted_folders) > 1 else ''} with total size of ", end='')
    printWithColor(unwanted_size_formatted, Fore.CYAN, end='')
    printWithColor(f". ({Fore.CYAN}{percentage}%{Fore.RESET} of total)")
    
    if askYesNoQuestion(f"Do you want to clear {Fore.CYAN}ALL{Fore.RESET} unwanted folders?"):
        printWithColor("Removing ", end='')
        printWithColor(str(len(unwanted_folders)), Fore.CYAN, end='')
        printWithColor(f" folder{'s' if len(unwanted_folders) > 1 else ''}.")
        try:
            for (i, folder) in enumerate(unwanted_folders):
                print(f'\rRemoving {os.path.basename(os.path.normpath(folder.path))} ', end='')
                printWithColor('(', Fore.MAGENTA, end='')
                printWithColor(str(i+1), Fore.CYAN, end='')
                printWithColor('/', Fore.MAGENTA, end='')
                printWithColor(str(len(unwanted_folders)), Fore.CYAN, end='')
                printWithColor(')', Fore.MAGENTA, end='')
                print(' ' * 10, end='')
                
                shutil.rmtree(folder.path)
            print()
        except KeyboardInterrupt:
            printWithColor("Got KeyboardInterrupt. Aborting...", Fore.RED)
        except Exception as e:
            printWithColor(f"Catched an exception while removing folders: {e}. Aborting...")
        else:
            printWithColor("Succesfully cleared all unused folders!", Fore.GREEN)
    else:
        printWithColor("Aborting...", Fore.RED)

    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        printWithColor("\nGot KeyboardInterrupt. Aborting...", Fore.RED)
    except Exception as e:
        printWithColor(f"\nGot an exception while executing script: {e}", Fore.YELLOW)

