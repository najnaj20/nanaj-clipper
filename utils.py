import os
import subprocess
from faster_whisper import WhisperModel

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

def run_ytdlp(args):
    """Helper to run yt-dlp as a CLI command to bypass Python module bugs."""
    cmd = ["yt-dlp"] + args
    # We use subprocess to isolate the execution from the Streamlit Python process
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp CLI Error: {result.stderr}")
    return result.stdout

def download_audio(url, cookie_path=None, output_path="audio.mp3"):
    # Using CLI flags instead of Python dict to avoid the 'metadata_errors' bug
    args = [
        "-f", "bestaudio/best",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "128K",
        "-o", "audio.%(ext)s",
        "--no-playlist",
        "--nocheckcertificate",
        "--extractor-args", "youtube:player_client=android,web",
        url
    ]
    if cookie_path:
        args.extend(["--cookies", cookie_path])
        
    run_ytdlp(args)
    return "audio.mp3"

def transcribe_audio(audio_path):
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
    args = [
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", "video.%(ext)s",
        "--no-playlist",
        "--nocheckcertificate",
        "--extractor-args", "youtube:player_client=android,web",
        url
    ]
    if cookie_path:
        args.extend(["--cookies", cookie_path])
        
    run_ytdlp(args)
    return "video.mp4"

def crop_video_vertical(video_path, start, end, output_path="clip_vertical.mp4"):
    duration = end - start
    
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", video_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    dims = result.stdout.strip().split('x')
    if len(dims) != 2:
        raise RuntimeError("Could not determine video dimensions")
    
    w, h = int(dims[0]), int(dims[1])
    target_w = int(h * (9/16))
    x_offset = (w - target_w) // 2
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", video_path,
        "-vf", f"crop={target_w}:{h}:{x_offset}:0",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {process.stderr}")
        
    return output_path
