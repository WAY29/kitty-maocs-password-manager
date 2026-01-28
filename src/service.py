"""Service name parsing and formatting utilities."""


def parse_service_name(service: str) -> tuple[str, str, str]:
    """
    Parse service name in format "friendly-name|username@hostname".

    Args:
        service: Service name from keychain

    Returns:
        Tuple of (friendly_name, username, hostname)
    """
    if "|" in service:
        friendly_name, connection = service.split("|", 1)
        if "@" in connection:
            username, hostname = connection.split("@", 1)
            return friendly_name, username, hostname
    # Fallback for malformed entries
    return service, "", ""


def format_display_name(service: str) -> str:
    """
    Format service name for display in fzf.

    Args:
        service: Service name from keychain

    Returns:
        Formatted display string like "friendly-name (username@hostname)"
    """
    friendly_name, username, hostname = parse_service_name(service)
    if username and hostname:
        return f"{friendly_name} ({username}@{hostname})"
    return friendly_name
