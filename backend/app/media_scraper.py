import io
import os
import tempfile
import logging

logger = logging.getLogger("finswarm.media_parser")

async def transcribe_audio(file_bytes: bytes) -> str:
    """Converts audio bytes into text using SpeechRecognition."""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
        
        # Load audio bytes into pydub and force conversion to WAV (required by SpeechRecognition)
        audio_stream = io.BytesIO(file_bytes)
        audio_segment = AudioSegment.from_file(audio_stream)
        
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            
        # Using Google's free Web Speech API for zero-setup transcription
        text = recognizer.recognize_google(audio_data)
        logger.info("Successfully transcribed audio file.")
        return text
        
    except ImportError:
        logger.error("Audio parsing dependencies missing.")
        return "Error: speechrecognition and pydub are not installed. Run `pip install SpeechRecognition pydub`."
    except sr.UnknownValueError:
        return "Notice: Audio was processed, but no speech could be clearly understood."
    except Exception as e:
        logger.exception(f"Audio Parsing Error: {e}")
        return f"Error transcribing audio: {str(e)}"

async def transcribe_video(file_bytes: bytes) -> str:
    """Extracts audio from a video file and sends it to the audio transcriber."""
    temp_video_path = None
    temp_audio_path = None
    try:
        from moviepy.editor import VideoFileClip
        
        # MoviePy requires physical files, so we write the bytes to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(file_bytes)
            temp_video_path = temp_video.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio_path = temp_audio.name
            
        # Extract the audio track
        video_clip = VideoFileClip(temp_video_path)
        video_clip.audio.write_audiofile(temp_audio_path, logger=None)
        video_clip.close()
        
        # Read the extracted audio and reuse our transcribe_audio function
        with open(temp_audio_path, "rb") as f:
            audio_bytes = f.read()
            
        logger.info("Successfully extracted audio from video, beginning transcription.")
        text = await transcribe_audio(audio_bytes)
        return text
        
    except ImportError:
        logger.error("Video parsing dependencies missing.")
        return "Error: moviepy is not installed. Run `pip install moviepy`."
    except Exception as e:
        logger.exception(f"Video Parsing Error: {e}")
        return f"Error transcribing video: {str(e)}"
    finally:
        # Clean up temporary files to prevent disk bloat
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)