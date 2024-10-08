import os
import zipfile
import requests
import json
import shutil
import sys
from flask import Flask, render_template

game_data = {}

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

os.chdir(BASE_DIR)
if "_internal" in BASE_DIR:
    os.chdir("..")
    BASE_DIR = os.getcwd()

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))


# Function to download and unzip files
def download_and_unzip(url, save_folder='app', folder_name=None):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    zip_filename = url.split('/')[-1]
    zip_filepath = os.path.join(save_folder, zip_filename)

    print(f"Downloading game...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        if 'zip' not in response.headers.get('Content-Type', ''):
            raise ValueError("The URL does not point to a ZIP file.")

        with open(zip_filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    if folder_name is None:
        folder_name = os.path.splitext(zip_filename)[0]

    extract_folder = os.path.join(save_folder, folder_name)
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)

    print(f"Installing game...")
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
    except zipfile.BadZipFile as e:
        print(f"Error: {e} - The downloaded file is not a valid ZIP archive.")
        return

    print(f"Cleaning up...")
    os.remove(zip_filepath)

    print(f"Download, extraction, and cleanup complete.")

# Function to read and process the JSON file
def process_json_file(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {json_file}. Ensure it is valid JSON.")
        return []

    return data

# Function to ask the user which games they want to update
def ask_user_for_selection(game_data):
    print("\nAvailable games for update:")
    for i, game in enumerate(game_data):
        print(f"{i + 1}. {game['displayName']}")
    if len(game_data) == 0:
        print("None")

    selected_indices = input("\nEnter the numbers of the games you'd like to update, separated by commas (e.g., 1,3): ")

    try:
        selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    except ValueError:
        return []

    selected_games = [game_data[i] for i in selected_indices if 0 <= i < len(game_data)]
    return selected_games

def ask_user_uninstall(game_data):
    print("\nAvailable games to uninstall:")
    for i, game in enumerate(game_data):
        print(f"{i + 1}. {game['displayName']}")
    if len(game_data) == 0:
        print("None")

    selected_indices = input("\nEnter the number of the game you'd like to uninstall: ")

    try:
        selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    except ValueError:
        return []

    selected_games = [game_data[i] for i in selected_indices if 0 <= i < len(game_data)]
    return selected_indices

# Function to render the template and replace the static file
def render_and_replace_static_index(game_data):
    # Render the template with the game data
    rendered_content = render_template('index.html', games=game_data)
    # Write the rendered content to the static file "app/index.html"
    static_index_path = os.path.join(BASE_DIR, 'app', 'index.html')
    with open(static_index_path, 'w') as f:
        f.write(rendered_content)

def save_json(json_file):
    global game_data
    with open(json_file, "w") as jsf:
        json.dump(game_data, jsf)

def downloadGames(json_file, url=None):
    if url:
        url = url # don't you dare criticise me for this it looks better
    else:
        url = input("Enter a URL for a new game (ending in .shredspace): ")
    try:
        game = requests.get(url)
        game.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return
    try:
        gameJSON = game.json()
        if gameJSON in game_data:
            print("This game is already in your library!")
        else:
            game_data.append(gameJSON)
            save_json(json_file)
            print("Game added to library successfully. Update game before running.")
    except Exception as e:
        print(f"Error: {e}")


def updateGames(latest=False):
    global game_data
    # Ask the user to select the games they want to update
    if latest:
        selected_games = [game_data[len(game_data)-1]]
    else:
        selected_games = ask_user_for_selection(game_data)

    if selected_games:
        print("\nDownloading and updating selected games...\n")
        for game in selected_games:
            download_and_unzip(game['url'], folder_name=game['name'])
    else:
        print("\nNo games selected for update.")

def uninstallGames():
    global game_data
    selected_games = ask_user_uninstall(game_data)
    if len(selected_games) == 1:
        print("\nUninstalling selected games...\n")
        try:
            game_path = f'app/{game_data[selected_games[0]]["name"]}'
            if os.path.exists(game_path):
                shutil.rmtree(game_path)
            ic = game_data.pop(selected_games[0])
            print(len(game_data))
            print("Games uninstalled successfully.")
        except Exception as e:
            print(f"Error: {e}")
    elif len(selected_games) > 1:
        print("\nYou can only uninstall one game at a time.\n")
    else:
        print("\nNo games selected to uninstall.")
    save_json(json_file)

def create_reg_file_for_pyinstaller(protocol_name, exe_path, output_file="register_protocol.reg"):
    """
    Generates a .reg file for registering a custom URL protocol in Windows using a PyInstaller executable.

    Args:
    protocol_name (str): The custom protocol name (e.g., 'myapp').
    exe_path (str): Full path to the PyInstaller-generated executable (e.g., 'C:\\path\\to\\your_app.exe').
    output_file (str): The output .reg file name (default is 'register_protocol.reg').
    """
    
    # Escape backslashes for .reg file format
    exe_path = exe_path.replace("\\", "\\\\")
    
    # .reg file content
    reg_content = f"""Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\\{protocol_name}]
@="ShredSpace"
"URL Protocol"=""

[HKEY_CLASSES_ROOT\\{protocol_name}\\shell]

[HKEY_CLASSES_ROOT\\{protocol_name}\\shell\\open]

[HKEY_CLASSES_ROOT\\{protocol_name}\\shell\\open\\command]
@="\\"{exe_path}\\" \\"%1\\""
"""
    
    # Write content to the .reg file
    with open(output_file, "w") as file:
        file.write(reg_content)

# Create a .reg file
create_reg_file_for_pyinstaller("shredspace", BASE_DIR + "/update.exe", output_file=BASE_DIR + "/register_protocol.reg")

if __name__ == "__main__":
    print("ShredSpace Updator (Text Edition) v1.0.0\n\n")
    # Specify the path to the JSON file
    json_file = 'games.json'

    # Read the game data from the JSON file
    game_data = process_json_file(json_file)
    if len(sys.argv) > 1:
        url = sys.argv[1]
        # Process the URL or execute actions based on the URL
        downloadGames(json_file, url=url.replace("shredspace://", "https://"))
        updateGames(latest=True)
    else:
        running = True
        if not game_data:
            print("No games found.")
        while running:
            print("Would you like to:")
            print("1. Download a New Game")
            print("2. Update Existing Games")
            print("3. Uninstall Games")
            print("4. Quit")
            selection = int(input("Select an option: ").strip())
            if selection == 2:
                updateGames()
            elif selection == 1:
                downloadGames(json_file)
            elif selection == 3:
                uninstallGames()
            elif selection == 4:
                running = False
            else:
                print("No option selected.")

            # Render the template and replace the static index.html
            with app.app_context():
                render_and_replace_static_index(game_data)
            print("\n")

    print("Goodbye!")

    save_json(json_file)



