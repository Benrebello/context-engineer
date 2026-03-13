# Changelog

All notable changes to Context Engineer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-03-13

### 🚀 Added

#### Context Engineering Layer
- **Context Capture** (`ce discuss`): Identifies gray areas in PRP phases and captures user decisions before planning starts → generates `CONTEXT.md` (`core/context_capture.py`, `cli/commands/discuss.py`)
- **Verification & UAT** (`ce verify`): Extracts deliverables from PRPs and generates UAT checklists after execution → produces `UAT.md` (`core/verification.py`, `cli/commands/verify.py`)
- **Research Phase** (`core/research.py`): Automated `RESEARCH.md` generation to enrich PRP planning with external context
- **Project Constitution** (`core/constitution.py`): `PROJECT_CONSTITUTION.md` — defines principles, tech stack, and development guidelines

#### Project Management
- **Execution State** (`ce state status|update`): Real-time task tracking via `STATE.json` + human-readable `STATE.md` (`core/progress.py`, `cli/commands/state.py`)
- **Health Checks** (`ce health [--repair]`): Diagnostic engine for project integrity with auto-repair of common issues (`core/health.py`, `cli/commands/health_cmd.py`)
- **Session Management** (`ce session pause|resume|status`): Pause/resume development sessions with context preservation (`cli/commands/session.py`)

#### Wave-Based Execution
- **Wave Executor** (`core/wave_executor.py`): Dependency-aware parallel task execution — topological sort organizes tasks into sequential waves with intra-wave parallelism

#### Git Workflow
- **Atomic Commits** (`ce commit task <id> <msg>`): Scoped commits per task with traceability metadata (`core/git_service.py`, `cli/commands/commit.py`)
- **Commit Map** (`ce commit map`): Generate JSON mapping of commits → tasks → PRPs for full traceability
- **Phase Branching** (`core/git_service.py`): Branching strategies with create/merge phase branches

### 🔧 Changed

#### CLI Registration
- All new commands registered in `cli/main.py` via Click groups: `commit`, `state`, `session`, `discuss`, `verify`, `health`

#### Documentation (Major Update)
- **README.md**: Added 3 new interaction tracks and 10 new features (EN + PT)
- **CLI_COMMANDS.md**: 7 new commands documented with full bilingual reference; workflow expanded from 8 → 12 steps; version bumped to 1.2.0
- **QUICK_REFERENCE.md**: 3 new command tracks in both language tables
- **INDEX.md**: New "Context Engineering Commands" table (10 commands) + expanded folder structure
- **FRAMEWORK_OVERVIEW.md**: Version 1.2.0, 7 new core modules, 6 new CLI files, 7 new components in architecture table
- **MAIN_USAGE_GUIDE.md**: 3 new interaction tracks (EN + PT)
- **AI_GOVERNANCE.md**: Embedded flow diagram inline

#### Visual Assets
- **`context_engineer_flow.mmd`**: Added 2 new subgraphs (Context Engineering Layer with 7 components, Git Workflow with 3 components); fixed Mermaid syntax for CLI compatibility
- **`context_engineer_flow.png`**: Regenerated with all 11 subgraphs
- **`visual_architecture.svg`**: Complete redesign — 9 component blocks across 3 layers with color-coded legend (blue=core, green=new, yellow=templates, purple=git)
- **`cli-workflow-diagram.md`**: 5 new Mermaid diagrams: Context Capture, Health Check, Session Management, Wave Execution, Verification/UAT; pipeline updated with `ce discuss` + `ce verify`; version 1.2

#### Image Embeds
- Embedded `visual_architecture.svg` and `context_engineer_flow.png` visually inline in 7 docs (README, FRAMEWORK_OVERVIEW, QUICK_REFERENCE, INDEX, MAIN_USAGE_GUIDE, AI_GOVERNANCE)

### 🐛 Fixed

- **`core/health.py`**: Removed broken imports (`core.progress.ExecutionState`, `core.constitution.Constitution`) — replaced with direct file operations for `STATE.json` and `PROJECT_CONSTITUTION.md` repair
- **Mermaid `.mmd` syntax**: Replaced em-dash (`—`), `<br/>`, `&`, `•`, `°`, `@` in labels with parser-compatible alternatives; quoted all node labels for robust rendering

---

## [1.1.0] - 2026-02-01

### 🚀 Added

#### Cache System
- **SQLite Backend**: Migrated cache from individual JSON files to SQLite database
  - Binary storage for embeddings (90% disk space reduction)
  - Indexed queries for 60-80% faster lookups
  - Automatic schema creation with optimized indices
  - Persistent embedding cache with deduplication

#### Type Safety
- **TypedDict Definitions**: Added `core/types.py` with comprehensive type definitions
  - `ProjectInitResult`, `PRDGenerationResult`, `PRPGenerationResult`
  - `TaskGenerationResult`, `ValidationResult`, `TraceabilityResult`
  - `ContractValidationResult`, `MockServerResult`
  - `PatternMetadata`, `ContextDict`, `MetricsDict`, `ROIMetrics`

#### Development Tools
- **mypy Configuration**: Strict type checking enabled in `pyproject.toml`
- **ruff Configuration**: Code quality checks with sensible defaults
- **pytest Configuration**: Coverage reporting configured
- **Development Dependencies**: Added `[dev]` optional dependencies group

### ⚡ Performance

