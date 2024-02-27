from pytube import YouTube
from moviepy.editor import VideoFileClip
import pandas as pd
from tqdm import tqdm
import os

def parse_time(time_str):
    mins, secs = map(int, time_str.split(':'))
    return mins * 60 + secs

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_video_full_length(yt, video_path, audio_path, title):
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    safe_title = title.replace(',', '').replace(' ', '_')
    filename = f"{safe_title}.mp4"
    final_video_path = os.path.join(video_path, filename)
    stream.download(output_path=video_path, filename=filename)

    # 오디오 추출
    final_audio_path = os.path.join(audio_path, f"{safe_title}.wav")
    clip = VideoFileClip(final_video_path)
    clip.audio.write_audiofile(final_audio_path, codec='pcm_s16le')

def download_and_cut_video(url, video_path, audio_path, titles, timelines):
    yt = YouTube(url)
    ensure_dir(video_path)
    ensure_dir(audio_path)

    if not timelines or timelines[0] == '':
        download_video_full_length(yt, video_path, audio_path, titles[0])
    else:
        temp_filename = "temp_video.mp4"
        temp_path = os.path.join(video_path, temp_filename)
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(
            output_path=video_path, filename=temp_filename)

        for timeline, title in zip(timelines, titles):
            start_str, end_str = timeline.split('~')
            start = parse_time(start_str)
            end = parse_time(end_str)
            clip = VideoFileClip(temp_path).subclip(start, end)

            safe_title = title.replace(',', '').replace(' ', '_')
            cut_filename = f"{safe_title}_{start_str.replace(':', '-')}-{end_str.replace(':', '-')}.mp4"
            final_video_path = os.path.join(video_path, cut_filename)
            clip.write_videofile(final_video_path, codec='libx264', audio_codec='aac')

            final_audio_path = os.path.join(audio_path, cut_filename.replace(".mp4", ".wav"))
            clip.audio.write_audiofile(final_audio_path, codec='pcm_s16le')

        os.remove(temp_path)
def load_csv(csv_path):
    csv = pd.read_csv(csv_path, encoding='cp949')
    data = []
    for index, row in csv.iterrows():
        url = row['url']
        titles = row['title'].split(', ')
        timelines = row.get('timeline', '').split(', ') if pd.notna(row.get('timeline')) else ['']
        data.append((url, titles, timelines))
    return data

csv_path = './list.csv'
data = load_csv(csv_path)

video_path = "./mp4_file/"
audio_path = "./wav_file/"

for url, titles, timelines in tqdm(data):
    download_and_cut_video(url, video_path, audio_path, titles, timelines)