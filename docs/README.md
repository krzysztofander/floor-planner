# Floor Planner Documentation

This directory contains documentation for developers and users of the Floor Planner project.

## For Developers

### Feature Development
- **[Feature Development Workflow](features/README.md)** - How to plan and implement new features
- **[Feature Template](features/TEMPLATE.md)** - Copy this to plan complex features
- **[Planned Features](/memories/repo/planned-features.md)** - Backlog and active features

### Feature Documentation
- [Landscaping Elements](features/landscaping-elements.md) - Trees, shrubs, fences, ponds (Planned)


## Quick Start for AI Agents

When working on this project:
1. Review `.github/copilot-instructions.md` for project context
2. Check `docs/features/README.md` for feature development workflow
3. Run `make all` after any source code changes (regression testing)
4. Use feature documents in `docs/features/` for complex implementations

## Documentation Structure

```
docs/
├── README.md              ← You are here (documentation index)
└── features/              ← Feature planning and design documents
    ├── README.md          ← Feature development workflow
    ├── TEMPLATE.md        ← Template for new features
    ├── landscaping-elements.md
```

## Contributing

When adding new features:
1. Create a feature document using the template
2. Follow the workflow in `features/README.md`
3. Update this index with links to new documentation
