# Task Viewer Frontend Architecture

**Version:** 1.0
**Date:** November 2, 2025
**Status:** Planning Document
**Stack:** HTML + Tailwind CSS + Alpine.js (zero build process)

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Page Layout & Component Structure](#page-layout--component-structure)
4. [Tailwind CSS Integration](#tailwind-css-integration)
5. [Alpine.js Patterns](#alpinejs-patterns)
6. [UI/UX Components](#uiux-components)
7. [Responsive Design Strategy](#responsive-design-strategy)
8. [Accessibility Considerations](#accessibility-considerations)
9. [Performance Optimization](#performance-optimization)
10. [Future Extensibility](#future-extensibility)

---

## Overview

### Purpose
A lightweight, professional task management viewer for internal use. Displays tasks from task-mcp with filtering, sorting, and detail views.

### Design Goals
- **Clean & Professional:** Internal tool aesthetic, focused on usability
- **Zero Build Complexity:** Pure HTML + CDN resources, no webpack/vite
- **Fast & Responsive:** Instant interactions, <100ms perceived latency
- **Mobile-Friendly:** Works on phones/tablets for on-the-go access
- **Easy to Extend:** Clear patterns for adding features

### Non-Goals
- Not a full CRUD interface (read-only viewer - no task creation/editing)
- Not replacing Claude Desktop task-mcp integration
- Not a public-facing application
- No entity management UI (entities not in v1.0)

---

## Technology Stack

### Core Technologies

**HTML5**
- Semantic markup for accessibility
- Native form elements where possible
- Progressive enhancement mindset

**Tailwind CSS v3.4+ (CDN)**
- Utility-first styling
- Built-in dark mode support
- Responsive breakpoints (sm, md, lg, xl, 2xl)
- JIT-like features via CDN Play

**Alpine.js v3.13+ (CDN)**
- Lightweight reactivity (15KB gzipped)
- Declarative syntax
- No virtual DOM overhead
- Built-in directives for common patterns

### CDN Strategy

**Why CDN vs Local:**
- ✅ Zero build process required
- ✅ Instant updates to latest versions
- ✅ Browser caching across sites
- ✅ Simplified deployment
- ❌ Requires internet connection (acceptable for internal tool)
- ❌ CDN dependency (mitigated by using reliable providers)

**Selected CDNs:**
```html
<!-- Tailwind CSS Play CDN (includes all features) -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Alpine.js from official CDN -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

<!-- Optional: Inter font for professional typography -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Fallback Strategy:**
- Critical CSS inlined in `<head>` for skeleton UI
- Graceful degradation if CDN unavailable (rare for internal tool)

---

## Page Layout & Component Structure

### Single-Page Layout

```
┌─────────────────────────────────────────────┐
│ HEADER (sticky)                             │
│ - Logo/Title                                │
│ - Project Selector (dropdown)               │
│ - User Info (optional)                      │
├─────────────────────────────────────────────┤
│ FILTERS BAR (sticky below header)           │
│ - Status Chips (todo/in_progress/done/all)  │
│ - Priority Filter (dropdown)                │
│ - Search Input (live filter)                │
│ - Sort Options (dropdown)                   │
├─────────────────────────────────────────────┤
│ MAIN CONTENT AREA (scrollable)              │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ TASK CARD 1                             │ │
│ │ - Title, status badge, priority badge   │ │
│ │ - Truncated description                 │ │
│ │ - Metadata (created, tags)              │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ TASK CARD 2                             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ... (scrollable list)                       │
│                                             │
├─────────────────────────────────────────────┤
│ FOOTER (optional)                           │
│ - Task count, last updated                  │
└─────────────────────────────────────────────┘

MODAL OVERLAY (when task clicked)
┌─────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────┐ │
│ │ TASK DETAIL MODAL                       │ │
│ │ - Full title                            │ │
│ │ - Full description (markdown rendered?) │ │
│ │ - All metadata                          │ │
│ │ - Subtasks (if any)                     │ │
│ │ - Dependencies (if any)                 │ │
│ │ - File references                       │ │
│ │ - [Close button]                        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Component Hierarchy

```
App (Alpine root)
├── Header
│   ├── ProjectSelector (x-data)
│   └── Logo
├── FiltersBar (x-data)
│   ├── StatusChips (x-for loop)
│   ├── PriorityDropdown (x-show)
│   ├── SearchInput (x-model)
│   └── SortDropdown (x-show)
├── TaskList (x-data)
│   ├── LoadingState (x-show)
│   ├── ErrorState (x-show)
│   ├── EmptyState (x-show)
│   └── TaskCards (x-for loop)
│       └── TaskCard (x-on:click)
└── TaskDetailModal (x-data, x-show)
    ├── Backdrop (x-on:click to close)
    └── ModalContent
        ├── TaskHeader
        ├── TaskBody
        └── TaskMetadata
```

---

## Tailwind CSS Integration

### Custom Configuration

Tailwind Play CDN allows inline configuration:

```html
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          // Custom brand colors if needed
          primary: {
            50: '#eff6ff',
            100: '#dbeafe',
            500: '#3b82f6',
            600: '#2563eb',
            700: '#1d4ed8',
          },
          // Status colors
          status: {
            todo: '#94a3b8',      // slate-400
            in_progress: '#3b82f6', // blue-500
            done: '#10b981',       // green-500
            blocked: '#ef4444',    // red-500
          },
          // Priority colors
          priority: {
            low: '#94a3b8',       // slate-400
            medium: '#f59e0b',    // amber-500
            high: '#ef4444',      // red-500
          }
        },
        fontFamily: {
          sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        },
      }
    },
    darkMode: 'class', // Enable class-based dark mode
  }
</script>
```

### Utility Patterns

**Card Styling:**
```html
<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-4 border border-gray-200 dark:border-gray-700">
  <!-- Card content -->
</div>
```

**Badge Styling:**
```html
<!-- Status badge -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
  In Progress
</span>

<!-- Priority badge -->
<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
  High
</span>
```

**Button Styling:**
```html
<!-- Primary button -->
<button class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors">
  Action
</button>

<!-- Secondary button -->
<button class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600">
  Cancel
</button>
```

### Dark Mode Strategy

**Default:** Light mode
**Toggle:** Optional dark mode toggle in header
**Persistence:** Use `localStorage` to remember preference

```html
<script>
  // Initialize dark mode from localStorage
  if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
</script>
```

---

## Alpine.js Patterns

### Core State Management

**Main App State:**
```javascript
<div x-data="taskApp()" x-init="init()">
  <!-- App content -->
</div>

<script>
  function taskApp() {
    return {
      // State
      projects: [],
      currentProject: null,
      tasks: [],
      filteredTasks: [],
      selectedTask: null,
      totalTasks: 0,
      apiKey: '', // TODO: Load from config/localStorage

      // Filters
      statusFilter: 'all', // 'all', 'todo', 'in_progress', 'done', 'blocked'
      priorityFilter: 'all', // 'all', 'low', 'medium', 'high'
      searchQuery: '',
      sortBy: 'created_desc', // 'created_desc', 'priority_desc', 'title_asc'

      // UI State
      loading: false,
      error: null,
      showModal: false,

      // Lifecycle
      async init() {
        await this.loadProjects();
        if (this.projects.length > 0) {
          this.currentProject = this.projects[0];
          await this.loadTasks();
        }
      },

      // API Methods
      async loadProjects() {
        this.loading = true;
        this.error = null;
        try {
          const response = await fetch('http://localhost:8001/api/projects', {
            headers: { 'X-API-Key': this.apiKey }
          });
          if (!response.ok) throw new Error('Failed to load projects');
          const data = await response.json();
          this.projects = data.projects; // Extract projects array
        } catch (err) {
          this.error = err.message;
        } finally {
          this.loading = false;
        }
      },

      async loadTasks() {
        if (!this.currentProject) return;

        this.loading = true;
        this.error = null;
        try {
          const params = new URLSearchParams({
            project_id: this.currentProject.id, // Use hash ID, not workspace_path
          });

          const response = await fetch(`http://localhost:8001/api/tasks?${params}`, {
            headers: { 'X-API-Key': this.apiKey }
          });
          if (!response.ok) throw new Error('Failed to load tasks');
          const data = await response.json();
          this.tasks = data.tasks; // Extract tasks array from response
          this.totalTasks = data.total; // Store total for pagination
          this.applyFilters();
        } catch (err) {
          this.error = err.message;
        } finally {
          this.loading = false;
        }
      },

      async selectProject(project) {
        this.currentProject = project;
        await this.loadTasks();
      },

      // Filter Methods
      applyFilters() {
        let filtered = [...this.tasks];

        // Status filter
        if (this.statusFilter !== 'all') {
          filtered = filtered.filter(t => t.status === this.statusFilter);
        }

        // Priority filter
        if (this.priorityFilter !== 'all') {
          filtered = filtered.filter(t => t.priority === this.priorityFilter);
        }

        // Search filter
        if (this.searchQuery.trim()) {
          const query = this.searchQuery.toLowerCase();
          filtered = filtered.filter(t =>
            t.title.toLowerCase().includes(query) ||
            (t.description && t.description.toLowerCase().includes(query)) ||
            (t.tags && t.tags.toLowerCase().includes(query))
          );
        }

        // Sort
        filtered.sort((a, b) => {
          switch (this.sortBy) {
            case 'created_desc':
              return new Date(b.created_at) - new Date(a.created_at);
            case 'created_asc':
              return new Date(a.created_at) - new Date(b.created_at);
            case 'priority_desc':
              const priorityOrder = { high: 3, medium: 2, low: 1 };
              return (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0);
            case 'title_asc':
              return a.title.localeCompare(b.title);
            default:
              return 0;
          }
        });

        this.filteredTasks = filtered;
      },

      // UI Methods
      openTaskDetail(task) {
        this.selectedTask = task;
        this.showModal = true;
      },

      closeModal() {
        this.showModal = false;
        setTimeout(() => {
          this.selectedTask = null;
        }, 300); // Wait for fade-out animation
      },

      // Computed properties (via getters)
      get taskCount() {
        return this.filteredTasks.length;
      },

      get statusCounts() {
        return {
          total: this.tasks.length,
          todo: this.tasks.filter(t => t.status === 'todo').length,
          in_progress: this.tasks.filter(t => t.status === 'in_progress').length,
          done: this.tasks.filter(t => t.status === 'done').length,
          blocked: this.tasks.filter(t => t.status === 'blocked').length,
        };
      }
    }
  }
</script>
```

### Reactive Watchers

```javascript
// Watch filters and re-apply when changed
x-effect="
  statusFilter;
  priorityFilter;
  searchQuery;
  sortBy;
  applyFilters();
"
```

### Template Patterns

**Conditional Rendering:**
```html
<!-- Loading state -->
<div x-show="loading" class="flex justify-center items-center py-12">
  <svg class="animate-spin h-8 w-8 text-blue-600" ...>...</svg>
  <span class="ml-2 text-gray-600">Loading tasks...</span>
</div>

<!-- Error state -->
<div x-show="error && !loading" class="bg-red-50 border border-red-200 rounded-lg p-4">
  <p class="text-red-800" x-text="error"></p>
</div>

<!-- Empty state -->
<div x-show="!loading && !error && filteredTasks.length === 0" class="text-center py-12">
  <p class="text-gray-500 text-lg">No tasks found</p>
  <p class="text-gray-400 text-sm mt-2">Try adjusting your filters</p>
</div>

<!-- Task list -->
<div x-show="!loading && !error && filteredTasks.length > 0">
  <template x-for="task in filteredTasks" :key="task.id">
    <div @click="openTaskDetail(task)" class="...">
      <!-- Task card content -->
    </div>
  </template>
</div>
```

**List Rendering:**
```html
<template x-for="task in filteredTasks" :key="task.id">
  <div class="task-card" @click="openTaskDetail(task)">
    <div class="flex items-start justify-between">
      <h3 class="font-semibold text-gray-900 dark:text-gray-100" x-text="task.title"></h3>
      <span
        class="ml-2 px-2 py-1 text-xs font-medium rounded-full"
        :class="{
          'bg-slate-100 text-slate-800': task.status === 'todo',
          'bg-blue-100 text-blue-800': task.status === 'in_progress',
          'bg-green-100 text-green-800': task.status === 'done',
          'bg-red-100 text-red-800': task.status === 'blocked'
        }"
        x-text="task.status.replace('_', ' ')"
      ></span>
    </div>

    <p
      class="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2"
      x-text="task.description || 'No description'"
    ></p>

    <div class="mt-3 flex items-center gap-2">
      <span
        class="px-2 py-0.5 text-xs font-medium rounded"
        :class="{
          'bg-gray-100 text-gray-700': task.priority === 'low',
          'bg-amber-100 text-amber-800': task.priority === 'medium',
          'bg-red-100 text-red-800': task.priority === 'high'
        }"
        x-text="task.priority"
      ></span>

      <span class="text-xs text-gray-500" x-text="formatDate(task.created_at)"></span>
    </div>
  </div>
