# Kitty macOS Keychain Password Manager

A kitty kitten plugin that integrates with macOS Keychain for secure password management with fuzzy finding capabilities.

## Features

- 🔐 Stores passwords securely in macOS Keychain
- 🔍 Uses `fzf` for fast fuzzy finding of password keys
- ⌨️ Automatically pastes passwords when selected
- ✨ Simple interface for adding new passwords
- 🗑️ Delete passwords with `ctrl+D` and one-step confirmation
- 🛡️ No password storage in plain text files

## Requirements

- macOS (uses `security` command)
- [kitty terminal](https://sw.kovidgoyal.net/kitty/)
- [fzf](https://github.com/junegunn/fzf) - Install with: `brew install fzf`

## Installation

1. Copy `password_manager.py` to your kitty config directory:
   ```bash
   cp password_manager.py ~/.config/kitty/
   ```

2. Add a keyboard mapping to your `kitty.conf`:
   ```
   map ctrl+shift+p kitten password_manager.py
   ```

3. Reload kitty configuration or restart kitty.

## Usage

### Adding a New Password

1. Press `Ctrl+Shift+P` (or your configured shortcut)
2. Type a new key name in the fzf prompt
3. Press `Enter`
4. Enter the password when prompted (input is hidden)
5. Confirm the password
6. The password is now stored in your macOS Keychain

### Using an Existing Password

1. Press `Ctrl+Shift+P` (or your configured shortcut)
2. Use fzf to search and select an existing password key
3. Press `Enter`
4. The password is automatically retrieved and pasted to your terminal

### Deleting a Password

1. Press `Ctrl+Shift+P` (or your configured shortcut)
2. Use fzf to search and select the password key you want to delete
3. Press `Ctrl+D` instead of Enter
4. Review the warning message
5. Press `Enter` to confirm deletion, or type `no` to cancel
6. The password is permanently removed from your keychain

## How It Works

- All passwords are stored in macOS Keychain under the account name `kitty-pass`
- The service name is used as the key identifier
- When you select an existing key, the password is retrieved and automatically pasted with a carriage return
- When you create a new key, the password is stored but not pasted (security feature)

## Security

- Passwords are stored securely in macOS Keychain, not in plain text files
- Password input is hidden when creating new entries
- Password confirmation is required when creating new entries
- Uses macOS's native security mechanisms

## Technical Details

- Uses `security add-generic-password` to store passwords
- Uses `security find-generic-password` to retrieve passwords
- Uses `security delete-generic-password` to remove passwords
- Uses `security dump-keychain` to list available keys
- Integrates with kitty's remote control API to paste passwords
- Automatically detects fzf in Homebrew paths (both Intel and Apple Silicon)
- Handles shell environment variables to ensure PATH includes common tool locations
- Implements kitty's kitten interface with proper input handling
- Delete confirmation defaults to "yes" (press Enter) for quick deletion

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

### Password not pasting

Ensure you're using the latest version of kitty and that remote control is enabled (it should work by default with kittens).

## License

MIT

