NekoGPT
===
NekoGPT is a neko girl! Welcome to chat with me!
You can also set up this discord robot by yourself.

**🚧IMPORTANT NOTICE: This discord bot has stopped maintenance due to a major dependent library ceasing maintenance.🚧**

Invite me: https://nekogpt.cocomine.cc/ <br>
*Power by ChatGPT3*
<hr>

# How to deploy

## Docker (Recommended)
### Step 1: Install docker
Check out the official website: https://docs.docker.com/engine/install/
To install docker on your server.

### Step 2: Install docker-compose Plugin
Check out the official website: https://docs.docker.com/compose/install/
To install docker-compose on your server.

### Step 3: Download docker-compose-tamplate
Download [docker-compose-tamplate](/docker-compose-tamplate.yml) into your server.

### Step 3: Edit docker-compose-tamplate
Open the **docker-compose-tamplate** file and edit following content.
```YAML
environment:
    # Please fill up following environment variables
    - BOT_NAME=NekoGPT
    - CHATGPT_TOKEN=
    - DISCORD_TOKEN=
    - SPEECH_KEY=
    - SPEECH_REGION=
    - CHATGPT_BASE_URL=
```

3.1: Fill in the corresponding information in the file.
- DISCORD_TOKEN: Your discord bot token. 
  - You can get it from https://discord.com/developers/applications
  - Learn more: https://discordpy.readthedocs.io/en/stable/discord.html
- CHATGPT_TOKEN: Your ChatGPT3 token.
    - Read the following documents for information: https://github.com/acheong08/ChatGPT/wiki/Authentication
- BOT_NAME: The name of your bot.
- SPEECH_KEY and SPEECH_REGION are used to convert text to speech.
    - You can get it from https://speech.microsoft.com/portal

3.2: Replace **volumes** with the path to the folder where you want to store the database.
```YAML
volumes:
    # Replace this with the path to the folder where you want to store the database.
    - ./database:/path/to/your/data/folder
```
- Replace `/path/to/your/data/folder` with the path to the folder where you want to store the database.
- This folder will be used to store the database, so you can use it to back up the database.

### Step 4: Run docker-compose
Run the following command to start the bot.
```shell
docker-compose up -d
```

### Step 6: Invite your bot to your server
You can use the following link to invite your bot to your server.
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274881562688&scope=bot
```
- Replace `YOUR_CLIENT_ID` with your bot's client ID.
- You can get it from https://discord.com/developers/applications
- Learn more: https://discordpy.readthedocs.io/en/stable/discord.html

### Step 7: Enjoy!