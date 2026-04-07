<script>
  import { onMount, onDestroy } from 'svelte';
  import * as maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import * as pmtiles from 'pmtiles';

  // Props
  let { selectedCity = 'San Francisco', valueType = 'normalized', selectedTypes = [] } = $props();

  let map = $state();
  let mapContainer = $state();
  let isMapLoaded = $state(false);
  let usePmtiles = $state(true); // Try PMTiles first with improved URL resolution
  let popup = null; // MapLibre Popup instance

  // City center coordinates
  const cityCoords = {
    'San Francisco': { center: [-122.4194, 37.7749], zoom: 12 },
    'Washington': { center: [-77.0369, 38.9072], zoom: 12 }
  };

  // Get data URL based on city and format
  function getDataUrl(city, format = 'pmtiles') {
    const citySlug = city === 'San Francisco' ? 'sf_districts' : 'dc_districts';
    const ext = format === 'pmtiles' ? 'pmtiles' : 'geojson';
    return `${import.meta.env.BASE_URL}data/${citySlug}.${ext}`;
  }

  function toAbsoluteUrl(path) {
    return new URL(path, window.location.origin).toString();
  }

  // Build color expression for raw differences
  function getRawColorExpression() {
    return [
      'interpolate',
      ['linear'],
      ['get', 'raw_diff'],
      -1000000, '#d73027',   // Strong decrease - red
      -100000, '#fc8d59',    // Moderate decrease
      -10000, '#fee08b',     // Slight decrease
      0, '#ffffbf',          // Neutral - yellow
      10000, '#d9ef8b',      // Slight increase
      100000, '#91cf60',     // Moderate increase
      1000000, '#1a9850'     // Strong increase - green
    ];
  }

  // Build expression for normalized percent change: (normed_diff / |2019|) * 100
  function getNormalizedPercentChangeExpression() {
    return [
      'case',
      ['<', ['abs', ['get', 'normed_2019']], 0.000000001],
      0,
      [
        '*',
        [
          '/',
          ['get', 'normed_diff'],
          ['abs', ['get', 'normed_2019']]
        ],
        100
      ]
    ];
  }

  // Build color expression for normalized percent changes
  function getNormedColorExpression() {
    return [
      'interpolate',
      ['linear'],
      getNormalizedPercentChangeExpression(),
      -50, '#d73027',
      -25, '#fc8d59',
      -10, '#fee08b',
      0, '#ffffbf',
      10, '#d9ef8b',
      25, '#91cf60',
      50, '#1a9850'
    ];
  }

  // Update map when city changes using $effect
  $effect(() => {
    if (map && isMapLoaded && selectedCity) {
      updateMapSource();
    }
  });

  // Update colors when value type changes
  $effect(() => {
    if (map && isMapLoaded && valueType) {
      updateMapColors();
    }
  });

  // Update filter when types change
  $effect(() => {
    // Access array length to ensure reactivity triggers
    const typesCount = selectedTypes.length;
    if (map && isMapLoaded) {
      console.log('Updating filter for types:', selectedTypes, 'count:', typesCount);
      updateTypeFilter();
    }
  });

  async function updateMapSource() {
    const layerId = 'districts-layer';
    const outlineLayerId = 'districts-outline';
    const sourceId = 'districts-source';

    // Remove existing layers and source
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);

    const citySlug = selectedCity === 'San Francisco' ? 'sf_districts' : 'dc_districts';

    // Try PMTiles first
    if (usePmtiles) {
      try {
        const relativePath = `data/${citySlug}.pmtiles`;
        const candidateUrls = [
          toAbsoluteUrl(getDataUrl(selectedCity, 'pmtiles')),
          new URL(relativePath, window.location.href).toString(),
          new URL(`/${relativePath}`, window.location.origin).toString()
        ];

        const uniqueCandidateUrls = [...new Set(candidateUrls)];
        let pmtilesUrl = null;
        let lastError = null;

        // Try to fetch the PMTiles file to see which URL works
        for (const url of uniqueCandidateUrls) {
          try {
            const response = await fetch(url, { method: 'HEAD' });
            if (response.ok) {
              pmtilesUrl = url;
              console.log('Found PMTiles at:', pmtilesUrl);
              break;
            }
          } catch (e) {
            lastError = e;
          }
        }

        if (!pmtilesUrl) {
          throw new Error('PMTiles file not found at any candidate URL');
        }
        
        // Create PMTiles instance
        const p = new pmtiles.PMTiles(pmtilesUrl);
        
        // Add this PMTiles instance to the protocol handler
        protocolInstance.add(p);
        
        map.addSource(sourceId, {
          type: 'vector',
          url: `pmtiles://${pmtilesUrl}`,
          attribution: 'District boundaries'
        });

        addDistrictLayers(layerId, outlineLayerId, sourceId, citySlug);
      } catch (err) {
        console.warn('PMTiles failed, falling back to GeoJSON:', err);
        
        // Clean up any partially added sources/layers from failed PMTiles attempt
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getLayer(outlineLayerId)) map.removeLayer(outlineLayerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
        
        usePmtiles = false;
        await loadGeoJSON(sourceId, layerId, outlineLayerId);
      }
    } else {
      await loadGeoJSON(sourceId, layerId, outlineLayerId);
    }

    // Fly to city
    const coords = cityCoords[selectedCity];
    map.flyTo({
      center: coords.center,
      zoom: coords.zoom,
      duration: 1500
    });
  }

  async function loadGeoJSON(sourceId, layerId, outlineLayerId) {
    const citySlug = selectedCity === 'San Francisco' ? 'sf_districts' : 'dc_districts';
    const relativePath = `data/${citySlug}.geojson`;
    const candidateUrls = [
      toAbsoluteUrl(getDataUrl(selectedCity, 'geojson')),
      new URL(relativePath, window.location.href).toString(),
      new URL(`/${relativePath}`, window.location.origin).toString()
    ];

    const uniqueCandidateUrls = [...new Set(candidateUrls)];
    let lastError = null;

    for (const geojsonUrl of uniqueCandidateUrls) {
      console.log('Loading GeoJSON from:', geojsonUrl);

      try {
        const response = await fetch(geojsonUrl);
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }

        const text = await response.text();
        const firstChar = text.trimStart().charAt(0);
        if (firstChar !== '{' && firstChar !== '[') {
          throw new Error('Response is not JSON (likely an HTML fallback page)');
        }

        const geojson = JSON.parse(text);

        map.addSource(sourceId, {
          type: 'geojson',
          data: geojson
        });

        addDistrictLayersGeoJSON(layerId, outlineLayerId, sourceId);
        return;
      } catch (err) {
        lastError = err;
        console.warn(`GeoJSON load attempt failed for ${geojsonUrl}:`, err);
      }
    }

    console.error('Failed to load GeoJSON from all candidate URLs:', uniqueCandidateUrls, lastError);
  }

  function addDistrictLayers(layerId, outlineLayerId, sourceId, sourceLayer) {
    const colorExpr = valueType === 'raw' ? getRawColorExpression() : getNormedColorExpression();

    // Fill layer
    map.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      'source-layer': sourceLayer,
      paint: {
        'fill-color': colorExpr,
        'fill-opacity': 0.8
      }
    });

    // Outline layer
    map.addLayer({
      id: outlineLayerId,
      type: 'line',
      source: sourceId,
      'source-layer': sourceLayer,
      paint: {
        'line-color': '#ffffff',
        'line-width': 1.5,
        'line-opacity': 0.7
      }
    });

    setupHoverInteraction(layerId);
  }

  function addDistrictLayersGeoJSON(layerId, outlineLayerId, sourceId) {
    const colorExpr = valueType === 'raw' ? getRawColorExpression() : getNormedColorExpression();

    // Fill layer (no source-layer for GeoJSON)
    map.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      paint: {
        'fill-color': colorExpr,
        'fill-opacity': 0.8
      }
    });

    // Outline layer
    map.addLayer({
      id: outlineLayerId,
      type: 'line',
      source: sourceId,
      paint: {
        'line-color': '#ffffff',
        'line-width': 1.5,
        'line-opacity': 0.7
      }
    });

    setupHoverInteraction(layerId);
  }

  function updateMapColors() {
    const layerId = 'districts-layer';
    if (!map.getLayer(layerId)) return;

    const colorExpr = valueType === 'raw' ? getRawColorExpression() : getNormedColorExpression();
    map.setPaintProperty(layerId, 'fill-color', colorExpr);
  }

  function updateTypeFilter() {
    const layerId = 'districts-layer';
    const outlineLayerId = 'districts-outline';
    if (!map.getLayer(layerId)) {
      console.log('Layer not found, skipping filter update');
      return;
    }

    let filter = null;
    if (selectedTypes.length > 0) {
      // MapLibre filter: check if district_type matches any value in selectedTypes array
      filter = ['in', ['get', 'district_type'], ['literal', selectedTypes]];
      console.log('Applying filter:', filter);
    } else {
      console.log('Clearing filter (showing all types)');
    }

    map.setFilter(layerId, filter);
    map.setFilter(outlineLayerId, filter);
  }

  function setupHoverInteraction(layerId) {
    // Create popup instance if it doesn't exist
    if (!popup) {
      popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        maxWidth: '300px',
        className: 'district-popup'
      });
    }

    map.on('mousemove', layerId, (e) => {
      if (e.features.length > 0) {
        map.getCanvas().style.cursor = 'pointer';
        const feature = e.features[0];
        const props = feature.properties;
        
        // Format numbers
        const formatNumber = (num) => {
          if (num === null || num === undefined) return 'N/A';
          if (Math.abs(num) >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
          }
          if (Math.abs(num) >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
          }
          return num.toLocaleString();
        };

        const formatNormed = (num) => {
          if (num === null || num === undefined) return 'N/A';
          return (num * 1000000).toFixed(2) + ' (×10⁻⁶)';
        };

        const getPercentChange = (fromValue, diffValue) => {
          if (fromValue === null || fromValue === undefined || diffValue === null || diffValue === undefined) {
            return null;
          }
          if (fromValue === 0) {
            return diffValue === 0 ? 0 : null;
          }
          return (diffValue / Math.abs(fromValue)) * 100;
        };

        const formatPercentChange = (num) => {
          if (num === null || num === undefined || Number.isNaN(num) || !Number.isFinite(num)) {
            return 'N/A';
          }
          return `${num > 0 ? '+' : ''}${num.toFixed(1)}%`;
        };

        const getChangeColor = (value) => {
          if (value > 0) return 'var(--brandMedGreen)'; // green
          if (value < 0) return 'var(--brandRed)'; // red
          return '#ffffbf'; // yellow
        };

        const changeValue = valueType === 'raw'
          ? props.raw_diff
          : getPercentChange(props.normed_2019, props.normed_diff);
        const changeColor = getChangeColor(changeValue);
        const detailSection = valueType === 'raw'
          ? `
            <div class="popup-detail-grid">
              <div>
                <div class="popup-detail-label">2019 Stops</div>
                <div class="popup-detail-value">
                  ${formatNumber(props.total_stops_2019)}
                </div>
              </div>
              <div>
                <div class="popup-detail-label">2025 Stops</div>
                <div class="popup-detail-value">
                  ${formatNumber(props.total_stops_2025)}
                </div>
              </div>
            </div>
          `
          : '';
        const changeLabel = valueType === 'raw' ? 'Change' : 'Percent Change (2019 to 2025)';
        const changeDisplay = valueType === 'raw'
          ? `${changeValue > 0 ? '+' : ''}${formatNumber(changeValue)}`
          : formatPercentChange(changeValue);

        // Build popup HTML
        const html = `
          <div class="popup-container">
            <h3 class="popup-title">
              ${props.district_name}
            </h3>
            <p class="popup-subtitle">
              ${props.district_type}
            </p>
            ${detailSection}
            <div class="popup-change-row">
              <div class="popup-change-label">${changeLabel}</div>
              <div class="popup-change-value" style="color: ${changeColor};">
                ${changeDisplay}
              </div>
            </div>
          </div>
        `;

        // Set popup content and position
        popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
      }
    });

    map.on('mouseleave', layerId, () => {
      map.getCanvas().style.cursor = '';
      if (popup) {
        popup.remove();
      }
    });
  }

  // Store protocol instance globally so we can use it later
  let protocolInstance;

  onMount(() => {
    // Register PMTiles protocol globally
    protocolInstance = new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles', protocolInstance.tile);

    // Initialize map with CartoDB dark basemap (open source)
    map = new maplibregl.Map({
      container: mapContainer,
      style: {
        version: 8,
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
          }
        },
        layers: [
          {
            id: 'carto-dark-layer',
            type: 'raster',
            source: 'carto-dark',
            minzoom: 0,
            maxzoom: 22
          }
        ]
      },
      center: cityCoords[selectedCity].center,
      zoom: cityCoords[selectedCity].zoom,
      attributionControl: true
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-right');

    map.on('load', () => {
      isMapLoaded = true;
      updateMapSource();
    });
  });

  onDestroy(() => {
    if (popup) {
      popup.remove();
      popup = null;
    }
    if (map) {
      map.remove();
    }
  });
</script>

<div class="map-container" bind:this={mapContainer}></div>

<style>
  .map-container {
    flex: 1;
    height: 100%;
  }

  :global(.popup-container) {
    padding: 8px;
  }

  :global(.popup-title) {
    margin: 0 0 4px 0;
    font-size: 14px;
    font-weight: 600;
    color: #000;
  }

  :global(.popup-subtitle) {
    margin: 0 0 8px 0;
    font-size: 11px;
    color: #000;
  }

  :global(.popup-detail-grid) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
  }

  :global(.popup-detail-label) {
    font-size: 10px;
    color: var(--brandGray70);
  }

  :global(.popup-detail-value) {
    font-size: 13px;
    font-weight: 600;
    color: #000;
  }

  :global(.popup-change-row) {
    border-top: 1px solid var(--brandGray70);
    padding-top: 8px;
  }

  :global(.popup-change-label) {
    font-size: 10px;
    color: #000;
  }

  :global(.popup-change-value) {
    font-size: 14px;
    font-weight: 700;
  }
</style>
