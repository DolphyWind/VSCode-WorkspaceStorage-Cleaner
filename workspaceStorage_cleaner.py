import datetime as dt
import getpass
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
import readline
from dataclasses import dataclass

import colorama
from colorama import Back, Fore, Style

colorama.init()


def printWithColor(
    message: str,
    foreground_color: Fore = Fore.RESET,
    background_color: Back = Back.BLACK,
    end: str = "\n",
):
    """Prints colored text if colorama is installed

    Args:
        message (str): The thing you want to print
        foreground_color (Fore): Foreground color of the text. Defaults to Fore.RESET.
        background_color (Back): Background coor of the text. Defaults to Back.BLACK.
        end (str, optional): end paramater of the print. Defaults to '\n'.
    """

    print(foreground_color + background_color + message + Style.RESET_ALL, end=end)

@dataclass
class Folder:
    path: str
    workspace_exists: bool
    is_old: bool
    sizeinbytes: int

def format_size(size_bytes: int) -> str:
    """Converts size as bytes to human readable format

    Args:
        size_bytes (int): Size to convert

    Returns:
        str: Human readable size in str format
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = size_bytes
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def getDefaultWSSFolderPath() -> str:
    """Returns default workspaceStorage path based on operating system that the script ran on

    Returns:
        str: Path of workspaceStorage folder
    """
    username = getpass.getuser()

    if sys.platform in ("linux", "linux2"):
        return str(Path(f"/home/{username}/.config/Code/User/workspaceStorage/"))
    elif sys.platform == "darwin":
        return str(
            Path(
                f"/Users/{username}/Library/Application Support/Code/User/workspaceStorage/"
            )
        )
    elif sys.platform in ("win32", "win64"):
        return str(
            Path(f"C:/Users/{username}/AppData/Roaming/Code/User/workspaceStorage/")
        )

    return ""


def isValidWSSPath(path: str) -> bool:
    """Checks if the given folder path is a valid workspaceStorage folder

    Args:
        path (str): Path to check

    Returns:
        bool: True if given folder path is a valid workspaceStorage folder
    """
    if not Path(path).exists() or not Path(path).is_dir():
        return False

    folders = [content for content in Path(path).iterdir()]
    return all(
        Path( Path(path) / folder / "workspace.json" ).exists()
        for folder in folders
    )


def askForValidWSSPath() -> str:
    """Continuously asks user for a valid workspaceStorage path

    Returns:
        str: A valid workspaceStorage path
    """
    while True:
        path = input("Please enter a valid workspaceStorage path: ")
        if isValidWSSPath(path):
            return path


def askYesNoQuestion(
    questionBody: str, yes_patterns: list[str] = None, no_patterns: list[str] = None, return_for_none: bool = False
) -> bool:
    """Asks user a yes/no question.

    Args:
        questionBody (str): Body of the question
        yes_patterns (list[str], optional): Strings that are considered yes. User input is lowered by default so no need to put both lower and upper versions of the same string. Defaults to ['y', 'yes'].
        no_patterns (list[str], optional): Strings that are considered no. User input is lowered by default so no need to put both lower and upper versions of the same string.. Defaults to ['n', 'no'].

    Returns:
        bool: Returns true if lowered input is in yes_patterns, false if lowered input is in no_patterns
    """
    if yes_patterns is None:
        yes_patterns = ["y", "yes"]
    if no_patterns is None:
        no_patterns = ["n", "no"]
    while True:
        print(questionBody, end="")
        printWithColor(" (", Fore.MAGENTA, end="")
        printWithColor("Y" if return_for_none else "y", Fore.GREEN, end="")
        printWithColor("/", Fore.MAGENTA, end="")
        printWithColor("N" if not return_for_none else "n", Fore.RED, end="")
        printWithColor(")", Fore.MAGENTA, end="")
        inp = input(": ")
        if inp.lower() in yes_patterns:
            return True
        elif inp.lower() in no_patterns:
            return False

        if not inp:
            return return_for_none

        printWithColor("Please provide a valid answer...", Fore.RED)


def getSizeOfFolder(path: str) -> int:
    """Calculates a foldersize recursively

    Args:
        path (str): Path to calculate size of

    Returns:
        int: Total size in bytes
    """

    total_size = 0
    for full_path in Path(path).iterdir():
        if Path(full_path).is_file():
            total_size += Path(full_path).stat().st_size
        elif Path(full_path).is_dir():
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
    for folder_path in Path(path).iterdir():
        json_text = ""

        with (folder_path / "workspace.json").open("r") as file:
            json_text = file.read()

        data = json.loads(json_text)

        if "folder" not in data:
            continue

        target_folder_name = Path(unquote(urlparse(data["folder"]).path))

        # Consider a folder "old" if it isn't modified in the last 30 days
        last_modified = dt.datetime.fromtimestamp(Path(folder_path).stat().st_mtime)
        now = dt.datetime.now()
        delta = now - last_modified
        is_old = delta.days > 30

        result_list.append(
            Folder(
                path=str(folder_path),
                workspace_exists=target_folder_name.is_dir(),
                is_old=is_old,
                sizeinbytes=getSizeOfFolder(str(folder_path)),
            )
        )

    return result_list

def main():
    # Enable filesystem autocompletion
    readline.set_completer_delims('\t\n')
    readline.parse_and_bind('tab: complete')
    
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
    unwanted_size = sum(x.sizeinbytes for x in unwanted_folders)
    unwanted_size_formatted = format_size(unwanted_size)
    total_size = getSizeOfFolder(wss_path)
    total_size_formatted = format_size(total_size)

    if not unwanted_folders:
        printWithColor("No unwanted workspaceStorage folder found!", Fore.GREEN)
        return

    percentage = round(100 * unwanted_size / total_size, 2)

    printWithColor("Found ", end="")
    printWithColor(str(len(unwanted_folders)), Fore.CYAN, end="")
    printWithColor(
        f" folder{'s' if len(unwanted_folders) > 1 else ''} with total size of ", end=""
    )
    printWithColor(unwanted_size_formatted, Fore.CYAN, end="")
    printWithColor(f". ({Fore.CYAN}{percentage}%{Fore.RESET} of total)")

    if askYesNoQuestion(
        f"Do you want to clear {Fore.CYAN}ALL{Fore.RESET} unwanted folders?"
    ):
        try:
            for (i, folder) in enumerate(unwanted_folders):
                print(
                    f"\rRemoving \"{Path(folder.path).name}\" ",
                    end="",
                )
                printWithColor("(", Fore.MAGENTA, end="")
                printWithColor(str(i + 1), Fore.CYAN, end="")
                printWithColor("/", Fore.MAGENTA, end="")
                printWithColor(str(len(unwanted_folders)), Fore.CYAN, end="")
                printWithColor(")", Fore.MAGENTA, end=" ")
                shutil.rmtree(folder.path)
            print()
            printWithColor("Successfully cleared all unused folders!", Fore.GREEN)
        except KeyboardInterrupt:
            printWithColor("Got KeyboardInterrupt. Aborting...", Fore.RED)
        except Exception as e:
            printWithColor(
                f"Caught an exception while removing folders: {e}. Aborting..."
            )
        finally:
            return
    else:
        printWithColor("Aborting...", Fore.RED)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        printWithColor("\nGot KeyboardInterrupt. Aborting...", Fore.RED)
    except Exception as e:
        printWithColor(f"\nGot an exception while executing script: {e}", Fore.YELLOW)