#### Cache Optimizations
- **Lazy Loading**: Embedding models load only when needed (2-3x faster startup)
- **LRU Cache**: Added `@lru_cache(maxsize=1000)` to Levenshtein distance calculation
- **Binary Embeddings**: Store embeddings as numpy arrays in SQLite BLOB (60% smaller)
- **Connection Pooling**: Efficient SQLite connection management

#### Parallel Processing
- **Contract Validation**: Parallelized with `ThreadPoolExecutor` (3-5x faster)
- **Pre-compiled Regex**: Compile patterns once at module level
- **Batch Processing**: Process multiple tasks concurrently

#### Query Optimization
- **Database Indices**: Added indices on `context_hash`, `success_rate`, `usage_count`
- **Efficient Joins**: Optimized JOIN queries between patterns and embeddings
- **Query Planning**: Use `ORDER BY` with indices for fast sorting

### 🔧 Changed

#### Build System
- **Removed `setup.py`**: Consolidated all configuration to `pyproject.toml`
- **Standardized Dependencies**: Single source of truth for package versions
- **Modern Build Backend**: Using `setuptools>=61.0` with PEP 621

#### Logging
- **Structured Logging**: Replaced all `print()` with `logging` module
  - `logger.info()` for informational messages
  - `logger.warning()` for warnings
  - `logger.error()` for errors with `exc_info=True`
- **Named Loggers**: Each module has its own logger via `__name__`

#### Code Quality
- **Type Hints**: Added comprehensive type hints throughout codebase
- **Future Imports**: Added `from __future__ import annotations` for forward compatibility
- **Error Handling**: Improved exception handling with proper logging

### 🐛 Fixed

- **Dependency Conflicts**: Resolved version mismatches between `pyproject.toml` and `requirements.txt`
- **Memory Leaks**: Fixed potential memory leaks in cache operations
- **Race Conditions**: Thread-safe database operations
- **Type Errors**: Fixed numerous type-related bugs caught by mypy

### 📚 Documentation

- **Migration Guide**: Comprehensive guide for upgrading from v1.0 to v1.1
- **Type Definitions**: Documented all TypedDict classes
- **Performance Metrics**: Added benchmarks and expected improvements
- **Troubleshooting**: Common issues and solutions

### 🔒 Security

- **SQL Injection Prevention**: Parameterized queries throughout
- **Path Validation**: Proper path sanitization
- **Error Messages**: Sanitized error messages to prevent information leakage

---

## Performance Benchmarks

### Cache Operations
| Operation | v1.0 | v1.1 | Improvement |
|-----------|------|------|-------------|
| Store pattern | 15ms | 3ms | **5x faster** |
| Get pattern | 10ms | 2ms | **5x faster** |
| Search similar (100 patterns) | 500ms | 100ms | **5x faster** |
| Embedding cache hit | 50ms | 5ms | **10x faster** |

### Validation
| Operation | v1.0 | v1.1 | Improvement |
|-----------|------|------|-------------|
| Contract validation (50 tasks) | 30s | 6s | **5x faster** |
| Traceability check | 5s | 5s | No change |
| PRP validation | 2s | 2s | No change |

### Memory Usage
| Scenario | v1.0 | v1.1 | Improvement |
|----------|------|------|-------------|
| Light mode startup | 50MB | 50MB | No change |
| AI mode startup | 2.5GB | 500MB | **80% reduction** |
| Cache with 1000 patterns | 200MB | 50MB | **75% reduction** |

---

## Migration Notes

### Breaking Changes
1. Cache format changed from JSON to SQLite (automatic migration)
2. `setup.py` removed (use `pip install -e .` instead)
3. Some internal APIs changed (public APIs unchanged)

### Deprecations
- Direct use of `setup.py` (use `pyproject.toml`)
- Untyped return values (use TypedDict)

### Recommendations
1. Run `pip install -e ".[dev]"` to get development tools
2. Configure your IDE to use mypy for type checking
3. Enable ruff in your pre-commit hooks
4. Review migration guide before upgrading production systems

---

## [1.0.0] - 2025-12-01

### Initial Release
- Core engine for PRD/PRP/Task generation
- Intelligence cache with semantic search
- Pattern library and validators
- CLI with multiple commands
- AI governance with soft-gate
- Metrics and ROI tracking
- Multi-stack support
- Template engine with Jinja2
- Git hooks integration

---

## Upgrade Instructions

### From 1.1.x to 1.2.0

```bash
# 1. Update package
pip install --upgrade context-engineer

# 2. Initialize new project state (optional)
ce health --repair

# 3. Verify new commands work
ce health
ce state status
ce session status

# 4. Regenerate flow diagram (requires Node.js)
npx -y @mermaid-js/mermaid-cli -i docs/assets/context_engineer_flow.mmd -o docs/assets/context_engineer_flow.png
```

> **No breaking changes** from 1.1.x — all new features are additive. Existing workflows continue to work unchanged.

### From 1.0.x to 1.1.0

```bash
# 1. Backup cache (optional)
cp -r .cache .cache.backup

# 2. Update package
pip install --upgrade context-engineer

# 3. Install dev dependencies (optional)
pip install "context-engineer[dev]"

# 4. Verify installation
ce --version

# 5. Run tests
pytest

# 6. Check types
mypy core cli
```

---

## Contributors

- Benjamin Rebello (@benrebello) - Core development and optimizations

---

## Links

- [Repository](https://github.com/Benrebello/context-engineer)
- [Documentation](docs/INDEX.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Issue Tracker](https://github.com/Benrebello/context-engineer/issues)

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) principles.
