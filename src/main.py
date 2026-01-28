#!/usr/bin/env python3
"""
A kitty kitten plugin that integrates with macOS Keychain for SSH connection management.
Uses fzf for selection and stores SSH credentials under the account 'kitty-ssh'.
"""

import getpass
import sys
import time

from kitty.fast_data_types import add_timer, get_boss

from src.exceptions import KittenError
from src.fzf import select_key_with_fzf
from src.keychain import (
    add_ssh_to_keychain,
    delete_ssh_from_keychain,
    get_existing_keys,
    get_password_from_keychain,
)
from src.service import parse_service_name
from src.ui import confirm_delete
from src.utils import kitty_input


def main(args):  # noqa: ARG001
    """
    Main function for the kitten - handles the terminal UI.

    Returns:
        SSH command string to execute, or empty string
    """
    while True:
        try:
            # Get existing keys from keychain
            existing_keys = get_existing_keys()

            # Let user select or enter a key using fzf
            selected_key, action = select_key_with_fzf(existing_keys)

            if not selected_key:
                # User cancelled
                return {}

            # Handle delete action
            if action == "delete":
                if selected_key in existing_keys:
                    if confirm_delete(selected_key):
                        delete_ssh_from_keychain(selected_key)
                        time.sleep(1)  # Brief delay to show success message
                        continue  # Return to fzf selection
                    else:
                        time.sleep(0.5)  # Brief delay before returning to fzf
                        continue  # Return to fzf selection
                else:
                    raise KittenError(f"Cannot delete: '{selected_key}' does not exist")

            # Handle paste only action
            if action == "paste_only":
                if selected_key in existing_keys:
                    # Existing connection - retrieve password and return for paste only
                    friendly_name, username, hostname = parse_service_name(selected_key)

                    if not username or not hostname:
                        raise KittenError(f"Invalid SSH connection format for '{selected_key}'")

                    password = get_password_from_keychain(selected_key)

                    print(f"Pasting password for '{friendly_name}' ({username}@{hostname})")

                    # Return dict with password only for paste (no SSH command)
                    return {
                        "password_only": password,
                    }
                else:
                    raise KittenError(f"Cannot paste password: '{selected_key}' does not exist")

            # Check if this is a new connection or existing one
            if selected_key in existing_keys:
                # Existing connection - retrieve password and return SSH command with password
                friendly_name, username, hostname = parse_service_name(selected_key)

                if not username or not hostname:
                    raise KittenError(f"Invalid SSH connection format for '{selected_key}'")

                password = get_password_from_keychain(selected_key)

                print(f"Connecting to '{friendly_name}' ({username}@{hostname})")

                # Return dict with SSH command and password for auto-paste
                ssh_cmd = (
                    f"kitty +kitten ssh -o UserKnownHostsFile=/dev/null "
                    f"-o StrictHostKeyChecking=no {username}@{hostname}"
                )
                return {
                    "ssh_command": ssh_cmd,
                    "password": password,
                }
            else:
                # New connection - prompt for details and store it
                friendly_name = selected_key
                print(f"\n Creating new SSH connection: {friendly_name}")

                username = kitty_input("Enter SSH username: ").strip()
                if not username:
                    raise KittenError("Username cannot be empty")

                hostname = kitty_input("Enter SSH hostname: ").strip()
                if not hostname:
                    raise KittenError("Hostname cannot be empty")

                password = getpass.getpass("Enter SSH password (hidden): ")
                if not password:
                    raise KittenError("Password cannot be empty")

                # Confirm password
                password_confirm = getpass.getpass("Confirm password: ")
                if password != password_confirm:
                    raise KittenError("Passwords do not match")

                # Store in keychain
                add_ssh_to_keychain(friendly_name, username, hostname, password)
                time.sleep(1)  # Brief delay to show success message
                continue  # Return to fzf selection

        except KittenError as e:
            # Display error message and wait for user to acknowledge
            print(f"\nError: {e}", file=sys.stderr)
            kitty_input("\nPress Enter to continue...")
            return {}
        except KeyboardInterrupt:
            # User interrupted with Ctrl+C
            return {}
        except Exception as e:
            # Unexpected error
            print(f"\nUnexpected error: {e}", file=sys.stderr)
            kitty_input("\nPress Enter to continue...")
            return {}


from kittens.tui.handler import result_handler


@result_handler(type_of_input="text")
def handle_result(args, answer, target_window_id, boss):  # noqa: ARG001
    """
    Handle the result from main() - send SSH command to the active window and auto-fill password.

    Args:
        args: Command line arguments
        answer: Return value from main() (dict with ssh_command and password, or password_only)
        target_window_id: ID of the window that launched the kitten
        boss: Boss instance for controlling kitty
    """
    # Get the target window
    w = boss.window_id_map.get(target_window_id)

    if w is None:
        return

    # If answer is empty dict, nothing to do
    if not answer:
        return

    # Check if this is a password-only paste request
    password_only = answer.get("password_only", "")
    if password_only:
        # Just paste the password without pressing Enter
        w.paste_text(password_only)
        return

    # Extract ssh_command and password from the answer dict
    ssh_command = answer.get("ssh_command", "")
    password = answer.get("password", "")

    if not ssh_command:
        return

    w.paste_text(ssh_command)
    w.send_key("Enter")

    # If we have a password, set up a timer to detect password prompt
    if password:
        attempt_count = 0  # Use list to allow modification in nested function
        max_attempts = 50
        interval = 0.05

        def check_for_password_prompt(timer_id: int | None) -> None:
            """Check screen content for password prompt and paste password if found."""
            nonlocal attempt_count
            attempt_count += 1

            # Get current active window dynamically
            current_boss = get_boss()
            current_window = current_boss.active_window

            # Fallback to original window if active window is None
            if current_window is None or current_window.destroyed:
                current_window = current_boss.window_id_map.get(target_window_id)

            # Check if window is valid
            if current_window is None or current_window.destroyed:
                return

            try:
                # Read screen content
                screen_text = current_window.as_text(as_ansi=False, add_history=False)

                # Check if "password:" appears in the screen (case-sensitive lowercase)
                if "password:" in screen_text.lower():
                    # Found password prompt! Paste password and send Enter
                    current_window.paste_text(password)
                    current_window.send_key("Enter")
                    return  # Stop checking

                # Check if we've reached max attempts
                if attempt_count >= max_attempts:
                    return  # Stop checking after max attempts

                # Schedule next check
                add_timer(check_for_password_prompt, interval, False)

            except Exception:
                # Silently handle any errors reading screen content
                pass

        # Start the timer
        add_timer(check_for_password_prompt, interval, False)

    # Paste the SSH command and execute it
    w.paste(ssh_command)
    w.send_key("Enter")
