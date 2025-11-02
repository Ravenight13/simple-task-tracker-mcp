# Task Viewer Quick Start Guide

## Prerequisites

1. **Backend API** running on `http://localhost:8001`
   - See `docs/task-viewer/BACKEND_ARCHITECTURE.md` for setup
2. **Valid API Key** from backend configuration

## Start the Frontend

### Option 1: Python HTTP Server (Recommended)

```bash
cd task-viewer/static
python3 -m http.server 8080
```

Open: http://localhost:8080

### Option 2: Node.js HTTP Server

```bash
npx http-server task-viewer/static -p 8080
```

Open: http://localhost:8080

### Option 3: PHP Server

```bash
cd task-viewer/static
php -S localhost:8080
```

Open: http://localhost:8080

### Option 4: Live Server (VS Code Extension)

1. Install "Live Server" extension
2. Right-click `task-viewer/static/index.html`
3. Select "Open with Live Server"

## First-Time Setup

1. **Open browser** to http://localhost:8080
2. **Enter API Key** when prompted
   - Get API key from backend `.env` file
   - Key is stored in browser localStorage
3. **Select Project** from dropdown
4. **Browse Tasks** with filters

## Testing the Interface

### Basic Navigation

1. ✅ Projects load in dropdown
2. ✅ Select a project
3. ✅ Tasks display in grid
4. ✅ Click a task to see details
5. ✅ Close modal with X or Esc key

### Filtering

1. ✅ Click status chips (Todo, In Progress, Done, Blocked)
2. ✅ Use priority dropdown (Low, Medium, High)
3. ✅ Type in search box (debounced 300ms)
4. ✅ Use sort dropdown (Newest, Oldest, Priority, Title)

### Responsive Design

1. ✅ Resize browser window
2. ✅ Check mobile view (<640px): 1 column
3. ✅ Check tablet view (640-1024px): 2 columns
4. ✅ Check desktop view (>1024px): 3 columns

### Accessibility

1. ✅ Tab through interface (keyboard only)
2. ✅ Press "/" to focus search (if implemented)
3. ✅ Press Esc to close modal
4. ✅ Use screen reader to verify announcements

## Troubleshooting

### "Cannot GET /" Error

- You're accessing the wrong URL
- Go to `http://localhost:8080` (not just `localhost:8080`)

### "Invalid API Key" Error

1. Check backend is running: `curl http://localhost:8001/health`
2. Verify API key in backend `.env` file
3. Clear browser localStorage: DevTools > Application > Local Storage > Clear
4. Re-enter API key

### Tasks Not Loading

1. **Check browser console** (F12) for errors
2. **Verify backend URL** in `js/config.js`
3. **Check CORS configuration** on backend
4. **Test API directly**: `curl -H "X-API-Key: your-key" http://localhost:8001/api/projects`

### Styling Issues

1. **Check Tailwind CDN** is loading (Network tab)
2. **Hard refresh** browser (Cmd/Ctrl + Shift + R)
3. **Clear browser cache**

### Alpine.js Not Working

1. **Check Alpine CDN** is loading (Network tab)
2. **Look for JavaScript errors** in console
3. **Ensure `x-cloak` is hidden** in CSS

## Development Workflow

### Making Changes

1. Edit `index.html` or `js/config.js`
2. Save file
3. Refresh browser (or use live reload)
4. Check browser console for errors

### Testing API Integration

```javascript
// Open browser console (F12)
// Test API manually

// Check API config
console.log(API_CONFIG.baseUrl);
console.log(API_CONFIG.getApiKey());

// Test projects endpoint
fetch('http://localhost:8001/api/projects', {
  headers: { 'X-API-Key': API_CONFIG.getApiKey() }
})
.then(r => r.json())
.then(d => console.log(d));

// Test tasks endpoint
fetch('http://localhost:8001/api/tasks?project_id=1e7be4ae', {
  headers: { 'X-API-Key': API_CONFIG.getApiKey() }
})
.then(r => r.json())
.then(d => console.log(d));
```

### Debugging Alpine.js State

```javascript
// In browser console, access Alpine data
// (only works if Alpine DevTools enabled)

// View current state
$data

// View filtered tasks
$data.filteredTasks

// View current project
$data.currentProject

// Manually trigger actions
$data.loadTasks()
```

## Performance Tips

### Slow Loading?

1. **Check network tab** for slow requests
2. **Reduce limit** in API calls (if implemented)
3. **Enable caching** in browser
4. **Use production CDNs** (not dev builds)

### High Memory Usage?

1. **Clear filteredTasks** when switching projects
2. **Implement pagination** for large task lists
3. **Limit concurrent API calls**

## Production Deployment

### Update API URL

Edit `js/config.js`:

```javascript
baseUrl: 'https://your-production-api.com/api'
```

### Deploy Static Files

1. **Upload to static host** (Netlify, Vercel, GitHub Pages)
2. **Configure CORS** on backend for production domain
3. **Enable HTTPS** (required for secure API key transmission)
4. **Set CSP headers** for security

### Example: GitHub Pages

```bash
# Create gh-pages branch
git checkout -b gh-pages

# Copy static files to root
cp -r task-viewer/static/* .

# Commit and push
git add .
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages
```

Access: `https://username.github.io/repo-name/`

## Next Steps

1. ✅ Start backend on port 8001
2. ✅ Start frontend on port 8080
3. ✅ Enter API key
4. ✅ Test all features
5. ✅ Report any issues

## Support

- **Documentation**: See `task-viewer/README.md`
- **Backend Setup**: See `docs/task-viewer/BACKEND_ARCHITECTURE.md`
- **API Reference**: See `docs/task-viewer/API_SPECIFICATION.md`

---

**Quick Reference**

| Action | Command |
|--------|---------|
| Start Frontend | `cd task-viewer/static && python3 -m http.server 8080` |
| Test Backend Health | `curl http://localhost:8001/health` |
| Test Projects API | `curl -H "X-API-Key: key" http://localhost:8001/api/projects` |
| Open Frontend | http://localhost:8080 |
| Clear API Key | DevTools > Application > Local Storage > Clear |
