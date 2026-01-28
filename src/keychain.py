"""macOS Keychain integration for SSH credential management."""

import subprocess

from src.exceptions import KittenError
from src.service import parse_service_name


def get_existing_keys() -> list[str]:
    """
    Retrieve all service keys from macOS Keychain where account='kitty-ssh'.

    Returns:
        List of service key names
    """
    awk_script = """
    BEGIN {RS="keychain: "}
    /acct"<blob>="kitty-ssh"/ {
        if (match($0, /"svce"<blob>="[^"]+/)) {
            start = RSTART + 14;
            len = RLENGTH - 14;
            print substr($0, start, len)
        }
    }
    """

    try:
        # Run security dump-keychain and pipe to awk
        security_proc = subprocess.Popen(["security", "dump-keychain"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        awk_proc = subprocess.Popen(
            ["awk", awk_script], stdin=security_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        security_proc.stdout.close()
        output, _ = awk_proc.communicate()

        if output:
            return [key.strip() for key in output.strip().split("\n") if key.strip()]
        return []
    except Exception as e:
        raise KittenError(f"Error retrieving keychain keys: {e}") from e


def add_ssh_to_keychain(friendly_name: str, username: str, hostname: str, password: str) -> None:
    """
    Add a new SSH connection to macOS Keychain.

    Args:
        friendly_name: Friendly name for the connection
        username: SSH username
        hostname: SSH hostname
        password: SSH password

    Raises:
        KittenError: If the SSH connection cannot be added
    """
    service = f"{friendly_name}|{username}@{hostname}"
    try:
        subprocess.run(
            ["security", "add-generic-password", "-a", "kitty-ssh", "-s", service, "-w", password],
            check=True,
            capture_output=True,
        )
        print(f"SSH connection '{friendly_name}' ({username}@{hostname}) added successfully")
    except subprocess.CalledProcessError as e:
        error_msg = f"Error adding SSH connection to keychain: {e.stderr.decode()}"
        raise KittenError(error_msg) from e


def get_password_from_keychain(service: str) -> str:
    """
    Retrieve a password from macOS Keychain.

    Args:
        service: Service name (key)

    Returns:
        Password string

    Raises:
        KittenError: If the password cannot be retrieved
    """
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "kitty-ssh", "-s", service, "-w"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Could not retrieve password for '{service}'"
        if e.stderr:
            error_msg += f": {e.stderr.decode()}"
        raise KittenError(error_msg) from e


def delete_ssh_from_keychain(service: str) -> None:
    """
    Delete an SSH connection from macOS Keychain.

    Args:
        service: Service name (key)

    Raises:
        KittenError: If the SSH connection cannot be deleted
    """
    try:
        subprocess.run(
            ["security", "delete-generic-password", "-a", "kitty-ssh", "-s", service],
            check=True,
            capture_output=True,
        )
        friendly_name, username, hostname = parse_service_name(service)
        print(f"SSH connection '{friendly_name}' ({username}@{hostname}) deleted successfully")
    except subprocess.CalledProcessError as e:
        error_msg = f"Error deleting SSH connection from keychain: {e.stderr.decode()}"
        raise KittenError(error_msg) from e