</template>
```

**Modal Pattern:**
```html
<!-- Modal backdrop & container -->
<div
  x-show="showModal"
  x-cloak
  x-transition:enter="transition ease-out duration-300"
  x-transition:enter-start="opacity-0"
  x-transition:enter-end="opacity-100"
  x-transition:leave="transition ease-in duration-200"
  x-transition:leave-start="opacity-100"
  x-transition:leave-end="opacity-0"
  class="fixed inset-0 z-50 overflow-y-auto"
  @click.self="closeModal()"
>
  <!-- Backdrop -->
  <div class="fixed inset-0 bg-black bg-opacity-50"></div>

  <!-- Modal content -->
  <div class="flex min-h-full items-center justify-center p-4">
    <div
      x-show="showModal"
      x-transition:enter="transition ease-out duration-300"
      x-transition:enter-start="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
      x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100"
      x-transition:leave="transition ease-in duration-200"
      x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100"
      x-transition:leave-end="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
      class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6"
      @click.stop
    >
      <!-- Close button -->
      <button
        @click="closeModal()"
        class="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Modal content (if task selected) -->
      <template x-if="selectedTask">
        <div>
          <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100" x-text="selectedTask.title"></h2>

          <div class="mt-4 flex gap-2">
            <span
              class="px-3 py-1 text-sm font-medium rounded-full"
              :class="{
                'bg-slate-100 text-slate-800': selectedTask.status === 'todo',
                'bg-blue-100 text-blue-800': selectedTask.status === 'in_progress',
                'bg-green-100 text-green-800': selectedTask.status === 'done',
                'bg-red-100 text-red-800': selectedTask.status === 'blocked'
              }"
              x-text="selectedTask.status.replace('_', ' ')"
            ></span>

            <span
              class="px-3 py-1 text-sm font-medium rounded"
              :class="{
                'bg-gray-100 text-gray-700': selectedTask.priority === 'low',
                'bg-amber-100 text-amber-800': selectedTask.priority === 'medium',
                'bg-red-100 text-red-800': selectedTask.priority === 'high'
              }"
              x-text="selectedTask.priority"
            ></span>
          </div>

          <div class="mt-6">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Description</h3>
            <p class="mt-2 text-gray-600 dark:text-gray-400 whitespace-pre-wrap" x-text="selectedTask.description || 'No description'"></p>
          </div>

          <!-- Additional metadata sections -->
          <div class="mt-6 grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="font-semibold text-gray-700 dark:text-gray-300">Created:</span>
              <span class="text-gray-600 dark:text-gray-400" x-text="formatDate(selectedTask.created_at)"></span>
            </div>

            <div x-show="selectedTask.tags">
              <span class="font-semibold text-gray-700 dark:text-gray-300">Tags:</span>
              <span class="text-gray-600 dark:text-gray-400" x-text="selectedTask.tags"></span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</div>
