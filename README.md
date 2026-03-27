# District Comparison Map

An interactive Svelte application to visualize district-level activity changes between 2019 and 2025 for San Francisco and Washington D.C.

## Features

- **City selection**: Toggle between San Francisco and Washington D.C.
- **Value comparison**: Switch between raw difference and normalized values
- **District type filtering**: Filter by Historic District, Arts District, Tax District, etc.
- **Interactive map**: Hover over districts to see detailed statistics
- **Open source basemap**: Uses CartoDB Dark tiles via OpenStreetMap

## Setup

### 1. Generate the data

First, run the data preparation script to convert the large CSV into GeoJSON files:

```bash
cd scripts
python prepare_district_data.py
```

This reads `district_stops_for_mapping.csv` and outputs:
- `district-map-app/static/data/sf_districts.geojson`
- `district-map-app/static/data/dc_districts.geojson`

### 2. (Optional) Convert to PMTiles

For better performance with large datasets, convert GeoJSON to PMTiles:

```bash
# Requires tippecanoe: https://github.com/felt/tippecanoe
cd scripts
bash generate_pmtiles.sh
```

### 3. Install dependencies

```bash
cd district-map-app
npm install
```

### 4. Run development server

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

### 5. Build for production

```bash
npm run build
```

The built files will be in `dist/`.

## Deploying to GitHub Pages

### Option A: GitHub Actions (Recommended)

1. Create the workflow directory:
   ```bash
   mkdir -p .github/workflows
   ```

2. Copy the deployment workflow:
   ```bash
   cp district-map-app/deploy.yml .github/workflows/deploy.yml
   ```

3. Update `vite.config.js` to match your repository name:
   ```js
   base: '/your-repo-name/',
   ```

4. Push to GitHub and enable Pages in repository settings.

### Option B: Manual deployment

1. Build the project:
   ```bash
   cd district-map-app
   npm run build
   ```

2. Deploy the `dist` folder to your web server or GitHub Pages.

## Data Schema

Each district feature includes:

| Property | Description |
|----------|-------------|
| `district_name` | Name of the district |
| `district_type` | Type (Historic, Arts, Tax, etc.) |
| `city` | San Francisco or Washington |
| `total_stops_2019` | Raw stop count in 2019 |
| `total_stops_2025` | Raw stop count in 2025 |
| `raw_diff` | Difference: 2025 - 2019 |
| `normed_2019` | Normalized value for 2019 |
| `normed_2025` | Normalized value for 2025 |
| `normed_diff` | Normalized difference |

## Tech Stack

- **Svelte** - Frontend framework
- **Vite** - Build tool
- **MapLibre GL JS** - Map rendering
- **PMTiles** - Efficient tile storage (optional)
- **CartoDB** - Open source basemap tiles

## License

MIT
