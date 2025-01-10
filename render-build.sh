#!/usr/bin/env bash

# Update package list and install dependencies
apt-get update && apt-get install -y wget unzip

# Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Cleanup
rm google-chrome-stable_current_amd64.deb
