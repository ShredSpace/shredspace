import os
import zipfile
import requests
import json
from flask import Flask, render_template

app = Flask(__name__)

game_data = {}

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

    selected_indices = input("\nEnter the numbers of the games you'd like to update, separated by commas (e.g., 1,3): ")

    try:
        selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    except ValueError:
        return []

    selected_games = [game_data[i] for i in selected_indices if 0 <= i < len(game_data)]
    return selected_games

# Function to render the template and replace the static file
def render_and_replace_static_index(game_data):
    # Render the template with the game data
    rendered_content = render_template('index.html', games=game_data)

    # Write the rendered content to the static file "app/index.html"
    static_index_path = os.path.join('app', 'index.html')
    with open(static_index_path, 'w') as f:
        f.write(rendered_content)

def save_json(json_file):
    global game_data
    with open(json_file, "w") as jsf:
        json.dump(game_data, jsf)

def downloadGames(json_file):
    url = input("Enter a URL for a new game (ending in .shredspace): ")
    try:
        game = requests.get(url)
        game.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return
    try:
        game_data.append(game.json())
        save_json(json_file)
        print("Game added to library successfully. Update game before running.")
    except Exception as e:
        print(f"Error: {e}")


def updateGames():
    global game_data
    # Ask the user to select the games they want to update
    selected_games = ask_user_for_selection(game_data)

    if selected_games:
        print("\nDownloading and updating selected games...\n")
        for game in selected_games:
            download_and_unzip(game['url'], folder_name=game['name'])
    else:
        print("\nNo games selected for update.")

if __name__ == "__main__":
    print("ShredSpace Updator (Text Edition) v1.0.0")
    print()
    print()
    # Specify the path to the JSON file
    json_file = 'games.json'

    # Read the game data from the JSON file
    game_data = process_json_file(json_file)
    running = True
    if not game_data:
        print("No games found.")
    while running:
        print("Would you like to:")
        print("1. Download a New Game")
        print("2. Update Existing Games")
        print("3. Quit")
        selection = int(input("Select an option: ").strip())
        if selection == 2:
            updateGames()
        elif selection == 1:
            downloadGames(json_file)
        elif selection == 3:
            running = False
        else:
            print("No option selected.")

        # Render the template and replace the static index.html
        with app.app_context():
            render_and_replace_static_index(game_data)

    print("Goodbye!")

    save_json(json_file)



