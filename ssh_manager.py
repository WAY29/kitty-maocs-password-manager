#!/usr/bin/env python3

import contextlib as __stickytape_contextlib

@__stickytape_contextlib.contextmanager
def __stickytape_temporary_dir():
    import tempfile
    import shutil
    dir_path = tempfile.mkdtemp()
    try:
        yield dir_path
    finally:
        shutil.rmtree(dir_path)

with __stickytape_temporary_dir() as __stickytape_working_dir:
    def __stickytape_write_module(path, contents):
        import os, os.path

        def make_package(path):
            parts = path.split("/")
            partial_path = __stickytape_working_dir
            for part in parts:
                partial_path = os.path.join(partial_path, part)
                if not os.path.exists(partial_path):
                    os.mkdir(partial_path)
                    with open(os.path.join(partial_path, "__init__.py"), "wb") as f:
                        f.write(b"\n")

        make_package(os.path.dirname(path))

        full_path = os.path.join(__stickytape_working_dir, path)
        with open(full_path, "wb") as module_file:
            module_file.write(contents)

    import sys as __stickytape_sys
    __stickytape_sys.path.insert(0, __stickytape_working_dir)

    __stickytape_write_module('src/__init__.py', b'"""\nKitty SSH Manager - A kitty kitten plugin for SSH connection management.\n"""\n\nfrom src.exceptions import KittenError\nfrom src.keychain import (\n    add_ssh_to_keychain,\n    delete_ssh_from_keychain,\n    get_existing_keys,\n    get_password_from_keychain,\n)\nfrom src.utils import copy_to_clipboard, get_shell_env, kitty_input\n\n__all__ = [\n    "KittenError",\n    "add_ssh_to_keychain",\n    "copy_to_clipboard",\n    "delete_ssh_from_keychain",\n    "get_existing_keys",\n    "get_password_from_keychain",\n    "get_shell_env",\n    "kitty_input",\n]\n')
    __stickytape_write_module('src/exceptions.py', b'"""Custom exceptions for the SSH manager."""\n\n\nclass KittenError(Exception):\n    """Base exception for kitten errors that should be displayed to the user."""\n')
    __stickytape_write_module('src/keychain.py', b'"""macOS Keychain integration for SSH credential management."""\n\nimport subprocess\n\nfrom src.exceptions import KittenError\nfrom src.service import parse_service_name\n\n\ndef get_existing_keys() -> list[str]:\n    """\n    Retrieve all service keys from macOS Keychain where account=\'kitty-ssh\'.\n\n    Returns:\n        List of service key names\n    """\n    awk_script = """\n    BEGIN {RS="keychain: "}\n    /acct"<blob>="kitty-ssh"/ {\n        if (match($0, /"svce"<blob>="[^"]+/)) {\n            start = RSTART + 14;\n            len = RLENGTH - 14;\n            print substr($0, start, len)\n        }\n    }\n    """\n\n    try:\n        # Run security dump-keychain and pipe to awk\n        security_proc = subprocess.Popen(["security", "dump-keychain"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n\n        awk_proc = subprocess.Popen(\n            ["awk", awk_script], stdin=security_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True\n        )\n\n        security_proc.stdout.close()\n        output, _ = awk_proc.communicate()\n\n        if output:\n            return [key.strip() for key in output.strip().split("\\n") if key.strip()]\n        return []\n    except Exception as e:\n        raise KittenError(f"Error retrieving keychain keys: {e}") from e\n\n\ndef add_ssh_to_keychain(friendly_name: str, username: str, hostname: str, password: str) -> None:\n    """\n    Add a new SSH connection to macOS Keychain.\n\n    Args:\n        friendly_name: Friendly name for the connection\n        username: SSH username\n        hostname: SSH hostname\n        password: SSH password\n\n    Raises:\n        KittenError: If the SSH connection cannot be added\n    """\n    service = f"{friendly_name}|{username}@{hostname}"\n    try:\n        subprocess.run(\n            ["security", "add-generic-password", "-a", "kitty-ssh", "-s", service, "-w", password],\n            check=True,\n            capture_output=True,\n        )\n        print(f"SSH connection \'{friendly_name}\' ({username}@{hostname}) added successfully")\n    except subprocess.CalledProcessError as e:\n        error_msg = f"Error adding SSH connection to keychain: {e.stderr.decode()}"\n        raise KittenError(error_msg) from e\n\n\ndef get_password_from_keychain(service: str) -> str:\n    """\n    Retrieve a password from macOS Keychain.\n\n    Args:\n        service: Service name (key)\n\n    Returns:\n        Password string\n\n    Raises:\n        KittenError: If the password cannot be retrieved\n    """\n    try:\n        result = subprocess.run(\n            ["security", "find-generic-password", "-a", "kitty-ssh", "-s", service, "-w"],\n            check=True,\n            capture_output=True,\n            text=True,\n        )\n        return result.stdout.strip()\n    except subprocess.CalledProcessError as e:\n        error_msg = f"Could not retrieve password for \'{service}\'"\n        if e.stderr:\n            error_msg += f": {e.stderr.decode()}"\n        raise KittenError(error_msg) from e\n\n\ndef delete_ssh_from_keychain(service: str) -> None:\n    """\n    Delete an SSH connection from macOS Keychain.\n\n    Args:\n        service: Service name (key)\n\n    Raises:\n        KittenError: If the SSH connection cannot be deleted\n    """\n    try:\n        subprocess.run(\n            ["security", "delete-generic-password", "-a", "kitty-ssh", "-s", service],\n            check=True,\n            capture_output=True,\n        )\n        friendly_name, username, hostname = parse_service_name(service)\n        print(f"SSH connection \'{friendly_name}\' ({username}@{hostname}) deleted successfully")\n    except subprocess.CalledProcessError as e:\n        error_msg = f"Error deleting SSH connection from keychain: {e.stderr.decode()}"\n        raise KittenError(error_msg) from e\n')
    __stickytape_write_module('src/service.py', b'"""Service name parsing and formatting utilities."""\n\n\ndef parse_service_name(service: str) -> tuple[str, str, str]:\n    """\n    Parse service name in format "friendly-name|username@hostname".\n\n    Args:\n        service: Service name from keychain\n\n    Returns:\n        Tuple of (friendly_name, username, hostname)\n    """\n    if "|" in service:\n        friendly_name, connection = service.split("|", 1)\n        if "@" in connection:\n            username, hostname = connection.split("@", 1)\n            return friendly_name, username, hostname\n    # Fallback for malformed entries\n    return service, "", ""\n\n\ndef format_display_name(service: str) -> str:\n    """\n    Format service name for display in fzf.\n\n    Args:\n        service: Service name from keychain\n\n    Returns:\n        Formatted display string like "friendly-name (username@hostname)"\n    """\n    friendly_name, username, hostname = parse_service_name(service)\n    if username and hostname:\n        return f"{friendly_name} ({username}@{hostname})"\n    return friendly_name\n')
    __stickytape_write_module('src/utils.py', b'"""Utility functions for the SSH manager."""\n\nimport os\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nfrom src.exceptions import KittenError\n\n\ndef kitty_input(prompt: str = "") -> str:\n    """\n    Read input from the user in a kitty kitten context.\n\n    This function reads directly from /dev/tty to ensure it works correctly\n    in kitten environment where stdin might be redirected.\n\n    Args:\n        prompt: The prompt to display to the user\n\n    Returns:\n        The user\'s input as a string (stripped of whitespace)\n    """\n    try:\n        with open("/dev/tty", encoding="utf-8") as tty:\n            if prompt:\n                sys.stdout.write(prompt)\n                sys.stdout.flush()\n            response = tty.readline().strip()\n            return response\n    except Exception:  # noqa: BLE001\n        # Fallback to regular input if /dev/tty is not available\n        return input(prompt).strip()\n\n\ndef get_shell_env():\n    """\n    Get the environment variables from the user\'s shell to ensure PATH includes homebrew and other tools.\n\n    Returns:\n        Dictionary of environment variables with properly configured PATH\n    """\n    env = os.environ.copy()\n\n    # Common homebrew paths on macOS\n    homebrew_paths = [\n        "/opt/homebrew/bin",  # Apple Silicon Macs\n        "/usr/local/bin",  # Intel Macs\n        "/opt/homebrew/sbin",\n        "/usr/local/sbin",\n    ]\n\n    # Get existing PATH\n    current_path = env.get("PATH", "")\n    path_parts = current_path.split(":") if current_path else []\n\n    # Add homebrew paths if they exist and aren\'t already in PATH\n    for brew_path in homebrew_paths:\n        if Path(brew_path).exists() and brew_path not in path_parts:\n            path_parts.insert(0, brew_path)\n\n    # Update PATH in environment\n    env["PATH"] = ":".join(path_parts)\n\n    return env\n\n\ndef copy_to_clipboard(text: str) -> None:\n    """\n    Copy text to macOS clipboard using pbcopy.\n\n    Args:\n        text: Text to copy to clipboard\n    """\n    try:\n        subprocess.run(["pbcopy"], input=text.encode(), check=True)\n    except subprocess.CalledProcessError as e:\n        raise KittenError(f"Failed to copy to clipboard: {e}") from e\n')
    __stickytape_write_module('src/fzf.py', b'"""FZF integration for SSH connection selection."""\n\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nfrom src.exceptions import KittenError\nfrom src.service import format_display_name\nfrom src.utils import get_shell_env\n\n\ndef find_fzf_path():\n    """\n    Try to find the fzf executable in common locations.\n\n    Returns:\n        Path to fzf executable, or just "fzf" if not found in known locations\n    """\n    # Try to find fzf using \'which\' with the proper environment\n    try:\n        env = get_shell_env()\n        result = subprocess.run(\n            ["which", "fzf"],\n            capture_output=True,\n            text=True,\n            check=False,\n            env=env,\n        )\n        if result.returncode == 0 and result.stdout.strip():\n            return result.stdout.strip()\n    except Exception:\n        pass\n\n    # Common fzf installation locations\n    common_paths = [\n        "/opt/homebrew/bin/fzf",\n        "/usr/local/bin/fzf",\n        Path.home() / ".fzf/bin/fzf",\n    ]\n\n    for fzf_path in common_paths:\n        fzf_file = Path(fzf_path)\n        if fzf_file.exists() and fzf_file.is_file():\n            return str(fzf_file)\n\n    # Fallback to just "fzf" and let PATH resolution handle it\n    return "fzf"\n\n\ndef select_key_with_fzf(existing_keys: list[str]) -> tuple[str, str]:\n    """\n    Use fzf to select an existing SSH connection or create a new one.\n\n    Args:\n        existing_keys: List of existing service keys\n\n    Returns:\n        Tuple of (selected_key, action) where action is one of:\n        - "connect": Connect to SSH (default)\n        - "delete": Delete the connection\n        - "paste_only": Only paste password without connecting\n    """\n    try:\n        # Format display names for fzf\n        display_items = [format_display_name(key) for key in existing_keys]\n        input_data = "\\n".join(display_items)\n        env = get_shell_env()\n        fzf_cmd = find_fzf_path()\n\n        result = subprocess.run(\n            [\n                fzf_cmd,\n                "--print-query",\n                "--prompt=Select SSH connection or enter new name: ",\n                "--bind=ctrl-d:become(echo DELETE:{})+accept",\n                "--bind=ctrl-e:become(echo PASTE:{})+accept",\n                "--header=Enter Connect | ctrl+D Delete | ctrl+E Paste password | Ctrl+C Cancel",\n            ],\n            input=input_data,\n            text=True,\n            capture_output=True,\n            check=False,  # fzf returns non-zero exit codes for valid states (1=no match, 130=cancelled)\n            env=env,\n        )\n\n        # Check the output for action prefixes\n        output = result.stdout.strip()\n\n        # Check if user wants to delete (output starts with DELETE:)\n        if output.startswith("DELETE:"):\n            display_name = output[7:]  # Remove "DELETE:" prefix\n            # Find the actual service key from display name\n            for i, display in enumerate(display_items):\n                if display == display_name:\n                    return (existing_keys[i], "delete")\n            # If not found in display items, try to use as-is\n            return (display_name, "delete")\n\n        # Check if user wants to paste only (output starts with PASTE:)\n        if output.startswith("PASTE:"):\n            display_name = output[6:]  # Remove "PASTE:" prefix\n            # Find the actual service key from display name\n            for i, display in enumerate(display_items):\n                if display == display_name:\n                    return (existing_keys[i], "paste_only")\n            # If not found in display items, try to use as-is\n            return (display_name, "paste_only")\n\n        # fzf returns:\n        # - exit code 0: user selected an item\n        # - exit code 1: user entered new text (no match)\n        # - exit code 130: user cancelled (Ctrl+C)\n\n        if result.returncode == 130:\n            # User cancelled\n            return ("", "")\n\n        output_lines = output.split("\\n")\n\n        # fzf with --print-query outputs: query on first line, selection on last line\n        # returncode 0 means user selected an item, 1 means no match/new input\n\n        if result.returncode == 0:\n            # User selected an existing item\n            # With --print-query, last non-empty line is the selection\n            selected_display = output_lines[-1] if output_lines else ""\n            if not selected_display and len(output_lines) > 1:\n                selected_display = output_lines[-2]\n\n            # Find the actual service key from display name\n            for i, display in enumerate(display_items):\n                if display == selected_display:\n                    print(f"DEBUG: Matched! Returning existing key: \'{existing_keys[i]}\'", file=sys.stderr)\n                    return (existing_keys[i], "connect")\n\n            return ("", "")\n        elif result.returncode == 1:\n            # User entered new text (no match)\n            # First line is the query text\n            new_name = output_lines[0] if output_lines else ""\n            print(f"DEBUG: New name entered: \'{new_name}\'", file=sys.stderr)\n            # Make sure it\'s not a display format name\n            if "(" in new_name and ")" in new_name and "@" in new_name:\n                # User might have typed something like the display format, extract friendly name\n                new_name = new_name.split("(")[0].strip()\n            return (new_name, "connect")\n\n        return ("", "")\n    except FileNotFoundError as e:\n        env = get_shell_env()\n        current_path = env.get("PATH", "")\n        error_msg = (\n            f"fzf command not found: {e}\\n"\n            f"Current PATH: {current_path}\\n\\n"\n            "To install fzf:\\n"\n            "  brew install fzf\\n\\n"\n            "Or if already installed, ensure it\'s in your PATH."\n        )\n        raise KittenError(error_msg) from e\n    except Exception as e:\n        raise KittenError(f"Error during fzf selection: {e}") from e\n')
    __stickytape_write_module('src/ui.py', b'"""User interface functions for SSH manager."""\n\nfrom src.service import parse_service_name\nfrom src.utils import kitty_input\n\n\ndef confirm_delete(service: str) -> bool:\n    """\n    Ask user to confirm deletion. Press Enter to delete, type \'no\' to cancel.\n\n    Args:\n        service: Service name to delete\n\n    Returns:\n        True if user confirms deletion, False otherwise\n    """\n    friendly_name, username, hostname = parse_service_name(service)\n    print("\\nWARNING: About to DELETE SSH connection:")\n    print(f"  Name: {friendly_name}")\n    print(f"  Connection: {username}@{hostname}")\n    print("This action cannot be undone!")\n\n    response = kitty_input("\\nPress Enter to DELETE, or type \'no\' to cancel: ").lower()\n\n    if response == "" or response not in ["no", "n"]:\n        return True\n    else:\n        print("Deletion cancelled.")\n        return False\n')
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
    