```

### Helper Functions

```javascript
// Date formatting
formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
},

// Relative time (optional)
formatRelativeTime(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return this.formatDate(dateString);
}
```

---

## UI/UX Components

### 1. Header Component

**Purpose:** Branding, project selection, optional user info

**Layout:**
```html
<header class="sticky top-0 z-40 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <!-- Left: Logo/Title -->
      <div class="flex items-center">
        <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
          Task Viewer
        </h1>
      </div>

      <!-- Center: Project Selector -->
      <div class="flex-1 max-w-md mx-8" x-data="{ open: false }">
        <div class="relative">
          <button
            @click="open = !open"
            class="w-full px-4 py-2 text-left bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <span x-text="currentProject?.friendly_name || 'Select Project'"></span>
            <svg class="float-right h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>

          <div
            x-show="open"
            @click.away="open = false"
            x-cloak
            x-transition
            class="absolute z-10 mt-2 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-auto"
          >
            <template x-for="project in projects" :key="project.workspace_path">
              <button
                @click="selectProject(project); open = false"
                class="block w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
                :class="{ 'bg-blue-50 dark:bg-blue-900': currentProject?.workspace_path === project.workspace_path }"
              >
                <div class="font-medium" x-text="project.friendly_name"></div>
                <div class="text-xs text-gray-500 dark:text-gray-400" x-text="project.workspace_path"></div>
              </button>
            </template>
          </div>
        </div>
      </div>

      <!-- Right: Dark mode toggle (optional) -->
      <div>
        <button
          @click="toggleDarkMode()"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <!-- Sun/moon icon -->
          </svg>
        </button>
      </div>
    </div>
  </div>
