// Define navigation items - keep this structure as it's useful
const navItems = {
  home: { linkId: 'homeLink', pageId: 'homePage' },
  standings: { linkId: 'standingsLink', pageId: 'standingsPage' },
  ofm: { linkId: 'ofmLink', pageId: 'ofmPage' },
  bounties: { linkId: 'bountiesLink', pageId: 'bountiesPage' },
  links: { linkId: 'linksLink', pageId: 'linksPage' },
  week1: { linkId: 'week1Link', pageId: 'week1Page' },
  week2: { linkId: 'week2Link', pageId: 'week2Page' },
  week3: { linkId: 'week3Link', pageId: 'week3Page' },
  rosters: { linkId: 'rostersLink', pageId: 'rostersPage' },
  season1: { linkId: 'season1Link', pageId: 'season1Page' },
};

// Data storage for all loaded content
let seasonData = null;

// Set up navigation event listeners
Object.entries(navItems).forEach(([key, { linkId, pageId }]) => {
  document.getElementById(linkId).addEventListener('click', () => {
    if (key === 'home') {
      window.location.href = '/GLTP/';
      return;
    }
    if (key === 'season1') {
      window.location.href = '/GLTP/S1/home.html';
      return;
    }
    window.location.hash = key;
    showPage(pageId, linkId);
  });
});

// Show/hide pages and update active state for navigation
function showPage(pageId, linkId) {
  // Hide all pages and remove active class from all links
  Object.values(navItems).forEach(({ pageId }) => {
    const page = document.getElementById(pageId);
    if (page) page.classList.remove('active');
  });

  Object.values(navItems).forEach(({ linkId }) => {
    const link = document.getElementById(linkId);
    if (link) link.classList.remove('active');
  });

  // Show selected page and mark link as active
  const page = document.getElementById(pageId);
  const link = document.getElementById(linkId);
  if (page) page.classList.add('active');
  if (link) link.classList.add('active');
}

async function loadStaticContent(elementId, htmlPath) {
  const version = window.BUILD_VERSION || Date.now(); // fallback to current timestamp
  const cacheBustedPath = `${htmlPath}?v=${version}`;
  const response = await fetch(cacheBustedPath);
  const html = await response.text();
  document.getElementById(elementId).innerHTML = html;
}

// Main function to fetch and parse JSON data
function fetchSeasonData() {
  fetch(`season2data.json?v=${window.BUILD_VERSION}`)
    .then(res => res.json())
    .then(data => {
      seasonData = data;

      // Calculate points for all teams
      calculateAllTeamPoints(data);

      // Render content for each page based on JSON data
      loadPageContent('homeContent', data.pages?.home?.content || "Home content not found.");
      loadPageContent('season1Content', data.pages?.season1?.content || "Season 1 content not found.");

      // Load static content
      loadStaticContent('ofmContent', 'ofm.html');
      loadStaticContent('bountiesContent', 'bounties.html');
      loadStaticContent('linksContent', 'gltp_links.html');

      // Handle week content - check if data exists first
      if (data.week1 && data.week1.length > 0) {
        renderWeekContent('week1Content', data.week1);
      } else {
        loadStaticContent('week1Content', 'S2W1.html');
      }

      if (data.week2 && data.week2.length > 0) {
        renderWeekContent('week2Content', data.week2);
      } else {
        loadStaticContent('week2Content', 'S2W2.html');
      }

      if (data.week3 && data.week3.length > 0) {
        renderWeekContent('week3Content', data.week3);
      } else {
        loadStaticContent('week3Content', 'S2W3.html');
      }

      // Render standings and rosters
      renderStandings('standingsContent', data.teams);
      renderRosters('rosterContent', data.teams);

      // Add event listeners after content is loaded
      enableToggleListeners();
    })
    .catch(err => {
      console.error("Error loading season2data.json:", err);
      document.getElementById('standingsContent').innerHTML = "Failed to load season data.";
    });
}

