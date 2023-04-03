import os
import sys
import getpass

def getDefaultFolderPath() -> str:
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
    
def main():
    wss_folderpath = getDefaultFolderPath()
    
    if not wss_folderpath:
        print("This OS is not supported.")
        return

        
if __name__ == '__main__':
    main()