</header>
```

### 2. Filters Bar Component

**Purpose:** Quick filtering and sorting controls

**Layout:**
```html
<div class="sticky top-16 z-30 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
    <!-- Status chips with counts -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Status:</span>

      <template x-for="status in ['all', 'todo', 'in_progress', 'done', 'blocked']" :key="status">
        <button
          @click="statusFilter = status"
          class="px-3 py-1 rounded-full text-sm font-medium transition-colors"
          :class="statusFilter === status
            ? 'bg-blue-600 text-white'
            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'"
          :aria-pressed="statusFilter === status"
        >
          <span x-text="status === 'all' ? 'All' : status.replace('_', ' ')"></span>
          <span
            x-show="status !== 'all'"
            class="ml-1 opacity-75"
            x-text="`(${statusCounts[status] || 0})`"
          ></span>
          <span
            x-show="status === 'all'"
            class="ml-1 opacity-75"
            x-text="`(${statusCounts.total})`"
          ></span>
        </button>
      </template>
    </div>

    <!-- Search and filters row -->
    <div class="flex flex-col sm:flex-row gap-3">
      <!-- Search input -->
      <div class="flex-1">
        <input
          type="text"
          x-model="searchQuery"
          placeholder="Search tasks..."
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Priority filter -->
      <div class="relative" x-data="{ open: false }">
        <button
          @click="open = !open"
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Priority: <span x-text="priorityFilter === 'all' ? 'All' : priorityFilter"></span>
        </button>

        <div
          x-show="open"
          @click.away="open = false"
          x-cloak
          class="absolute right-0 mt-2 w-40 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg"
        >
          <template x-for="priority in ['all', 'low', 'medium', 'high']" :key="priority">
            <button
              @click="priorityFilter = priority; open = false"
              class="block w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100"
            >
              <span x-text="priority === 'all' ? 'All' : priority"></span>
            </button>
          </template>
        </div>
      </div>

      <!-- Sort dropdown -->
      <div class="relative" x-data="{ open: false }">
        <button
          @click="open = !open"
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Sort
        </button>

        <div
          x-show="open"
          @click.away="open = false"
          x-cloak
          class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg"
        >
          <template x-for="option in [
            { value: 'created_desc', label: 'Newest first' },
            { value: 'created_asc', label: 'Oldest first' },
            { value: 'priority_desc', label: 'Priority (high to low)' },
            { value: 'title_asc', label: 'Title (A-Z)' }
          ]" :key="option.value">
            <button
              @click="sortBy = option.value; open = false"
              class="block w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100"
              :class="{ 'bg-blue-50 dark:bg-blue-900': sortBy === option.value }"
            >
              <span x-text="option.label"></span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 3. Task Card Component

