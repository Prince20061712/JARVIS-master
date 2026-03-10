# Documentation

This directory contains comprehensive documentation for the JARVIS Flashcard System v3.0.

## File Index

### Version Information
- **[V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md)** - Complete v2.0 → v3.0 migration guide with code examples
- **[V3_STRUCTURE.md](V3_STRUCTURE.md)** - Detailed v3.0 directory structure, statistics, and deployment checklist

### Architecture & Structure
- **[ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)** - System architecture overview and component relationships
- **[STRUCTURE.md](STRUCTURE.md)** - Directory structure and module organization
- **[MODULE_REFERENCE.md](MODULE_REFERENCE.md)** - Comprehensive module glossary with all classes and functions

### Integration & Migration
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - v2.0 integration completion summary
- **[V2_SUMMARY.md](V2_SUMMARY.md)** - v2.0 feature summary and capabilities

### Developer Guides
- **[IMPORTS_V2.md](IMPORTS_V2.md)** - Import structure and dependency management
- **[IMPORT_GUIDE.md](IMPORT_GUIDE.md)** - Guide for using and importing modules in the system

## Quick Start Documentation

### For New Users
1. Start with [README.md](../README.md) in the root directory
2. Review [V3_STRUCTURE.md](V3_STRUCTURE.md) for complete system layout
3. Check [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) for detailed design

### For Developers
1. Review [V3_STRUCTURE.md](V3_STRUCTURE.md) for directory layout
2. Use [MODULE_REFERENCE.md](MODULE_REFERENCE.md) for API reference
3. Check [IMPORT_GUIDE.md](IMPORT_GUIDE.md) when adding new code
4. Reference [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md) for integration patterns

### For Integration (v2.0 → v3.0)
1. Start with [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md) for overview
2. Follow the migration checklist section
3. Review import changes section
4. Run tests from [V3_STRUCTURE.md](V3_STRUCTURE.md#testing-framework)

### For System Architecture
1. Read [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) for design principles
2. Review [V3_STRUCTURE.md](V3_STRUCTURE.md) for v3.0 implementation
3. Check [STRUCTURE.md](STRUCTURE.md) for directory details
4. Use [MODULE_REFERENCE.md](MODULE_REFERENCE.md) for specific classes

## System Overview

### Core Components
- **Flashcard Management** - Create, retrieve, update, and delete flashcards
- **Spaced Repetition** - SM-2 algorithm implementation for optimal learning
- **Adaptive Learning** - Dynamic question generation and difficulty adjustment
- **Academic QA** - Comprehensive academic question answering system
- **Viva Simulation** - Simulated examination environment

### Key Features (v3.0)
- Multi-modal learning (flashcards, viva simulations, academic QA)
- Intelligent card generation using LLMs (Ollama)
- Vector storage for semantic search (Chroma)
- WebSocket support for real-time updates
- Hand-drawing recognition and diagram analysis
- OCR capabilities for text extraction
- Comprehensive analytics and learning patterns
- **NEW**: Configuration management system
- **NEW**: Repository pattern for data access
- **NEW**: Unified caching layer
- **NEW**: Centralized logging infrastructure
- **NEW**: Input validation with Pydantic

## New in v3.0

### Infrastructure Modules
- **config/** - Centralized application settings and logging
- **storage/** - Repository pattern and caching layer
- **utils/** - Validators, helpers, and shared constants

### Enhanced Modules
- **vision/** - New OCR processor and diagram analyzer
- **websocket/** - Centralized connection manager
- **tests/** - Full test structure with fixtures

### Documentation
- **docs/** - All documentation organized in one place
- **V3_MIGRATION_GUIDE.md** - Comprehensive migration guide
- **V3_STRUCTURE.md** - Detailed structure and statistics

## Version Information
- **Current Version**: 3.0.0
- **Previous Version**: 2.0.0
- **Python Version**: 3.8+
- **Framework**: FastAPI
- **Database**: SQLite
- **Vector Store**: Chroma DB

## Configuration

System configuration is managed through:
- `config/settings.py` - Application settings (pydantic-based)
- `config/logging_config.py` - Logging configuration
- Environment variables (see `.env.example`)
- `utils/constants.py` - Shared application constants

## Testing

Test structure is organized in:
- `tests/test_api/` - API endpoint tests
- `tests/test_core/` - Core functionality tests
- `tests/test_academic/` - Academic module tests
- `tests/conftest.py` - Pytest configuration and fixtures

## Key Statistics

### Code
- 25+ modules
- 50+ submodules
- 48KB spaced repetition engine
- 1600+ lines of vision processing
- 14,000+ lines of total code

### Documentation
- 10 comprehensive guides
- 50+ pages of documentation
- API reference for all classes
- Code examples throughout

## Support & Troubleshooting

### Common Questions
1. **How do I upgrade from v2.0?** See [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md)
2. **How do I use the new config system?** See [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md#configuration-management-config) section
3. **Where's the API reference?** See [MODULE_REFERENCE.md](MODULE_REFERENCE.md)
4. **How do I write tests?** See [V3_STRUCTURE.md](V3_STRUCTURE.md#testing-framework)

### Troubleshooting
1. Check the relevant documentation file
2. Review [MODULE_REFERENCE.md](MODULE_REFERENCE.md) for API details
3. Consult [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) for system design
4. Check test examples in `tests/` for usage patterns

## Integration Points

### FastAPI Integration
See [README.md](../README.md) for quick usage examples

### Database Integration
See [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md#storage--persistence-layer-storage) for Repository pattern

### WebSocket Integration
See [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md#websocket-connection-manager-websocket) for ConnectionManager

### Configuration
See [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md#configuration-management-config) for Settings integration

## Document Navigation

```
For Understanding...        → Read This
Architecture               → ARCHITECTURE_V2.md
v3.0 Changes               → V3_MIGRATION_GUIDE.md
Complete Structure          → V3_STRUCTURE.md
API Reference              → MODULE_REFERENCE.md
Import Examples            → IMPORT_GUIDE.md
Upgrade Path (v2→v3)       → V3_MIGRATION_GUIDE.md
Module Tree                → STRUCTURE.md
Historical Context         → V2_SUMMARY.md
Integration Status         → INTEGRATION_COMPLETE.md
```

## Related Files

- **[../README.md](../README.md)** - Main system README with quick start
- **[../config/settings.py](../config/settings.py)** - Settings class with documentation
- **[../config/logging_config.py](../config/logging_config.py)** - Logging setup function
- **[../utils/constants.py](../utils/constants.py)** - Application constants
- **[../tests/conftest.py](../tests/conftest.py)** - Test fixtures and configuration

## Deployment Information

See [V3_STRUCTURE.md - Deployment Considerations](V3_STRUCTURE.md#deployment-considerations) for:
- Requirements checklist
- Production deployment steps
- Configuration recommendations
- Monitoring setup

## Contributing

When adding documentation:
1. Place files in `docs/` directory
2. Update this `README.md` with the new file entry
3. Add table of contents entry if needed
4. Cross-link related documents
5. Follow existing documentation style

---

**Last Updated**: v3.0.0 - Production Release
**Status**: Stable and Production-Ready

