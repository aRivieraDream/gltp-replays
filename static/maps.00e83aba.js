import {
    formatTime,
    formatRelativeTime,
    getMapsPlayerKey,
    getMapsPlayerDisplayName,
    launchTagproGroup
} from './shared.97137a2a.js';
import { ReplayUploader } from './replayUploader.b48dab83.js';

export class MapsTable {
    constructor(presets, recordsByMap, mapMetadata) {
        this.presets = presets;
        this.recordsByMap = recordsByMap;
        this.mapMetadata = mapMetadata;
        this.currentSort = {
            property: "timestamp",
            direction: "desc"
        };
        this.mapsTableBody = document.getElementById('mapsTableBody');
        this.setupSorting();
        this.setupSearch();
        this.setupFilters();
        this.replayUploader = new ReplayUploader();
        this.allRecords = []; // Store the full, unfiltered list
    }

    setupFilters() {
        // Ensure this is linked to the correct filter
        this.gravityFilter = document.getElementById('gravityFilter');
        // Listen for filter changes
        this.gravityFilter.addEventListener('change', () => this.applyFilters());
    }

    applyFilters() {
        const grav_or_classic = document.getElementById('gravityFilter').value.toLowerCase();
        const searchTerm = document.getElementById('mapSearch').value.toLowerCase().trim();

        const filtered = this.allRecords.filter(record => {
            const metadata = this.mapMetadata[record.map_name] || {};

            const mapType = (metadata.grav_or_classic || "").toLowerCase();
            const matchesType = grav_or_classic === '' || mapType === grav_or_classic;

            const matchesSearch =
                record.map_name.toLowerCase().includes(searchTerm) ||
                (record.capping_player && record.capping_player.toLowerCase().includes(searchTerm));

            return matchesType && matchesSearch;
        });

        this.recordsArray = filtered;
        this.mapsTableBody.innerHTML = "";
        filtered.forEach(record => this.renderRow(record));
    }

