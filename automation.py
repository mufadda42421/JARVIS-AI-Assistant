
import os
import re
import json
import shutil
import subprocess
import webbrowser

from pathlib import Path
from difflib import get_close_matches
from urllib.parse import quote_plus


# ==========================================
#          J.A.R.V.I.S. AUTOMATION
# ==========================================

IS_WINDOWS = os.name == "nt"

if not IS_WINDOWS:
    raise RuntimeError(
        "This automation module is designed for Windows."
    )


# ==========================================
#          WINDOWS DIRECTORIES
# ==========================================

HOME = Path.home()

FOLDER_ALIASES = {
    "desktop": HOME / "Desktop",
    "my desktop": HOME / "Desktop",
    "documents": HOME / "Documents",
    "my documents": HOME / "Documents",
    "downloads": HOME / "Downloads",
    "my downloads": HOME / "Downloads",
    "pictures": HOME / "Pictures",
    "photos": HOME / "Pictures",
    "music": HOME / "Music",
    "videos": HOME / "Videos",
    "home": HOME,
    "user folder": HOME,
}

START_MENU_PATHS = [
    Path(os.environ.get("APPDATA", "")) /
    "Microsoft/Windows/Start Menu/Programs",

    Path(os.environ.get("PROGRAMDATA", "")) /
    "Microsoft/Windows/Start Menu/Programs",
]


# ==========================================
#          APPLICATION ALIASES
# ==========================================

APP_ALIASES = {
    "notepad": ["notepad", "notepad.exe"],
    "calculator": ["calculator", "calc", "calc.exe"],
    "paint": ["paint", "mspaint"],
    "command prompt": ["cmd", "cmd.exe"],
    "terminal": ["windows terminal", "wt", "wt.exe"],
    "powershell": ["powershell", "powershell.exe"],
    "vscode": ["visual studio code", "code", "code.exe"],
    "vs code": ["visual studio code", "code", "code.exe"],
    "visual studio code": ["vscode", "code"],
    "task manager": ["taskmgr", "taskmgr.exe"],
    "file explorer": ["explorer", "explorer.exe"],
    "explorer": ["file explorer", "explorer.exe"],
    "settings": ["windows settings", "ms-settings:"],
    "control panel": ["control", "control.exe"],
    "word": ["microsoft word"],
    "excel": ["microsoft excel"],
    "powerpoint": ["microsoft powerpoint"],
    "chrome": ["google chrome"],
    "edge": ["microsoft edge"],
    "firefox": ["mozilla firefox"],
}


# ==========================================
#          NORMALIZE TEXT
# ==========================================

