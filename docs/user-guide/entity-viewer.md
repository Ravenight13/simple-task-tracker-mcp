# Entity Viewer User Guide

## Introduction

The Entity Viewer is a powerful interface for browsing, searching, and managing entities in your Task MCP workspace. Entities represent resources like code files, vendors, dependencies, or any other trackable items that you want to associate with your development tasks.

This guide will help you understand how to use the Entity Viewer effectively to organize your project resources and maintain connections between entities and tasks.

## What Are Entities?

Entities in Task MCP are flexible resources that can be linked to tasks. There are two main types:

- **File Entities**: Code files, documentation, configuration files, or any other file-based resources in your project
- **Other Entities**: Vendors, external services, team members, dependencies, or any custom resource type

Each entity can store:
- A descriptive name
- A unique identifier (like a file path or vendor code)
- Rich metadata in JSON format
- Tags for organization
- Links to related tasks

## Navigating to the Entities Tab

1. Open the Task Viewer application in your browser
2. Click the **"Entities"** tab in the navigation bar at the top of the page
3. The entity list will load, displaying all entities in your workspace

![Screenshot: Navigation to Entities Tab](screenshots/entity-navigation.png)

## Understanding the Entity List

### Entity Cards

Each entity is displayed as a card with the following information:

- **Type Badge**: A colored badge indicating the entity type
  - Blue badge for "File" entities
  - Purple badge for "Other" entities
- **Entity Name**: The primary display name in large text
- **Identifier**: The unique identifier (if set), shown in gray below the name
- **Description**: A brief description (if provided), shown in lighter text
- **Linked Tasks Count**: Shows how many tasks are associated with this entity
- **Tags**: Visual tag badges for quick filtering and organization

![Screenshot: Entity Card Layout](screenshots/entity-card.png)

### Statistics Panel

At the top of the entity list, you'll find the Statistics Panel showing:

- **Total Entities**: The total number of entities in your workspace
- **Files**: Count of file-type entities
- **Other**: Count of other-type entities
- **Top Tags**: The most frequently used tags across all entities

This panel helps you understand the composition of your entity collection at a glance.

![Screenshot: Entity Statistics Panel](screenshots/entity-statistics.png)

## Searching for Entities

The search bar at the top of the entity list allows you to quickly find specific entities.

### How to Search

1. Click in the **search box** at the top of the page
2. Type your search term
3. Results update automatically as you type
4. Search looks for matches in:
   - Entity names
   - Identifiers
   - Descriptions

### Search Tips

- **Be specific**: Searching for "auth" will find entities with "authentication", "authorize", etc.
- **Case-insensitive**: Searches work regardless of capitalization
- **Partial matches**: You don't need to type the complete word
- **Clear search**: Click the X button or delete your text to show all entities again

**Example**: If you have vendors named "ABC Insurance", "XYZ Insurance", and "DEF Telecom", searching for "insurance" will show only the first two.

![Screenshot: Search Bar in Action](screenshots/entity-search.png)

## Filtering Entities

### Filter by Type

Use the type dropdown to show only entities of a specific type:

1. Click the **"All Types"** dropdown menu
2. Select:
   - **All Types**: Show all entities (default)
   - **File**: Show only file entities
   - **Other**: Show only other-type entities

The entity count updates to reflect the filtered results.

![Screenshot: Type Filter Dropdown](screenshots/entity-type-filter.png)

### Filter by Tags

Filter entities by clicking on tag badges:

1. **In the Statistics Panel**: Click any tag in the "Top Tags" section
2. **On Entity Cards**: Click any tag badge on an individual entity
3. **Multiple Tags**: Click multiple tags to filter by all selected tags
4. **Clear Filters**: Click an active tag again to deselect it, or click "Clear all filters" link

Active tag filters are highlighted with a darker background color.

**Example**: Filter by the "vendor" tag to see all vendor entities, then add the "insurance" tag to narrow down to insurance vendors only.

![Screenshot: Tag Filtering](screenshots/entity-tag-filters.png)

### Combining Filters

You can combine type and tag filters for precise results:

- Filter by type "Other" + tag "vendor" = Show only vendor entities
- Filter by type "File" + tag "backend" = Show only backend code files

The entity list updates in real-time as you adjust filters.

## Viewing Entity Details

### Opening the Detail Modal

To view complete information about an entity:

1. Click the **"View Details"** button on any entity card
2. A modal window opens showing full entity information

### Detail Modal Contents

The detail modal displays:

