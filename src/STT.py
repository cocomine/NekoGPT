import asyncio

import azure.cognitiveservices.speech as speechsdk


class STT:
    def __init__(self, speech_key: str, speech_region: str):
        self.speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        self.speech_config.speech_recognition_language = "zh-HK"
        self.auto_detect_source_language_config = speechsdk.AutoDetectSourceLanguageConfig(
            languages=["zh-HK", "zh-TW", "en-US"]
        )

    async def speech_to_text(self, audio_file: str):
        # Creates stream reader object to read audio from an external file.
        binary_file_reader = BinaryFileReaderCallback(audio_file)
        compressed_format = speechsdk.audio.AudioStreamFormat(
            compressed_stream_format=speechsdk.AudioStreamContainerFormat.OGG_OPUS)
        stream = speechsdk.audio.PullAudioInputStream(stream_format=compressed_format, pull_stream_callback=binary_file_reader)

        # Creates a speech recognizer using a file as audio input.
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=self.auto_detect_source_language_config
        )

        # Starts speech recognition, and returns after a single utterance is recognized.
        done = False
        text = ""

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            speech_recognizer.stop_continuous_recognition()
            nonlocal done
            done = True

        def recognized_cb(evt):
            nonlocal text
            text += evt.result.text

        # speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
        speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
        # speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
        # speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
        # speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))

        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.recognized.connect(recognized_cb)

        speech_recognizer.start_continuous_recognition()
        while not done:
            await asyncio.sleep(1)

        return text


class BinaryFileReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, filename: str):
        super().__init__()
        self._file_h = open(filename, "rb")

    def read(self, buffer: memoryview) -> int:
        # print('trying to read {} frames'.format(buffer.nbytes))
        try:
            size = buffer.nbytes
            frames = self._file_h.read(size)

            buffer[:len(frames)] = frames
            # print('read {} frames'.format(len(frames)))

            return len(frames)
        except Exception as ex:
            # print('Exception in `read`: {}'.format(ex))
            raise

    def close(self) -> None:
        # print('closing file')
        try:
            self._file_h.close()
        except Exception as ex:
            # print('Exception in `close`: {}'.format(ex))
            raise
