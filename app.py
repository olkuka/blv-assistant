import streamlit as st
import requests
import base64
import time
from mutagen.mp3 import MP3
import logging

# config
API_GPT_ENDPOINT = st.secrets["OPENAI_GPT4O_ENDPOINT"]
API_TTS_ENDPOINT = st.secrets["OPENAI_TTS_ENDPOINT"]
logger = logging.getLogger(__name__)
logging.basicConfig(filename='study.log', encoding='utf-8', level=logging.INFO)

# message history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
        "role": "system",
        "content": "You are a chatbot that interacts with blind and low-vision users. You should be able to generate responses in a way that they can be converted to speech and sound natural. They cannot be too long because the user cannot stop you from speaking. You should accept user's feedback regarding the quality of responses and ask for repeating the last question if you cannot understand it. You should also be able to ask for clarification if the user's input is ambiguous. The conversation should be as natural as possible. If the user asks you about booking specific hotels, flights or anything else that can be needed during a trip, act as if you could do that, ask for more details is needed and provide feedback that you succesfully did that."
        },
    ]

# simple frontend 
st.title("Blind and Low-Vision Assistant")

def autoplay_audio(file_path: str, time_delay: int = 5):
    sound = st.empty()
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        sound.markdown(
            md,
            unsafe_allow_html=True,
        )
    time.sleep(time_delay)  # wait for 2 seconds to finish the playing of the audio
    sound.empty()  # optionally delete the element afterwards

prompt = st.chat_input("Say something")

if prompt:
    autoplay_audio('feedback_response.mp3', MP3("feedback_response.mp3").info.length+1)

    # add message to the history
    st.session_state.messages.append({"role": "user", "content": prompt})
    logger.info('USER:' + prompt)

    # send request
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": st.secrets["OPENAI_API_KEY"],
        }
        payload = {
            "messages": st.session_state.messages,
        }
        response = requests.post(API_GPT_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")
        
    # retrieve response
    response_message = response.json()["choices"][0]["message"]["content"]

    # add message to the history
    st.session_state.messages.append({"role": "assistant", "content": response_message})
    logger.info('ASSISTANT:' + response_message)

    # send request for text-to-speech output
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": st.secrets["OPENAI_API_KEY"],
        }
        payload = {
            "model": "tts-1",
            "voice": "alloy",
            "input": response_message,
        }
        audio_response = requests.post(API_TTS_ENDPOINT, headers=headers, json=payload)
        audio_response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")

    # save output to mp3 file
    with open("output.mp3", "wb") as fout:
        fout.write(audio_response.content)

    autoplay_audio('output.mp3', MP3("output.mp3").info.length+1)

# display last chat message from history on app rerun
for i in range(len(st.session_state.messages)-2, len(st.session_state.messages)):
    if st.session_state.messages[i]["role"] != "system":
        with st.chat_message(st.session_state.messages[i]["role"]):
            st.markdown(st.session_state.messages[i]["content"])
