# Task Viewer Frontend

A lightweight, read-only web interface for viewing tasks from the task-mcp system.

## Features

- **Zero Build Process**: Pure HTML + CDN resources (Tailwind CSS, Alpine.js)
- **Responsive Design**: Mobile-first, works on phones, tablets, and desktops
- **Accessible**: WCAG AA compliant with keyboard navigation and screen reader support
- **Real-time Filtering**: Client-side filtering for instant response
- **API Key Authentication**: Secure access via X-API-Key header

## Tech Stack

- HTML5
- [Tailwind CSS 3.4+](https://tailwindcss.com/) (CDN)
- [Alpine.js 3.13+](https://alpinejs.dev/) (CDN)
- FastAPI backend (port 8001)

## Quick Start

### Prerequisites

1. Task-mcp backend API running on `http://localhost:8001`
2. Valid API key for authentication

### Setup

1. **Serve the static files** using any HTTP server:

   ```bash
   # Using Python
   cd task-viewer/static
   python3 -m http.server 8080

   # Using Node.js
   npx http-server task-viewer/static -p 8080

   # Using PHP
   cd task-viewer/static
   php -S localhost:8080
   ```

2. **Open in browser**: http://localhost:8080

3. **Configure API Key**: On first visit, you'll be prompted to enter your API key. This is stored in localStorage.

## Configuration

### API Endpoint

Edit `js/config.js` to change the API base URL:

```javascript
const API_CONFIG = {
  baseUrl: 'http://localhost:8001/api', // Change for production
  // ...
};
```

### Production Deployment

For production, update the base URL to your deployed backend:

```javascript
baseUrl: 'https://your-api.example.com/api'
```

## File Structure

```
task-viewer/
├── static/
│   ├── index.html          # Main application file
│   ├── js/
│   │   └── config.js       # API configuration
│   └── css/
│       └── (empty - using Tailwind CDN)
└── README.md
```

## Features

### Project Selection
- Dropdown to switch between projects
- Shows friendly name and workspace path

### Task Filtering
- **Status**: All, Todo, In Progress, Done, Blocked (with counts)
- **Priority**: All, Low, Medium, High
- **Search**: Real-time search across title, description, and tags
- **Sort**: Newest first, Oldest first, Priority, Title (A-Z)

### Task Display
- Responsive card grid (1/2/3 columns)
- Status and priority badges
- Truncated descriptions
- Relative timestamps

### Task Detail Modal
- Full task information
- Description, tags, dates
- File references
- Blocker reason (if blocked)
- Keyboard accessible (Esc to close)

### Accessibility
- Skip to main content link
- ARIA labels and live regions
- Keyboard navigation
- Focus trapping in modals
- Screen reader announcements
- Reduced motion support

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### "Invalid API Key" Error
- Check that the backend is running on port 8001
- Verify your API key is correct
- Clear localStorage and re-enter the key

### Tasks Not Loading
- Check browser console for errors
- Verify backend URL in `js/config.js`
- Ensure CORS is configured on backend

### Styling Issues
- Check that Tailwind CDN is loading (view network tab)
- Hard refresh (Cmd/Ctrl + Shift + R)

## Development

No build process required! Simply:

1. Edit `index.html` or `js/config.js`
2. Refresh browser to see changes
3. Use browser DevTools for debugging

## Security Notes

- API key stored in browser localStorage (not secure for sensitive data)
- Only use over HTTPS in production
- Read-only viewer - no task creation/editing
- No server-side sessions or cookies

## Future Enhancements

- Dark mode toggle (currently respects system preference)
- Pagination for large task lists
- Export tasks to JSON/CSV
- Saved filter presets
- Keyboard shortcuts

## License

See parent project for license information.