// Calculate points for all teams
function calculateAllTeamPoints(data) {
  // Initialize point counters for all teams
  data.teams.forEach(team => {
    team["Completion\nPoints"] = 0;
    team["Speedrun\nPoints"] = 0;
    team["Week1\nPoints"] = 0;
    team["Week2\nPoints"] = 0;
    team["Week3\nPoints"] = 0;
    team["Total\nPoints"] = 0;
    team.bounties = 0;
  });

  // Calculate points for each week
  if (data.week1 && data.week1.length > 0) {
    calculateWeekPoints(data.teams, data.week1, 1);
  }

  if (data.week2 && data.week2.length > 0) {
    calculateWeekPoints(data.teams, data.week2, 2);
  }

  if (data.week3 && data.week3.length > 0) {
    calculateWeekPoints(data.teams, data.week3, 3);
  }

  if (data.bounties && data.bounties.length > 0) {
    calculateBountyPoints(data.teams, data.bounties);
  }

  // Calculate total points
  data.teams.forEach(team => {
    team["Total\nPoints"] = team["Completion\nPoints"] + team["Speedrun\nPoints"] + team.bounties;
  });
}

// Calculate points for a specific week
function calculateWeekPoints(teams, weekData, weekNumber) {
  teams.forEach(team => {
    let weekCompletionPoints = 0;
    let weekSpeedrunPoints = 0;

    weekData.forEach(map => {
      // Calculate completion points
      const completionPoints = calculateCompletionPoints(team.name, map);
      weekCompletionPoints += completionPoints;

      // Calculate speedrun points
      const speedrunPoints = calculateSpeedrunPoints(team.name, map);
      weekSpeedrunPoints += speedrunPoints;
    });

    // Update team data
    team["Completion\nPoints"] += weekCompletionPoints;
    team["Speedrun\nPoints"] += weekSpeedrunPoints;
    team[`Week${weekNumber}\nPoints`] = weekCompletionPoints + weekSpeedrunPoints;
  });
}

// Calculate points for a specific week
function calculateBountyPoints(teams, bountyData) {
  teams.forEach(team => {
    let bountyCompletionPoints = 0;

    bountyData.forEach(map => {
      // Calculate completion points
      const completionPoints = calculateCompletionPoints(team.name, map);
      bountyCompletionPoints += completionPoints;
    });

    // Update team data
    team.bounties += bountyCompletionPoints;
  });
}


// Calculate completion points for a team on a specific map
function calculateCompletionPoints(teamName, map) {
  const hasCompleted = teamCompletedMap(teamName, map);
  return hasCompleted ? map.points : 0;
}

// Calculate speedrun points for a team on a specific map
function calculateSpeedrunPoints(teamName, map) {
  const speedrunRank = teamSpeedrunRank(teamName, map);
  return speedrunRank ? getPointsForRank(speedrunRank) : 0;
}

// Helper function to load simple page content
function loadPageContent(containerId, content) {
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = content;
  }
}

function getValidSortedSpeedruns(speedruns) {
  // Filter out speedruns that should not be included
  const validRuns = speedruns
    .filter(run => run.includeOnSpeedrun === "yes")
    .sort((a, b) => timeStringToSeconds(a.time) - timeStringToSeconds(b.time));

  return validRuns;
}

