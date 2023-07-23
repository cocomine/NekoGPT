FROM python:latest
LABEL authors="cocomine"
LABEL version="0.2.10"
WORKDIR /bot

ENV DISCORD_TOKEN (Your Discord token)
ENV CHATGPT_TOKEN (Your ChatGPT access token)
ENV BOT_NAME (Your Bot Name)
ENV SPEECH_KEY (Your Speech key)
ENV SPEECH_REGION (Your Speech region)

# set-up command
RUN apt-get --yes update; apt-get --yes upgrade;
RUN apt --yes install libgstreamer1.0-0
RUN apt --yes install gstreamer1.0-plugins-base
RUN apt --yes install gstreamer1.0-plugins-good
RUN apt --yes install gstreamer1.0-plugins-bad
RUN apt --yes install gstreamer1.0-plugins-ugly
RUN apt --yes install ffmpeg
RUN mkdir "../database"

# Add file
ADD src/ ./

RUN pip install -r requirements.txt

# Add volume
VOLUME ["/database"]

# start-up command
ENTRYPOINT ["python", "main.py"]

