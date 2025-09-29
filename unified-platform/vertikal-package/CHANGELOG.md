# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- File size limits (5MB max)
- Better error handling and validation
- Improved CLI with version info
- Comprehensive documentation

## [0.1.0] - 2024-09-26

### Added
- Initial release
- Terminal file-aware ChatGPT assistant
- RStudio Terminal integration
- File operations: list, read, search
- R/SQL programming assistance
- Security sandboxing
- Groq API integration
- Cross-platform support (Windows, Mac, Linux)

### Features
- **File Navigation**: List directories, read files, search content
- **AI Assistant**: Programming help with file context
- **Security**: Sandboxed file access, path validation
- **RStudio Integration**: Works in Terminal pane
- **Fast**: Uses Groq's lightning-fast LLM

### Security
- Project directory isolation
- Path traversal protection
- Read-only file access
- Safe mode for additional restrictions

### Dependencies
- Python 3.9+
- groq>=0.9

## [0.0.1] - 2024-09-26

### Added
- Initial development version
- Basic file operations
- Groq integration
- Terminal interface
