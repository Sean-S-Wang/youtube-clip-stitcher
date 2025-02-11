import re
import requests
import json
import os
from bs4 import BeautifulSoup
from pytubefix import YouTube
import moviepy as mp


def get_clip_metadata(clip_url):
    """Fetches original video ID and timestamps from a YouTube Clip page."""
    headers = {"User-Agent": "Mozilla/5.0"}  # Mimic a browser request
    response = requests.get(clip_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page: {clip_url}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.prettify()

    # Extract JSON-like script containing "clipConfig"
    clip_config_match = re.search(r'"clipConfig":({.*?})', page_text)
    video_match = re.search(r'"videoId":"(.*?)"', page_text)

    if clip_config_match and video_match:
        clip_config = json.loads(clip_config_match.group(1))
        video_id = video_match.group(1)

        start_time = int(clip_config["startTimeMs"]) / 1000
        end_time = int(clip_config["endTimeMs"]) / 1000
        duration = end_time - start_time

        return {
            "video_id": video_id,
            "start_time": start_time,
            "duration": duration,
        }
    else:
        print(f"Failed to extract metadata for {clip_url}")
        return None


def download_video(video_id, output_path):
    """Downloads a YouTube video and returns the file path."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    yt = YouTube(video_url)

    print(f"Downloading video: {yt.title}")
    stream = yt.streams.filter(file_extension="mp4", res="1080p").first()
    audio_stream = yt.streams.filter(only_audio=True).first()
    video_path = stream.download(output_path)
    audio_path = audio_stream.download(output_path)

    return video_path, audio_path


def trim_video(video_path, start_time, duration, output_clip, audio_path):
    """Trims a video from start_time to start_time + duration."""
    audio_clip = mp.AudioFileClip(audio_path)
    video_clip = mp.VideoFileClip(video_path)

    # Trim video and audio to the specified segment
    video_clip = video_clip.subclipped(start_time, start_time + duration)
    audio_clip = audio_clip.subclipped(start_time + 0.25, start_time + duration)  # Sync audio to video duration

    # Set audio
    clip = video_clip.with_audio(audio_clip)
    clip.write_videofile(output_clip, codec="libx264")
    clip.close()


def process_clips(clip_urls, output_folder="downloads", final_video_name="final_compilation.mp4"):
    """Processes multiple YouTube Clips and merges them into one video."""
    os.makedirs(output_folder, exist_ok=True)
    clips = []

    for clip_url in clip_urls:
        metadata = get_clip_metadata(clip_url)
        if not metadata:
            continue

        video_id = metadata["video_id"]
        start_time = metadata["start_time"]
        duration = metadata["duration"]

        # Download full video
        full_video_path, full_audio_path = download_video(video_id, output_folder)

        # Trim the clip
        clip_output_path = os.path.join(output_folder, f"clip_{video_id}_{start_time}.mp4")
        trim_video(full_video_path, start_time, duration, clip_output_path, full_audio_path)

        # Add to clips list for merging
        clips.append(mp.VideoFileClip(clip_output_path))

    if clips:
        print("Merging all clips into final video...")
        final_video = mp.concatenate_videoclips(clips, method="compose")
        final_video_path = os.path.join(output_folder, final_video_name)
        final_video.write_videofile(final_video_path, codec="libx264")
        print(f"Final video saved as: {final_video_path}")

    # Cleanup individual clips (optional)
    for clip in clips:
        clip.close()
        os.remove(clip.filename)


# Example usage
file_path = "kova_clips.txt"
with open(file_path, 'r') as file:
    lines = [line.strip() for line in file]
    clip_urls = lines

process_clips(clip_urls, final_video_name="kova_highlights.mp4")
