import gradio as gr
import whisper
import yt_dlp
import os
import subprocess

def process_video(url):
    try:
        # Очистка места перед работой
        for f in ["in.mp4", "out.mp4", "s.srt"]:
            if os.path.exists(f): os.remove(f)

        # 1. Скачивание (самое низкое качество, чтобы не забить память)
        opts = {
            'format': 'worst[ext=mp4]', 
            'outtmpl': 'in.mp4',
            'overwrites': True
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # 2. Загружаем модель ИИ только ВНУТРИ функции и сразу удаляем потом
        model = whisper.load_model("tiny")
        result = model.transcribe("in.mp4", language="ru")
        
        # 3. Создаем SRT
        with open("s.srt", "w", encoding="utf-8") as f:
            for i, seg in enumerate(result['segments']):
                s = seg['start']; e = seg['end']
                f.write(f"{i+1}\n{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},000 --> {int(e//3600):02d}:{int((e%3600)//60):02d}:{int(e%60):02d},000\n{seg['text'].strip()}\n\n")

        # Удаляем модель из памяти сразу после использования
        del model

        # 4. Вшиваем субтитры (очень медленно, но экономно по памяти)
        subprocess.run([
            'ffmpeg', '-i', 'in.mp4', 
            '-vf', 'subtitles=s.srt', 
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '35',
            '-c:a', 'copy', '-y', 'out.mp4'
        ])
        
        return "out.mp4"
    except Exception as e:
        return None

# Облегченный интерфейс
with gr.Blocks() as demo:
    gr.Markdown("### AI Video Translator (Free Edition)")
    input_text = gr.Textbox(label="YouTube Link")
    output_video = gr.Video()
    btn = gr.Button("Start")
    btn.click(process_video, inputs=input_text, outputs=output_video)

demo.launch(server_name="0.0.0.0", server_port=10000)
        