**Purpose:** Compact, scannable task summary

**Design Principles:**
- Clear visual hierarchy (title > description > metadata)
- Status and priority immediately visible
- Hover state indicates clickability
- Truncate long descriptions with ellipsis

**Template:**
```html
<div
  @click="openTaskDetail(task)"
  class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 p-4 border border-gray-200 dark:border-gray-700 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600"
>
  <!-- Header: Title + Status Badge -->
  <div class="flex items-start justify-between gap-3">
    <h3 class="flex-1 font-semibold text-gray-900 dark:text-gray-100 leading-snug" x-text="task.title"></h3>

    <span
      class="flex-shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium"
      :class="{
        'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200': task.status === 'todo',
        'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200': task.status === 'in_progress',
        'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': task.status === 'done',
        'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': task.status === 'blocked'
      }"
      x-text="task.status.replace('_', ' ')"
    ></span>
  </div>

  <!-- Description (truncated) -->
  <p
    class="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2"
    x-text="task.description || 'No description provided'"
  ></p>

  <!-- Footer: Priority + Metadata -->
  <div class="mt-3 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <!-- Priority badge -->
      <span
        class="px-2 py-0.5 rounded text-xs font-medium"
        :class="{
          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300': task.priority === 'low',
          'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200': task.priority === 'medium',
          'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': task.priority === 'high'
        }"
        x-text="task.priority"
      ></span>

      <!-- Tags (if present) -->
      <span
        x-show="task.tags"
        class="text-xs text-gray-500 dark:text-gray-400"
        x-text="task.tags"
      ></span>
    </div>

    <!-- Created date -->
    <span class="text-xs text-gray-500 dark:text-gray-400" x-text="formatRelativeTime(task.created_at)"></span>
  </div>
</div>
```

### 4. Loading States

**Skeleton Loading:**
```html
<div class="space-y-4">
  <template x-for="i in 3" :key="i">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700 animate-pulse">
      <div class="flex justify-between">
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
      </div>
      <div class="mt-2 h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
      <div class="mt-1 h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5"></div>
      <div class="mt-3 flex gap-2">
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
      </div>
    </div>
  </template>
</div>
```

**Spinner (for button actions):**
```html
<svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
```

### 5. Error States

