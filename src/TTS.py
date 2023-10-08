import logging

import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream


class TTS:
    def __init__(self, speech_key: str, speech_region: str):
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3)
        speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "log.txt")  #debug
        speech_config.speech_synthesis_voice_name = 'zh-CN-XiaoyiNeural'
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    async def text_to_speech_bytes(self, text: str) -> bytes:
        speech_synthesis_result = self.speech_synthesizer.speak_text_async(text).get()

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logging.debug("Speech synthesized for text [{}]".format(text))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            logging.debug("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logging.error("Error details: {}".format(cancellation_details.error_details))
                    logging.error("Did you set the speech resource key and region values?")

        return speech_synthesis_result.audio_data

    async def text_to_speech_file(self, text: str, file_name: str) -> None:
        speech_synthesis_result = self.speech_synthesizer.speak_text_async(text).get()

        audio_data_stream = AudioDataStream(speech_synthesis_result)
        audio_data_stream.save_to_wav_file(file_name)

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logging.debug("Speech synthesized for text [{}]".format(text))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            logging.debug("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logging.error("Error details: {}".format(cancellation_details.error_details))
                    logging.error("Did you set the speech resource key and region values?")
