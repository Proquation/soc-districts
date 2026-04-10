<script>
  import { onMount, onDestroy } from 'svelte';
  import * as maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import * as pmtiles from 'pmtiles';
  import baseMap from '../../assets/base_map_style.json';

  // Props
  let { selectedCity = 'San Francisco', selectedTypes = [] } = $props();

  let map = $state();
  let mapContainer = $state();
  let isMapLoaded = $state(false);
  let usePmtiles = $state(true); // Try PMTiles first with improved URL resolution
  let popup = null; // MapLibre Popup instance
  const sourceId = 'districts-source';
  const layerId = 'districts-layer';
  const hoverFillLayerId = 'districts-hover-fill';
  const hoverOutlineLayerId = 'districts-hover-outline';
  const noHoverFilter = ['==', ['get', 'district_name'], '__NO_HOVER__'];
  let hoverMoveHandler = null;
  let hoverLeaveHandler = null;

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
      -50, '#DC4633',   // var(--brandRed)
      -25, '#F1C500',   // var(--brandYellow) - just blending nicely since red-green is tricky, let's use Yellow for middle-negative. Or maybe Pink? The user said "brandMedBlue for the increase amount instead of green"
      -10, '#D0D1C9',   // var(--brandGray)
      0,   '#D0D1C9',   // var(--brandGray)
      10,  '#6FC7EA',   // var(--brandLightBlue)
      25,  '#007FA3',   // var(--brandMedBlue)
      50,  '#1E3765'    // var(--brandDarkBlue)
    ];
  }

  // Update map when city changes using $effect
  $effect(() => {
    if (map && isMapLoaded && selectedCity) {
      updateMapSource();
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
    removeDistrictLayersAndSource();

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

        addDistrictLayers(layerId, sourceId, citySlug);
        updateTypeFilter();
      } catch (err) {
        console.warn('PMTiles failed, falling back to GeoJSON:', err);
        
        // Clean up any partially added sources/layers from failed PMTiles attempt
        removeDistrictLayersAndSource();
        
        usePmtiles = false;
        await loadGeoJSON(sourceId, layerId);
      }
    } else {
      await loadGeoJSON(sourceId, layerId);
    }

    // Fly to city
    const coords = cityCoords[selectedCity];
    map.flyTo({
      center: coords.center,
      zoom: coords.zoom,
      duration: 1500
    });
  }

  async function loadGeoJSON(sourceId, layerId) {
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

        const existingSource = map.getSource(sourceId);
        if (existingSource && typeof existingSource.setData === 'function') {
          existingSource.setData(geojson);
        } else {
          map.addSource(sourceId, {
            type: 'geojson',
            data: geojson
          });
        }

        if (!map.getLayer(layerId)) {
          addDistrictLayersGeoJSON(layerId, sourceId);
        }
        updateTypeFilter();
        return;
      } catch (err) {
        lastError = err;
        console.warn(`GeoJSON load attempt failed for ${geojsonUrl}:`, err);
      }
    }

    console.error('Failed to load GeoJSON from all candidate URLs:', uniqueCandidateUrls, lastError);
  }

  function addDistrictLayers(layerId, sourceId, sourceLayer) {
    const colorExpr = getNormedColorExpression();

    // Fill layer
    map.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      'source-layer': sourceLayer,
      layout: {
        'fill-sort-key': ['coalesce', ['get', 'z_sort'], 0]
      },
      paint: {
        'fill-color': colorExpr,
        'fill-opacity': 0.8
      }
    });

    map.addLayer({
      id: hoverFillLayerId,
      type: 'fill',
      source: sourceId,
      'source-layer': sourceLayer,
      filter: noHoverFilter,
      paint: {
        'fill-color': '#000000',
        'fill-opacity': 0.22
      }
    });

    map.addLayer({
      id: hoverOutlineLayerId,
      type: 'line',
      source: sourceId,
      'source-layer': sourceLayer,
      filter: noHoverFilter,
      paint: {
        'line-color': '#ffffff',
        'line-width': 1.6,
        'line-opacity': 0.95
      }
    });

    setupHoverInteraction(layerId);
  }

  function addDistrictLayersGeoJSON(layerId, sourceId) {
    const colorExpr = getNormedColorExpression();

    // Fill layer (no source-layer for GeoJSON)
    map.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      layout: {
        'fill-sort-key': ['coalesce', ['get', 'z_sort'], 0]
      },
      paint: {
        'fill-color': colorExpr,
        'fill-opacity': 0.8
      }
    });

    map.addLayer({
      id: hoverFillLayerId,
      type: 'fill',
      source: sourceId,
      filter: noHoverFilter,
      paint: {
        'fill-color': '#000000',
        'fill-opacity': 0.22
      }
    });

    map.addLayer({
      id: hoverOutlineLayerId,
      type: 'line',
      source: sourceId,
      filter: noHoverFilter,
      paint: {
        'line-color': '#ffffff',
        'line-width': 1.6,
        'line-opacity': 0.95
      }
    });

    setupHoverInteraction(layerId);
  }

  function updateTypeFilter() {
    const layerId = 'districts-layer';
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

    if (hoverMoveHandler) {
      map.off('mousemove', layerId, hoverMoveHandler);
    }
    if (hoverLeaveHandler) {
      map.off('mouseleave', layerId, hoverLeaveHandler);
    }

    hoverMoveHandler = (e) => {
      if (e.features.length > 0) {
        map.getCanvas().style.cursor = 'pointer';
        const feature = e.features[0];
        const props = feature.properties;
        const hoverFilter = [
          'all',
          ['==', ['get', 'district_name'], props.district_name],
          ['==', ['get', 'district_type'], props.district_type]
        ];

        if (map.getLayer(hoverFillLayerId)) {
          map.setFilter(hoverFillLayerId, hoverFilter);
        }

        if (map.getLayer(hoverOutlineLayerId)) {
          map.setFilter(hoverOutlineLayerId, hoverFilter);
        }
        
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
          if (value > 0) return '#007FA3'; // var(--brandMedBlue)
          if (value < 0) return '#DC4633'; // var(--brandRed)
          return '#D0D1C9'; // var(--brandGray)
        };

        const changeValue = getPercentChange(props.normed_2019, props.normed_diff);
        const changeColor = getChangeColor(changeValue);
        const changeLabel = 'Percent Change (2019 to 2025)';
        const changeDisplay = formatPercentChange(changeValue);

        // Build popup HTML
        const html = `
          <div class="popup-container">
            <h3 class="popup-title">
              ${props.district_name}
            </h3>
            <p class="popup-subtitle">
              ${props.district_type}
            </p>
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
    };

    hoverLeaveHandler = () => {
      map.getCanvas().style.cursor = '';
      if (map.getLayer(hoverFillLayerId)) {
        map.setFilter(hoverFillLayerId, noHoverFilter);
      }
      if (map.getLayer(hoverOutlineLayerId)) {
        map.setFilter(hoverOutlineLayerId, noHoverFilter);
      }
      if (popup) {
        popup.remove();
      }
    };

    map.on('mousemove', layerId, hoverMoveHandler);
    map.on('mouseleave', layerId, hoverLeaveHandler);
  }

  function removeDistrictLayersAndSource() {
    if (!map) return;
    if (map.getLayer(hoverOutlineLayerId)) map.removeLayer(hoverOutlineLayerId);
    if (map.getLayer(hoverFillLayerId)) map.removeLayer(hoverFillLayerId);
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);
  }

  // Store protocol instance globally so we can use it later
  let protocolInstance;

  onMount(() => {
    // Register PMTiles protocol globally
    protocolInstance = new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles', protocolInstance.tile);

    map = new maplibregl.Map({
      container: mapContainer,
      style: {
          version: 8,
          glyphs: 'https://schoolofcities.github.io/fonts/fonts/{fontstack}/{range}.pbf',
          sprite: 'https://protomaps.github.io/basemaps-assets/sprites/v4/dark',
          sources: {
              protomaps: {
                  type: 'vector',
                  url: 'https://api.protomaps.com/tiles/v4.json?key=f1d93c3bd5c79742',
                  attribution: '<a href="https://protomaps.com">Protomaps</a> © <a href="https://openstreetmap.org">OpenStreetMap</a>'
              }
          },
          layers: baseMap
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
    background-color: #000;
  }

  :global(.maplibregl-popup-content) {
    background-color: #000;
    border: 1px solid #000;
    color: #fff;
  }

  :global(.maplibregl-popup-anchor-top .maplibregl-popup-tip) {
    border-bottom-color: #000;
  }

  :global(.maplibregl-popup-anchor-bottom .maplibregl-popup-tip) {
    border-top-color: #000;
  }

  :global(.maplibregl-popup-anchor-left .maplibregl-popup-tip) {
    border-right-color: #000;
  }

  :global(.maplibregl-popup-anchor-right .maplibregl-popup-tip) {
    border-left-color: #000;
  }

  :global(.popup-title) {
    margin: 0 0 4px 0;
    font-size: 14px;
    font-weight: 600;
    color: #fff;
  }

  :global(.popup-subtitle) {
    margin: 0 0 8px 0;
    font-size: 11px;
    color: #fff;
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
    color: #fff;
  }

  :global(.popup-change-row) {
    border-top: 1px solid var(--brandGray70);
    padding-top: 8px;
  }

  :global(.popup-change-label) {
    font-size: 10px;
    color: #fff;
  }

  :global(.popup-change-value) {
    font-size: 14px;
    font-weight: 700;
  }
</style>