**Error Banner:**
```html
<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
  <div class="flex items-start">
    <svg class="h-5 w-5 text-red-400 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
    </svg>
    <div class="ml-3">
      <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading tasks</h3>
      <p class="mt-1 text-sm text-red-700 dark:text-red-300" x-text="error"></p>
      <button
        @click="loadTasks()"
        class="mt-3 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
      >
        Retry
      </button>
    </div>
  </div>
</div>
```

### 6. Empty States

**No Tasks Found:**
```html
<div class="text-center py-12">
  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
  <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No tasks found</h3>
  <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
    <template x-if="searchQuery || statusFilter !== 'all' || priorityFilter !== 'all'">
      <span>Try adjusting your filters</span>
    </template>
    <template x-if="!searchQuery && statusFilter === 'all' && priorityFilter === 'all'">
      <span>This project has no tasks yet</span>
    </template>
  </p>
</div>
```

---

## Responsive Design Strategy

### Breakpoint Strategy

**Tailwind Breakpoints:**
- `sm`: 640px (small tablets, large phones landscape)
- `md`: 768px (tablets)
- `lg`: 1024px (laptops, small desktops)
- `xl`: 1280px (desktops)
- `2xl`: 1536px (large desktops)

**Design Approach:**
- **Mobile-first:** Base styles for mobile, enhance upward
- **Content priority:** Most important content visible on all sizes
- **Touch-friendly:** Min 44px tap targets on mobile
- **Readable:** Max width containers prevent excessive line length

### Mobile Layout (< 640px)

**Header:**
- Stack logo and project selector vertically if needed
- Hide secondary actions in menu

**Filters:**
- Stack search, priority, sort vertically
- Status chips wrap to multiple lines
- Simplify dropdown menus

**Task Cards:**
- Full width, single column
- Larger touch targets
- Truncate text more aggressively

**Modal:**
- Full screen on mobile (or near full with small margin)
- Scroll within modal body

### Tablet Layout (640px - 1024px)

**Header:**
- Horizontal layout with breathing room

**Filters:**
- 2-column layout (search takes full width row 1, filters row 2)

**Task Cards:**
- Single column or 2 columns depending on content density

### Desktop Layout (> 1024px)

**Header:**
- Max width container (7xl = 1280px)
- All elements in single row

**Filters:**
- Single row, all controls visible

**Task Cards:**
- 2-3 column grid depending on screen size
- More metadata visible per card

**Modal:**
- Max width 2xl (672px), centered

### Responsive Utilities

```html
<!-- Responsive grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Task cards -->
</div>

<!-- Hide on mobile, show on desktop -->
<div class="hidden md:block">
  <!-- Desktop-only content -->
</div>

<!-- Show on mobile, hide on desktop -->
<div class="block md:hidden">
  <!-- Mobile-only content -->
</div>

<!-- Responsive padding -->
<div class="px-4 sm:px-6 lg:px-8">
  <!-- Content -->
</div>

<!-- Responsive text size -->
<h1 class="text-xl sm:text-2xl lg:text-3xl">
  <!-- Heading -->
</h1>
```

---

## Accessibility Considerations

### Skip to Main Content

**Add skip link for keyboard users:**
```html
<a
  href="#main-content"
  class="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:bg-blue-600 focus:text-white"
>
  Skip to main content
</a>

<main id="main-content">
  <!-- Task list -->
</main>
```

### Semantic HTML

**Use proper elements:**
```html
<!-- ✅ Good -->
<button @click="openModal()">View Details</button>

<!-- ❌ Bad -->
<div @click="openModal()">View Details</div>
```

**Headings hierarchy:**
```html
<h1>Task Viewer</h1>
  <h2>Project Name</h2>
    <h3>Task Title</h3>
```

### ARIA Labels

**Interactive elements:**
```html
<button
  @click="closeModal()"
  aria-label="Close task details"
  class="..."
>
  <svg>...</svg> <!-- Icon without text -->
</button>

<button
  @click="statusFilter = 'todo'"
  :aria-pressed="statusFilter === 'todo'"
  class="..."
>
  Todo
</button>
```

**Live regions for dynamic content:**
```html
<!-- Announce filter results to screen readers -->
<div
  aria-live="polite"
  aria-atomic="true"
  class="sr-only"
>
  <span x-text="`Showing ${filteredTasks.length} of ${tasks.length} tasks`"></span>
</div>
```

**Modal accessibility:**
```html
<div
  x-show="showModal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  class="..."
>
  <h2 id="modal-title" x-text="selectedTask?.title"></h2>
  <!-- Modal content -->
</div>
```

### Keyboard Navigation