// Render weekly content (maps and speedruns)
function renderWeekContent(containerId, weekData) {
  const container = document.getElementById(containerId);
  if (!container || !weekData) return;

  let weekNumber = containerId.replace('week', '').replace('Content', '');
  let html = `<h1>GLTP Season 2 Week ${weekNumber} Maps</h1>`;

  // Create maps table
  html += `
  <table style="width: 100%; table-layout: fixed;">
    <colgroup>
      <col style="width: 13%;">
      <col style="width: 24%;">
      <col style="width: 28%;">
      <col style="width: 15%;">
      <col style="width: 5%;">
      <col style="width: 9%;">
      <col style="width: 6%;">
    </colgroup>
    <tr>
      <th>Map</th>
      <th>Group Preset</th>
      <th>Speedrun Group Preset</th>
      <th>Settings</th>
      <th>Points</th>
      <th>Fastest Time <br> points</th>
      <th>Difficulty <br> Rank</th>
    </tr>
  `;

  // Add each map to the table
  weekData.forEach(map => {
    html += `
    <tr>
      <td><a href="${map.link}" target="_blank">${map.mapName} <br> by ${map.author} </a> <br><br> ${map.recommendedBalls} balls recommended</td>
      <td>
        <span class="map-id">${map.preset}</span> <br> <br>
        <button class="copy-button" onclick="copyMapID(this)">Copy Preset</button>
        <button class="open-button" onclick="openMap(this)">Launch Group</button>
      </td>
      <td>
        <span class="map-id">${map.speedrunPreset}</span> <br> <br>
        <button class="copy-button" onclick="copyMapID(this)">Copy Preset</button>
        <button class="open-button" onclick="openMap(this)">Launch Group</button>
      </td>
      <td>${map.settings.replace(/\n/g, "<br>")}</td>
      <td>${map.points}</td>
      <td>${map.fastestPoints.replace(/\n/g, "<br>")}</td>
      <td>${map.difficulty}</td>
    </tr>
    `;
  });

  html += `</table><h1>Speedruns</h1>`;

  // Add speedrun tables for each map
  weekData.forEach(map => {
    html += `
    <table>
      <tr>
        <th class="centered" colspan="6">${map.mapName}</th>
      </tr>
      <tr>
        <th>Rank</th>
        <th>Time</th>
        <th>Players</th>
        <th>Team</th>
        <th>Replay</th>
        <th>Points</th>
      </tr>
    `;

    // Add speedrun entries if they exist
    if (map.speedruns && map.speedruns.length > 0) {
      const validRuns = getValidSortedSpeedruns(map.speedruns);

      validRuns.forEach((run, index) => {
        const points = getPointsForRank(index + 1);
        const replayLinks = `
        <a href="${run.replay}" target="_blank">Link</a>
        ${run.youtube ? `<br><a href="${run.youtube}" target="_blank">YouTube</a>` : ''}
      `;

        html += `
          <tr>
            <td>${index + 1}</td>
            <td>${run.time}</td>
            <td>${Array.isArray(run.players) ? run.players.join('<br>') : run.players}</td>
            <td>${run.team}</td>
            <td>${replayLinks}</td>
            <td>${points}</td>
          </tr>
        `;
      });
    } else if (map.speedruns && map.speedruns.length == 0) {
      // Add an empty row for aesthetics
      html += `
        <tr>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td><a href="#">Link</a></td>
          <td></td>
        </tr>
      </table>
      `;
    }
  });

  container.innerHTML = html;
}

