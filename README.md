NekoGPT
===
NekoGPT is a neko girl! Welcome to chat with me!
You can also set up this discord robot by yourself.

Invite me: https://nekogpt.cocomine.cc/ <br>
*Power by ChatGPT3*
<hr>

# How to deploy

## Docker (Recommended)
### Step 1: Install docker
Check out the official website: https://docs.docker.com/engine/install/
To install docker on your server.

### Step 2: Pull image
Run follow command to pull the latest image.
```bash 
docker pull cocomine/nekogpt:latest
```

### Step 3: Create .env file and edit it
3.1: Create a .env file.
```bash
touch .env
```
3.2: Open the .env file and enter the following
```dotenv
DISCORD_TOKEN=
CHATGPT_TOKEN=
BOT_NAME=
SPEECH_KEY=
SPEECH_REGION=
```

3.3: Fill in the corresponding information in the .env file.
- DISCORD_TOKEN: Your discord bot token. 
  - You can get it from https://discord.com/developers/applications
  - Learn more: https://discordpy.readthedocs.io/en/stable/discord.html
- CHATGPT_TOKEN: Your ChatGPT3 token.
    - Read the following documents for information: https://github.com/acheong08/ChatGPT/wiki/Authentication
- BOT_NAME: The name of your bot.
- SPEECH_KEY and SPEECH_REGION are used to convert text to speech.
    - You can get it from https://speech.microsoft.com/portal

### Step 4: Run the following command to start the bot.
```bash
docker run -d --name neko-gpt --env-file .env cocomine/nekogpt:latest --restart=always ---mount type=bind,source=/path/to/your/data/folder,target=/database
```
- Replace `/path/to/your/data/folder` with the path to the folder where you want to store the database.
- This folder will be used to store the database, so you can use it to back up the database.

### Step 5: Invite your bot to your server
You can use the following link to invite your bot to your server.
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274881562688&scope=bot
```
- Replace `YOUR_CLIENT_ID` with your bot's client ID.
- You can get it from https://discord.com/developers/applications
- Learn more: https://discordpy.readthedocs.io/en/stable/discord.html

### Step 6: Enjoy!

<hr>

## Local installation
### Step 1: Clone this repository
```bash
git clone https://github.com/cocomine/NekoGPT.git
```

### Step 2: Install gstreamer
#### Ubuntu
```bash
sudo apt install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
```
#### Arch Linux
```bash
sudo pacman -S gstreamer gst-plugins-good gst-plugins-bad gst-plugins-ugly
```
#### Windows
Download and install from https://gstreamer.freedesktop.org/download/

### Step 3: Install ffmpeg
#### Ubuntu
```bash
sudo apt install ffmpeg
```
#### Arch Linux
```bash
sudo pacman -S ffmpeg
```
#### Windows
Download and install from https://ffmpeg.org/download.html <br>
Make sure to add ffmpeg to your **PATH**. <br>
Learn more: https://www.wikihow.com/Install-FFmpeg-on-Windows

### Step 4: Install requirements
```bash
pip3 install -r requirements.txt
```

### Step 5: Create .env file and edit it
Read [step 3](#step-3-create-env-file-and-edit-it) in the docker installation.

### Step 6: Run the bot
```bash
python3 main.py
```

### Step 7: Invite your bot to your server
Read [step 5](#step-5-invite-your-bot-to-your-server) in the docker installation.

### Step 8: Enjoy!