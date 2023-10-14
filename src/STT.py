import asyncio
import io
import logging

import azure.cognitiveservices.speech as speechsdk


class STT:
    def __init__(self, speech_key: str, speech_region: str):
        """
        Azure Speech to Text
        https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#speech-to-text

        :param speech_key: Speech Key
        :param speech_region: Speech Region
        """
        self.speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        self.speech_config.speech_recognition_language = "zh-HK"
        self.auto_detect_source_language_config = speechsdk.AutoDetectSourceLanguageConfig(
            languages=["zh-HK", "zh-TW", "en-US"]
        )
        self.compressed_format = speechsdk.audio.AudioStreamFormat(
            compressed_stream_format=speechsdk.AudioStreamContainerFormat.OGG_OPUS)

    async def speech_to_text(self, audio_file: bytes) -> str:
        """
        Speech to Text
        https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/quickstart-python#speech-to-text

        :param audio_file: Input audio File (bytes)
        :return: Detected Text
        """
        # Creates stream reader object to read audio from an external file.
        binary_file_reader = BinaryReaderCallback(audio_file)
        stream = speechsdk.audio.PullAudioInputStream(stream_format=self.compressed_format,
                                                      pull_stream_callback=binary_file_reader)

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

        # session_stopped callback
        def stop_cb(evt):
            logging.debug('CLOSING on {}'.format(evt))
            speech_recognizer.stop_continuous_recognition_async()
            nonlocal done
            done = True

        # recognized callback
        def recognized_cb(evt):
            nonlocal text
            text += evt.result.text

        # Connect callbacks to the events fired by the speech recognizer
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.recognized.connect(recognized_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition_async()

        # Waits for recognition to finish
        while not done:
            await asyncio.sleep(1)

        return text


class BinaryReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, file: bytes):
        """
        Binary Reader Callback
        https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.audio.pullaudioinputstreamcallback?view=azure-python

        :param file: File (bytes)
        """
        super().__init__()
        self._file = io.BytesIO(file)

    def read(self, buffer: memoryview) -> int:
        """
        Read
        https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.audio.pullaudioinputstreamcallback?view=azure-python#read

        :param buffer: Buffer
        """
        # print('trying to read {} frames'.format(buffer.nbytes))
        try:
            size = buffer.nbytes
            frames = self._file.read(size)

            buffer[:len(frames)] = frames
            # print('read {} frames'.format(len(frames)))

            return len(frames)
        except Exception as ex:
            # print('Exception in `read`: {}'.format(ex))
            raise

    def close(self) -> None:
        """
        Close
        https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.audio.pullaudioinputstreamcallback?view=azure-python#close
        """
        # print('closing file')
        try:
            self._file.close()
        except Exception as ex:
            # print('Exception in `close`: {}'.format(ex))
            raise