def normalize(text):

    text = str(text).lower().strip()

    text = re.sub(r"[\-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text


# ==========================================
#          DETECT LOCAL COMMANDS
# ==========================================

def is_local_command(command):

    text = normalize(command)

    patterns = [
        r"^(open|launch|start|run)\b",
        r"^(go to|visit)\b",
        r"^(search|google)\b",
        r"^(find|locate)\b.*\b(file|folder|document|picture|photo)\b",
        r"^(create|make|new)\b.*\bfolder\b",
        r"^(take|capture)\b.*\bscreenshot\b",
        r"^screenshot$",
        r"^show (me )?(my )?(desktop|downloads|documents|pictures|music|videos)$",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


# ==========================================
#          FIND START MENU SHORTCUTS
# ==========================================

def get_start_menu_apps():

    apps = []

    for root in START_MENU_PATHS:

        if not root.exists():
            continue

        try:

            for shortcut in root.rglob("*"):

                if shortcut.suffix.lower() in [".lnk", ".url"]:

                    apps.append({
                        "name": shortcut.stem,
                        "path": shortcut
                    })

        except (PermissionError, OSError):
            continue

    return apps


# ==========================================
#          GET INSTALLED WINDOWS APPS
# ==========================================

def get_windows_apps():

    if not shutil.which("powershell"):
        return []

    script = (
        "Get-StartApps | "
        "Select-Object Name, AppID | "
        "ConvertTo-Json -Compress"
    )

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                script
            ],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        apps = []

        for item in data:

            name = item.get("Name")
            app_id = item.get("AppID")

            if name and app_id:
                apps.append({
                    "name": name,
                    "app_id": app_id
                })

        return apps

    except (
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
        OSError
    ):
        return []


# ==========================================
#          MATCH APPLICATION
# ==========================================

def find_application(app_name):

    requested = normalize(app_name)

    shortcuts = get_start_menu_apps()
    windows_apps = get_windows_apps()

    # First: exact Start Menu shortcut match

    for app in shortcuts:

        if normalize(app["name"]) == requested:
            return {
                "type": "shortcut",
                "name": app["name"],
                "path": app["path"]
            }

    # Second: exact Windows app match

    for app in windows_apps:

        if normalize(app["name"]) == requested:
            return {
                "type": "windows_app",
                "name": app["name"],
                "app_id": app["app_id"]
            }

    # Third: aliases

    aliases = APP_ALIASES.get(requested, [])

    for alias in aliases:

        if shutil.which(alias):
            return {
                "type": "command",
                "name": requested,
                "path": alias
            }

        for app in shortcuts:

            if normalize(app["name"]) == normalize(alias):
                return {
                    "type": "shortcut",
                    "name": app["name"],
                    "path": app["path"]
                }

        for app in windows_apps:

            if normalize(app["name"]) == normalize(alias):
                return {
                    "type": "windows_app",
                    "name": app["name"],
                    "app_id": app["app_id"]
                }

    # Fourth: unique partial match

    candidates = []

    for app in shortcuts:

        name = normalize(app["name"])

        if requested in name or name in requested:
            candidates.append({
                "type": "shortcut",
                "name": app["name"],
                "path": app["path"]
            })

    for app in windows_apps:

        name = normalize(app["name"])

        if requested in name or name in requested:
            candidates.append({
                "type": "windows_app",
                "name": app["name"],
                "app_id": app["app_id"]
            })

    # Remove duplicate names

    unique = {}

    for item in candidates:
        unique[normalize(item["name"])] = item

    candidates = list(unique.values())

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        return {
            "type": "ambiguous",
            "candidates": candidates[:6]
        }

    # Fifth: fuzzy match

    all_names = [
        app["name"] for app in shortcuts + windows_apps
    ]

    matches = get_close_matches(
        requested,
        [normalize(name) for name in all_names],
        n=1,
        cutoff=0.82
    )

    if matches:

        matched_name = matches[0]

        for app in shortcuts:

            if normalize(app["name"]) == matched_name:
                return {
                    "type": "shortcut",
                    "name": app["name"],
                    "path": app["path"]
                }

        for app in windows_apps:

            if normalize(app["name"]) == matched_name:
                return {
                    "type": "windows_app",
                    "name": app["name"],
                    "app_id": app["app_id"]
                }

    return None


# ==========================================
#          OPEN APPLICATION
# ==========================================

def open_application(app_name):

    app = find_application(app_name)

    if not app:

        return (
            f"I couldn't find an installed application named "
            f"{app_name}, Sir. Check its name or install it first."
        )

    if app["type"] == "ambiguous":

        names = [
            item["name"] for item in app["candidates"]
        ]

        return (
            "I found multiple matching applications, Sir: "
            + ", ".join(names)
            + ". Please specify which one."
        )

    try:

        if app["type"] == "shortcut":

            os.startfile(str(app["path"]))

        elif app["type"] == "windows_app":

            subprocess.Popen([
                "explorer.exe",
                f"shell:AppsFolder\\{app['app_id']}"
            ])

        elif app["type"] == "command":

            subprocess.Popen(
                [app["path"]],
                shell=False
            )

        return f"Launching {app['name']}, Sir."

    except Exception as error:

        print("Application launch error:", repr(error))

        return (
            f"I found {app['name']}, Sir, "
            "but Windows couldn't launch it."
        )


# ==========================================
#          OPEN FOLDER
# ==========================================

def open_folder(folder_name):

    requested = normalize(folder_name)

    folder = FOLDER_ALIASES.get(requested)

    if folder is None:
        folder = Path(os.path.expandvars(folder_name.strip().strip('"')))

    try:

        if not folder.exists() or not folder.is_dir():

            return f"I couldn't find that folder, Sir: {folder}"

        os.startfile(str(folder))

        return f"Opening {folder.name}, Sir."

    except Exception as error:

        print("Folder error:", repr(error))
        return "I couldn't open that folder, Sir."


# ==========================================
#          OPEN FILE
# ==========================================

def open_file(file_path):

    path = Path(
        os.path.expandvars(
            os.path.expanduser(file_path.strip().strip('"'))
        )
    )

    try:

        if not path.exists() or not path.is_file():
            return f"I couldn't find that file, Sir: {path}"

        os.startfile(str(path))

        return f"Opening {path.name}, Sir."

    except Exception as error:

        print("File opening error:", repr(error))
        return "I couldn't open that file, Sir."


# ==========================================
#          OPEN WEBSITE
# ==========================================

WEBSITE_ALIASES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "x": "https://x.com",
    "twitter": "https://x.com",
}