    setupSorting() {
        const thElements = document.querySelectorAll("#mapsTable thead th");
        thElements.forEach(th => {
            const sortProperty = th.getAttribute("data-sort");
            const sortType = th.getAttribute("data-type");
            if (sortProperty && sortType) {
                th.style.cursor = "pointer";
                th.addEventListener("click", () => {
                    this.sortRecords(sortProperty, sortType);
                });
            }
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('mapSearch');
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase().trim();
            if (searchTerm === '') {
                this.render(this.allRecords); // Reset to full list
            } else {
                this.filterRecords(searchTerm);
            }
        });

        // Add clear button functionality
        const clearButton = document.getElementById('search-clear');

        const searchContainer = searchInput.parentElement;
        searchContainer.style.position = 'relative';

        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            gravityFilter.value = '';
            this.render(this.allRecords);
            this.applyFilters();
            clearButton.style.display = 'none';
            searchInput.focus();
        });

        searchInput.addEventListener('input', () => {
            clearButton.style.display = searchInput.value ? 'block' : 'none';
            this.applyFilters();
        });
    }

    setupUploadModal() {
        const modal = document.getElementById('uploadModal');
        const uploadButton = document.getElementById('uploadWrButton');
        const cancelButton = document.getElementById('cancelUpload');
        const submitButton = document.getElementById('submitReplayUrl');
        const urlInput = document.getElementById('replayUrlInput');

        // Show modal
        uploadButton.addEventListener('click', () => {
            modal.style.display = 'block';
            urlInput.focus();
        });

        // Hide modal
        const hideModal = () => {
            modal.style.display = 'none';
            urlInput.value = '';
        };

        // Cancel button
        cancelButton.addEventListener('click', hideModal);

        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                hideModal();
            }
        });

        // Handle form submission
        submitButton.addEventListener('click', () => {
            const url = urlInput.value.trim();
            if (url) {
                // TODO: Handle the URL submission
                console.log('Submitting URL:', url);
                hideModal();
            }
        });

        // Handle Enter key in input
        urlInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                submitButton.click();
            }
        });
    }

    filterRecords(searchTerm) {
        const filteredRecords = this.allRecords.filter(record =>
            record.map_name.toLowerCase().includes(searchTerm) ||
            (record.capping_player && record.capping_player.toLowerCase().includes(searchTerm))
        );
        this.recordsArray = filteredRecords;
        this.mapsTableBody.innerHTML = "";
        filteredRecords.forEach(record => this.renderRow(record));
    }

    sortRecords(property, type) {
        if (this.currentSort.property === property) {
            this.currentSort.direction = (this.currentSort.direction === "asc" ? "desc" : "asc");
        } else {
            this.currentSort.property = property;
            this.currentSort.direction = "asc";
        }

        this.recordsArray.sort((a, b) => {
            let aVal, bVal;

            // Handle metadata fields
            if (property === "difficulty" || property === "balls_req") {
                const aMetadata = this.mapMetadata[a.map_name] || {};
                const bMetadata = this.mapMetadata[b.map_name] || {};
                aVal = aMetadata[property] || "N/A";
                bVal = bMetadata[property] || "N/A";
            } else {
                aVal = a[property];
                bVal = b[property];
            }

            if (property === "capping_player") {
                aVal = aVal || "DNF";
                bVal = bVal || "DNF";
            }

            if (type === "numeric") {
                if (property === "timestamp") {
                    const aTime = new Date(aVal).getTime();
                    const bTime = new Date(bVal).getTime();
                    return this.currentSort.direction === "asc" ? aTime - bTime : bTime - aTime;
                } else {
                    // Convert to numbers for numeric sorting, handling "N/A" cases
                    const aNum = aVal === "N/A" ? -1 : parseFloat(aVal);
                    const bNum = bVal === "N/A" ? -1 : parseFloat(bVal);
                    return this.currentSort.direction === "asc" ? aNum - bNum : bNum - aNum;
                }
            } else {
                aVal = aVal ? aVal.toLowerCase() : "";
                bVal = bVal ? bVal.toLowerCase() : "";
                if (aVal < bVal) return this.currentSort.direction === "asc" ? -1 : 1;
                if (aVal > bVal) return this.currentSort.direction === "asc" ? 1 : -1;
                return 0;
            }
        });
        this.render(this.recordsArray);
    }

    render(records) {
        this.allRecords = records; // Always keep the full list up to date
        this.recordsArray = records;
        this.mapsTableBody.innerHTML = "";
        records.forEach(record => this.renderRow(record));
    }

    renderRow(record) {
        const tr = document.createElement('tr');
        tr.className = "map-row";

        // Map Name cell with clickable details toggle
        const mapNameCell = document.createElement('td');
        mapNameCell.className = "map-name";
        mapNameCell.textContent = record.map_name;

        // Create detail section
        const detailDiv = document.createElement('div');
        detailDiv.className = "detail";
        detailDiv.style.display = "none";

        // Create left detail section
        const leftDetailDiv = document.createElement('div');
        leftDetailDiv.className = "left-detail";

        // Add date information
        const dateDiv = document.createElement('div');
        dateDiv.textContent = "Date: " + new Date(record.timestamp).toLocaleDateString();
        leftDetailDiv.appendChild(dateDiv);

        // Add replay link
        const replayLink = document.createElement('a');
        replayLink.href = `https://tagpro.koalabeast.com/replays?uuid=${record.uuid}`;
        replayLink.textContent = "Watch Replay";
        replayLink.target = "_blank";
        leftDetailDiv.appendChild(replayLink);

        // Add players list
        const playersDiv = document.createElement('div');
        playersDiv.textContent = "Players: ";
        const uniquePlayers = [];
        const seenPlayers = new Set();
        record.players.forEach(player => {
            let key = getMapsPlayerKey(player);
            if (!seenPlayers.has(key)) {
                seenPlayers.add(key);
                uniquePlayers.push(player);
            }
        });
        uniquePlayers.forEach((player, index) => {
            if (player.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(player.name)) {
                const playerLink = document.createElement('a');
                playerLink.href = `https://tagpro.koalabeast.com/profile/${player.user_id}`;
                playerLink.textContent = getMapsPlayerDisplayName(player);
                playersDiv.appendChild(playerLink);
            } else {
                const span = document.createElement('span');
                span.textContent = getMapsPlayerDisplayName(player);
                playersDiv.appendChild(span);
            }
            if (index < uniquePlayers.length - 1) {
                playersDiv.appendChild(document.createTextNode(", "));
            }
        });
        leftDetailDiv.appendChild(playersDiv);

        // Add preset and map ID info
        const infoDiv = document.createElement('div');
        const presetValue = this.presets[record.map_name] || "N/A";
        infoDiv.textContent = "Preset: " + presetValue + " | Map ID: " + record.map_id;
        leftDetailDiv.appendChild(infoDiv);

        // Add capping player quote if exists
        if (record.capping_player_quote) {
            const quoteDiv = document.createElement('div');
            quoteDiv.className = "capping-player-quote";
            quoteDiv.textContent = `"${record.capping_player_quote}"`;
            leftDetailDiv.appendChild(quoteDiv);
        }

        // Add copy preset button
        const copyButton = document.createElement('button');
        copyButton.textContent = "Copy Preset";
        copyButton.classList.add("copy-button");
        copyButton.addEventListener('click', (event) => {
            event.stopPropagation();
            if (presetValue !== "N/A") {
                navigator.clipboard.writeText(presetValue)
                    .then(() => {
                        copyButton.textContent = "Copied!";
                        copyButton.classList.add("copied");
                        setTimeout(() => {
                            copyButton.textContent = "Copy Preset";
                            copyButton.classList.remove("copied");
                        }, 2000);
                    })
                    .catch(err => console.error("Error copying preset:", err));
            }
        });
        leftDetailDiv.appendChild(copyButton);

        // Add launch group button
        const launchButton = document.createElement('button');
        launchButton.textContent = "Launch Group";
        launchButton.classList.add("copy-button");
        launchButton.addEventListener('click', (event) => {
            event.stopPropagation();
            if (presetValue !== "N/A") {
                launchTagproGroup(presetValue);
            }
        });
        leftDetailDiv.appendChild(launchButton);

        // Create medal panel
        const medalPanelDiv = document.createElement('div');
        medalPanelDiv.className = "medal-panel";

        // Add top 3 records
        const mapRecords = this.recordsByMap[record.map_name] || [];
        const top3Records = mapRecords.slice(0, 3);
        const medalLabels = ["1st", "2nd", "3rd"];
        const medalColors = ["#FFD700", "#C0C0C0", "#CD7F32"]; // gold, silver, bronze

        top3Records.forEach((rec, index) => {
            const replayLinkMedal = document.createElement('a');
            replayLinkMedal.href = `https://tagpro.koalabeast.com/replays?uuid=${rec.uuid}`;
            replayLinkMedal.target = "_blank";
            replayLinkMedal.className = "medal-link";

            const medalRow = document.createElement('div');
            medalRow.className = "medal-row";
            medalRow.style.borderColor = medalColors[index];

            const medalLabelSpan = document.createElement('span');
            medalLabelSpan.className = "medal-label";
            medalLabelSpan.style.color = medalColors[index];
            medalLabelSpan.textContent = medalLabels[index];

            const timeSpan = document.createElement('span');
            timeSpan.textContent = formatTime(rec.record_time);
            timeSpan.className = "medal-time";
            timeSpan.style.color = medalColors[index];

            medalRow.appendChild(medalLabelSpan);
            medalRow.appendChild(timeSpan);
            replayLinkMedal.appendChild(medalRow);
            medalPanelDiv.appendChild(replayLinkMedal);
        });

        // Create detail wrapper
        const detailWrapper = document.createElement('div');
        detailWrapper.className = "detail-wrapper";
        detailWrapper.appendChild(leftDetailDiv);
        detailWrapper.appendChild(medalPanelDiv);
        detailDiv.appendChild(detailWrapper);

        // Add click handler for map name
        mapNameCell.addEventListener('click', function () {
            detailDiv.style.display = detailDiv.style.display === "none" ? "block" : "none";
        });
        mapNameCell.appendChild(detailDiv);
        tr.appendChild(mapNameCell);

        // Add time cell
        const timeCell = document.createElement('td');
        timeCell.textContent = formatTime(record.record_time);
        tr.appendChild(timeCell);

        // Add relative time cell
        const relativeTimeCell = document.createElement('td');
        relativeTimeCell.textContent = formatRelativeTime(record.timestamp);
        tr.appendChild(relativeTimeCell);

        // Add capping player cell
        const capCell = document.createElement('td');
        if (record.capping_player) {
            const dummyPlayer = { name: record.capping_player, user_id: record.capping_player_user_id };
            if (dummyPlayer.user_id && !/^Some Ball(?:\s*\d+)?$/i.test(dummyPlayer.name)) {
                const capLink = document.createElement('a');
                capLink.href = `https://tagpro.koalabeast.com/profile/${dummyPlayer.user_id}`;
                capLink.textContent = getMapsPlayerDisplayName(dummyPlayer);
                capCell.appendChild(capLink);
            } else {
                capCell.textContent = getMapsPlayerDisplayName(dummyPlayer);
            }
        } else {
            capCell.textContent = "DNF";
        }
        tr.appendChild(capCell);

        // Add difficulty cell
        const difficultyCell = document.createElement('td');
        const metadata = this.mapMetadata[record.map_name] || {};
        difficultyCell.textContent = metadata.difficulty || "N/A";
        tr.appendChild(difficultyCell);

        // Add balls required cell
        const ballsReqCell = document.createElement('td');
        ballsReqCell.textContent = metadata.balls_req || "N/A";
        tr.appendChild(ballsReqCell);

        this.mapsTableBody.appendChild(tr);
    }
}
