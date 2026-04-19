#!/usr/bin/env python3
"""
Discord Chat AI Setup Script
Automates the entire setup process
"""

import os
import sys
import subprocess
import config

def run_command(command, description, interactive=False):
    """Run command and display status"""
    print(f"🔄 {description}...")
    try:
        if interactive:
            # For interactive commands, don't capture output
            result = subprocess.run(command, shell=True, check=True)
        else:
            # For non-interactive commands, capture output
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if not interactive:
            print(f"Error output: {e.stderr}")
        return False

def check_requirements(input_file):
    """Check necessary"""
    required_files = [input_file, 'config.py']
    missing_files = []

    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    return len(missing_files) == 0, missing_files

def main():
    print("🤖 Discord Chat AI Setup Wizard")
    print("=" * 40)

    # Check API Key from config
    api_key = config.API_KEY
    if not api_key or api_key.strip() == "your_api_key_here":
        print("❌ API Key not set or invalid!")
        print("Please set your Google AI API Key in the .env file:")
        print("DISCORD_AI_API_KEY='your_actual_google_ai_api_key'")
        print("")
        print("How to get an API Key:")
        print("1. Visit https://aistudio.google.com/app/apikey")
        print("2. Create a new API Key")
        print("3. Copy the key and add it to your .env file")
        return

    print("✅ API Key is set")

    # Ask for input filename
    input_file = input("Enter the Discord chat history filename (default: MyA_Chat.json): ").strip()
    if not input_file:
        input_file = 'MyA_Chat.json'

    # Check requirements
    files_exist, missing_files = check_requirements(input_file)
    if not files_exist:
        print("❌ Missing the following files:")
        for file in missing_files:
            print(f"  - {file}")
        return

    print("✅ All required files exist")

    # Step 1: Data Cleaning
    if not run_command(f"python cleaner.py '{input_file}'", "Data Cleaning", interactive=True):
        return

    # Step 2: Generate Persona
    if run_command("python profile_builder.py", "Persona Generation"):
        print("📝 Persona profile updated in config.py")

    # Step 3: Data Analysis
    if run_command("python analyzer.py --update-config", "Data Analysis", interactive=True):
        print("📊 Analysis complete, response timing settings updated")

    # Step 4: Build Vector Database
    if not run_command("python build_vectordb.py", "Vector Database Construction"):
        return

    print("\n🎉 Setup complete!")
    print("You can now run 'python main.py' to test the bot")

if __name__ == "__main__":
    main()
