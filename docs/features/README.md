# Feature Development Workflow

## Planning a New Feature

### 1. Create Feature Document
```bash
cp docs/features/TEMPLATE.md docs/features/my-feature.md
```

Fill out all sections, especially:
- Clear goal and motivation
- Step-by-step implementation plan
- Testing strategy

### 2. Start Development Session
When ready to implement, tell the agent:
> "Let's implement the [feature name] from docs/features/my-feature.md"

The agent will:
- Read the feature document
- Create session memory to track progress
- Follow the implementation plan
- Run `make all` after each significant change

### 3. During Development
The agent maintains context using:
- **Feature doc** - the overall plan
- **Session memory** - current progress, decisions made
- **Todo list** - granular task tracking

### 4. After Completion
- [ ] Update feature status to "Complete"
- [ ] Add feature to README.md
- [ ] Commit both code and feature doc
- [ ] Move to `/memories/repo/planned-features.md` backlog if not fully done

## Quick Planning (Simple Features)

For simple features, just add to `/memories/repo/planned-features.md`:
```markdown
### Add Curved Wall Support
**Goal:** Allow walls to have curved segments
**Complexity:** Medium
**Steps:**
1. [ ] Add arc parameters to Wall class
2. [ ] Update rendering logic
3. [ ] Add example to templates
```

Then tell the agent:
> "Let's work on the curved wall feature from planned-features"

## Active Feature Documents

Current feature plans in this folder:

### Completed
- [species-rendering-feature.md](species-rendering-feature.md) - Species and bloom season display on vegetation
- [landscaping-elements.md](landscaping-elements.md) - Comprehensive landscaping elements
- [vertical-positioning-feature.md](vertical-positioning-feature.md) - Vertical positioning (v_anchor and height) for 2D rendering order and future 3D support

### In Planning
- [common-properties-refactor.md](common-properties-refactor.md) - Refactor Element hierarchy to consolidate common properties (color, length, thickness, diameter)
- [3d-mtl-generation.md](3d-mtl-generation.md) - 3D model generation in OBJ/MTL format with textures

## When to Use Each Approach

| Approach | When to Use |
|----------|-------------|
| **Repository Memory** | Quick ideas, simple features, backlog |
| **Feature Document** | Complex features, need detailed design, multi-day work |
| **Session Memory** | Active development (agent creates automatically) |
| **Todo List** | Active task tracking (agent creates automatically) |

## Tips for Working with Agents

1. **Be Specific**: "Implement Phase 1 from docs/features/my-feature.md"
2. **Reference Sections**: "Start with the 'Foundation' phase"
3. **Checkpoint Often**: "Let's verify this phase before moving on"
4. **Update Plans**: "Update the feature doc with what we learned"
