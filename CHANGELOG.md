# Changelog

All notable changes to the Task MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-27

### Added
- Auto-capture conversation ID in `created_by` field when available via FastMCP Context
  - Session ID automatically populated from MCP context when `create_task()` is called
  - Manual override still supported via explicit `created_by` parameter
  - Backward compatible: field remains optional, gracefully handles missing context

### Changed
- Standardized all timestamp fields to ISO 8601 format with microseconds
  - Format: `YYYY-MM-DDTHH:MM:SS.microseconds` (e.g., `2025-10-27T15:30:28.123456`)
  - Applies to: `created_at`, `updated_at`, `completed_at`, `deleted_at`
  - Backward compatible: existing records with space-separated format still parse correctly
- TaskUpdate validators now handle None values properly for true partial updates
  - No longer requires passing unchanged fields when updating tasks
  - `validate_status()` and `validate_priority()` return early for None values
  - Follows Pydantic v2 best practices for optional field validation

### Fixed
- TaskUpdate no longer requires `priority` and `status` fields for partial updates
  - Users can now update only the fields they want to change
  - Removes workaround requirement from v0.1.0
- Context parameter in `create_task()` now optional for test compatibility
  - Supports direct function calls without MCP context
  - Maintains auto-capture when called through MCP server

### Technical Details
- **Commits**: 4 micro-commits implementing enhancements + 1 integration fix
- **Test Coverage**: All 54 integration tests passing
- **Breaking Changes**: None (all changes are additive or more permissive)
- **Migration**: Not required - v0.2.0 is fully backward compatible with v0.1.0 databases

## [0.1.0] - 2025-10-27

### Added
- Initial release with 13 MCP tools for task management
- SQLite-based persistence with WAL mode for concurrent access
- Task hierarchy support (parent/child relationships)
- Dependency management with blocking and validation
- Project registry for multi-workspace isolation
- Soft delete with 30-day retention period
- Full-text search on title and description fields
- Status state machine (todo → in_progress → blocked → done → cancelled)
- Priority levels (low, medium, high)
- Tag organization with normalization
- File references for task context
- Cross-client compatibility (Claude Code + Claude Desktop)

### MCP Tools
1. `create_task` - Create new tasks with validation
2. `get_task` - Retrieve single task by ID
3. `update_task` - Update existing tasks with state validation
4. `list_tasks` - List tasks with optional filters
5. `delete_task` - Soft delete tasks with cascade option
6. `search_tasks` - Full-text search on title/description
7. `get_task_tree` - Retrieve task with all nested subtasks
8. `get_blocked_tasks` - List tasks with status='blocked'
9. `get_next_tasks` - Get actionable tasks (no unresolved dependencies)
10. `cleanup_deleted_tasks` - Purge soft-deleted tasks older than N days
11. `list_projects` - List all known projects from master database
12. `get_project_info` - Get project metadata and task statistics
13. `set_project_name` - Set friendly name for a project

### Database Architecture
- Per-project SQLite databases: `~/.task-mcp/databases/project_{hash}.db`
- Master registry database: `~/.task-mcp/master.db`
- Workspace path hashing (SHA256, 8 chars) for safe filenames
- WAL mode for concurrent reads between Claude Code and Desktop
- Foreign key enforcement for referential integrity
- Automatic timestamps for `created_at`, `updated_at`, `completed_at`, `deleted_at`

### Validation Constraints
- Description limit: 10,000 characters (prevent token overflow)
- Blocker reason required when status='blocked'
- Dependency resolution before task completion
- Status transition validation
- Tag normalization (lowercase, single spaces)

### Testing
- 54 integration tests with 100% pass rate
- Cross-client validation (Claude Code + Desktop)
- Type safety with mypy --strict
- Code quality with ruff

### Documentation
- Complete README with usage examples
- CLAUDE.md with architecture and implementation guidance
- MCP configuration guide for Claude Code and Desktop
- Production testing report with 17 test categories

---

## Version History Summary

- **v0.2.0** (2025-10-27): Polish release - timestamp standardization, partial updates, auto-capture
- **v0.1.0** (2025-10-27): Initial production release with 13 MCP tools

[0.2.0]: https://github.com/Ravenight13/simple-task-tracker-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Ravenight13/simple-task-tracker-mcp/releases/tag/v0.1.0