**Focus management:**
```html
<!-- Trap focus in modal -->
<div
  x-show="showModal"
  x-trap.noscroll="showModal"
  class="..."
>
  <!-- Modal content -->
</div>

<!-- First focusable element -->
<button x-ref="closeButton" @click="closeModal()">Close</button>

<!-- Focus on open -->
<div x-init="$nextTick(() => $refs.closeButton.focus())">
```

**Keyboard shortcuts (optional):**
```html
<div @keydown.escape.window="showModal && closeModal()">
  <!-- Close modal on ESC -->
</div>

<div @keydown.slash.window.prevent="$refs.searchInput.focus()">
  <!-- Focus search on '/' -->
</div>
```

### Visual Accessibility

**Color contrast:**
- Ensure 4.5:1 minimum for normal text (WCAG AA)
- Ensure 3:1 minimum for large text (18px+)
- Use Tailwind's accessible color combinations

**Focus indicators:**
```html
<button class="... focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
  <!-- Visible focus ring -->
</button>
```

**Screen reader only content:**
```html
<span class="sr-only">Loading tasks...</span>
<svg class="animate-spin" aria-hidden="true">...</svg>
```

**Reduced motion support:**
```html
<style>
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
```

### Testing Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Logical tab order (left-to-right, top-to-bottom)
- [ ] Skip to main content link (REQUIRED)
- [ ] Proper heading hierarchy
- [ ] Alt text for images (if any)
- [ ] ARIA labels for icon-only buttons
- [ ] Focus trapped in modal when open
- [ ] Focus returned to trigger when modal closes
- [ ] Screen reader announcements for loading states and filter changes
- [ ] Color contrast passes WCAG AA
- [ ] Works with browser zoom (200%+)
- [ ] Reduced motion support implemented

---

## Performance Optimization

### Initial Load Performance

**Critical CSS inlining:**
```html
<style>
  /* Inline critical CSS for skeleton UI */
  .skeleton { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: .5; }
  }
</style>
```

**Preconnect to CDNs:**
```html
<link rel="preconnect" href="https://cdn.tailwindcss.com">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
```

**Defer non-critical scripts:**
```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### Runtime Performance

**Debounce search input:**
```javascript
searchQuery: '',
debouncedSearch: '',

init() {
  // Debounce search
  this.$watch('searchQuery', () => {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.debouncedSearch = this.searchQuery;
      this.applyFilters();
    }, 300);
  });
}
```

**Limit re-renders:**
```html
<!-- Only re-render when filteredTasks actually changes -->
<template x-for="task in filteredTasks" :key="task.id">
  <!-- Use :key for efficient updates -->
</template>
```

**Lazy load modal content:**
```html
<!-- Don't render modal content until needed -->
<template x-if="selectedTask">
  <div>
    <!-- Heavy modal content only when task selected -->
  </div>
</template>
```

### Network Optimization

**Cache API responses:**
```javascript
projectsCache: null,
tasksCacheByProject: {},

async loadProjects() {
  if (this.projectsCache) {
    this.projects = this.projectsCache;
    return;
  }

  // Fetch and cache...
  this.projectsCache = await response.json();
  this.projects = this.projectsCache;
}
```

**Batch API calls:**
```javascript
// If we need project info + tasks, make single combined API call
async loadProjectWithTasks(projectId) {
  const response = await fetch(`/api/projects/${projectId}?include=tasks`);
  // ...
}
```

### Perceived Performance

**Optimistic UI updates:**
```javascript
// Show loading state immediately
this.loading = true;

// Then fetch
await this.loadTasks();
```

**Skeleton screens:**
- Show structural placeholder while loading
- Better UX than blank screen or spinner

**Smooth transitions:**
```html
<!-- Alpine transitions for perceived smoothness -->
<div
  x-show="showModal"
  x-transition:enter="transition ease-out duration-300"
  x-transition:enter-start="opacity-0"
  x-transition:enter-end="opacity-100"