def open_website(site):

    site = site.strip().strip('"').strip("'")
    normalized = normalize(site)

    url = WEBSITE_ALIASES.get(normalized)

    if not url:

        if re.match(
            r"^(https?://|www\.)",
            site,
            re.IGNORECASE
        ):
            url = site

        elif "." in site and " " not in site:
            url = "https://" + site

        else:
            return None

    try:

        webbrowser.open(url)

        return f"Opening {site}, Sir."

    except Exception as error:

        print("Website error:", repr(error))
        return "I couldn't open that website, Sir."


# ==========================================
#          GOOGLE SEARCH
# ==========================================

def google_search(query):

    query = query.strip()

    if not query:
        return "What would you like me to search for, Sir?"

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    try:

        webbrowser.open(url)

        return f"Searching Google for {query}, Sir."

    except Exception as error:

        print("Google search error:", repr(error))
        return "I couldn't perform that search, Sir."


# ==========================================
#          CREATE FOLDER
# ==========================================

def create_folder(folder_name):

    folder_name = folder_name.strip().strip('"')

    if not folder_name:
        return "Please tell me the folder name, Sir."

    path = Path(
        os.path.expandvars(
            os.path.expanduser(folder_name)
        )
    )

    if not path.is_absolute():
        path = HOME / "Desktop" / path

    try:

        if path.exists():
            return f"That folder already exists, Sir: {path}"

        path.mkdir(parents=True, exist_ok=False)

        return f"Folder created successfully, Sir: {path.name}"

    except Exception as error:

        print("Create folder error:", repr(error))
        return "I couldn't create that folder, Sir."


# ==========================================
#          FIND FILES
# ==========================================

def find_files(file_name):

    file_name = file_name.strip().strip('"')

    if not file_name:
        return "Please tell me which file to find, Sir."

    search_roots = [
        HOME / "Desktop",
        HOME / "Documents",
        HOME / "Downloads",
        HOME / "Pictures",
    ]

    matches = []
    query = normalize(file_name)

    for root in search_roots:

        if not root.exists():
            continue

        try:

            for path in root.rglob("*"):

                if len(matches) >= 10:
                    break

                try:

                    if not path.is_file():
                        continue

                    if query in normalize(path.name):
                        matches.append(path)

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            continue

        if len(matches) >= 10:
            break

    if not matches:
        return f"I couldn't find {file_name}, Sir, in your common folders."

    result = "I found these files, Sir: "

    result += "; ".join(
        str(path) for path in matches
    )

    return result


# ==========================================
#          TAKE SCREENSHOT
# ==========================================

