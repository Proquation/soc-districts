<script>
  import './assets/global.css';
  import Map from './lib/components/Map.svelte';
  import SidePanel from './lib/components/SidePanel.svelte';

  // App state using Svelte 5 runes
  let selectedCity = $state('San Francisco');
  let selectedTypes = $state([]); // empty = all types

  // Available district types (will be populated from data)
  let districtTypes = ['Historic District', 'Arts District', 'Business District', 'Tax District', 'Infrastructure District'];

  function handleCityChange(city) {
    selectedCity = city;
  }

  function handleTypeFilterChange(types) {
    selectedTypes = types;
  }
</script>

<main>
  <div class="sidebar-shell">
    <SidePanel
      {selectedCity}
      {selectedTypes}
      {districtTypes}
      onCityChange={handleCityChange}
      onTypeFilterChange={handleTypeFilterChange}
    />
  </div>
  <div class="map-shell">
    <Map
      {selectedCity}
      {selectedTypes}
    />
  </div>
</main>

<style>
  main {
    display: flex;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar-shell {
    width: var(--sidebar-width, 360px);
    height: 100%;
    flex: 0 0 var(--sidebar-width, 360px);
  }

  .map-shell {
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
  }

  .map-shell :global(.map-container) {
    height: 100%;
  }

  @media (max-width: 900px) {
    main {
      flex-direction: column-reverse;
    }

    .sidebar-shell {
      width: 100%;
      height: auto;
      flex: 0 0 clamp(220px, 38vh, 360px);
    }

    .map-shell {
      width: 100%;
      flex: 1 1 auto;
    }
  }
</style>
