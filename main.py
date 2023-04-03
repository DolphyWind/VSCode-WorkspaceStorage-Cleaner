import os
import sys
import getpass

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
        return f'C:\\Users\\{username}\\AppData\\Roaming\\Code\\User\\workspaceStorage\\'

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
        inp = input(questionBody)
        if inp.lower() in yes_patterns:
            return True
        elif inp.lower() in no_patterns:
            return False
        
        print("Please give a valid answer!")
    
def main():
    print("Looking for workspaceFolder path.")
    wss_path = getDefaultWSSFolderPath()
    
    if not wss_path:
        print("This OS is not supported.")
        return
    
    if not isValidWSSPath(wss_path):
        print("Script couldn't find workspaceStorage folder.")
        askForValidWSSPath()
    else:
        print(f"Found workspaceStorageFolder in {wss_path}.")
        if askYesNoQuestion("Do you want to provide an alternative path? (y/n): "):
            askForValidWSSPath()
        
        
        
if __name__ == '__main__':
    main()

