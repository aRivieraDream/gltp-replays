#!/bin/bash

# Update package list
sudo apt-get update

# Install Python and pip if not already installed
sudo apt-get install -y python3 python3-pip

# Install Chrome dependencies
sudo apt-get install -y wget unzip xvfb libxi6 libgconf-2-4

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
wget -N "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}"
CHROMEDRIVER_VERSION=$(cat "LATEST_RELEASE_${CHROME_VERSION}")
wget -N "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -o chromedriver_linux64.zip
chmod +x chromedriver
sudo mv -f chromedriver /usr/local/bin/chromedriver
rm chromedriver_linux64.zip "LATEST_RELEASE_${CHROME_VERSION}"

# Install Python dependencies
pip3 install -r requirements.txt

# Setup systemd service
sudo cp tagpro-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tagpro-bot
sudo systemctl start tagpro-bot

# Create log directory
mkdir -p logs 