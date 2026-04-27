import os
from google.cloud import speech_v2
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv("GCP_PROJECT_ID")
location = "asia-northeast1"
client = speech_v2.SpeechClient(client_options={"api_endpoint": f"{location}-speech.googleapis.com"})

# Try 'long'
request = speech_v2.CreateRecognizerRequest(
    parent=f"projects/{project_id}/locations/{location}",
    recognizer_id="test-recognizer-long",
    recognizer=speech_v2.Recognizer(
        default_recognition_config=speech_v2.RecognitionConfig(
            language_codes=["ja-JP"],
            model="long",
            features=speech_v2.RecognitionFeatures(
                diarization_config=speech_v2.SpeakerDiarizationConfig(
                    min_speaker_count=2, max_speaker_count=10
                )
            )
        )
    )
)

try:
    res = client.create_recognizer(request=request)
    print("LONG model in asia-northeast1: SUCCESS")
    client.delete_recognizer(name=res.name)
except Exception as e:
    print("LONG model in asia-northeast1: FAILED", e)

# Try 'latest_long' in V2
request2 = speech_v2.CreateRecognizerRequest(
    parent=f"projects/{project_id}/locations/{location}",
    recognizer_id="test-recognizer-latest-long",
    recognizer=speech_v2.Recognizer(
        default_recognition_config=speech_v2.RecognitionConfig(
            language_codes=["ja-JP"],
            model="latest_long",
            features=speech_v2.RecognitionFeatures(
                diarization_config=speech_v2.SpeakerDiarizationConfig(
                    min_speaker_count=2, max_speaker_count=10
                )
            )
        )
    )
)

try:
    res2 = client.create_recognizer(request=request2)
    print("LATEST_LONG model in asia-northeast1: SUCCESS")
    client.delete_recognizer(name=res2.name)
except Exception as e:
    print("LATEST_LONG model in asia-northeast1: FAILED", e)
