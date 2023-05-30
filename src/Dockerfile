FROM python:latest
LABEL authors="cocomine"
WORKDIR /bot

ENV DISCORD_TOKEN (Your Discord token)
ENV CHATGPT_TOKEN (Your ChatGPT access token)
ENV MYSQL_HOST (Your SQL host)
ENV MYSQL_USER (Your SQL username)
ENV MYSQL_PASSWORD (Your SQL password)
ENV MYSQL_DATABASE (Your SQL database)
ENV BOT_NAME (Your Bot Name)

# Add file
ADD ./ ./

# set-up command
RUN apt-get --yes update; apt-get --yes upgrade;
RUN pip install -r requirements.txt

# start-up command
ENTRYPOINT ["python", "main.py"]

