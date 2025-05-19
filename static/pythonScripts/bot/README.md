# Install
- 1) install chromium and chromedriver per your distros instructions
- 2) `pip install selenium requests rapidfuzz`

# Run
In the directory with `leader.py` and `maps.py`:

`python3 leader.py` 

# VM Setup
### Instance:
Name: group-bot-1234 (use the number of iteration we're on)
Instance: e2-micro
Boot Disk: Ubuntu 22.04 LTS (jammy) - avoiding other builds for esoteric reasons
Firewall: Allow HTTP and HTTPS traffic

### SSH into the VM and run basic commands:
`sudo apt update`
`sudo apt upgrade -y`
`sudo apt install -y git python3 python3-pip`
`sudo apt install tmux` - used to handle running the bot after closing the shell. Should already be installed


### Installations:
Chromium --> `sudo apt install -y chromium-browser chromium-chromedriver`
The code --> `git clone https://github.com/BambiTP/GLTP.git` 
`cd GLTP/src/pythonScripts/bot`
`pip3 install -r requirements.txt`

### Run the Bot
`tmux`
`python3 leader.py`