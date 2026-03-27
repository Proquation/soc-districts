<script>
  // Props using Svelte 5 syntax
  let {
    selectedCity = 'San Francisco',
    valueType = 'normalized',
    selectedTypes = [],
    districtTypes = [],
    onCityChange = () => {},
    onValueTypeChange = () => {},
    onTypeFilterChange = () => {}
  } = $props();

  // Cities available
  const cities = ['San Francisco', 'Washington'];

  // Handle city button click
  function selectCity(city) {
    onCityChange(city);
  }

  // Handle value type toggle
  function selectValueType(type) {
    onValueTypeChange(type);
  }

  // Handle type filter checkbox
  function toggleTypeFilter(type) {
    // If clicking the already selected type, deselect it (show all)
    if (selectedTypes.length === 1 && selectedTypes[0] === type) {
      onTypeFilterChange([]);
    } else {
      // Otherwise, select only this type
      onTypeFilterChange([type]);
    }
  }

  // Handle "All" button
  function selectAllTypes() {
    onTypeFilterChange([]);
  }
</script>

<aside class="side-panel">
  <header>
    <h1>District Comparison</h1>
    <p class="subtitle">2019 vs 2025 Activity Changes</p>
  </header>

  <section class="filter-section">
    <h2>Select City</h2>
    <div class="button-group">
      {#each cities as city}
        <button
          class="city-button"
          class:selected={selectedCity === city}
          on:click={() => selectCity(city)}
        >
          {city === 'Washington' ? 'Washington D.C.' : city}
        </button>
      {/each}
    </div>
  </section>

  <section class="filter-section">
    <h2>Value Type</h2>
    <div class="button-group">
      <button
        class="type-button"
        class:selected={valueType === 'normalized'}
        on:click={() => selectValueType('normalized')}
      >
        Normalized
      </button>
      <button
        class="type-button"
        class:selected={valueType === 'raw'}
        on:click={() => selectValueType('raw')}
      >
        Raw Difference
      </button>
    </div>
    <p class="description">
      {#if valueType === 'raw'}
        Shows the absolute change in total stops between 2019 and 2025.
      {:else}
        Shows normalized percent change from 2019 to 2025.
      {/if}
    </p>
  </section>

  <section class="filter-section">
    <h2>District Types</h2>
    <div class="button-group">
      <button
        class="type-button"
        class:selected={selectedTypes.length === 0}
        on:click={selectAllTypes}
      >
        All
      </button>
      {#each districtTypes as type}
        <button
          class="type-button"
          class:selected={selectedTypes.length === 1 && selectedTypes[0] === type}
          on:click={() => toggleTypeFilter(type)}
        >
          {type.replace(' District', '')}
        </button>
      {/each}
    </div>
    <p class="description">
      {#if selectedTypes.length === 0}
        Showing all district types.
      {:else}
        Filtering by: {selectedTypes.join(', ')}
      {/if}
    </p>
  </section>

  <section class="legend-section">
    <h2>Legend</h2>
    <div class="legend">
      <div class="gradient-bar"></div>
      <div class="legend-labels">
        <span>Decrease</span>
        <span>No Change</span>
        <span>Increase</span>
      </div>
    </div>
  </section>

  <footer>
    <p>Data: <a href="https://cuebiq.com/">Cuebiq</a> mobile phone activity stops</p>
    <p>Map: <a href="https://carto.com/" target="_blank" rel="noopener">CARTO</a> &amp; <a href="https://openstreetmap.org/" target="_blank" rel="noopener">OpenStreetMap</a></p>
  </footer>
</aside>

<style>
  .side-panel {
    width: var(--sidebar-width, 360px);
    height: 100vh;
    background-color: var(--brand-dark-bg, #111a1a);
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
    border-right: 1px solid var(--brand-gray-70, rgba(148, 146, 138, 0.3));
  }

  header h1 {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 4px;
    color: var(--brand-white, #fff);
  }

  .subtitle {
    font-size: 0.9rem;
    color: var(--brand-gray, #94928a);
  }

  h2 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--brand-white, #fff);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .filter-section,
  .legend-section,
  .info-section {
    padding-bottom: 15px;
    border-bottom: 1px solid var(--brand-gray-70, rgba(148, 146, 138, 0.3));
  }

  .button-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .city-button,
  .type-button {
    flex: 1;
    min-width: 120px;
    padding: 10px 16px;
    border: 1px solid var(--brand-gray, #94928a);
    border-radius: 6px;
    background-color: transparent;
    color: var(--brand-white, #fff);
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s ease;
    opacity: 0.6;
    cursor: pointer;
  }

  .type-button {
    min-width: 80px;
    padding: 8px 12px;
    font-size: 0.85rem;
  }

  .city-button:hover,
  .type-button:hover {
    background-color: var(--brand-dark-blue, #1e3765);
    opacity: 1;
  }

  .city-button.selected,
  .type-button.selected {
    background-color: var(--brand-medium-blue, #007fa3);
    border-color: var(--brand-light-blue, #6fc7ea);
    opacity: 1;
  }

  .description {
    font-size: 0.8rem;
    color: var(--brand-gray, #94928a);
    margin-top: 8px;
    line-height: 1.4;
  }

  .legend {
    padding: 10px 0;
  }

  .gradient-bar {
    height: 20px;
    border-radius: 4px;
    background: linear-gradient(
      to right,
      #d73027 0%,
      #fc8d59 25%,
      #ffffbf 50%,
      #91cf60 75%,
      #1a9850 100%
    );
    margin-bottom: 6px;
  }

  .legend-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--brand-gray, #94928a);
  }

  .district-info {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 12px;
  }

  .district-info h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--brand-white, #fff);
  }

  .district-type {
    font-size: 0.8rem;
    color: var(--brand-light-blue, #6fc7ea);
    margin-bottom: 12px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .stat {
    display: flex;
    flex-direction: column;
  }

  .stat.full-width {
    grid-column: span 2;
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--brand-gray, #94928a);
    margin-bottom: 2px;
  }

  .stat-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--brand-white, #fff);
  }

  .stat-value.increase {
    color: #91cf60;
  }

  .stat-value.decrease {
    color: #fc8d59;
  }

  .stat-value.neutral {
    color: #ffffbf;
  }

  .hover-hint {
    font-style: italic;
    color: var(--brand-gray, #94928a);
    text-align: center;
    padding: 20px;
  }

  footer {
    margin-top: auto;
    padding-top: 15px;
    font-size: 0.75rem;
    color: var(--brand-gray, #94928a);
  }

  footer p {
    margin-bottom: 4px;
  }

  footer a {
    color: var(--brand-light-blue, #6fc7ea);
  }
</style>