**Header Section:**
- Entity name (large heading)
- Type badge (File or Other)
- Unique identifier (if set)

**Description Section:**
- Full entity description (if provided)

**Metadata Section:**
- JSON metadata viewer with syntax highlighting
- **Copy to Clipboard** button for easy copying of metadata
- Formatted for readability with proper indentation

**Tags Section:**
- All tags associated with the entity
- Click tags to filter the entity list (modal closes automatically)

**Linked Tasks Section:**
- Complete list of all tasks associated with this entity
- Each task shows:
  - Status badge (color-coded)
  - Priority indicator
  - Task title
  - Created date
- Click **"View Task"** to navigate to the task in the Tasks tab
- Shows "No linked tasks" message if entity has no associations

![Screenshot: Entity Detail Modal](screenshots/entity-detail-modal.png)

### Metadata Viewer

The metadata viewer provides a formatted view of the entity's JSON metadata:

- **Syntax Highlighting**: Keys and values are color-coded for readability
- **Indentation**: Proper formatting for nested structures
- **Copy Button**: One-click copying to clipboard
- **No Metadata Message**: Shows friendly message if entity has no metadata

**Example Metadata** (for a vendor entity):
```json
{
  "vendor_code": "ABC-INS",
  "phase": "active",
  "formats": ["xlsx", "pdf"],
  "brands": ["Brand A", "Brand B"],
  "contact": {
    "email": "support@abc-insurance.com",
    "phone": "555-0123"
  }
}
```

## Understanding Linked Tasks

The linked tasks feature creates powerful connections between your entities and development work.

### Why Link Tasks to Entities?

- **Track work by resource**: See all tasks related to a specific file or vendor
- **Context switching**: Quickly navigate from entity to related tasks
- **Impact analysis**: Understand what tasks involve a particular resource
- **Vendor management**: Track all development work for external partners

### Viewing Linked Tasks

In the entity detail modal:

1. Scroll to the **"Linked Tasks"** section
2. View the count: "X linked task(s)"
3. Browse the task list showing:
   - Status (todo, in_progress, done, blocked)
   - Priority (low, medium, high)
   - Task title
   - Creation date

### Navigating to Tasks

1. Find the task you want to view in the linked tasks list
2. Click the **"View Task"** button
3. You'll be redirected to the Tasks tab with the task details visible

This creates a seamless workflow between entity management and task tracking.

## Entity Statistics Explained

### Total Entities
Shows the complete count of all entities in your workspace, giving you a sense of your resource inventory.

### Type Breakdown
- **Files**: Count of file entities (code, docs, configs)
- **Other**: Count of non-file entities (vendors, services, people)

Use this to understand the balance of your tracked resources.

### Top Tags
Displays the most commonly used tags across all entities:

- Helps identify main categories in your workspace
- Click any tag to instantly filter entities
- Shows maximum of 10 tags
- Sorted by frequency (most used first)

## Common Use Cases

### Use Case 1: Vendor Tracking Workflow

**Scenario**: You're integrating with multiple insurance vendors and need to track vendor-specific tasks.

**Setup:**
1. Create vendor entities with type "Other"
2. Add metadata: vendor codes, contact info, integration details
3. Tag with: "vendor", "insurance", and phase tags like "active" or "testing"

**Daily Workflow:**
1. Navigate to Entities tab
2. Filter by tag "vendor" to see all vendors
3. Click a vendor to view details
4. Review linked tasks to see integration progress
5. Click "View Task" to work on vendor-specific tasks

**Benefits:**
- Quick vendor overview without searching through tasks
- Easy access to vendor metadata (codes, contacts, formats)
- Track all tasks related to each vendor
- Filter by phase to focus on active vs. testing vendors

**Example Metadata for Vendor:**
```json
{
  "vendor_code": "ABC-INS",
  "phase": "active",
  "formats": ["xlsx", "pdf"],
  "brands": ["Brand A", "Brand B"],
  "contact": {
    "name": "Jane Smith",
    "email": "jane@abc-insurance.com"
  },
  "integration_date": "2025-10-15"
}
```

### Use Case 2: File Tracking Workflow

**Scenario**: You're refactoring authentication code and need to track which files are involved.

**Setup:**
1. Create file entities for each code file
2. Set identifier to file path: `/src/auth/login.py`
3. Add metadata: language, line count, last modified
4. Tag with: "backend", "authentication", "refactor"

