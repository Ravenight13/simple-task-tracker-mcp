# Migration Guide: workflow-mcp to task-mcp

## Introduction

This comprehensive guide assists teams migrating from **workflow-mcp** (the legacy hierarchical task system) to **task-mcp** (the modern flexible task tracking system). While workflow-mcp provided a rigid 5-level hierarchy with custom entity types and built-in deployment tracking, task-mcp offers a more flexible and extensible approach using generic metadata, entity linking, and natural task decomposition.

### Why Migrate to task-mcp?

1. **Flexibility Over Rigidity**: Natural task hierarchies instead of forced 5-level structure
2. **Generic Over Specific**: Extensible metadata system instead of hard-coded schemas
3. **Relationships Over Embedding**: Entity linking instead of embedded vendor tracking
4. **Simple Over Complex**: Focused tools that compose well instead of monolithic features

### Document Structure

This guide covers:
- Architecture comparison and mapping strategies
- Vendor entity tracking with complete examples
- Deployment history alternatives
- Work item hierarchy patterns
- Test metrics and phase tracking solutions
- Step-by-step conversion process
- Best practices and FAQs

## Architecture Comparison

### High-Level Differences

| Feature | workflow-mcp | task-mcp |
|---------|--------------|----------|
| **Hierarchy** | Fixed 5-level (project→session→task→research→subtask) | Flexible parent_task_id relationships |
| **Entity Types** | Custom schemas per type | Generic entity_type with JSON metadata |
| **Vendor Tracking** | Built-in vendor_entity type | entity_type="other" with metadata |
| **Deployments** | record_deployment() function | Tasks or entities with metadata |
| **Test Metrics** | METRIC_SCHEMA validation | Flexible metadata fields |
| **Phase Tracking** | vendor_phase field | Tags + metadata combination |
| **Dependencies** | Implicit through hierarchy | Explicit depends_on field |
| **File References** | Embedded in task | Both file_references field and entity linking |

### Key Architectural Shifts

**workflow-mcp** enforced structure through database schema:
- Fixed hierarchy levels with specific IDs (project_id, session_id, etc.)
- Custom entity types with predefined fields
- Built-in deployment and metrics tables
- Rigid phase transitions

**task-mcp** enables flexibility through composition:
- Single parent_task_id for any depth hierarchy
- Generic entities with JSON metadata
- Tasks and entities can represent anything
- Tags and metadata for categorization

## Vendor Entity Tracking

### Problem Statement
workflow-mcp had custom `vendor_entity` type with fields like `vendor_code`, `vendor_name`, `phase`, `formats`, etc. How do we represent vendors in task-mcp without losing functionality?

### Solution: Generic Entities with Metadata

**Reasoning**: Instead of hard-coding vendor-specific fields, use the flexible entity system with entity_type="other" and structured JSON metadata. This approach:
- Allows vendor-specific fields without schema changes
- Enables different metadata for different vendor types
- Supports evolution of vendor data over time
- Maintains queryability through tags and search

### Complete Working Examples

#### Creating a Vendor Entity

```python
# workflow-mcp approach (OLD)
vendor_id = create_vendor_entity(
    vendor_code="ABC-INS",
    vendor_name="ABC Insurance",
    phase="active",
    formats=["xlsx", "pdf"],
    brands=["Brand A", "Brand B"],
    contact_info={"email": "vendor@abc.com"}
)

# task-mcp approach (NEW)
vendor = create_entity(
    entity_type="other",  # Generic type for domain entities
    name="ABC Insurance",  # Human-readable name
    identifier="ABC-INS",  # Unique vendor code
    description="Primary insurance data vendor for northeast region",
    metadata={
        "vendor_code": "ABC-INS",  # Preserve original code
        "phase": "active",         # Vendor lifecycle phase
        "formats": ["xlsx", "pdf"], # Data formats they provide
        "brands": ["Brand A", "Brand B"],  # Associated brands
        "contact": {
            "email": "vendor@abc.com",
            "phone": "+1-555-0123",
            "account_manager": "John Smith"
        },
        "contract": {
            "start_date": "2024-01-01",
            "renewal_date": "2025-01-01",
            "monthly_cost": 5000
        }
    },
    tags="vendor insurance active northeast"  # Searchable tags
)
```

**Reasoning for this approach**:
1. **entity_type="other"**: Distinguishes from file entities while remaining generic
2. **identifier field**: Provides unique, searchable vendor code
3. **Rich metadata**: Stores all vendor-specific data without schema constraints
4. **Normalized tags**: Enable fast filtering and discovery
5. **Description field**: Human context for vendor purpose

