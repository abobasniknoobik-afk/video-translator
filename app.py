import gradio as gr
from faster_whisper import WhisperModel
import yt_dlp
import os
import subprocess

def process_video(url):
    try:
        # Очистка старых файлов
        for f in ["in.mp4", "out.mp4", "s.srt"]:
            if os.path.exists(f): os.remove(f)

        # 1. Скачиваем только звук (это сэкономит кучу памяти!)
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.mp3',
            'overwrites': True
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            # Также скачаем видео без звука для склейки
            ydl.params['format'] = 'worst[ext=mp4]'
            ydl.params['outtmpl'] = 'in.mp4'
            ydl.download([url])

        # 2. ИИ распознавание (самая быстрая и легкая модель)
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe("audio.mp3", beam_size=1)
        
        # 3. Сохраняем субтитры
        with open("s.srt", "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments):
                s = seg.start; e = seg.end
                f.write(f"{i+1}\n{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},000 --> {int(e//3600):02d}:{int((e%3600)//60):02d}:{int(e%60):02d},000\n{seg.text.strip()}\n\n")

        # 4. Вшиваем субтитры через ffmpeg
        subprocess.run([
            'ffmpeg', '-i', 'in.mp4', '-vf', 'subtitles=s.srt', 
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '35', '-y', 'out.mp4'
        ])
        
        return "out.mp4"
    except Exception as e:
        print(f"Error: {e}")
        return None

demo = gr.Interface(fn=process_video, inputs="text", outputs="video", title="Fast Video Translator")
demo.launch(server_name="0.0.0.0", server_port=10000)
            
