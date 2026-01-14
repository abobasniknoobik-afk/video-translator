import gradio as gr
import whisper
import yt_dlp
import os
import subprocess

model = whisper.load_model("tiny")

def process_video(url):
    try:
        for f in ["in.mp4", "out.mp4", "s.srt"]:
            if os.path.exists(f): os.remove(f)

        # Скачиваем 480p или ниже для скорости
        opts = {'format': 'mp4[height<=480]', 'outtmpl': 'in.mp4'}
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        result = model.transcribe("in.mp4", language="ru")

        with open("s.srt", "w", encoding="utf-8") as f:
            for i, seg in enumerate(result['segments']):
                s = seg['start']; e = seg['end']
                f.write(f"{i+1}\n{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},000 --> {int(e//3600):02d}:{int((e%3600)//60):02d}:{int(e%60):02d},000\n{seg['text'].strip()}\n\n")

        # Вшиваем субтитры
        subprocess.run(['ffmpeg', '-i', 'in.mp4', '-vf', 'subtitles=s.srt', '-c:a', 'copy', '-preset', 'ultrafast', 'out.mp4'])

        return "out.mp4"
    except Exception as e:
        return None

demo = gr.Interface(fn=process_video, inputs="text", outputs="video", title="AI Video Translator")
demo.launch(server_name="0.0.0.0", server_port=8000)
              
