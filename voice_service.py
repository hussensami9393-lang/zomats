"""
Voice Service - Speech-to-Text and Text-to-Speech
Supports OpenAI Whisper (STT) and TTS
"""
import io
import os
import tempfile
from typing import Optional
from loguru import logger
from config.settings import config


class VoiceService:
    """
    Voice processing service:
    - Speech to Text (Whisper)
    - Text to Speech (OpenAI TTS / gTTS)
    """
    
    async def speech_to_text(self, audio_bytes: bytes, file_format: str = "ogg") -> Optional[str]:
        """
        Convert speech to text using OpenAI Whisper
        """
        if not config.OPENAI_API_KEY:
            return await self._stt_fallback(audio_bytes, file_format)
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            # Create temp file
            suffix = f".{file_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, "rb") as audio_file:
                    response = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                return response
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Whisper STT error: {e}")
            return await self._stt_fallback(audio_bytes, file_format)
    
    async def _stt_fallback(self, audio_bytes: bytes, file_format: str) -> Optional[str]:
        """Fallback STT using SpeechRecognition library"""
        try:
            import speech_recognition as sr
            import tempfile
            
            suffix = f".{file_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                r = sr.Recognizer()
                with sr.AudioFile(tmp_path) as source:
                    audio = r.record(source)
                
                # Try Google STT (free)
                text = r.recognize_google(audio, language="ar-SA")
                return text
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Fallback STT error: {e}")
            return None
    
    async def text_to_speech(self, text: str, language: str = "ar", voice: str = "alloy") -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS
        Returns audio bytes (MP3)
        """
        if config.OPENAI_API_KEY:
            return await self._tts_openai(text, voice)
        else:
            return await self._tts_gtts(text, language)
    
    async def _tts_openai(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """OpenAI TTS - high quality voices"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            # Available voices: alloy, echo, fable, onyx, nova, shimmer
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text[:4096]  # TTS limit
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return await self._tts_gtts(text, "ar")
    
    async def _tts_gtts(self, text: str, language: str = "ar") -> Optional[bytes]:
        """gTTS fallback - uses Google TTS (free)"""
        try:
            from gtts import gTTS
            import io
            
            tts = gTTS(text=text[:500], lang=language, slow=False)
            
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            return mp3_buffer.read()
            
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return None
    
    async def convert_ogg_to_wav(self, ogg_bytes: bytes) -> Optional[bytes]:
        """Convert OGG audio (Telegram voice messages) to WAV"""
        try:
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(ogg_bytes)
                ogg_path = f.name
            
            wav_path = ogg_path.replace(".ogg", ".wav")
            
            subprocess.run(
                ["ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                capture_output=True,
                check=True
            )
            
            with open(wav_path, "rb") as f:
                wav_bytes = f.read()
            
            os.unlink(ogg_path)
            os.unlink(wav_path)
            
            return wav_bytes
            
        except Exception as e:
            logger.error(f"OGG to WAV conversion error: {e}")
            return ogg_bytes


# Global voice service instance
voice_service = VoiceService()
