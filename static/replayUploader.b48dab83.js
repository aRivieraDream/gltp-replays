import { parseReplayFromReplayLink, parseReplayFromUUID} from './replayParser.a4387366.js';

// creates the UI for the upload WR replay button, and 
class ReplayUploader {
    constructor() {
        this.modal = document.getElementById('uploadModal');
        this.uploadButton = document.getElementById('uploadWrButton');
        this.cancelButton = document.getElementById('cancelUpload');
        this.submitButton = document.getElementById('submitReplayUrl');
        this.urlInput = document.getElementById('replayUrlInput');
        this.errorMessage = null;
        this.isSubmitting = false;
        this.resultsContainer = null;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Show modal
        this.uploadButton.addEventListener('click', () => {
            this.showModal();
        });

        // Cancel button
        this.cancelButton.addEventListener('click', () => {
            if (!this.isSubmitting) {
                this.hideModal();
            }
        });

        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.modal && !this.isSubmitting) {
                this.hideModal();
            }
        });

        // Handle form submission
        this.submitButton.addEventListener('click', () => {
            this.handleSubmit();
        });

        // Handle Enter key in input
        this.urlInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !this.isSubmitting) {
                this.handleSubmit();
            }
        });
    }

    showModal() {
        this.modal.style.display = 'block';
        this.urlInput.focus();
        this.clearError();
        this.setSubmitting(false);
        
        // Keep results hidden when showing modal
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }

    hideModal() {
        this.modal.style.display = 'none';
        this.urlInput.value = '';
        this.clearError();
        this.setSubmitting(false);
        
        // Hide results when closing modal
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }

    showError(message) {
        this.clearError();
        this.errorMessage = document.createElement('div');
        this.errorMessage.className = 'error-message';
        this.errorMessage.textContent = message;
        this.urlInput.parentElement.insertBefore(this.errorMessage, this.urlInput.nextSibling);
    }

    clearError() {
        if (this.errorMessage) {
            this.errorMessage.remove();
            this.errorMessage = null;
        }
    }

    // Disable the submit button and the input field when submitting
    setSubmitting(isSubmitting) {
        this.isSubmitting = isSubmitting;
        this.submitButton.disabled = isSubmitting;
        this.cancelButton.disabled = isSubmitting;
        this.urlInput.disabled = isSubmitting;
        
        if (isSubmitting) {
            this.submitButton.textContent = 'Submitting...';
            this.submitButton.classList.add('submitting');
        } else {
            this.submitButton.textContent = 'Submit';
            this.submitButton.classList.remove('submitting');
        }
    }

    // Validate the URL has the correct prefix
    validateUrl(url) {
        const validPrefix = 'https://tagpro.koalabeast.com/';
        if (url.startsWith(validPrefix)) {
            if (url.includes('replay=')) {
                return 'replay';
            }
            if (url.includes('uuid=')) {
                return 'uuid';
            }
            // URL looks like this: https://tagpro.koalabeast.com/game?replay=aBqgmEYJ6LRbiauGZTv8/iW0XY1d3tCp 
        }
        
        // validate if input matches a UUID format
        const uuidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;
        if (uuidRegex.test(url)) {
            return 'uuid';
        }
        throw new Error('URLs should include either replay=/uuid= or be a valid UUID. Go to the replay page and copy the URL from the replay you want to validate');
    }

    async loadReplayResults() {
        try {
            // Use a path that will work both locally and on GitHub Pages
            const basePath = window.location.hostname === 'localhost' ? '' : '/GLTP';
            const response = await fetch(`${basePath}/html/replay_results.html`);
            const html = await response.text();
            return html;
        } catch (error) {
            console.error('Error loading replay results component:', error);
            return null;
        }
    }

    updateUI(data) {
        // Display the results container
        document.getElementById('replayContent').style.display = 'block';
        document.getElementById('loadingMessage').style.display = 'none';

        // Update record time (highlighted)
        document.getElementById('recordTime').querySelector('span').textContent = data.record_time || "Not available";

        // Update map information
        document.getElementById('mapName').textContent = data.map_name || "Unknown";
        document.getElementById('mapAuthor').textContent = data.map_author || "Unknown";
        document.getElementById('mapId').textContent = data.effective_map_id || "Unknown";
        document.getElementById('capsToWin').textContent = data.caps_to_win === Infinity ? "Special" : data.caps_to_win;
        document.getElementById('allowBlueCaps').textContent = data.allow_blue_caps ? "Yes" : "No";

        // Update replay details
        document.getElementById('uuid').textContent = data.uuid || "Unknown";
        document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleString() || "Unknown";
        document.getElementById('cappingPlayer').textContent = data.capping_player || "Unknown";
        document.getElementById('soloStatus').textContent = data.is_solo ? "Yes" : "No";
        document.getElementById('playerQuote').textContent = data.capping_player_quote || "None";

        // Update players table
        const tableBody = document.getElementById('playerTableBody');
        tableBody.innerHTML = '';

        data.players.forEach(player => {
            const row = document.createElement('tr');
            if (player.name === data.capping_player) {
                row.classList.add('capping-player');
            }

            const nameCell = document.createElement('td');
            nameCell.textContent = player.name;

            const teamCell = document.createElement('td');
            teamCell.textContent = player.is_red ? 'Red' : 'Blue';
            teamCell.classList.add(player.is_red ? 'team-red' : 'team-blue');

            const userIdCell = document.createElement('td');
            userIdCell.textContent = player.user_id || '-';

            row.appendChild(nameCell);
            row.appendChild(teamCell);
            row.appendChild(userIdCell);

            tableBody.appendChild(row);
        });

        // Update JSON view
        document.getElementById('jsonOutput').textContent = JSON.stringify(data, null, 2);
    }

    async displayReplayResults(parsedData) {
        // Load and insert the replay results HTML if not already present
        if (!this.resultsContainer) {
            const replayResults = await this.loadReplayResults();
            if (replayResults) {
                // Insert after the form, but keep the form visible
                const modalForm = this.modal.querySelector('.modal-form');
                modalForm.insertAdjacentHTML('afterend', replayResults);
                this.resultsContainer = document.getElementById('results');
                
                // Initialize tab functionality after inserting the HTML
                this.initializeTabs();
            }
        }

        // Show the results container and update UI with parsed data
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
            this.updateUI(parsedData);
        }
        
        // Reset submitting state after displaying results
        this.setSubmitting(false);
    }

    // Add this new method to handle tab functionality
    initializeTabs() {
        const tabButtons = this.resultsContainer.querySelectorAll('.tab-btn');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and content
                this.resultsContainer.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.resultsContainer.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });

                // Add active class to clicked button and corresponding content
                button.classList.add('active');
                const tabId = button.getAttribute('data-tab');
                this.resultsContainer.querySelector(`#${tabId}-view`).classList.add('active');
            });
        });
    }

    validateInput(input) {
        if (!input) {
            throw new Error('Please enter a URL');
        }
        if (!input)
        return true;
    }

    async handleSubmit() {
        if (this.isSubmitting) return;
        
        const url = this.urlInput.value.trim();
        if (!url) return;

        try {
            this.setSubmitting(true);
            const type = this.validateUrl(url);
            if (type === 'replay') {
                // First get the parsed data
                const parsedData = await parseReplayFromReplayLink(url);
                console.log('Parsed data:', parsedData);
                
                // Then display the results with the parsed data
                await this.displayReplayResults(parsedData);
            } else if (type === 'uuid') {
                const parsedData = await parseReplayFromUUID(url);
                await this.displayReplayResults(parsedData);
            }
            
            // Show success message in the results area instead of the modal
            if (this.resultsContainer) {
                const successMessage = document.createElement('div');
                successMessage.className = 'success-message';
                successMessage.textContent = 'Replay submitted successfully!';
                this.resultsContainer.insertBefore(successMessage, this.resultsContainer.firstChild);
                
                // Remove success message after a delay
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
            }
        } catch (error) {
            this.showError(error.message);
            this.setSubmitting(false);
        }
    }
} 

export { ReplayUploader };