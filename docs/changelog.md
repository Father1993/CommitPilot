# Changelog

## [2026-01-18] - AITUNNEL default and documentation simplification

### Changed

-   AITUNNEL set as default provider
-   Default model updated to gpt-4.1
-   Updated .env examples and configuration documentation
-   Documentation simplified: removed extra files, kept only README.md and changelog.md
-   Updated aliases in documentation: `acommit`, `acommit-here`, `acommit-dev`, `acommit-main`, `acommit-master`
-   Configuration now stored in CommitPilot directory (no .commits created in projects)
-   Added `config.ini.example` as configuration example
-   Removed `config.ini` from `.gitignore` (doesn't contain sensitive data)
-   Simplified program output: only commit message and push status
-   Default branch changed to `master`
-   `max_diff_size` increased to 7000 characters
-   All documentation and prompts translated to English
-   Improved commit message prompts with best practices

## [2023-10-15] - First Release

### Added

-   First working version of CommitPilot
-   Hugging Face API integration
-   OpenAI API integration
-   Installation script for quick setup
-   Git hooks for automatic message generation

### Changed

-   Optimized API request format for better results

### Fixed

-   Correct error handling when internet connection is missing
-   Correct handling of various API response formats

## [2023-10-20] - Documentation Improvements

### Added

-   Extended documentation in Markdown format
-   Usage examples with various scenarios
-   Developer guide

### Changed

-   Improved error message format
-   Clarified command line interface messages

## [2023-11-05] - Version 1.0.0

### Added

-   Full Conventional Commits format support
-   New aliases for convenient use (acommit-dev, acommit-main)
-   Configuration file for saving settings

### Changed

-   Improved commit scope detection mechanism
-   Optimized large diff file processing

### Fixed

-   Encoding issue when getting git diff
-   Correct handling of empty commits

## [2024-05-30] - Commit Generation Improvements

### Added

-   Mixtral model support for better message quality
-   Updated AI prompts in English
-   Updated API response processing logic

### Changed

-   Improved message extraction mechanism from API responses
-   Default commit message now in English
-   Updated API request parameters for more stable results

### Fixed

-   Hugging Face API response parsing issue
-   Incorrect handling of large diff files
-   Improved error handling for API requests

## [2023-12-10] - Project Rebranding

### Changed

-   Project name changed to "CommitPilot"
-   Updated all mentions of old name in documentation and code
-   Improved documentation formatting