#### Updating Vendor Information

```python
# Update vendor phase and add new metadata
update_entity(
    entity_id=vendor["id"],
    metadata={
        "vendor_code": "ABC-INS",
        "phase": "testing",  # Changed from "active"
        "formats": ["xlsx", "pdf", "json"],  # Added JSON format
        "brands": ["Brand A", "Brand B", "Brand C"],  # Added Brand C
        "contact": {
            "email": "vendor@abc.com",
            "phone": "+1-555-0123",
            "account_manager": "Jane Doe"  # New account manager
        },
        "contract": {
            "start_date": "2024-01-01",
            "renewal_date": "2025-01-01",
            "monthly_cost": 5500  # Rate increased
        },
        "testing": {
            "start_date": "2024-11-01",
            "test_environment": "staging",
            "assigned_qa": "QA Team Alpha"
        }
    },
    tags="vendor insurance testing northeast"  # Updated tags
)
```

#### Querying Vendors

```python
# Find all active insurance vendors
active_vendors = list_entities(
    entity_type="other",
    tags="vendor insurance active"
)

# Search for specific vendor by code
abc_vendor = search_entities(
    search_term="ABC-INS",
    entity_type="other"
)

# Get all vendors in testing phase
testing_vendors = list_entities(
    entity_type="other",
    tags="vendor testing"
)

# Parse metadata for detailed filtering
for vendor in active_vendors:
    metadata = json.loads(vendor["metadata"])
    if "xlsx" in metadata.get("formats", []):
        print(f"{vendor['name']} supports Excel format")
```

#### Linking Vendors to Tasks

```python
# Create integration task
task = create_task(
    title="Integrate ABC Insurance data pipeline",
    description="Set up ETL pipeline for ABC Insurance vendor data",
    priority="high",
    tags="integration vendor pipeline"
)

# Link vendor to task
link_entity_to_task(
    task_id=task["id"],
    entity_id=vendor["id"]
)

# Query all tasks for a vendor
vendor_tasks = get_entity_tasks(
    entity_id=vendor["id"],
    status="in_progress"  # Optional: filter by status
)

# Get all vendors for a task
task_vendors = get_task_entities(
    task_id=task["id"]
)
```

**Reasoning for entity linking**:
- Maintains referential integrity between tasks and vendors
- Enables bidirectional queries (tasks→vendors, vendors→tasks)
- Tracks which conversation created each link
- Soft delete preserves history

## Deployment History Tracking

### Problem Statement
workflow-mcp had `record_deployment()` with version, commit_sha, environment fields. How do we track deployments without a dedicated system?

### Solution: Two Approaches

#### Approach 1: Deployments as Entities (Recommended for Most Cases)

```python
# Create deployment entity
deployment = create_entity(
    entity_type="other",
    name="v2.3.4 Production Deployment",
    identifier="deploy-2024-11-15-prod-v2.3.4",
    description="Quarterly feature release with vendor integration improvements",
    metadata={
        "type": "deployment",
        "version": "2.3.4",
        "commit_sha": "abc123def456",
        "environment": "production",
        "timestamp": "2024-11-15T14:30:00Z",
        "deployed_by": "CI/CD Pipeline",
        "features": [
            "ABC Insurance integration",
            "Performance improvements",
            "Bug fixes for data validation"
        ],
        "rollback_sha": "789ghi012jkl",  # For emergency rollback
        "metrics": {
            "deployment_time": 324,  # seconds
            "tests_passed": 1248,
            "tests_failed": 0,
            "coverage": 94.2
        }
    },
    tags="deployment production v2.3.4 q4-2024"
)

# Link deployment to related tasks
link_entity_to_task(task_id=integration_task_id, entity_id=deployment["id"])
link_entity_to_task(task_id=testing_task_id, entity_id=deployment["id"])

# Query deployment history
recent_deployments = list_entities(
    entity_type="other",
    tags="deployment production"
)

# Find specific deployment
deployment = search_entities(
    search_term="v2.3.4",
    entity_type="other"
)
```

**Reasoning for entities approach**:
- Deployments are long-lived records that multiple tasks reference
- Rich metadata captures all deployment details
- Can link to multiple tasks that went into the deployment
- Easy to query deployment history

#### Approach 2: Deployments as Tasks (Better for Deployment Workflows)

