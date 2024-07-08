import requests
import streamlit as st

API_TTS_ENDPOINT = st.secrets["OPENAI_TTS_ENDPOINT"]

try:
    headers = {
        "Content-Type": "application/json",
        "api-key": st.secrets["OPENAI_API_KEY"],
    }
    payload = {
        "model": "tts-1",
        "voice": "alloy",
        "input": "Generating the response.",
    }
    audio_response = requests.post(API_TTS_ENDPOINT, headers=headers, json=payload)
    audio_response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
except requests.RequestException as e:
    raise SystemExit(f"Failed to make the request. Error: {e}")

# save output to mp3 file
with open("feedback_response.mp3", "wb") as fout:
    fout.write(audio_response.content)