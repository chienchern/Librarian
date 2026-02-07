# CLAUDE.md

## Commit Guidelines

- Never include Claude session links or URLs in commit messages
- Follow conventional commit style: concise subject line, optional body explaining "why"
- Keep commit messages focused on the "why" rather than the "what"

## Documentation Maintenance

**CRITICAL**: Documentation must be kept in sync with code changes.

Before each commit, review and update the following documentation if affected by your changes:

1. **README.md** - Update if changes affect:
   - Project overview or purpose
   - Tech stack or dependencies
   - Installation or setup instructions
   - API endpoints
   - Project structure

2. **docs/ARCHITECTURE.md** - Update if changes affect:
   - User journey flow or core functionality
   - Architectural patterns or design decisions
   - System components or their interactions
   - Data models or API contracts
   - External integrations or dependencies
   - Technology choices

3. **Other relevant docs** - Update any other documentation that describes modified functionality

### Documentation Update Process

1. After implementing code changes, review the sections above
2. If any documentation is outdated, update it BEFORE committing
3. Include documentation updates in the same commit as the code changes
4. In the commit message, mention if documentation was updated (e.g., "Update README to reflect new API endpoint")

### When Documentation Updates Are Required

- **Adding/removing features**: Update README and ARCHITECTURE.md
- **Changing API endpoints**: Update README API section and ARCHITECTURE.md API Design section
- **Modifying data models**: Update ARCHITECTURE.md Data Models section
- **Changing tech stack**: Update README and ARCHITECTURE.md
- **Altering component interactions**: Update ARCHITECTURE.md Component Architecture section
- **Adding/removing external dependencies**: Update README, ARCHITECTURE.md Integration Points

### When Documentation Updates Are Optional

- Bug fixes that don't change functionality
- Internal refactoring that doesn't affect architecture
- Code quality improvements (linting, formatting)

## Project Conventions

This file contains instructions for Claude Code when working on the Librarian project.
