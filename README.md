# Kitty macOS Keychain SSH Manager

A kitty kitten plugin that integrates with macOS Keychain for SSH connection management with fuzzy finding capabilities.

## Features

- 🔐 Stores SSH credentials securely in macOS Keychain
- 🔍 Uses `fzf` for fast fuzzy finding of SSH connections
- 🚀 Automatically connects to SSH and enters password
- 📋 Paste password only with `ctrl+E` (without auto-connecting)
- ✨ Simple interface for adding new SSH connections
- 🗑️ Delete connections with `ctrl+D` and confirmation
- 🔄 Loops back to selection menu after create/delete operations
- 🛡️ No credential storage in plain text files
- 🏷️ Friendly names for SSH connections (e.g., "production-server" → user@host)

## Requirements

- macOS (uses `security` command)
- [kitty terminal](https://sw.kovidgoyal.net/kitty/)
- [fzf](https://github.com/junegunn/fzf) - Install with: `brew install fzf`

## Installation

1. Copy `ssh_manager.py` to your kitty config directory:
   ```bash
   cp ssh_manager.py ~/.config/kitty/
   ```

2. Add a keyboard mapping to your `kitty.conf`:
   ```
   map ctrl+shift+s kitten ssh_manager.py
   ```

3. Reload kitty configuration or restart kitty.

## Usage

### Adding a New SSH Connection

1. Press `Ctrl+Shift+S` (or your configured shortcut)
2. Type a friendly name for the connection in the fzf prompt (e.g., "production-server")
3. Press `Enter`
4. Enter the SSH username when prompted
5. Enter the SSH hostname when prompted
6. Enter the password (input is hidden)
7. Confirm the password
8. The connection is now stored in your macOS Keychain
9. You'll be returned to the fzf menu to select another action or connect

### Connecting to an SSH Server

1. Press `Ctrl+Shift+S` (or your configured shortcut)
2. Use fzf to search and select an existing SSH connection
3. Press `Enter`
4. The SSH connection command is automatically executed
5. The password is automatically entered when prompted

### Pasting Password Only (without connecting)

1. Press `Ctrl+Shift+S` (or your configured shortcut)
2. Use fzf to search and select an existing SSH connection
3. Press `Ctrl+E` instead of Enter
4. The password is pasted to your terminal without pressing Enter
5. You'll be returned to the fzf menu

### Deleting an SSH Connection

1. Press `Ctrl+Shift+S` (or your configured shortcut)
2. Use fzf to search and select the connection you want to delete
3. Press `Ctrl+D` instead of Enter
4. Review the warning message showing the connection details
5. Press `Enter` to confirm deletion, or type `no` to cancel
6. The connection is permanently removed from your keychain
7. You'll be returned to the fzf menu

## Keyboard Shortcuts in fzf

- `Enter` - Connect to selected SSH server (auto-enter password)
- `Ctrl+D` - Delete selected connection (with confirmation)
- `Ctrl+E` - Paste password only (without connecting)
- `Ctrl+C` - Cancel and exit

## How It Works

- All SSH credentials are stored in macOS Keychain under the account name `kitty-ssh`
- The service name format is: `friendly-name|username@hostname`
- When you select a connection, the script executes `kitty +kitten ssh` with auto-password entry
- When you press `Ctrl+E`, only the password is pasted (useful for manual SSH commands)
- After creating or deleting a connection, you're returned to the fzf menu to perform another action
- The script automatically detects the password prompt and fills it in

## Security

- SSH credentials are stored securely in macOS Keychain, not in plain text files
- Password input is hidden when creating new entries
- Password confirmation is required when creating new entries
- Uses macOS's native security mechanisms
- Auto-password entry uses screen content detection to find the password prompt
- Connects with `StrictHostKeyChecking=no` for convenience (can be modified in script)

## Technical Details

- Uses `security add-generic-password` to store SSH credentials
- Uses `security find-generic-password` to retrieve passwords
- Uses `security delete-generic-password` to remove credentials
- Uses `security dump-keychain` to list available connections
- Integrates with kitty's remote control API to execute SSH commands and paste passwords
- Automatically detects fzf in Homebrew paths (both Intel and Apple Silicon)
- Handles shell environment variables to ensure PATH includes common tool locations
- Implements kitty's kitten interface with proper input handling
- Uses kitty's screen content reading API to detect password prompts
- Delete confirmation defaults to "yes" (press Enter) for quick deletion
- Main loop continues after create/delete operations for better workflow

## Troubleshooting

### fzf not found

The kitten automatically searches for fzf in common Homebrew locations:
- `/opt/homebrew/bin/fzf` (Apple Silicon)
- `/usr/local/bin/fzf` (Intel)
- `~/.fzf/bin/fzf` (manual install)

If fzf is not found, install it:
```bash
brew install fzf
```

The kitten will show the current PATH in the error message if fzf cannot be found, which can help diagnose PATH issues.

### Permission denied when accessing keychain

Grant terminal access to keychain in System Preferences → Security & Privacy → Privacy → Automation

You may also need to allow kitty to access the keychain. The first time you run the kitten, macOS will prompt you to allow access.

### Password not auto-filling

- Ensure you're using the latest version of kitty
- The script detects "password:" prompt on the screen (case-insensitive)
- If the prompt uses different text, the password may not auto-fill
- In that case, use `Ctrl+E` to paste the password manually

### SSH connection issues

- The script uses `UserKnownHostsFile=/dev/null` and `StrictHostKeyChecking=no` for convenience
- You can modify these settings in the script if you prefer stricter security
- If you need to use SSH keys, you can still use `Ctrl+E` to paste the password for key passphrases

## License

MIT
