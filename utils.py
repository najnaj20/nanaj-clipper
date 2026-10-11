import os
import yt_dlp
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip
import subprocess

def validate_cookies(cookie_path):
    if not cookie_path or not os.path.exists(cookie_path):
        return False, "cookies.txt tidak ditemukan."
    
    required = ["SID", "HSID", "SSID", "APISID", "SAPISID", "LOGIN_INFO"]
    with open(cookie_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    missing = [c for c in required if c not in content]
    if missing:
        return False, f"Cookies tidak lengkap. Kurang: {', '.join(missing)}. Silakan export ulang cookies saat sudah login YouTube."
    
    return True, ""

def download_audio(url, cookie_path=None, output_path="audio.mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', # Lower quality for faster processing
        }],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'concurrent_fragment_downloads': 1,
        'nocheckcertificate': True,
    }
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "audio.mp3"

def transcribe_audio(audio_path):
    # SWITCH TO 'tiny' MODEL FOR MEMORY EFFICIENCY (Prevents Streamlit OOM)
    model_size = "tiny" 
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    transcript = []
    for segment in segments:
        transcript.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    return transcript

def analyze_viral_potential(transcript):
    viral_keywords = ["secret", "never", "actually", "stop", "how to", "why", "mistake", "truth", "hack", "amazing", "shocking"]
    suggestions = []
    
    for i, seg in enumerate(transcript):
        text_lower = seg["text"].lower()
        if any(kw in text_lower for kw in viral_keywords):
            suggestions.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "reason": "Contains viral trigger word"
            })
        elif len(seg["text"].split()) < 10 and i < 5:
            suggestions.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "reason": "Strong opening hook potential"
            })
            
    return suggestions[:5]

def download_video(url, cookie_path=None, output_path="video.mp4"):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'video',
        'merge_output_format': 'mp4',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'concurrent_fragment_downloads': 1,
        'nocheckcertificate': True,
    }
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "video.mp4"

def crop_video_vertical(video_path, start, end, output_path="clip_vertical.mp4"):
    # use context manager for better memory cleanup
    with VideoFileClip(video_path) as clip:
        sub = clip.subclip(start, end)
        
        w, h = sub.size
        target_ratio = 9/16
        target_w = h * target_ratio
        
        x_center = w / 2
        x1 = x_center - (target_w / 2)
        x2 = x_center + (target_w / 2)
        
        cropped = sub.crop(x1=x1, y1=0, x2=x2, y2=h)
        cropped.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=1) # Limit threads for stability
    return output_path