// Render standings table and team details
function renderStandings(containerId, teamsData) {
  const container = document.getElementById(containerId);
  if (!container || !teamsData) return;

  // Sort teams by total points descending
  const sortedTeams = [...teamsData].sort((a, b) =>
    b["Total\nPoints"] - a["Total\nPoints"]
  );

  let html = `<h2 class="white-header">GLTP Season 2 Standings</h2>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Team</th>
        <th>Total Points</th>
        <th>Completion Points</th>
        <th>Speedrun Points</th>
        <th>Week1 Points</th>
        <th>Week2 Points</th>
        <th>Week3 Points</th>
        <th>Bounties</th>
      </tr>
    </thead>
    <tbody>`;

  // Add each team's standings
  sortedTeams.forEach((team, index) => {
    html += `
      <tr>
        <td>${index + 1}</td>
        <td>${team.name}</td>
        <td>${team["Total\nPoints"]}</td>
        <td>${team["Completion\nPoints"]}</td>
        <td>${team["Speedrun\nPoints"]}</td>
        <td>${team["Week1\nPoints"]}</td>
        <td>${team["Week2\nPoints"]}</td>
        <td>${team["Week3\nPoints"]}</td>
        <td>${team.bounties}</td>
      </tr>
    `;
  });

  html += `</tbody></table>`;

  // Add collapsible sections for each team's points
  teamsData.forEach(team => {
    const teamIdSafe = team.name.toLowerCase().replace(/\s+/g, '-');

    html += `
    <h2 class="toggle-header" data-toggle-target="${teamIdSafe}-points-table">
      <span class="arrow">▶</span>${team.name} Points
    </h2>
    <div id="${teamIdSafe}-points-table" class="toggle-section" style="display: none;">
      <table>
        <thead>
          <tr>
            <th>Week</th>
            <th>Map</th>
            <th>Completion</th>
            <th>Speedrun</th>
            <th>CPoints</th>
            <th>SPoints</th>
          </tr>
        </thead>
        <tbody>
    `;

    // Loop through each week's maps
    const weeks = ['week1', 'week2', 'week3'];

    weeks.forEach(weekKey => {
      if (seasonData && seasonData[weekKey]) {
        const weekNumber = weekKey.replace('week', '');

        seasonData[weekKey].forEach((map, idx) => {
          // Check if team completed this map (has a speedrun entry)
          const hasCompleted = teamCompletedMap(team.name, map);
          const speedrunRank = teamSpeedrunRank(team.name, map);
          const completionPoints = hasCompleted ? map.points : 0;
          const speedrunPoints = speedrunRank ? getPointsForRank(speedrunRank) : 0;

          html += `
          <tr>
            <td>${weekNumber}</td>
            <td><a href="${map.link}" target="_blank">${map.mapName}</a></td>
            <td>${hasCompleted ?
              '<i class="fas fa-check green-icon" aria-label="Yes"></i>' :
              '<i class="fas fa-times red-icon" aria-label="No"></i>'}</td>
            <td>${speedrunRank ? getMedalForRank(speedrunRank) :
              '<i class="fas fa-times red-icon" aria-label="No"></i>'}</td>
            <td>${completionPoints}</td>
            <td>${speedrunPoints}</td>
          </tr>
          `;
        });
      }
    });

    html += `</tbody></table></div>`;
  });

  container.innerHTML = html;
}

// Helper function to check if a team completed a map
function teamCompletedMap(teamName, map) {
  // Check if the team has a speedrun entry for this map
  return map.speedruns && map.speedruns.some(run => run.team === teamName);
}

function timeStringToSeconds(timeStr) {
  if (timeStr.includes(':')) {
    const parts = timeStr.split(':');
    if (parts.length === 3) {
      // Format is "hh:mm:ss.ms" or similar
      const [hours, minutes, seconds] = parts;
      return parseInt(hours, 10) * 3600 + parseInt(minutes, 10) * 60 + parseFloat(seconds);
    } else if (parts.length === 2) {
      // Format is "mm:ss.ms" or similar
      const [minutes, seconds] = parts;
      return parseInt(minutes, 10) * 60 + parseFloat(seconds);
    }
  }
  // Format is just seconds (e.g. "40.123")
  return parseFloat(timeStr);
}

// Helper function to get a team's speedrun rank on a map
function teamSpeedrunRank(teamName, map) {
  if (!map.speedruns) return null;

  const validRuns = getValidSortedSpeedruns(map.speedruns);

  // Find the team's position in the valid, sorted runs
  for (let i = 0; i < validRuns.length; i++) {
    if (validRuns[i].team === teamName) {
      return i + 1; // Return 1-based rank
    }
  }

  return null; // Team didn't have a valid run
}

// Helper function to get medal emoji based on rank
function getMedalForRank(rank) {
  const medals = ['🥇', '🥈', '🥉'];
  return rank <= 3 ? medals[rank - 1] : '<i class="fas fa-times red-icon" aria-label="Not top 3"></i>';
}

// Helper function to get points based on rank
// Using the fastestPoints logic: 1st = 2 points, 2nd = 1 point
function getPointsForRank(rank) {
  return rank === 1 ? 2 : rank === 2 ? 1 : 0;
}