```python
# Create deployment task with subtasks
deployment_task = create_task(
    title="Deploy v2.3.4 to Production",
    description="Quarterly release deployment with vendor integrations",
    status="in_progress",
    priority="high",
    tags="deployment production release",
    file_references=["/deployment/configs/v2.3.4.yaml"]
)

# Create deployment subtasks
pre_deploy = create_task(
    title="Run pre-deployment checks",
    parent_task_id=deployment_task["id"],
    status="done"
)

deploy = create_task(
    title="Execute deployment",
    parent_task_id=deployment_task["id"],
    depends_on=[pre_deploy["id"]],
    status="in_progress"
)

# Store deployment metadata in task (alternative approach)
update_task(
    task_id=deployment_task["id"],
    description=json.dumps({
        "original_description": "Quarterly release deployment",
        "deployment_metadata": {
            "version": "2.3.4",
            "commit_sha": "abc123def456",
            "environment": "production",
            "timestamp": "2024-11-15T14:30:00Z"
        }
    }),
    status="done"
)
```

**Reasoning for tasks approach**:
- Better when deployment is an active workflow with steps
- Natural hierarchy for deployment stages
- Status tracking for in-progress deployments
- Dependencies between deployment steps

## Work Item Hierarchy

### Problem Statement
workflow-mcp enforced: project → session → task → research → subtask. How do we represent complex hierarchies without rigid levels?

### Solution: Flexible Parent-Child with Tags

```python
# workflow-mcp approach (OLD - Rigid)
project_id = create_project("Vendor Integration")
session_id = create_session(project_id, "Sprint 23")
task_id = create_task(session_id, "ABC Insurance Pipeline")
research_id = create_research(task_id, "API Analysis")
subtask_id = create_subtask(research_id, "Test endpoints")

# task-mcp approach (NEW - Flexible)
# Natural hierarchy based on actual work decomposition

# Top-level epic/project
epic = create_task(
    title="Vendor Integration Platform",
    description="Complete vendor data integration system",
    priority="high",
    tags="epic project vendor-integration q4-2024"
)

# Feature-level task
feature = create_task(
    title="ABC Insurance Integration",
    parent_task_id=epic["id"],
    priority="high",
    tags="feature sprint-23 vendor integration"
)

# Implementation tasks
backend_task = create_task(
    title="Implement ABC Insurance API client",
    parent_task_id=feature["id"],
    tags="implementation backend api"
)

# Research/investigation task
research_task = create_task(
    title="Analyze ABC Insurance data format variations",
    parent_task_id=feature["id"],
    status="done",
    tags="research analysis data-format",
    description="Research findings: Three format versions detected..."
)

# Subtasks at any level as needed
validation_subtask = create_task(
    title="Add format version detection",
    parent_task_id=backend_task["id"],
    depends_on=[research_task["id"]],  # Depends on research completion
    tags="subtask validation"
)
```

**Reasoning for flexible hierarchy**:
1. **Natural decomposition**: Work breaks down differently for different projects
2. **No artificial constraints**: Don't force 5 levels when 3 or 7 make more sense
3. **Tags for categorization**: Use tags like "epic", "feature", "research" for work types
4. **Dependencies across levels**: Any task can depend on any other task

### Mapping Old Concepts

| workflow-mcp Concept | task-mcp Approach | Reasoning |
|---------------------|-------------------|-----------|
| **Project** | Top-level task with tag="project" or "epic" | Projects are just large tasks |
| **Session** | Task with tag="sprint" or "session" | Sessions are time-boxed task groups |
| **Task** | Regular task at any level | No special meaning needed |
| **Research** | Task with tag="research" or "investigation" | Research is a type of work |
| **Subtask** | Child task via parent_task_id | Natural parent-child relationship |

### Complex Hierarchy Example

