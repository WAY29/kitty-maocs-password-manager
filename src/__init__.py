"""
Kitty SSH Manager - A kitty kitten plugin for SSH connection management.
"""

from src.exceptions import KittenError
from src.keychain import (
    add_ssh_to_keychain,
    delete_ssh_from_keychain,
    get_existing_keys,
    get_password_from_keychain,
)
from src.utils import copy_to_clipboard, get_shell_env, kitty_input

__all__ = [
    "KittenError",
    "add_ssh_to_keychain",
    "copy_to_clipboard",
    "delete_ssh_from_keychain",
    "get_existing_keys",
    "get_password_from_keychain",
    "get_shell_env",
    "kitty_input",
]