>
```

---

## Future Extensibility

### Design Note: Read-Only Viewer (v1.0)

**Current Scope:** This is a read-only task viewer. No task creation, editing, or deletion in v1.0.

**Future Enhancement Considerations:**
- Task creation/editing would require authentication and authorization
- UI would need "New Task" button and form modal
- API already supports CRUD operations (ready when needed)

### Planned Features (Easy to Add)

**1. Search Endpoint Integration**
```javascript
async searchTasks(query) {
  if (!query.trim()) {
    await this.loadTasks();
    return;
  }

  this.loading = true;
  try {
    const params = new URLSearchParams({
      q: query,
      project_id: this.currentProject.id
    });
    const response = await fetch(`http://localhost:8001/api/tasks/search?${params}`, {
      headers: { 'X-API-Key': this.apiKey }
    });
    const data = await response.json();
    this.tasks = data.tasks;
    this.applyFilters();
  } catch (err) {
    this.error = err.message;
  } finally {
    this.loading = false;
  }
}
```

**2. Pagination Support**
```javascript
async loadTasks(offset = 0, limit = 50) {
  // API already returns total, limit, offset
  const params = new URLSearchParams({
    project_id: this.currentProject.id,
    limit: limit,
    offset: offset
  });
  // ... rest of implementation
}
```

**3. Export to CSV/JSON**
```javascript
exportTasks(format = 'json') {
  let content, mimeType, filename;

  if (format === 'json') {
    content = JSON.stringify(this.filteredTasks, null, 2);
    mimeType = 'application/json';
    filename = 'tasks.json';
  } else if (format === 'csv') {
    const headers = ['ID', 'Title', 'Status', 'Priority', 'Created'];
    const rows = this.filteredTasks.map(t => [
      t.id, t.title, t.status, t.priority, t.created_at
    ]);
    content = [headers, ...rows].map(row => row.join(',')).join('\n');
    mimeType = 'text/csv';
    filename = 'tasks.csv';
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
}
```

### Architecture for Extensions

**Component-based approach:**
- Each major feature in separate `x-data` scope
- Communicate via Alpine stores (global state)
- Emit custom events for cross-component communication

**Alpine Stores (for global state):**
```html
<script>
  document.addEventListener('alpine:init', () => {
    Alpine.store('tasks', {
      items: [],
      selected: null,

      setTasks(tasks) {
        this.items = tasks;
      },

      selectTask(task) {
        this.selected = task;
      }
    });
  });
</script>

<!-- Access from any component -->
<div x-data>
  <div x-text="$store.tasks.items.length"></div>
</div>
```

**Plugin architecture:**
```javascript
// Define reusable behaviors
Alpine.magic('clipboard', () => {
  return text => navigator.clipboard.writeText(text);
});

// Use anywhere
<button @click="$clipboard(task.title)">Copy Title</button>
```

---

## File Structure

```
task-viewer/
├── index.html              # Main HTML file (all-in-one)
├── README.md               # Setup instructions
└── assets/                 # Optional: if we add local assets
    ├── logo.svg
    └── favicon.ico
```

**Alternative (if we split for maintainability):**
```
task-viewer/
├── index.html              # Shell HTML
├── js/
│   ├── app.js             # Alpine app logic
│   └── api.js             # API client wrapper
├── css/
│   └── custom.css         # Custom styles (if needed)
└── README.md
```

**Recommendation:** Start with single-file `index.html` for simplicity. Split only if exceeds ~500 lines.

---

## Summary

### Key Design Decisions

1. **Single-page application** with Alpine.js for reactivity
2. **CDN-based stack** for zero build complexity
3. **Mobile-first responsive design** using Tailwind breakpoints
4. **Component-based architecture** for extensibility
5. **Accessibility-first** with ARIA labels and keyboard nav
6. **Performance-focused** with debouncing, caching, skeleton screens

### UI/UX Principles

- **Clarity:** Status and priority immediately visible
- **Efficiency:** Quick filtering with status chips
- **Feedback:** Loading states, error states, empty states
- **Consistency:** Tailwind's design system throughout
- **Accessibility:** WCAG AA compliant, keyboard navigable

### Development Workflow

1. Build `index.html` with static mock data
2. Test responsive layouts on different devices
3. Connect to FastAPI backend
4. Test with real data from task-mcp
5. Add polish (transitions, loading states)
6. Accessibility audit
7. Deploy alongside FastAPI server

---

**Next Steps:**
1. Review and approve this architecture
2. Create `index.html` skeleton
3. Implement static version with mock data
4. Connect to FastAPI backend
5. Test and iterate

**Design Decisions Made:**
- ✅ Read-only viewer (no task creation/editing in v1.0)
- ✅ No entity UI (entities not in v1.0)
- ✅ API uses port 8001 with `/api/` prefix
- ✅ API key authentication via `X-API-Key` header
- ✅ Project selection uses hash IDs (not workspace paths)
- ✅ Response format extracts arrays from wrapper objects
- ✅ Status/priority counts displayed on filter chips
- ✅ Three accessibility improvements added:
  - Skip to main content link
  - Reduced motion support
  - Live region announcements

---

**Document Status:** REVISED - Updated for Read-Only Viewer with API Key Auth
**Author:** Frontend Architecture Planning Agent
**Date:** November 2, 2025
**Version:** 1.1 (Revised after architecture review)