def take_screenshot():

    try:

        from PIL import ImageGrab

        screenshot_folder = (
            HOME / "Pictures" / "JARVIS_Screenshots"
        )

        screenshot_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        from datetime import datetime

        filename = (
            "Screenshot_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".png"
        )

        screenshot_path = screenshot_folder / filename

        image = ImageGrab.grab()
        image.save(screenshot_path)

        return (
            f"Screenshot captured successfully, Sir. "
            f"Saved at {screenshot_path}"
        )

    except ImportError:

        return (
            "Screenshot support requires Pillow. "
            "Install it using: pip install Pillow"
        )

    except Exception as error:

        print("Screenshot error:", repr(error))
        return "I couldn't capture the screenshot, Sir."


# ==========================================
#          COMMAND PARSER
# ==========================================

def execute_command(command):

    text = command.strip()
    normalized = normalize(text)

    # --------------------------------------
    # SCREENSHOT
    # --------------------------------------

    if (
        normalized == "screenshot"
        or re.search(r"\b(take|capture)\b.*\bscreenshot\b", normalized)
    ):

        return take_screenshot()

    # --------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------

    match = re.match(
        r"^(?:search(?:\s+google)?(?:\s+for)?|google(?:\s+search)?(?:\s+for)?)\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:
        return google_search(match.group(1))

    # --------------------------------------
    # CREATE FOLDER
    # --------------------------------------

    match = re.match(
        r"^(?:create|make|new)\s+(?:a\s+)?folder(?:\s+called|\s+named)?\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:
        return create_folder(match.group(1))

    # --------------------------------------
    # FIND FILE
    # --------------------------------------

    match = re.match(
        r"^(?:find|locate|search for)\s+(?:the\s+)?(?:file|document|picture|photo)\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:
        return find_files(match.group(1))

    # --------------------------------------
    # OPEN COMMON FOLDERS
    # --------------------------------------

    match = re.match(
        r"^(?:open|show)\s+(?:my\s+)?(desktop|downloads|documents|pictures|photos|music|videos|home|user folder)$",
        normalized
    )

    if match:
        return open_folder(match.group(1))

    # --------------------------------------
    # OPEN WEBSITE
    # --------------------------------------

    match = re.match(
        r"^(?:open|visit|go to)\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:

        target = match.group(1).strip()

        website_result = open_website(target)

        if website_result:
            return website_result

    # --------------------------------------
    # OPEN FILE OR FOLDER BY PATH
    # --------------------------------------

    match = re.match(
        r"^(?:open|launch|start)\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:

        target = match.group(1).strip().strip('"')

        path = Path(
            os.path.expandvars(
                os.path.expanduser(target)
            )
        )

        if path.exists():

            if path.is_dir():
                return open_folder(str(path))

            if path.is_file():
                return open_file(str(path))

    # --------------------------------------
    # OPEN APPLICATION
    # --------------------------------------

    match = re.match(
        r"^(?:open|launch|start|run)\s+(.+)$",
        text,
        re.IGNORECASE
    )

    if match:

        app_name = match.group(1).strip()

        # Remove polite trailing phrases

        app_name = re.sub(
            r"\s+(please|for me|sir)$",
            "",
            app_name,
            flags=re.IGNORECASE
        ).strip()

        return open_application(app_name)

    # --------------------------------------
    # UNSUPPORTED LOCAL COMMAND
    # --------------------------------------

    return (
        "I recognized a computer command, Sir, "
        "but couldn't determine the requested action."
    )


# ==========================================
#          MODULE TEST
# ==========================================

if __name__ == "__main__":

    print("====================================")
    print("      J.A.R.V.I.S. AUTOMATION")
    print("====================================")

    print("Windows automation system ready.")

    while True:

        try:

            command = input("\nYou: ").strip()

            if command.lower() in ["exit", "quit"]:
                print("Goodbye, Sir.")
                break

            if not command:
                continue

            if is_local_command(command):

                result = execute_command(command)

                print("\nJ.A.R.V.I.S.:", result)

            else:

                print(
                    "\nThis is not a recognized local command."
                )

        except KeyboardInterrupt:

            print("\nGoodbye, Sir.")
            break

        except Exception as error:

            print("\nAutomation error:", repr(error))