```python
# Multi-level project structure
platform = create_task(
    title="Multi-Vendor Integration Platform",
    tags="platform epic 2024"
)

# Quarterly objective level
q4_objective = create_task(
    title="Q4: Onboard 5 Insurance Vendors",
    parent_task_id=platform["id"],
    tags="objective quarterly q4-2024"
)

# Sprint level
sprint_23 = create_task(
    title="Sprint 23: ABC and XYZ Insurance",
    parent_task_id=q4_objective["id"],
    tags="sprint sprint-23"
)

# Feature level
abc_feature = create_task(
    title="ABC Insurance Integration",
    parent_task_id=sprint_23["id"],
    tags="feature vendor integration"
)

# Work items level
tasks = []
for work_item in ["API Client", "Data Validation", "Testing", "Documentation"]:
    task = create_task(
        title=f"ABC Insurance: {work_item}",
        parent_task_id=abc_feature["id"],
        tags=f"task {work_item.lower().replace(' ', '-')}"
    )
    tasks.append(task)

# Deep subtask nesting where needed
test_cases = create_task(
    title="Write integration test cases",
    parent_task_id=tasks[2]["id"],  # Under Testing
    tags="subtask testing"
)

# Cross-hierarchy dependency
doc_task = create_task(
    title="Update integration guide",
    parent_task_id=tasks[3]["id"],  # Under Documentation
    depends_on=[tasks[0]["id"], tasks[1]["id"]],  # Depends on API and Validation
    tags="documentation guide"
)

# Query the entire tree
full_tree = get_task_tree(task_id=platform["id"])
```

## Test Metrics & Status Tracking

### Problem Statement
workflow-mcp had METRIC_SCHEMA with test_coverage, last_test_run, test_status fields. How do we track testing metrics flexibly?

### Solution: Metadata Fields in Tasks and Entities

#### Task-Level Test Metrics

```python
# Create task with embedded test metrics
task = create_task(
    title="Implement vendor data validation",
    description="Add comprehensive validation for vendor data formats",
    tags="implementation validation testing"
)

# Update task with test results
update_task(
    task_id=task["id"],
    description=json.dumps({
        "description": "Add comprehensive validation for vendor data formats",
        "test_metrics": {
            "last_run": "2024-11-15T10:30:00Z",
            "test_status": "passing",
            "coverage": 89.5,
            "tests": {
                "unit": {"passed": 45, "failed": 0, "skipped": 2},
                "integration": {"passed": 12, "failed": 0, "skipped": 0},
                "e2e": {"passed": 3, "failed": 0, "skipped": 1}
            },
            "performance": {
                "avg_response_time": 234,  # ms
                "p95_response_time": 567,
                "throughput": 1000  # requests/sec
            }
        }
    }),
    status="done"
)
```

#### Vendor-Level Test Status

```python
# Track vendor testing status in entity metadata
vendor = create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    metadata={
        "vendor_code": "ABC-INS",
        "phase": "testing",
        "testing": {
            "status": "in_progress",
            "environment": "staging",
            "start_date": "2024-11-01",
            "test_results": {
                "data_format": "passed",
                "api_integration": "passed",
                "data_validation": "in_progress",
                "performance": "pending",
                "security": "pending"
            },
            "issues": [
                {
                    "id": "TEST-001",
                    "severity": "medium",
                    "description": "Date format inconsistency",
                    "status": "resolved"
                }
            ],
            "coverage": {
                "unit": 92.3,
                "integration": 78.5,
                "e2e": 45.0
            },
            "last_run": "2024-11-15T14:00:00Z",
            "next_milestone": "2024-11-20"
        }
    },
    tags="vendor insurance testing staging"
)
```

**Reasoning for metadata approach**:
1. **Flexibility**: Different projects need different metrics
2. **Evolution**: Metrics can evolve without schema changes
3. **Context**: Metrics stay with the relevant task/entity
4. **Querying**: Can still search and filter using tags

#### Creating Test Report Entities

```python
# Create test report as entity for historical tracking
test_report = create_entity(
    entity_type="other",
    name="ABC Insurance Test Report - 2024-11-15",
    identifier="test-report-abc-ins-2024-11-15",
    description="Comprehensive test results for ABC Insurance integration",
    metadata={
        "type": "test_report",
        "vendor": "ABC-INS",
        "date": "2024-11-15",
        "summary": {
            "total_tests": 60,
            "passed": 57,
            "failed": 2,
            "skipped": 1,
            "coverage": 88.7,
            "duration": 1847  # seconds
        },
        "details": {
            "unit_tests": {...},
            "integration_tests": {...},
            "performance_tests": {...}
        },
        "recommendations": [
            "Increase E2E test coverage",
            "Add edge case testing for date formats"
        ]
    },
    tags="test-report vendor abc-insurance november-2024"
)

# Link test report to vendor and tasks
link_entity_to_task(task_id=test_task["id"], entity_id=test_report["id"])
```

## Phase Tracking

### Problem Statement
workflow-mcp had vendor_phase field for lifecycle tracking. How do we track phases at multiple levels?

### Solution: Multi-Level Phase Strategy

