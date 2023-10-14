FROM python:3.11.6
LABEL authors="cocomine"
LABEL version="0.2.3"
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

# Install openssl 1.1.1w
RUN wget -O - https://www.openssl.org/source/openssl-1.1.1w.tar.gz | tar zxf -
RUN ./openssl-1.1.1w/config --prefix=/usr/local
RUN make -j $(nproc)
RUN make install_sw install_ssldirs
RUN ldconfig -v
ENV SSL_CERT_DIR /etc/ssl/certs

# Add requirements
RUN mkdir "../database"
ADD src/requirements.txt ./
RUN pip install -r requirements.txt

# Add file
ADD src/ ./

# Add volume
VOLUME ["/database"]

# start-up command
ENTRYPOINT ["python", "main.py"]

