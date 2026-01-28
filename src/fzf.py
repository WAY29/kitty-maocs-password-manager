"""FZF integration for SSH connection selection."""

import subprocess
import sys
from pathlib import Path

from src.exceptions import KittenError
from src.service import format_display_name
from src.utils import get_shell_env


def find_fzf_path():
    """
    Try to find the fzf executable in common locations.

    Returns:
        Path to fzf executable, or just "fzf" if not found in known locations
    """
    # Try to find fzf using 'which' with the proper environment
    try:
        env = get_shell_env()
        result = subprocess.run(
            ["which", "fzf"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Common fzf installation locations
    common_paths = [
        "/opt/homebrew/bin/fzf",
        "/usr/local/bin/fzf",
        Path.home() / ".fzf/bin/fzf",
    ]

    for fzf_path in common_paths:
        fzf_file = Path(fzf_path)
        if fzf_file.exists() and fzf_file.is_file():
            return str(fzf_file)

    # Fallback to just "fzf" and let PATH resolution handle it
    return "fzf"


def select_key_with_fzf(existing_keys: list[str]) -> tuple[str, str]:
    """
    Use fzf to select an existing SSH connection or create a new one.

    Args:
        existing_keys: List of existing service keys

    Returns:
        Tuple of (selected_key, action) where action is one of:
        - "connect": Connect to SSH (default)
        - "delete": Delete the connection
        - "paste_only": Only paste password without connecting
    """
    try:
        # Format display names for fzf
        display_items = [format_display_name(key) for key in existing_keys]
        input_data = "\n".join(display_items)
        env = get_shell_env()
        fzf_cmd = find_fzf_path()

        result = subprocess.run(
            [
                fzf_cmd,
                "--print-query",
                "--prompt=Select SSH connection or enter new name: ",
                "--bind=ctrl-d:become(echo DELETE:{})+accept",
                "--bind=ctrl-e:become(echo PASTE:{})+accept",
                "--header=Enter Connect | ctrl+D Delete | ctrl+E Paste password | Ctrl+C Cancel",
            ],
            input=input_data,
            text=True,
            capture_output=True,
            check=False,  # fzf returns non-zero exit codes for valid states (1=no match, 130=cancelled)
            env=env,
        )

        # Check the output for action prefixes
        output = result.stdout.strip()

        # Check if user wants to delete (output starts with DELETE:)
        if output.startswith("DELETE:"):
            display_name = output[7:]  # Remove "DELETE:" prefix
            # Find the actual service key from display name
            for i, display in enumerate(display_items):
                if display == display_name:
                    return (existing_keys[i], "delete")
            # If not found in display items, try to use as-is
            return (display_name, "delete")

        # Check if user wants to paste only (output starts with PASTE:)
        if output.startswith("PASTE:"):
            display_name = output[6:]  # Remove "PASTE:" prefix
            # Find the actual service key from display name
            for i, display in enumerate(display_items):
                if display == display_name:
                    return (existing_keys[i], "paste_only")
            # If not found in display items, try to use as-is
            return (display_name, "paste_only")

        # fzf returns:
        # - exit code 0: user selected an item
        # - exit code 1: user entered new text (no match)
        # - exit code 130: user cancelled (Ctrl+C)

        if result.returncode == 130:
            # User cancelled
            return ("", "")

        output_lines = output.split("\n")

        # fzf with --print-query outputs: query on first line, selection on last line
        # returncode 0 means user selected an item, 1 means no match/new input

        if result.returncode == 0:
            # User selected an existing item
            # With --print-query, last non-empty line is the selection
            selected_display = output_lines[-1] if output_lines else ""
            if not selected_display and len(output_lines) > 1:
                selected_display = output_lines[-2]

            # Find the actual service key from display name
            for i, display in enumerate(display_items):
                if display == selected_display:
                    print(f"DEBUG: Matched! Returning existing key: '{existing_keys[i]}'", file=sys.stderr)
                    return (existing_keys[i], "connect")

            return ("", "")
        elif result.returncode == 1:
            # User entered new text (no match)
            # First line is the query text
            new_name = output_lines[0] if output_lines else ""
            print(f"DEBUG: New name entered: '{new_name}'", file=sys.stderr)
            # Make sure it's not a display format name
            if "(" in new_name and ")" in new_name and "@" in new_name:
                # User might have typed something like the display format, extract friendly name
                new_name = new_name.split("(")[0].strip()
            return (new_name, "connect")

        return ("", "")
    except FileNotFoundError as e:
        env = get_shell_env()
        current_path = env.get("PATH", "")
        error_msg = (
            f"fzf command not found: {e}\n"
            f"Current PATH: {current_path}\n\n"
            "To install fzf:\n"
            "  brew install fzf\n\n"
            "Or if already installed, ensure it's in your PATH."
        )
        raise KittenError(error_msg) from e
    except Exception as e:
        raise KittenError(f"Error during fzf selection: {e}") from e
