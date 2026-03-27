# Debug Fixes Applied

## Issue 1: Bash Script Line Endings ✅ FIXED

**Problem**: Windows line endings (CRLF) causing `$'\r': command not found` errors

**Solution**: Converted `generate_pmtiles.sh` to Unix line endings (LF)

**How to run**:
```bash
cd scripts
bash generate_pmtiles.sh
```

## Issue 2: Svelte 5 Compatibility ✅ FIXED

**Problem**: Code was written for Svelte 4, but npm installed Svelte 5.55.0

**Changes Made**:

### 1. `src/main.js`
- Changed from `new App()` to `mount(App, {...})`

### 2. `src/App.svelte`
- Changed `let variable` to `let variable = $state(...)`
- State variables: `selectedCity`, `valueType`, `selectedTypes`, `hoveredDistrict`

### 3. `src/lib/components/Map.svelte`
- Changed `export let prop` to `let { prop } = $props()`
- Changed `let variable` to `let variable = $state(...)`
- Changed `$:` reactive statements to `$effect(() => {...})`

### 4. `src/lib/components/SidePanel.svelte`
- Changed `export let prop` to `let { prop } = $props()`

## Test the App

```bash
cd district-map-app
npm run dev
```

Open http://localhost:5173 and you should see:
- Side panel with filters on the left
- Map displaying San Francisco districts (default)
- Toggle between SF and DC
- Switch between Raw and Normalized values
- Filter by district type

## Next Steps

1. **Generate PMTiles** (optional but recommended):
   ```bash
   cd scripts
   bash generate_pmtiles.sh
   ```

2. **Adjust color scales** if needed - edit the color expressions in `Map.svelte`

3. **Deploy to GitHub Pages** - follow README.md instructions
