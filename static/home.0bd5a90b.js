import { dataUrl, setupNavigation } from './shared.97137a2a.js';
import { MapsTable } from './maps.00e83aba.js';
import { Leaderboard, processLeaderboardData } from './leaderboard.a6bf37e4.js';

// Load presets
const presets = await fetch(`./presets.json`)
    .then(response => response.json());
const mapMetadata = await fetch(`./map_metadata.json`)
    .then(response => response.json());

// Setup navigation
setupNavigation();

// Fetch and process data
fetch(dataUrl)
  .then(response => response.json())
  .then(data => {
    // Process data for both maps and leaderboards
    const {
      gamesCompletedLeaderboard,
      worldRecordsLeaderboard,
      soloWorldRecordsLeaderboard,
      cappingWorldRecordsLeaderboard,
      bestRecords,
      recordsByMap
    } = processLeaderboardData(data);

    // Initialize and render maps table
    const mapsTable = new MapsTable(presets, recordsByMap, mapMetadata);
    const recordsArray = Object.values(bestRecords);
    recordsArray.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    mapsTable.render(recordsArray);

    // Initialize and render leaderboards
    const leaderboard = new Leaderboard();
    leaderboard.render(
      worldRecordsLeaderboard,
      soloWorldRecordsLeaderboard,
      cappingWorldRecordsLeaderboard,
      gamesCompletedLeaderboard
    );
  })
  .catch(error => console.error("Error fetching data:", error)); 