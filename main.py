import os
import sys
import getpass
import json
try:
    import colorama
    from colorama import Fore, Back, Style
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
except ImportError:
    def printWithColor(message: str, end: str='\n'):
        """Implement printWithColor function for systems that doesn't have colorama installed. Does not print with colors.

        Args:
            message (str): The thing you want to print.
            end (str, optional): end parameter of the print. Defaults to '\n'.
        """

        print(message, end=end)

class Folder:
    def __init__(self, path: str, workspace_exists: bool, sizeinbytes: int) -> None:
        self.path: str = path
        self.workspace_exists: bool = workspace_exists
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
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

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
        
        print("Please give a valid answer!")

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
        
        try:
            target_folder_name: str = data['folder']
            target_folder_name = target_folder_name.removeprefix('file://')
            
            result_list.append(Folder(
                full_path,
                os.path.exists(target_folder_name),
                getSizeOfFolder(full_path),
            ))
        except KeyError:
            pass
    
    return result_list
        
    
def main():
    printWithColor("Looking for workspaceFolder path...", Fore.BLUE)
    wss_path = getDefaultWSSFolderPath()
    
    if not wss_path:
        printWithColor("This OS is not supported.", Fore.RED)
        return
    
    if not isValidWSSPath(wss_path):
        printWithColor("Script couldn't find workspaceStorage folder.", Fore.RED)
        askForValidWSSPath()
    else:
        printWithColor(f"Found workspaceStorage folder in {wss_path}!", Fore.GREEN)
        if askYesNoQuestion("Do you want to provide an alternative path?"):
            askForValidWSSPath()
        
    folders = parseWSSFolder(wss_path)
    
        
if __name__ == '__main__':
    main()