#### Entity-Level Phase (Vendor Lifecycle)

```python
# Vendor phases tracked in metadata
vendor = create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    metadata={
        "vendor_code": "ABC-INS",
        "lifecycle": {
            "current_phase": "testing",
            "phase_history": [
                {"phase": "discovery", "start": "2024-09-01", "end": "2024-09-15"},
                {"phase": "evaluation", "start": "2024-09-15", "end": "2024-10-01"},
                {"phase": "contracting", "start": "2024-10-01", "end": "2024-10-15"},
                {"phase": "onboarding", "start": "2024-10-15", "end": "2024-11-01"},
                {"phase": "testing", "start": "2024-11-01", "end": null}
            ],
            "next_phase": "production",
            "phase_gate_criteria": {
                "testing_complete": false,
                "security_review": true,
                "contract_signed": true,
                "training_complete": false
            }
        }
    },
    tags="vendor insurance testing phase-testing"
)
```

#### Task-Level Phase (Work Status)

```python
# Task lifecycle is the status field
task = create_task(
    title="ABC Insurance Integration",
    status="in_progress",  # This IS the task phase
    tags="integration vendor"
)

# For more complex task phases, use metadata
complex_task = create_task(
    title="Multi-Phase Vendor Rollout",
    description=json.dumps({
        "description": "Complete vendor rollout process",
        "phases": {
            "current": "development",
            "completed": ["planning", "design"],
            "remaining": ["testing", "deployment", "monitoring"],
            "phase_details": {
                "development": {
                    "start": "2024-11-01",
                    "progress": 75,
                    "blockers": []
                }
            }
        }
    }),
    tags="rollout vendor multi-phase"
)
```

**Reasoning for dual approach**:
- **Vendor lifecycle** ≠ **Task status**: Different concerns
- Vendor can be in "testing" phase while tasks are "done"
- Enables tracking both business phases and work progress
- Flexibility for different phase models per domain

#### Query Patterns for Phases

```python
# Find all vendors in testing phase
testing_vendors = list_entities(
    entity_type="other",
    tags="vendor phase-testing"
)

# Find all tasks for vendors in testing
for vendor in testing_vendors:
    tasks = get_entity_tasks(
        entity_id=vendor["id"],
        status="in_progress"
    )
    print(f"{vendor['name']}: {len(tasks)} active tasks")

# Phase transition tracking
def transition_vendor_phase(entity_id: int, new_phase: str):
    """Transition vendor to new phase with history tracking."""
    vendor = get_entity(entity_id=entity_id)
    metadata = json.loads(vendor["metadata"])

    # Update phase history
    current_phase = metadata["lifecycle"]["current_phase"]
    phase_history = metadata["lifecycle"]["phase_history"]

    # Close current phase
    for phase in phase_history:
        if phase["phase"] == current_phase and phase["end"] is None:
            phase["end"] = datetime.now().isoformat()

    # Start new phase
    phase_history.append({
        "phase": new_phase,
        "start": datetime.now().isoformat(),
        "end": None
    })

    # Update metadata
    metadata["lifecycle"]["current_phase"] = new_phase
    metadata["lifecycle"]["phase_history"] = phase_history

    # Update entity with new tags
    update_entity(
        entity_id=entity_id,
        metadata=metadata,
        tags=f"vendor insurance {new_phase} phase-{new_phase}"
    )

    # Create phase transition task for audit
    create_task(
        title=f"Phase Transition: {vendor['name']} to {new_phase}",
        description=f"Vendor {vendor['identifier']} transitioned from {current_phase} to {new_phase}",
        status="done",
        tags="phase-transition audit vendor"
    )
```

## Conversion Strategy

### Step-by-Step Migration Process

#### Phase 1: Assessment and Planning

```python
# 1. Inventory existing workflow-mcp data
projects = list_workflow_projects()
vendors = list_vendor_entities()
deployments = list_deployments()

# 2. Create migration tracking task
migration_epic = create_task(
    title="workflow-mcp to task-mcp Migration",
    description="Complete system migration with data preservation",
    priority="high",
    tags="migration epic technical-debt"
)

# 3. Create phase tasks
phases = [
    "Assessment and Planning",
    "Vendor Entity Migration",
    "Task Hierarchy Migration",
    "Deployment History Migration",
    "Testing and Validation",
    "Cutover and Cleanup"
]

for phase in phases:
    create_task(
        title=f"Migration Phase: {phase}",
        parent_task_id=migration_epic["id"],
        tags="migration phase"
    )
```