// Render team rosters
function renderRosters(containerId, teamsData) {
  const container = document.getElementById(containerId);
  if (!container || !teamsData) return;

  let html = `
  <table>
    <tr>
      <th class="title" colspan="${teamsData.length}">Season 2 GLTP Rosters</th>
    </tr>
    <tr>
  `;

  // Add team names as headers
  teamsData.forEach(team => {
    html += `<th>${team.name}</th>`;
  });

  html += `</tr>`;

  // Determine the maximum roster size
  const maxRosterSize = Math.max(...teamsData.map(team => team.roster.length));

  // Create rows for each player position
  for (let i = 0; i < maxRosterSize; i++) {
    html += `<tr>`;

    teamsData.forEach(team => {
      if (i === 0) {
        // First player is captain (with gold icon)
        html += team.roster[i] ?
          `<td><img src="http://i.imgur.com/U3KTppv.png" alt="icon" style="height: 1em; vertical-align: middle; margin-right: 5px;">${team.roster[i]}</td>` :
          `<td></td>`;
      } else if (i < team.roster.length) {
        // Regular players with silver icon
        html += `<td><img src="http://i.imgur.com/Qw987lA.png" alt="icon" style="height: 1em; vertical-align: middle; margin-right: 5px;">${team.roster[i]}</td>`;
      } else {
        // Empty cells for teams with fewer players
        html += `<td></td>`;
      }
    });

    html += `</tr>`;
  }

  html += `</table>`;

  container.innerHTML = html;
}

// Event listener setup for collapsible sections
function enableToggleListeners() {
  document.querySelectorAll('.toggle-header').forEach(header => {
    header.addEventListener('click', () => {
      const targetId = header.getAttribute('data-toggle-target');
      const target = document.getElementById(targetId);
      const arrow = header.querySelector('.arrow');

      if (target) {
        const isHidden = target.style.display === 'none' || getComputedStyle(target).display === 'none';
        target.style.display = isHidden ? 'block' : 'none';
        if (arrow) arrow.textContent = isHidden ? '▼' : '▶';
      }
    });
  });
}

// Copy map ID to clipboard
function copyMapID(button) {
  const span = button.parentElement.querySelector('.map-id');
  const mapId = span.textContent;
  if (mapId && mapId !== "N/A") {
    navigator.clipboard.writeText(mapId).then(() => {
      button.textContent = "✅";
      button.classList.add("copied");
      setTimeout(() => {
        button.textContent = "Copy Preset";
        button.classList.remove("copied");
      }, 1500);
    }).catch(err => console.error("Error copying map:", err));
  }
}

// Open map in a new tab
function openMap(button) {
  const span = button.parentElement.querySelector('.map-id');
  const mapId = span.textContent;
  if (mapId && mapId !== "N/A") {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "https://tagpro.koalabeast.com/groups/create";
    form.target = "_blank";

    const nameInput = document.createElement("input");
    nameInput.type = "hidden";
    nameInput.name = "name";
    nameInput.value = "GLTP IS THE BEST";

    const privateInput = document.createElement("input");
    privateInput.type = "hidden";
    privateInput.name = "private";
    privateInput.value = "on";

    const presetInput = document.createElement("input");
    presetInput.type = "hidden";
    presetInput.name = "preset";
    presetInput.value = mapId;

    form.appendChild(nameInput);
    form.appendChild(privateInput);
    form.appendChild(presetInput);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  }
}

// Toggle dropdown menu
function toggleDropdown() {
  document.getElementById("dropdownContent").classList.toggle("show");
}

// Close dropdown when clicking outside
window.addEventListener("click", function (e) {
  if (!e.target.matches('.dropbtn')) {
    const dropdown = document.getElementById("dropdownContent");
    if (dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
    }
  }
});

// Initialize page on load
document.addEventListener('DOMContentLoaded', () => {
  // Determine which page to show based on URL hash
  const hash = window.location.hash.slice(1);
  if (navItems[hash]) {
    const { pageId, linkId } = navItems[hash];
    showPage(pageId, linkId);
  } else {
    const { pageId, linkId } = navItems['standings'];
    showPage(pageId, linkId);
  }

  // Fetch all data from JSON and render pages
  fetchSeasonData();
});
