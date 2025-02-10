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
    audio_clip = audio_clip.subclipped(start_time + 0.5, start_time + duration)  # Sync audio to video duration

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


# Example usage
clip_urls = [
    "https://www.youtube.com/clip/Ugkxyl80X_un31ttZ-mcMstosh9jMiarqHoY",
    "https://www.youtube.com/clip/Ugkx04MBG-dtuh0K4NG4U9gnjKxLQOB2uFOO",
    "https://youtube.com/clip/UgkxPID4-UyGpIYIdN2YwpDuWZUXyNTU2R_t?si=yA_IR7x9l0UObD9n",
    "https://youtube.com/clip/UgkxBxK-o56yBPdnqrmf5gamiseoatkynVYP?si=F9o3goJfFxAPfjqR",
    "https://youtube.com/clip/Ugkx32lDO7WDATZj0edecJPIij-W--zuVig7?si=W_zsnMruMfV5j4Ox",
    "https://youtube.com/clip/Ugkx29-T7DwcB0GQhX3fhfN3_BBJ_YQuSV4p?si=pYDQHX36WtbtUjfo",
    "https://youtube.com/clip/UgkxJm4jGmS35FSCeSnyfVkuShgv56ucEdof?si=1KVXQJf44M38CM9D",
    "https://youtube.com/clip/UgkxAZADrTne5weHcbj8tLDz1hMrraUlSyu3?si=FEl5mxpBlXhTE2oh",
    "https://youtube.com/clip/Ugkxr-9-pmPefXO3O_xgX4OKgFSMADvSsQab?si=p9zqDeH5iTkR3HzB",
    "https://youtube.com/clip/Ugkx9K9rYaVN5Ml0xolH5vXjn5NFBqnUb_SY?si=tCsexAkGjlYP_I-v",
    "https://youtube.com/clip/Ugkx0v07MljlpYuameXbKj_a48ItfyjtJTMe?si=X3xMt_-HdItfW_dx",
    "https://youtube.com/clip/UgkxL26XePGkj9J2avjJ76OKeUdN30pKqgAW?si=oMYFybjn0lDrFpSk",
    "https://youtube.com/clip/Ugkx15FumHdkmmV0A1HcryF0AbUqcc5BPK0k?si=Qs8y6cGc-czIyBXF",
    "https://youtube.com/clip/UgkxX9bzIZu8-NHyDlQMWi5Y4yAgeCGYPBLF?si=1wm81VizltMutK6x",
    "https://youtube.com/clip/Ugkx5qmNNs4ICLLm-lMCnOr0aJNslTUGBRsG?si=Mm_46FovIeVOGy9T",
    "https://youtube.com/clip/Ugkxs41aPQRs5lopY-5bYjcO1yBmmBPEWmkz?si=q6AGE4xomjnzMqne",
    "https://youtube.com/clip/UgkxSzdYCaZDhpxfWfZ5kO2iR69oKq5SpHl1?si=riVzr_M528jAN0N_",
    "https://youtube.com/clip/UgkxXTNgBCb_ip-ye_HBkYCQhT9NHQOGV5BF?si=ZSYvJr5n3U1pgOGc",
    "https://youtube.com/clip/Ugkx34pQXCtYkl3qKr2-vJk8ekoUctoyfvsw?si=QeAwDLqJt8IS0rY0",
    "https://youtube.com/clip/UgkxLGAZZH-rJ6EhhFZaMUXAAXnWzber2xiX?si=GGWByzJp0eETV07G",
    "https://youtube.com/clip/UgkxzimX7TEBCRGD3gCErkjgpcSYPuiypZUz?si=j6wcytnIz0mpCNK5",
    "https://youtube.com/clip/Ugkxs1_QXmRY_iLzWH9Cflx8Glgze32JrQ4r?si=xtDsNFwVFxRTpjC7",
    "https://youtube.com/clip/Ugkxzm1CcKGqRZVg1snjavu6dV4eQuXaSGn1?si=h3b9I_2gHsdBaVoU",
    "https://youtube.com/clip/UgkxSthsWUZid2WpzuXgfX5_eONFb57JzxoI?si=erU7kU5yIbobGStj",
    "https://youtube.com/clip/Ugkxe9Xoc1qfe0Zcj52wyYp3zRX2_qWnC3AB?si=DScQCHfagy0Bgx1f",
    "https://youtube.com/clip/UgkxlVeVqXEOY0A4kIDPbIbMU-AMXWjoU9TK?si=o6-p9x_iLPMaQ9-4",
    "https://youtube.com/clip/UgkxYbXdyO5wpbgcTNH4GgFI9UM794hXPdsu?si=WHNebA0P52CQp9bY",
    "https://youtube.com/clip/UgkxV8yAOFT2F-X6dCYwg_6xm_6sGXgXPXYo?si=NGO6wnGycyb9WEXA",
    "https://youtube.com/clip/UgkxGRikU_51p6meNC3PuDs4PS6TmoNktYtP?si=gPc2lR992Bd6ziZb",
]

process_clips(clip_urls)
