import { getLeaderboardPlayerKey, getLeaderboardPlayerDisplayName } from './shared.97137a2a.js';

export class Leaderboard {
  constructor() {
    this.leaderboardContainer = document.getElementById('leaderboardContainer');
  }

  render(worldRecordsLeaderboard, soloWorldRecordsLeaderboard, cappingWorldRecordsLeaderboard, gamesCompletedLeaderboard) {
    this.leaderboardContainer.innerHTML = "";

    this.createSection("Overall World Records", worldRecordsLeaderboard);
    this.createSection("Solo Records", soloWorldRecordsLeaderboard);
    this.createSection("Capping Records", cappingWorldRecordsLeaderboard);
    this.createSection("Games Completed", gamesCompletedLeaderboard);
  }

  createSection(title, leaderboardObj) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = "leaderboard-section";
    const table = document.createElement('table');
    table.className = "leaderboard-table";

    // Create title row
    const titleRow = document.createElement('tr');
    const titleCell = document.createElement('th');
    titleCell.textContent = title;
    titleCell.colSpan = 2;
    titleCell.className = "leaderboard-title";
    titleRow.appendChild(titleCell);
    table.appendChild(titleRow);

    // Create header row
    const headerRow = document.createElement('tr');
    const nameHeader = document.createElement('th');
    nameHeader.textContent = "Name";
    const scoreHeader = document.createElement('th');
    scoreHeader.textContent = "Score";
    headerRow.appendChild(nameHeader);
    headerRow.appendChild(scoreHeader);
    table.appendChild(headerRow);

    // Sort and add player rows
    let playersArray = Object.values(leaderboardObj)
      .filter(player => this.shouldShow(player))
      .sort((a, b) => b.score - a.score);

    playersArray.forEach(player => {
      const row = document.createElement('tr');
      const nameCell = document.createElement('td');
      nameCell.textContent = player.name;
      const scoreCell = document.createElement('td');
      scoreCell.textContent = player.score;
      row.appendChild(nameCell);
      row.appendChild(scoreCell);
      table.appendChild(row);
    });

    sectionDiv.appendChild(table);
    this.leaderboardContainer.appendChild(sectionDiv);
  }

  shouldShow(player) {
    return true;
  }
}

export function processLeaderboardData(data) {
  let gamesCompletedLeaderboard = {};
  let worldRecordsLeaderboard = {};
  let soloWorldRecordsLeaderboard = {};
  let cappingWorldRecordsLeaderboard = {};
  let bestRecords = {};
  let recordsByMap = {};

  // Process each record
  data.forEach(record => {
    if (record.record_time !== null) {
      // Update games completed leaderboard
      const seenForGame = new Set();
      record.players.forEach(player => {
        let key = getLeaderboardPlayerKey(player);
        let displayName = getLeaderboardPlayerDisplayName(player);
        let hasPlayerId = (player.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(player.name));
        if (!seenForGame.has(key)) {
          if (!gamesCompletedLeaderboard[key]) {
            gamesCompletedLeaderboard[key] = { name: displayName, score: 0, hasPlayerId: hasPlayerId };
          }
          gamesCompletedLeaderboard[key].score += 1;
          seenForGame.add(key);
        }
      });

      // Update best record per map
      if (!bestRecords[record.map_name] || record.record_time < bestRecords[record.map_name].record_time) {
        bestRecords[record.map_name] = record;
      }

      // Group records for each map
      if (!recordsByMap[record.map_name]) {
        recordsByMap[record.map_name] = [];
      }
      recordsByMap[record.map_name].push(record);
    }
  });

  // Update leaderboards using best records
  Object.values(bestRecords).forEach(record => {
    // Update overall world records leaderboard
    const seenForRecord = new Set();
    record.players.forEach(player => {
      let key = getLeaderboardPlayerKey(player);
      let displayName = getLeaderboardPlayerDisplayName(player);
      let hasPlayerId = (player.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(player.name));
      if (!seenForRecord.has(key)) {
        if (!worldRecordsLeaderboard[key]) {
          worldRecordsLeaderboard[key] = { name: displayName, score: 0, hasPlayerId: hasPlayerId };
        }
        worldRecordsLeaderboard[key].score += 1;
        seenForRecord.add(key);
      }
    });

    // Update solo records leaderboard
    if (record.is_solo) {
      const seenForSolo = new Set();
      record.players.forEach(player => {
        let key = getLeaderboardPlayerKey(player);
        let displayName = getLeaderboardPlayerDisplayName(player);
        let hasPlayerId = (player.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(player.name));
        if (!seenForSolo.has(key)) {
          if (!soloWorldRecordsLeaderboard[key]) {
            soloWorldRecordsLeaderboard[key] = { name: displayName, score: 0, hasPlayerId: hasPlayerId };
          }
          soloWorldRecordsLeaderboard[key].score += 1;
          seenForSolo.add(key);
        }
      });
    }

    // Update capping records leaderboard
    if (record.capping_player) {
      const dummyPlayer = { name: record.capping_player, user_id: record.capping_player_user_id };
      let key = getLeaderboardPlayerKey(dummyPlayer);
      let displayName = getLeaderboardPlayerDisplayName(dummyPlayer);
      let hasPlayerId = (dummyPlayer.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(dummyPlayer.name));
      if (!cappingWorldRecordsLeaderboard[key]) {
        cappingWorldRecordsLeaderboard[key] = { name: displayName, score: 0, hasPlayerId: hasPlayerId };
      }
      cappingWorldRecordsLeaderboard[key].score += 1;
    }
  });

  // Sort each map's records by time
  for (let map in recordsByMap) {
    recordsByMap[map].sort((a, b) => a.record_time - b.record_time);
  }

  return {
    gamesCompletedLeaderboard,
    worldRecordsLeaderboard,
    soloWorldRecordsLeaderboard,
    cappingWorldRecordsLeaderboard,
    bestRecords,
    recordsByMap
  };
} 