#### Phase 2: Vendor Migration

```python
def migrate_vendor_entity(old_vendor):
    """Convert workflow-mcp vendor to task-mcp entity."""

    # Map old fields to new metadata structure
    metadata = {
        "vendor_code": old_vendor["vendor_code"],
        "phase": old_vendor["phase"],
        "formats": old_vendor["formats"],
        "brands": old_vendor.get("brands", []),
        "legacy_id": old_vendor["id"],  # Preserve old ID for reference
        "migrated_from": "workflow-mcp",
        "migration_date": datetime.now().isoformat()
    }

    # Add any custom fields from old system
    for field in ["contact_info", "contract_details", "notes"]:
        if field in old_vendor:
            metadata[field] = old_vendor[field]

    # Create new entity
    new_entity = create_entity(
        entity_type="other",
        name=old_vendor["vendor_name"],
        identifier=old_vendor["vendor_code"],
        description=old_vendor.get("description", ""),
        metadata=metadata,
        tags=f"vendor migrated {old_vendor['phase']} {' '.join(old_vendor.get('tags', []))}"
    )

    return new_entity

# Batch migrate all vendors
vendor_mapping = {}  # Old ID -> New ID
for old_vendor in vendors:
    new_entity = migrate_vendor_entity(old_vendor)
    vendor_mapping[old_vendor["id"]] = new_entity["id"]
    print(f"Migrated vendor: {old_vendor['vendor_name']} -> Entity {new_entity['id']}")
```

#### Phase 3: Task Hierarchy Migration

```python
def migrate_task_hierarchy(project, session_mapping=None):
    """Convert 5-level hierarchy to flexible parent-child."""

    if session_mapping is None:
        session_mapping = {}

    # Create project as top-level task
    project_task = create_task(
        title=project["name"],
        description=project.get("description", ""),
        tags=f"project migrated {project.get('year', '')}"
    )

    # Migrate sessions under project
    for session in project["sessions"]:
        session_task = create_task(
            title=session["name"],
            parent_task_id=project_task["id"],
            tags="session sprint migrated"
        )
        session_mapping[session["id"]] = session_task["id"]

        # Migrate tasks under session
        for task in session["tasks"]:
            task_obj = create_task(
                title=task["title"],
                parent_task_id=session_task["id"],
                description=task.get("description", ""),
                status=map_old_status(task["status"]),
                priority=task.get("priority", "medium"),
                tags="task migrated"
            )

            # Migrate research items as child tasks
            for research in task.get("research_items", []):
                research_task = create_task(
                    title=f"Research: {research['title']}",
                    parent_task_id=task_obj["id"],
                    description=research.get("findings", ""),
                    status="done" if research.get("completed") else "todo",
                    tags="research migrated"
                )

                # Migrate subtasks
                for subtask in research.get("subtasks", []):
                    create_task(
                        title=subtask["title"],
                        parent_task_id=research_task["id"],
                        status=map_old_status(subtask["status"]),
                        tags="subtask migrated"
                    )

    return project_task

def map_old_status(old_status):
    """Map workflow-mcp status to task-mcp status."""
    mapping = {
        "pending": "todo",
        "active": "in_progress",
        "blocked": "blocked",
        "complete": "done",
        "abandoned": "cancelled"
    }
    return mapping.get(old_status, "todo")
```

### Entity System Usage Patterns

```python
# Pattern 1: Domain objects as entities
customer = create_entity(
    entity_type="other",
    name="Acme Corp",
    identifier="CUST-001",
    metadata={"type": "customer", "tier": "enterprise"},
    tags="customer enterprise active"
)

# Pattern 2: Configuration as entities
config = create_entity(
    entity_type="other",
    name="Production API Config",
    identifier="config-prod-api",
    metadata={"endpoints": {...}, "auth": {...}},
    tags="configuration production api"
)

# Pattern 3: Files with rich metadata
source_file = create_entity(
    entity_type="file",
    name="Vendor Integration Module",
    identifier="/src/integrations/vendor.py",
    metadata={"language": "python", "loc": 1500, "complexity": 12.5},
    tags="source-code python integration"
)
```

### Metadata Design Patterns

