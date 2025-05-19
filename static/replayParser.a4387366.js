// Make String.prototype.rsplit available
if (!String.prototype.rsplit) {
    String.prototype.rsplit = function (sep, maxsplit) {
        const split = this.split(sep);
        return maxsplit ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit)) : split;
    };
}

// Tab functionality
document.addEventListener('DOMContentLoaded', function () {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            // Remove active class from all buttons and content
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId + '-view').classList.add('active');
        });
    });
});

function extractUUID(input) {
    const uuidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;
    const match = input.match(uuidRegex);
    return match ? match[0] : null;
}


// takes a UUID and returns an array of JSON objects for each line in the replay file
async function fetchReplay(uuid) {
    const proxyUrl = "https://corsproxy.io/?";
    const metadataResponse = await fetch(`${proxyUrl}https://tagpro.koalabeast.com/replays/data?uuid=${uuid}`);
    if (!metadataResponse.ok) throw new Error("Failed to fetch metadata, make sure you're using the UUID");

    const metadata = await metadataResponse.json();
    if (!metadata.games || metadata.games.length !== 1) {
        throw new Error("Unexpected replay format");
    }

    const gameId = metadata.games[0].id;
    const gameResponse = await fetch(`${proxyUrl}https://tagpro.koalabeast.com/replays/gameFile?gameId=${gameId}`);
    if (!gameResponse.ok) throw new Error("Failed to fetch replay data");

    const text = await gameResponse.text();
    const lines = text.trim().split("\n").map(line => JSON.parse(line));
    return lines;
}

function formatMilliseconds(milliseconds) {
    const minutes = Math.floor(milliseconds / 60000);
    const seconds = (milliseconds % 60000) / 1000;
    return `${minutes}:${seconds.toFixed(3).padStart(6, '0')}`;
}

async function fetchMaps() {
    const response = await fetch("https://docs.google.com/spreadsheets/d/1OnuTCekHKCD91W39jXBG4uveTCCyMxf9Ofead43MMCU/export?format=csv&gid=1775606307");
    if (!response.ok) throw new Error("Failed to fetch map data");

    const csvText = await response.text();

    function parseCSV(text) {
        const rows = [];
        let row = [], field = '';
        let inQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i], next = text[i + 1];

            if (inQuotes) {
                if (char === '"' && next === '"') {
                    field += '"'; i++; // Escaped quote
                } else if (char === '"') {
                    inQuotes = false;
                } else {
                    field += char;
                }
            } else {
                if (char === '"') {
                    inQuotes = true;
                } else if (char === ',') {
                    row.push(field); field = '';
                } else if (char === '\n') {
                    row.push(field); rows.push(row);
                    row = []; field = '';
                } else if (char === '\r') {
                    continue;
                } else {
                    field += char;
                }
            }
        }
        if (field || row.length) {
            row.push(field);
            rows.push(row);
        }
        return rows;
    }

    const rows = parseCSV(csvText);
    const headers = rows.shift().map(h => h.trim());

    const get = (row, header) => {
        const index = headers.findIndex(h => h === header);
        return index !== -1 ? row[index]?.trim() || "" : "";
    };

    // Inject map ID into preset like in your Python
    function injectMapIdIntoPreset(preset, mapId) {
        const digits = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
        let n = parseInt(mapId, 10);
        let enc = n === 0 ? digits[0] : "";
        while (n) {
            const r = n % 52;
            n = Math.floor(n / 52);
            enc = digits[r] + enc;
        }
        const inner = "f" + enc;
        const inj = "M" + digits[inner.length] + inner;
        const pos = preset.indexOf("M");
        if (pos === -1) return preset;
        const oldLen = digits.indexOf(preset[pos + 1]);
        return preset.slice(0, pos) + inj + preset.slice(pos + 2 + oldLen);
    }

    const allMaps = rows.map(row => ({
        name: get(row, "Map / Player"),
        preset: get(row, "Group Preset"),
        difficulty: get(row, "Final Rating"),
        fun: get(row, "Final Fun \nRating"),
        category: get(row, "Category"),
        map_id: get(row, "Map ID"),
        equivalent_map_ids: get(row, "Pseudo \nMap ID").split(","),
        caps_to_win: get(row, "Num\nof caps"),
        allow_blue_caps: get(row, "Allow Blue Caps").toUpperCase() === "TRUE",
        balls_req: get(row, "Min\nBalls \nRec"),
        max_balls_rec: get(row, "Max\nBalls\nRec")
    })).filter(m => m.preset && m.preset.trim());

    const illegalMapIds = new Set(
        allMaps.filter(m =>
            !m.preset.trim() ||
            !m.map_id ||
            injectMapIdIntoPreset(m.preset, m.map_id) !== m.preset
        ).map(m => m.map_id)
    );

    return allMaps.filter(m => !illegalMapIds.has(m.map_id));
}

function cleanMapName(name) {
    const parts = name.rsplit(" by ", 1);
    return parts.length === 2 && parts[1].length <= 100 ? parts[0] : name;
}

