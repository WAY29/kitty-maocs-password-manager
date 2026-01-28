"""User interface functions for SSH manager."""

from src.service import parse_service_name
from src.utils import kitty_input


def confirm_delete(service: str) -> bool:
    """
    Ask user to confirm deletion. Press Enter to delete, type 'no' to cancel.

    Args:
        service: Service name to delete

    Returns:
        True if user confirms deletion, False otherwise
    """
    friendly_name, username, hostname = parse_service_name(service)
    print("\nWARNING: About to DELETE SSH connection:")
    print(f"  Name: {friendly_name}")
    print(f"  Connection: {username}@{hostname}")
    print("This action cannot be undone!")

    response = kitty_input("\nPress Enter to DELETE, or type 'no' to cancel: ").lower()

    if response == "" or response not in ["no", "n"]:
        return True
    else:
        print("Deletion cancelled.")
        return False
