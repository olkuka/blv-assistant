from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

with client.audio.speech.with_streaming_response.create(
        model = "tts-1",
        voice = "alloy",
        input = "Please start talking now.",
    ) as audio_response:
        audio_response.stream_to_file("feedback_response_start_talking.mp3")
            