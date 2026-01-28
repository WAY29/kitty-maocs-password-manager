"""Utility functions for the SSH manager."""

import os
import subprocess
import sys
from pathlib import Path

from src.exceptions import KittenError


def kitty_input(prompt: str = "") -> str:
    """
    Read input from the user in a kitty kitten context.

    This function reads directly from /dev/tty to ensure it works correctly
    in kitten environment where stdin might be redirected.

    Args:
        prompt: The prompt to display to the user

    Returns:
        The user's input as a string (stripped of whitespace)
    """
    try:
        with open("/dev/tty", encoding="utf-8") as tty:
            if prompt:
                sys.stdout.write(prompt)
                sys.stdout.flush()
            response = tty.readline().strip()
            return response
    except Exception:  # noqa: BLE001
        # Fallback to regular input if /dev/tty is not available
        return input(prompt).strip()


def get_shell_env():
    """
    Get the environment variables from the user's shell to ensure PATH includes homebrew and other tools.

    Returns:
        Dictionary of environment variables with properly configured PATH
    """
    env = os.environ.copy()

    # Common homebrew paths on macOS
    homebrew_paths = [
        "/opt/homebrew/bin",  # Apple Silicon Macs
        "/usr/local/bin",  # Intel Macs
        "/opt/homebrew/sbin",
        "/usr/local/sbin",
    ]

    # Get existing PATH
    current_path = env.get("PATH", "")
    path_parts = current_path.split(":") if current_path else []

    # Add homebrew paths if they exist and aren't already in PATH
    for brew_path in homebrew_paths:
        if Path(brew_path).exists() and brew_path not in path_parts:
            path_parts.insert(0, brew_path)

    # Update PATH in environment
    env["PATH"] = ":".join(path_parts)

    return env


def copy_to_clipboard(text: str) -> None:
    """
    Copy text to macOS clipboard using pbcopy.

    Args:
        text: Text to copy to clipboard
    """
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
    except subprocess.CalledProcessError as e:
        raise KittenError(f"Failed to copy to clipboard: {e}") from e
