import os
import subprocess
import shutil
from network_manager import download_steamcmd, extract_zip


def install_steamcmd(console_output, program_directory, user_directory):
    try:
        # Step 1: Download SteamCMD
        console_output.append("Downloading SteamCMD...")
        zip_path = download_steamcmd(program_directory)
        console_output.append("SteamCMD downloaded.")

        # Step 2: Extract SteamCMD
        console_output.append("Extracting SteamCMD...")
        extract_zip(zip_path, program_directory)
        console_output.append("SteamCMD extracted.")

        # Step 3: Move to user specified directory
        steamcmd_extracted_dir = os.path.join(program_directory, "steamcmd")
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        for item in os.listdir(steamcmd_extracted_dir):
            s = os.path.join(steamcmd_extracted_dir, item)
            d = os.path.join(user_directory, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        console_output.append("SteamCMD moved to user directory.")

        # Step 4: Install SteamCMD
        console_output.append("Installing SteamCMD...")
        result = subprocess.run([os.path.join(user_directory, 'steamcmd.sh')], capture_output=True, text=True)
        console_output.append(result.stdout)
        console_output.append("SteamCMD installed.")

        # Step 5: Cleanup
        os.remove(zip_path)
        shutil.rmtree(steamcmd_extracted_dir)
        console_output.append("Cleanup complete.")

    except Exception as e:
        console_output.append(f"Error: {str(e)}")
