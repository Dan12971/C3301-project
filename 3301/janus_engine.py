import json
import time
from datetime import datetime, timezone
import threading
import subprocess

# Import our custom modules
import discord_adapter
import content_oracle

def load_schedule():
    """Loads the mission schedule from the JSON file."""
    with open('schedule.json', 'r') as f:
        return json.load(f)

def save_schedule(schedule_data):
    """Saves the updated schedule back to the file."""
    with open('schedule.json', 'w') as f:
        json.dump(schedule_data, f, indent=4)

def sync_state_to_git(task_id):
    """
    Commits and pushes the updated schedule.json to the GitHub repository.
    This acts as our state synchronization mechanism for the failsafe.
    """
    print(f"Janus Engine: Syncing state to Git for task '{task_id}'...")
    try:
        # Stage the schedule.json file
        subprocess.run(["git", "add", "schedule.json"], check=True)
        
        # Commit the changes with a descriptive message
        commit_message = f"Update schedule: Task '{task_id}' completed."
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push the changes to the remote repository
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("Janus Engine: State successfully synced to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Janus Engine: ERROR - Failed to sync state to Git. {e}")
        print("Please ensure Git is configured correctly on this machine (credentials, etc.).")
    except FileNotFoundError:
        print("Janus Engine: ERROR - 'git' command not found. Is Git installed and in the system's PATH?")


def check_schedule_and_act():
    """The main loop that checks the schedule and triggers actions."""
    print(f"\n[{datetime.now()}] Janus Engine: Checking schedule...")
    
    schedule = load_schedule()
    task_to_sync = None

    for task in schedule:
        if not task.get('posted', False):
            post_time = datetime.fromisoformat(task['post_time'].replace('Z', '+00:00'))
            
            if datetime.now(timezone.utc) >= post_time:
                print(f"Janus Engine: Executing task '{task['id']}'...")
                
                content_to_post = ""
                if task['type'] == 'static_post':
                    content_to_post = task['content']
                elif task['type'] == 'generated_riddle':
                    riddle = content_oracle.generate_riddle()
                    content_to_post = f"{task['content_prefix']}\n\n>>> {riddle}"

                image = task.get('image')
                
                # Use the discord adapter to post the message
                # We run this in the bot's event loop using client.loop.create_task
                discord_adapter.client.loop.create_task(
                    discord_adapter.post_message(content_to_post, image_path=image)
                )
                
                task['posted'] = True
                task_to_sync = task['id'] # Mark which task we need to sync
                break # Process one task per cycle to ensure clean state updates

    if task_to_sync:
        print("Janus Engine: Updating schedule file...")
        save_schedule(schedule)
        # Sync the new state to GitHub AFTER saving it locally
        sync_state_to_git(task_to_sync)
    else:
        print("Janus Engine: No actions to perform at this time.")

def main_loop():
    """The main execution loop for the engine."""
    while True:
        if discord_adapter.client.is_ready():
            check_schedule_and_act()
        else:
            print("Janus Engine: Waiting for Discord bot to connect...")
        
        # Check the schedule every 60 seconds
        time.sleep(60)

if __name__ == '__main__':
    print("--- The Janus Initiative (High Availability Version) is starting ---")
    
    # Run the Discord bot in a separate thread so it doesn't block our main loop
    discord_thread = threading.Thread(target=discord_adapter.run_bot)
    discord_thread.daemon = True # Allows main program to exit even if thread is running
    discord_thread.start()
    
    main_loop()


