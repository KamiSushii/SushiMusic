<img src="https://raw.githubusercontent.com/KamiSushii/SushiMusic/main/logo.png" alt="beat-logo" width="15%" align="right">

# SushiMusic
**SushiMusic** is a Pycord rewrite of [**Beat**](https://github.com/Knedme/Beat) by [Knedme](https://github.com/Knedme).

## 🌌 Current Version
Current bot version is **1.0.1**.

## 📚 Commands

### /join
The bot joins to your voice channel.

### /play youtube-video-link | spotify-link | search-query
The bot joins to your voice channel and plays music from a link or search query.

### /lofi
The bot joins to your channel and plays lofi.

### /leave
Leave the voice channel.

### /skip
Skips current song.

### /pause
Pauses current song.

### /resume
Resumes current song if it is paused.

### /queue
Shows current queue.

### /control
Shows player control menu.

### /now-playing
Shows what song is playing now.

### /loop
Enables/Disables Queue/Track loop.

### /shuffle
Shuffles next songs in the queue.

### /commands
Shows a list of commands.

### /info 
Shows information about the bot.

## ⬇️ Getting started

### 1. Install Python 3.10.7

### 2. Clone this repo
Install Git and run this command in the terminal:
```commandline
git clone https://github.com/KamiSushii/SushiMusic.git
```

### 3. Install the dependencies
Run this command in the terminal in the cloned Beat folder:
````commandline
pip install -r requirements.txt
````

### 4. Install the FFmpeg on your OS

### 5. Get cookies.txt file
To do this, just google something like `How to get cookies.txt file in <your-browser-name>`

### 6. Create a Spotify application
Follow [this link](https://developer.spotify.com/dashboard/applications) and create there an application.

### 7. Change the bot config
Set the `TOKEN`, `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
Open `<bot-folder>/bot/misc/config.py` file in any text editor and define there path to FFmpeg executable file and cookies.txt file path.

### 8. Run the bot
Open terminal in the cloned Beat folder and run the bot:
```commandline
python run.py
```
