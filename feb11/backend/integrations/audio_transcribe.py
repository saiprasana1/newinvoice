import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Configuration from environment variables
OPENAI_TRANSCRIPTION_MODEL = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio(audio_file_path):
    """Transcribes audio file to text using OpenAI Whisper API."""
    if not OPENAI_API_KEY:
        return None, "OpenAI API key not configured."

    if not os.path.exists(audio_file_path):
        return None, f"Audio file not found: {audio_file_path}"

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=OPENAI_TRANSCRIPTION_MODEL,
                file=audio_file
            )
        return transcript.text, "Audio transcribed successfully."
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None, f"Error transcribing audio: {str(e)}"