```python
# Pattern 1: Flat metadata for simple cases
simple_metadata = {
    "version": "1.2.3",
    "author": "john.doe",
    "reviewed": true
}

# Pattern 2: Nested metadata for complex domains
complex_metadata = {
    "vendor": {
        "code": "ABC-INS",
        "tier": "gold"
    },
    "technical": {
        "api_version": "2.0",
        "protocols": ["REST", "GraphQL"],
        "rate_limits": {
            "requests_per_minute": 100,
            "burst_limit": 500
        }
    },
    "business": {
        "contract_value": 50000,
        "renewal_date": "2025-01-01"
    }
}

# Pattern 3: Array metadata for collections
collection_metadata = {
    "test_runs": [
        {"date": "2024-11-01", "passed": 45, "failed": 2},
        {"date": "2024-11-08", "passed": 47, "failed": 0}
    ]
}
```

## Best Practices

### When to Use Entities vs Tasks

**Use Entities When:**
- Representing persistent domain objects (vendors, customers, configs)
- Tracking non-actionable items (files, reports, deployments)
- Need many-to-many relationships with tasks
- Data outlives any specific task

**Use Tasks When:**
- Representing work to be done
- Need status tracking and workflow
- Building hierarchical work breakdown
- Managing dependencies between work items

### Tag Naming Conventions

```python
# Recommended tag patterns
tags = [
    # Work type tags
    "epic", "feature", "task", "subtask", "bug", "research",

    # Time-based tags
    "q4-2024", "sprint-23", "november-2024",

    # Domain tags
    "vendor", "customer", "integration", "api", "database",

    # Status/phase tags
    "active", "testing", "production", "archived",

    # Priority tags (redundant with field but useful for filtering)
    "urgent", "high-priority", "backlog",

    # Team/ownership tags
    "backend", "frontend", "qa", "devops"
]

# Tag composition
task_tags = "feature vendor integration sprint-23 backend high-priority"
entity_tags = "vendor insurance active production q4-2024"
```

### Dependency Management

```python
# Best Practice: Explicit dependencies over implicit hierarchy
# Bad: Assume subtasks must complete before parent
# Good: Explicitly declare dependencies

feature = create_task(title="Payment Integration")
api_task = create_task(
    title="Build payment API",
    parent_task_id=feature["id"]
)
ui_task = create_task(
    title="Build payment UI",
    parent_task_id=feature["id"]
)
integration_test = create_task(
    title="Integration testing",
    parent_task_id=feature["id"],
    depends_on=[api_task["id"], ui_task["id"]]  # Explicit dependencies
)

# Query dependency status
def check_dependencies(task_id):
    """Check if all dependencies are complete."""
    task = get_task(task_id=task_id)
    if not task["depends_on"]:
        return True

    dep_ids = json.loads(task["depends_on"])
    for dep_id in dep_ids:
        dep_task = get_task(task_id=dep_id)
        if dep_task["status"] != "done":
            print(f"Waiting on: {dep_task['title']} (status: {dep_task['status']})")
            return False
    return True
```

### Query Optimization

```python
# Best Practice: Use tags for common queries
# Instead of parsing metadata for every query, use tags

# Slow: Parse metadata to find active vendors
vendors = list_entities(entity_type="other")
active = [v for v in vendors if json.loads(v["metadata"]).get("phase") == "active"]

# Fast: Use tags for common filters
active_vendors = list_entities(
    entity_type="other",
    tags="vendor active"
)

# Best Practice: Create indexes through consistent identifiers
# Use predictable identifier patterns for fast lookups
identifier_patterns = [
    "vendor-{CODE}",           # vendor-ABC-INS
    "config-{ENV}-{SERVICE}",  # config-prod-api
    "deploy-{DATE}-{ENV}-{VERSION}",  # deploy-2024-11-15-prod-v2.3.4
]
```

## FAQ and Troubleshooting

### Common Migration Questions

**Q: Will I lose data during migration?**
A: No. The migration process preserves all data by storing legacy IDs and metadata. Old system remains read-only during migration.

**Q: How do I handle custom entity types from workflow-mcp?**
A: Use entity_type="other" with structured metadata. The metadata field accepts any JSON, accommodating all custom fields.

**Q: What about the 5-level hierarchy enforcement?**
A: task-mcp's flexible hierarchy is strictly more powerful. You can still create 5 levels if needed, but you're not forced to.

**Q: How do I query across the old project/session boundaries?**
A: Use tags and get_task_tree(). Tags like "project-X" and "sprint-23" provide the same grouping without rigid structure.

### Edge Case Handling

