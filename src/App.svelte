<script>
  import './assets/global.css';
  import Map from './lib/components/Map.svelte';
  import SidePanel from './lib/components/SidePanel.svelte';

  // App state using Svelte 5 runes
  let selectedCity = $state('San Francisco');
  let valueType = $state('normalized'); // 'raw' or 'normalized'
  let selectedTypes = $state([]); // empty = all types

  // Available district types (will be populated from data)
  let districtTypes = ['Historic District', 'Arts District', 'Tax District', 'Infrastructure District'];

  function handleCityChange(city) {
    selectedCity = city;
  }

  function handleValueTypeChange(type) {
    valueType = type;
  }

  function handleTypeFilterChange(types) {
    selectedTypes = types;
  }
</script>

<main>
  <SidePanel
    {selectedCity}
    {valueType}
    {selectedTypes}
    {districtTypes}
    onCityChange={handleCityChange}
    onValueTypeChange={handleValueTypeChange}
    onTypeFilterChange={handleTypeFilterChange}
  />
  <Map
    {selectedCity}
    {valueType}
    {selectedTypes}
  />
</main>

<style>
  main {
    display: flex;
    width: 100%;
    height: 100vh;
  }
</style>
