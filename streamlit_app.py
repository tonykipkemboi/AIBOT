import streamlit as st
import openai
import os
import pyaudio
import wave
import pyttsx3

from dotenv import load_dotenv


# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_chats():
    if "chats" not in st.session_state:
        st.session_state.chats = []
    return st.session_state.chats


def display_response(chats):
    chat_transcript = ""
    for chat in reversed(chats):
        if chat["role"] != 'system':
            chat_transcript += chat["role"] + ": " + chat["content"] + "\n\n"
    return chat_transcript


def save_audio(data, filename):
    # Set audio parameters
    audio_format = pyaudio.paInt16
    channels = 1
    sample_rate = 16000
    chunk = 1024

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open the audio stream
    stream = p.open(format=audio_format,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    # Record audio data
    for i in range(0, int(sample_rate / chunk * data)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the audio as an MP3 file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(audio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()


def clear_chats():
    st.session_state.chats = []


def record_audio(record_time):
    progress_text = "Recording in progress..."
    my_bar = st.progress(0, text=progress_text)

    frames_recorded = 0
    total_frames = int(record_time * 16000 / 1024)

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open the audio stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)

    frames = []

    # Record audio data
    while frames_recorded < total_frames:
        data = stream.read(1024)
        frames.append(data)
        frames_recorded += 1
        my_bar.progress(int((frames_recorded / total_frames)
                        * 100), text=progress_text)

    # Stop the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the audio as an MP3 file
    wf = wave.open("recording.mp3", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

    my_bar.empty()


def speak_response(output_text, engine):
    # Speak the response using pyttsx3
    if engine._inLoop:
        engine.endLoop()

    engine.say(output_text)
    engine.runAndWait()


def generate_response(chats):
    MODEL = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=chats
    )

    output_text = response['choices'][0]['message']['content']
    chats.append({"role": "assistant", "content": output_text})

    return output_text, chats


def transcribe_audio(chats):
    # Generate response using GPT-3 when the user clicks the "Generate Response" button
    if os.path.exists("recording.mp3"):
        # Transcribe the audio using OpenAI API
        with open("recording.mp3", "rb") as f:
            transcript = openai.Audio.transcribe(
                "whisper-1", f, name="recording.mp3")
        chats.append({"role": "user", "content": transcript["text"]})

        return chats


def main():
    # Set the app
    st.markdown("<h1 style='text-align: center; color: red;'>🤖 Converse with AI 🤖</h1>",
                unsafe_allow_html=True)
    st.write('---')

    # Initialize pyttsx3 Text-to-Speech engine
    engine = pyttsx3.init()

    # Set the female voice
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)

    # Set the speech rate
    engine.getProperty('rate')
    engine.setProperty('rate', 150)  # Decrease the speech rate by 50

    col1, col2 = st.columns(2)
    with col1:
        # Record audio using PyAudio
        record = st.button(
            "🎙️Record", use_container_width=True, type='primary')
        record_time = st.slider('Recording time (seconds)', 1, 60, 5)

    with col2:
        # Add a "Clear" button to clear the session state
        if st.button("💣Clear chat", use_container_width=True,  type='primary'):
            clear_chats()
    if record:
        record_audio(record_time)
        chats = get_chats()
        chats = transcribe_audio(chats)
        chat_history = display_response(chats)
        output_text, chats = generate_response(chats)
        with col2:
            output_text
            chat_history
        speak_response(output_text, engine)

        # Save the updated conversation history to session state
        st.session_state.chats = chats


if __name__ == "__main__":
    main()
