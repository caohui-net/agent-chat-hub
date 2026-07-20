# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflow for automated pytest execution ([#1])
- Token usage tracking via MessageBus events (P1-001)
- Message queue capacity limit (1000 messages) to prevent memory overflow (P2-004)
- Comprehensive test suite with 45 test cases covering core functionality
- Gemini HTTP API implementation with full message history support
- Technical decision lesson documentation (docs/LESSON-gemini-http-vs-cli.md)
- Standard model integration guide (docs/MODEL-INTEGRATION-GUIDE.md)

### Changed
- **BREAKING**: `ResponseCoordinator.select_agents()` now returns tuple `(agents, stop_reason)` instead of just `agents` list (P1-002)
  - See [Migration Guide](docs/MIGRATION.md) for upgrade path
- **BREAKING**: `ResponseCoordinator.start_round()` now requires `session_id` and `round_num` parameters (P1-003)
  - See [Migration Guide](docs/MIGRATION.md) for upgrade path
- **BREAKING**: `ConfigManager` persistence now requires explicit `save_configs()` and `load_configs()` calls (P2-001)
  - See [Migration Guide](docs/MIGRATION.md) for upgrade path
- Gemini model now uses HTTP API instead of CLI subprocess for improved reliability and multi-turn dialogue support
- Agent priority sorting changed to ascending order (lower number = higher priority) for clarity (P1-002)
- Improved error handling with structured logging using logger instead of print() statements (P3-002)
- Timestamp generation refactored to use dedicated `_current_timestamp()` helper function (P3-001)

### Removed
- Deprecated Gemini CLI implementation (subprocess-based calling method)
- Unused subprocess and json imports from executor module

### Fixed
- ConfigManager now accepts both `str` and `Path` types for `config_dir` parameter
- Model reference integrity validation to prevent orphaned agent configurations (P1-003)
- Provider support strategy with proper error messages for unsupported providers (P1-004)
- Exception handling documentation added for API call error scenarios (P3-005)
- pytest test suite fixed to achieve 100% pass rate (45/45 tests passing)
