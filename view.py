import streamlit as st
import os
import asyncio
from uuid import uuid4
from tika import parser
from moviepy.editor import AudioFileClip, concatenate_audioclips
import edge_tts
from edge_tts import VoicesManager

output_placeholder = st.empty()


def main():
    st.title("Audiobook Generator")

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file is not None:
        progress_bar = st.progress(0)

        final_audio_file = process_pdf(uploaded_file, progress_bar)

        if final_audio_file:
            st.markdown(f"## [Download Audio File]({final_audio_file})")


def process_pdf(uploaded_file, progress_bar):
    pdf_path = "uploaded_pdf.pdf"

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    final_audio_file = asyncio.run(read_book(pdf_path, progress_bar))

    return final_audio_file


async def read_book(path: str, progress_bar, chunk_size=500) -> str:
    raw = parser.from_file(path)
    text = raw["content"]

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    output_dir = path.replace(" ", "_").replace(".", "_")
    os.makedirs(output_dir, exist_ok=True)

    audio_files = []
    for i, chunk in enumerate(chunks):
        tts = TextToSpeech(chunk, ["en-US-GuyNeural"], output_dir=output_dir)
        audio_files.extend(await tts.generate_audio())
        progress_bar.progress((i + 1) / len(chunks))

    audio_clips = [AudioFileClip(audio_file) for audio_file in audio_files]
    final_audio = concatenate_audioclips(audio_clips)

    final_audio_file = f"final-{output_dir}.mp3"
    final_audio.write_audiofile(final_audio_file)

    return final_audio_file


class TextToSpeech:
    """Simple wrapper around edge_tts for converting text to speech."""

    def __init__(self, text, voices, output_dir="output"):
        self.text = text
        self.voices = voices
        self.output_dir = output_dir

    async def generate_audio(self):
        """Generate audio files for the configured voices.

        Returns
        -------
        list[str]
            Paths to the generated audio files.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        output_paths = []
        for voice in self.voices:
            communicate = edge_tts.Communicate(self.text, voice)
            output_file = os.path.join(self.output_dir, f"{uuid4()}.mp3")
            await communicate.save(output_file)
            output_paths.append(output_file)

        return output_paths


if __name__ == "__main__":
    main()