function getDetails(replay, maps) {
    if (replay[0][1] !== "recorder-metadata" || replay[2][1] !== "map" || replay[3][1] !== "clientInfo") {
        throw new Error("Invalid replay format");
    }

    const metadata = replay[0][2];
    const mapData = replay[2][2];
    const mapfile = replay[3][2]?.mapfile;
    const mapId = mapfile ? mapfile.split("/")[1] : null;

    const players = {};
    metadata.players.forEach(player => {
        players[player.id] = {
            name: player.displayName,
            user_id: player.userId,
            is_red: player.team === 1
        };
    });

    const firstTimerTs = replay.find(r => r[1] === 'time' && r[2]?.state === 1)?.[0] ?? 0;

    let recordTime = null;
    let cappingUserName = null;
    let cappingUserId = null;
    let cappingPlayerQuote = null;

    // Get the caps_to_win from the maps
    let matchedMap = maps.find(m => m.map_id === mapId);
    if (!matchedMap) {
        matchedMap = maps.find(m => m.equivalent_map_ids.includes(String(mapId)));
    }

    let capsToWin = 1;  // Default to 1 if no map is matched
    if (matchedMap) {
        const capsRaw = matchedMap.caps_to_win;
        capsToWin = capsRaw === "pups" ? Infinity : parseInt(capsRaw || "1", 10);
    }

    // Look for the timestamp when the correct s-captures value is reached (equal to capsToWin)
    for (const [ts, type, data] of replay) {
        if (type !== 'p') continue;

        for (const playerData of data) {
            const captures = playerData["s-captures"];
            if (captures !== capsToWin) continue;  // Only proceed if s-captures matches capsToWin

            const cappingPlayer = players[playerData.id];
            if (!cappingPlayer) continue;

            // Record the time and player info
            recordTime = ts - firstTimerTs;
            cappingUserName = cappingPlayer.name;
            cappingUserId = cappingPlayer.user_id;

            // Capture player chat (if any)
            const playerChats = replay.filter(r => r[1] === 'chat' && r[2].from === playerData.id);
            cappingPlayerQuote = playerChats.length ? playerChats[playerChats.length - 1][2].message : null;

            // Break the loop once the first matching capture is found
            break;
        }
        if (recordTime !== null) break;
    }

    return {
        map_name: mapData.info.name,
        map_author: mapData.info.author,
        players: Object.values(players),
        capping_player: cappingUserName,
        capping_player_user_id: cappingUserId,
        record_time: recordTime !== null ? formatMilliseconds(recordTime) : null,
        is_solo: Object.keys(players).length === 1,
        timestamp: metadata.started,
        uuid: metadata.uuid,
        capping_player_quote: cappingPlayerQuote,
        caps_to_win: capsToWin,
        allow_blue_caps: matchedMap ? matchedMap.allow_blue_caps : false,
        effective_map_id: mapId
    };
}



function showError(message) {
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('replayContent').style.display = 'none';
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = "Error: " + message;
    errorElement.style.display = 'block';
}


// Convert the URL to one that can be used to generate a replay file
function convertURL(url) {
    // URL looks like this: https://tagpro.koalabeast.com/game?replay=aBqgmEYJ6LRbiauGZTv8/iW0XY1d3tCp 
    // We need to conver the URL to https://tagpro.koalabeast.com/replays/gameFile?key=Z9/286ZugYquoKwYZ_ayjg7lzK42ipHD
    if (url.includes('replay=')) {
        const id = url.split('replay=')[1];
        const convertedUrl = `https://tagpro.koalabeast.com/replays/gameFile?key=${id}`;
        console.log('Converted URL:', convertedUrl);
        return convertedUrl;
    } else {
        throw new Error("Invalid URL");
    }
}

// takes a URL and returns a replay JSON
// URL format: https://tagpro.koalabeast.com/replays/gameFile?key=aBqgmEYJ6LRbiauGZTv8/iW0XY1d3tCp
async function getReplayData(url) {
    const convertedUrl = convertURL(url);
    let response;
    
    // Try direct fetch first
    try {
        response = await fetch(convertedUrl, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'text/plain',  // Changed to expect text
                'Origin': window.location.origin
            },
            credentials: 'omit'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    } catch (fetchError) {
        console.log('Direct fetch failed, trying with proxy...');
        
        // Try multiple CORS proxies in case one fails
        const proxies = [
            'https://corsproxy.io/?',
            'https://cors-anywhere.herokuapp.com/',
            'https://api.allorigins.win/raw?url='
        ];
        
        let proxyError = null;
        
        // Try each proxy until one works
        for (const proxy of proxies) {
            try {
                const proxyUrl = `${proxy}${convertedUrl}`;
                response = await fetch(proxyUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': 'text/plain',  // Changed to expect text
                        'Origin': window.location.origin
                    }
                });
                
                if (response.ok) {
                    console.log('Successfully fetched replay data from proxy:', proxy);
                    break;  // Success! Exit the loop
                }
            } catch (error) {
                proxyError = error;
                console.log(`Proxy ${proxy} failed, trying next...`);
                continue;
            }
        }
        
        // If all proxies failed
        if (!response || !response.ok) {
            throw new Error(`All fetch attempts failed. Last error: ${proxyError?.message || 'Unknown error'}`);
        }
    }

    try {
        // Get the response as text instead of JSON
        const text = await response.text();
        console.log('Replay data received, length:', text.length);
        return text;  // Return the text directly
    } catch (parseError) {
        throw new Error(`Failed to read replay data: ${parseError.message}`);
    }
}

// takes raw replay JSON and returns an array of JSON objects for each line in the replay file
function formatReplayData(data) {
    const lines = data.trim().split("\n").map(line => JSON.parse(line));
    return lines;
}

async function parseReplayFromReplayLink(url) {
    const data = await getReplayData(url);
    const lines = formatReplayData(data);
    const maps = await fetchMaps();
    const details = getDetails(lines, maps);
    return details;
}


async function parseReplayFromUUID(uuidLink) {
    const input = uuidLink;
    try {
        const uuid = extractUUID(input) || input;
        const replay = await fetchReplay(uuid);
        const maps = await fetchMaps();
        const details = getDetails(replay, maps);
        return details;
    } catch (error) {
        showError(error.message);
        console.error(error);
    }
}

export { parseReplayFromUUID, parseReplayFromReplayLink};

