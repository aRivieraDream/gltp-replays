import { dataUrl, setupNavigation } from './shared.97137a2a.js';
import { MapsTable } from './maps.00e83aba.js?v=20241220';
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
    console.log('🔧 Creating MapsTable...');
    const mapsTable = new MapsTable(presets, recordsByMap, mapMetadata);
    console.log('🔧 MapsTable created, recordsByMap:', recordsByMap);
    console.log('🔧 bestRecords:', bestRecords);
    
    const recordsArray = Object.values(bestRecords);
    recordsArray.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    console.log('🔧 Calling mapsTable.render with', recordsArray.length, 'records');
    mapsTable.render(recordsArray);
    console.log('🔧 render() completed');

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