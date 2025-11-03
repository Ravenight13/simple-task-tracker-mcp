# Entity Type Badge Component Usage

## Overview

The Task Viewer includes reusable entity type badge components for displaying entity types consistently across the UI. These badges use Alpine.js 3.x and Tailwind CSS.

## Badge Types

### File Entity (Blue)
- Background: `bg-blue-100` (light) / `bg-blue-900` (dark)
- Text: `text-blue-800` (light) / `text-blue-200` (dark)
- Icon: Document/file icon from Heroicons

### Other Entity (Purple)
- Background: `bg-purple-100` (light) / `bg-purple-900` (dark)
- Text: `text-purple-800` (light) / `text-purple-200` (dark)
- Icon: Tag icon from Heroicons

## Helper Functions

### 1. `getEntityTypeBadge(entityType)`

Returns complete badge HTML with icon and label. Use this for HTML string rendering (e.g., in `renderSubtasksRecursive` or similar methods).

**Parameters:**
- `entityType` (string): Either `'file'` or `'other'`

**Returns:** HTML string with complete badge markup

**Example Usage:**

```javascript
// In a rendering method that generates HTML strings
renderEntityCard(entity) {
  return `
    <div class="entity-card">
      <h3>${entity.name}</h3>
      ${this.getEntityTypeBadge(entity.entity_type)}
      <p>${entity.description}</p>
    </div>
  `;
}

// In Alpine.js template with x-html
<div x-html="getEntityTypeBadge(entity.entity_type)"></div>
```

### 2. `getEntityTypeBadgeClasses(entityType)`

Returns Tailwind CSS class string for use with Alpine.js `:class` binding. Use this for template-based rendering where you want more control over the structure.

**Parameters:**
- `entityType` (string): Either `'file'` or `'other'`

**Returns:** String of Tailwind CSS classes

**Example Usage:**

```html
<!-- Method 1: Using :class binding with full structure -->
<span
  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
  :class="getEntityTypeBadgeClasses(entity.entity_type)"
>
  <svg class="w-3 h-3 mr-1" x-show="entity.entity_type === 'file'"><!-- file icon --></svg>
  <svg class="w-3 h-3 mr-1" x-show="entity.entity_type === 'other'"><!-- tag icon --></svg>
  <span x-text="entity.entity_type"></span>
</span>

<!-- Method 2: Dynamic wrapper with conditional rendering -->
<template x-if="entity.entity_type === 'file'">
  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
    <svg class="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
    file
  </span>
</template>
<template x-if="entity.entity_type === 'other'">
  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
    <svg class="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
    other
  </span>
</template>
```

## Complete Implementation Examples

### Entity Card Display

```html
<!-- Entity list with badges -->
<template x-for="entity in entities" :key="entity.id">
  <div class="entity-card p-4 border rounded-lg">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold" x-text="entity.name"></h3>
      <!-- Using getEntityTypeBadge for simple rendering -->
      <div x-html="getEntityTypeBadge(entity.entity_type)"></div>
    </div>
    <p class="text-sm text-gray-600 mt-2" x-text="entity.description"></p>
  </div>
</template>
```

### Entity Modal with Badge

```html
<!-- Entity detail modal -->
<div x-show="selectedEntity" class="modal">
  <div class="modal-content">
    <div class="flex items-center gap-3 mb-4">
      <h2 x-text="selectedEntity.name"></h2>
      <!-- Using getEntityTypeBadge -->
      <div x-html="getEntityTypeBadge(selectedEntity.entity_type)"></div>
    </div>

    <!-- Rest of modal content -->
    <div class="entity-details">
      <p x-text="selectedEntity.description"></p>
    </div>
  </div>
</div>
```

### Entity List with Filtering by Type

```html
<!-- Entity type filter buttons -->
<div class="flex gap-2 mb-4">
  <button
    @click="filterByType('all')"
    class="px-3 py-1 rounded"
    :class="{ 'bg-blue-500 text-white': entityFilter === 'all' }"
  >
    All
  </button>

  <button
    @click="filterByType('file')"
    class="px-3 py-1 rounded"
    :class="{ 'bg-blue-500 text-white': entityFilter === 'file' }"
  >
    <div x-html="getEntityTypeBadge('file')"></div>
  </button>

  <button
    @click="filterByType('other')"
    class="px-3 py-1 rounded"
    :class="{ 'bg-blue-500 text-white': entityFilter === 'other' }"
  >
    <div x-html="getEntityTypeBadge('other')"></div>
  </button>
</div>

<!-- Filtered entity list -->
<template x-for="entity in filteredEntities" :key="entity.id">
  <div class="entity-item">
    <div x-html="getEntityTypeBadge(entity.entity_type)"></div>
    <span x-text="entity.name"></span>
  </div>
</template>
```

## Styling Guidelines

### Badge Dimensions
- Padding: `px-2.5 py-0.5` (horizontal: 10px, vertical: 2px)
- Border radius: `rounded-full`
- Font size: `text-xs` (12px)
- Font weight: `font-medium` (500)

### Icon Dimensions
- Width/Height: `w-3 h-3` (12px)
- Margin right: `mr-1` (4px)
- Stroke width: `stroke-width="2"`

### Color Scheme

**File Entity (Blue):**
- Light mode: bg-blue-100, text-blue-800
- Dark mode: bg-blue-900, text-blue-200

**Other Entity (Purple):**
- Light mode: bg-purple-100, text-purple-800
- Dark mode: bg-purple-900, text-purple-200

## Accessibility Considerations

- **Semantic HTML:** Use `<span>` for inline badges
- **Color contrast:** All color combinations meet WCAG AA standards
- **Icon alt text:** Consider adding `aria-label` for screen readers
- **Keyboard navigation:** Badges are informational, not interactive

## Best Practices

1. **Consistency:** Use the same helper throughout the application
2. **Fallback:** Both helpers default to 'other' styling for unknown types
3. **Performance:** Prefer `getEntityTypeBadgeClasses()` for large lists (avoids HTML parsing)
4. **Simplicity:** Use `getEntityTypeBadge()` for simple, one-off displays
5. **Dark mode:** All badges include dark mode variants automatically

## Testing

### Manual Testing Checklist

- [ ] File entity displays blue badge with document icon
- [ ] Other entity displays purple badge with tag icon
- [ ] Badge renders correctly in light mode
- [ ] Badge renders correctly in dark mode
- [ ] Badge maintains consistent sizing across different contexts
- [ ] Unknown entity types fall back to 'other' styling
- [ ] Badges are readable at various screen sizes

## Future Enhancements

Potential improvements for future iterations:

1. **Additional entity types:** vendor, person, document, etc.
2. **Custom icons:** Allow passing custom SVG icons
3. **Size variants:** small, medium, large badge sizes
4. **Interactive badges:** Click-to-filter functionality
5. **Tooltips:** Hover tooltips with entity metadata
6. **Badge groups:** Display multiple entity types in a compact format

## Related Components

- Status badges (task status: todo, in_progress, done, blocked)
- Priority badges (low, medium, high)
- Tag badges (user-defined tags)
- Subtask indicator badges

## References

- Alpine.js documentation: https://alpinejs.dev
- Tailwind CSS badge patterns: https://tailwindcss.com/docs/badge
- Heroicons: https://heroicons.com
- WCAG color contrast guidelines: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