**Daily Workflow:**
1. Filter entities by tag "refactor"
2. View file entity details to see metadata
3. Check linked tasks to see what work is planned/done
4. Navigate to tasks to update progress
5. Copy file paths from identifiers when needed

**Benefits:**
- Visual map of refactoring scope
- Track which files have pending tasks
- Easy access to file paths via identifiers
- Group related files with tags

**Example Metadata for File:**
```json
{
  "language": "python",
  "line_count": 250,
  "last_modified": "2025-10-28",
  "test_coverage": "85%",
  "dependencies": ["auth_utils.py", "token_manager.py"]
}
```

### Use Case 3: Dependency Management

**Scenario**: Track external dependencies and related upgrade tasks.

**Setup:**
1. Create entities for each major dependency
2. Type: "Other"
3. Identifier: Package name and version (e.g., "react@18.2.0")
4. Metadata: Version info, security status, upgrade notes
5. Tags: "dependency", "frontend" or "backend", "security"

**Workflow:**
1. Filter by tag "dependency"
2. Review entities for outdated versions in metadata
3. Check linked tasks for planned upgrades
4. Create new tasks and link to dependency entities
5. Update metadata when upgrades complete

### Use Case 4: Documentation Hub

**Scenario**: Track important documentation files and related writing tasks.

**Setup:**
1. Create file entities for each doc file
2. Identifier: File path (e.g., `/docs/user-guide/getting-started.md`)
3. Metadata: Word count, last updated, reviewers
4. Tags: "docs", "user-guide", "api-docs"

**Workflow:**
1. Filter by tag "docs"
2. View entities to see documentation structure
3. Check linked tasks for writing/review tasks
4. Track documentation coverage across project

## Tips and Best Practices

### Organization Tips

1. **Use Consistent Naming**: Establish naming conventions for entities
   - Files: Use descriptive names like "Authentication Controller"
   - Vendors: Use company names like "ABC Insurance"

2. **Leverage Tags**: Create a tagging strategy
   - Function tags: "backend", "frontend", "api"
   - Phase tags: "active", "testing", "deprecated"
   - Category tags: "vendor", "dependency", "docs"

3. **Populate Metadata**: Rich metadata makes entities more useful
   - Add contact information for vendors
   - Include version numbers for dependencies
   - Track file statistics (line count, coverage)

4. **Link Thoughtfully**: Connect entities to relevant tasks
   - Link vendor entities to integration tasks
   - Link file entities to refactoring tasks
   - Review linked tasks periodically

### Search and Filter Tips

1. **Start Broad, Then Narrow**: Begin with type filter, then add tag filters
2. **Use Search for Names**: The search bar is fastest for finding specific entities
3. **Bookmark Common Filters**: Mentally note your most-used tag combinations
4. **Clear Filters Regularly**: Reset view to avoid missing entities

### Maintenance Tips

1. **Regular Reviews**: Periodically review entities to remove obsolete ones
2. **Update Metadata**: Keep metadata current as projects evolve
3. **Clean Up Tags**: Consolidate similar tags to reduce clutter
4. **Archive Old Entities**: Use consistent tagging to mark deprecated entities

## Keyboard Shortcuts

Currently, the Entity Viewer is mouse/touch-driven. Future versions may include:
- `Ctrl/Cmd + F`: Focus search bar
- `Esc`: Close detail modal
- Arrow keys: Navigate entity cards

## Troubleshooting

### "No entities found"

**Cause**: No entities exist in your workspace yet

**Solution**: Create entities using the MCP tools via Claude Code or Claude Desktop

### Entity count seems wrong

**Cause**: Active filters are hiding some entities

**Solution**: Click "Clear all filters" to reset view

### Linked tasks not showing

**Cause**: Tasks may be deleted or links removed

**Solution**: Check task status in Tasks tab, recreate links if needed

### Search not finding entity

**Cause**: Search only looks at name, identifier, and description

**Solution**: Try filtering by tags instead, or check entity details to verify text

## Related Documentation

- **Entity System Overview**: Technical documentation for developers
- **MCP Tools Reference**: Complete list of entity-related MCP tools
- **Task Viewer Guide**: Guide to the Tasks tab and task management

## Next Steps

Now that you understand the Entity Viewer:

1. **Create Your First Entities**: Start with key vendors or important files
2. **Experiment with Filters**: Try different tag and type combinations
3. **Link to Tasks**: Connect existing tasks to relevant entities
4. **Explore Metadata**: Add rich metadata to track detailed information

The Entity Viewer becomes more powerful as you build your entity collection and create meaningful links to your development tasks.