```python
# Edge Case 1: Circular dependencies
# Solution: Validation prevents this
try:
    update_task(
        task_id=task_a["id"],
        depends_on=[task_b["id"]]
    )
    update_task(
        task_id=task_b["id"],
        depends_on=[task_a["id"]]  # Would create circle
    )
except ValueError as e:
    print(f"Circular dependency prevented: {e}")

# Edge Case 2: Orphaned entities after task deletion
# Solution: Soft delete preserves relationships
delete_task(task_id=task["id"])  # Soft delete
entities = get_task_entities(task_id=task["id"])  # Still returns linked entities

# Edge Case 3: Large metadata objects
# Solution: Store summary in entity, details in linked file
large_report = create_entity(
    entity_type="file",
    name="Q4 Test Report",
    identifier="/reports/q4-test-report.json",
    metadata={
        "summary": {"total": 1000, "passed": 950},
        "file_size": 1048576,
        "note": "Full details in file"
    }
)
```

### Performance Considerations

```python
# Performance Tip 1: Batch operations
# Instead of many individual creates, batch when possible
vendors_to_create = [...]
created_vendors = []
for vendor_data in vendors_to_create:
    entity = create_entity(**vendor_data)
    created_vendors.append(entity)

# Performance Tip 2: Limit tree depth queries
# get_task_tree() is recursive - use judiciously
tree = get_task_tree(task_id=epic["id"])  # May be large
# Alternative: Query specific levels
children = list_tasks(parent_task_id=epic["id"])  # One level only

# Performance Tip 3: Use search for text queries
# search_tasks() and search_entities() use indexes
results = search_entities(search_term="ABC")  # Fast
# Instead of:
all_entities = list_entities()  # Slow if many entities
filtered = [e for e in all_entities if "ABC" in e["name"]]
```

### Data Migration Tips

```python
# Tip 1: Migrate in phases with validation
def migrate_with_validation(old_data, migration_func):
    """Migrate with checkpoint and rollback capability."""
    migrated = []
    failed = []

    for item in old_data:
        try:
            new_item = migration_func(item)
            migrated.append((item["id"], new_item["id"]))

            # Checkpoint every 100 items
            if len(migrated) % 100 == 0:
                save_checkpoint(migrated)
        except Exception as e:
            failed.append((item["id"], str(e)))
            log_error(f"Failed to migrate {item['id']}: {e}")

    return migrated, failed

# Tip 2: Maintain mapping tables
migration_map = {
    "vendors": {},      # old_id -> new_entity_id
    "tasks": {},        # old_id -> new_task_id
    "deployments": {},  # old_id -> new_entity_id
}

# Tip 3: Add migration metadata to everything
def add_migration_metadata(metadata):
    """Add migration tracking to metadata."""
    metadata["_migration"] = {
        "source": "workflow-mcp",
        "migration_date": datetime.now().isoformat(),
        "migration_version": "1.0.0",
        "migration_tool": "task-mcp-migrator"
    }
    return metadata
```

## Conclusion

The migration from workflow-mcp to task-mcp represents a philosophical shift from rigid structure to flexible composition. While workflow-mcp enforced specific patterns through schema, task-mcp provides building blocks that compose into any pattern your project needs.

### Key Takeaways

1. **Entities are your domain objects**: Vendors, configs, deployments - anything that tasks reference
2. **Metadata replaces custom schemas**: JSON metadata fields provide unlimited flexibility
3. **Tags enable fast filtering**: Use consistent tagging for efficient queries
4. **Hierarchy is natural, not forced**: Build the structure that matches your work
5. **Dependencies are explicit**: Clear relationships instead of implicit assumptions

### Post-Migration Checklist

- [ ] All vendors migrated to entities with proper metadata
- [ ] Task hierarchies converted to parent-child relationships
- [ ] Dependencies explicitly declared via depends_on field
- [ ] Deployment history captured as entities or tasks
- [ ] Test metrics stored in metadata
- [ ] Phase tracking implemented via tags and metadata
- [ ] Legacy IDs preserved in metadata for reference
- [ ] Team trained on new patterns and tools
- [ ] Queries optimized with proper tag usage
- [ ] Backup of old system maintained

### Getting Help

For additional support during migration:
1. Review the task-mcp documentation at `/docs`
2. Check the example code in this guide
3. Test migrations in a development environment first
4. Maintain the old system in read-only mode during transition

The flexibility of task-mcp ensures that all workflow-mcp use cases are supported, often with simpler and more maintainable patterns. Welcome to a more flexible future!