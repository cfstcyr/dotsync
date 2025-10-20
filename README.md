# DotSync

A powerful and flexible tool for managing and synchronizing your dotfiles across multiple systems. DotSync allows you to create symbolic links or copy configuration files to their appropriate locations, making it easy to maintain consistent setups across different machines.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands](#commands)
- [Advanced Usage](#advanced-usage)
- [Example: Version-Controlled Dotfiles Across Multiple Computers](#example-version-controlled-dotfiles-across-multiple-computers)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Changelog](#changelog)

## Features

- **Multiple Sync Actions**: Support for both symbolic links and file/directory copying
- **Flexible Configuration**: YAML-based configuration with JSON schema validation
- **Dry Run Mode**: Preview changes before applying them
- **Interactive Prompts**: Safe operation with confirmation prompts for destructive actions
- **Rich CLI**: Beautiful terminal interface with progress indicators and colored output
- **Cross-Platform**: Works on macOS, Linux, and Windows

## Installation

### Using uv (Recommended)

```bash
uv tool install git+https://github.com/cfstcyr/dotsync
```

### From Source

```bash
git clone https://github.com/cfstcyr/dotsync.git
cd dotsync
uv install
uv tool install .
```

## Quick Start

1. **Initialize a new sync configuration** in your dotfiles directory:

```bash
cd ~/my-dotfiles
dotsync init .
```

This creates a `.sync.yaml` file with a basic example configuration.

2. **Edit the configuration** to match your needs:

```yaml
# .sync.yaml
my-shell:
  action: symlink
  src: ./zshrc
  dest: ~/.zshrc

my-config:
  action: copy
  src: ./config
  dest: ~/.config/my-app
```

3. **Sync your dotfiles**:

```bash
dotsync sync ~/my-dotfiles
```

4. **Preview changes first** with dry run:

```bash
dotsync sync ~/my-dotfiles --dry-run
```

## Configuration

DotSync uses YAML configuration files to define sync operations. Each configuration file contains a mapping of sync items, where each item specifies:

- `action`: Either `"symlink"` or `"copy"`
- `src`: Source path (relative to the config file or absolute)
- `dest`: Destination path (can use `~` for home directory)

### Example Configuration

```yaml
# ~/.sync.yaml
zsh-config:
  action: symlink
  src: ./zshrc
  dest: ~/.zshrc

vim-config:
  action: copy
  src: ./vim
  dest: ~/.vim

git-config:
  action: symlink
  src: ./gitconfig
  dest: ~/.gitconfig

tmux-config:
  action: symlink
  src: ./tmux.conf
  dest: ~/.tmux.conf
```

### Configuration Discovery

DotSync automatically discovers configuration files using these patterns:
- `.dotsync*`
- `dotsync*`
- `.sync*`

You can specify custom patterns in the app settings.

## Commands

### Sync Operations

```bash
# Sync dotfiles
dotsync sync <path>

# Preview sync operations
dotsync sync <path> --dry-run

# Remove synced files/links
dotsync unsync <path>

# Initialize new configuration
dotsync init <path>
```

### Settings Management

```bash
# View current settings
dotsync settings info

# Set a setting
dotsync settings set sync_config_patterns='["*.yaml", "*.yml"]'

# Reset to defaults
dotsync settings reset
```

### Utilities

```bash
# Show available utility commands
dotsync utils --help
```

## Advanced Usage

### Verbose Output

```bash
# Increase verbosity for debugging
dotsync sync ~/my-dotfiles -vvv
```

### Custom Settings Path

```bash
# Use custom settings file
dotsync --app-settings ~/custom-settings.yaml sync ~/my-dotfiles
```

### Override Settings

```bash
# Temporarily override settings
dotsync --with-setting sync_config_patterns='["config.yaml"]' sync ~/my-dotfiles
```

## Project Structure

A typical dotfiles repository with DotSync might look like:

```
my-dotfiles/
├── .sync.yaml          # Main sync configuration
├── zshrc               # Zsh configuration
├── vim/
│   └── vimrc          # Vim configuration
├── gitconfig          # Git configuration
└── config/
    └── some-app/      # Application-specific configs
```

## Development

### Prerequisites

- Python 3.13+
- uv package manager

### Setup

```bash
git clone https://github.com/cfstcyr/dotsync.git
cd dotsync
uv install
```

### Testing

```bash
make test
```

### Linting and Formatting

```bash
make lint      # Check code quality
make format    # Format code
make x         # Fix linting and formatting issues
```

### Building Schemas

```bash
make export_schemas
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code is linted
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/cfstcyr/dotsync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cfstcyr/dotsync/discussions)
