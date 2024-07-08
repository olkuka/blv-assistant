import streamlit as st
from streamlit_mic_recorder import speech_to_text
import requests
import streamlit.components.v1 as components
import base64
import time
from mutagen.mp3 import MP3

# config
API_GPT_ENDPOINT = st.secrets["OPENAI_GPT4O_ENDPOINT"]
API_TTS_ENDPOINT = st.secrets["OPENAI_TTS_ENDPOINT"]

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

def callback():
    if st.session_state.stt_prompt_output:
        autoplay_audio('feedback_response.mp3', MP3("feedback_response.mp3").info.length+1)

        # add message to the history
        st.session_state.messages.append({"role": "user", "content": st.session_state.stt_prompt_output})

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


# recognize speech
speak_button = speech_to_text(
    key = "stt_prompt",
    callback=callback)

components.html("""
    <script>
        const doc = window.parent.document;
        const blip = "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VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/70mQAD/AAAGkAAAAIAAANIAAAAQAAAaQAAAAgAAA0gAAABExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVMQU1FMy4xMDBVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//vSZAAP8AAAaQAAAAgAAA0gAAABAAABpAAAACAAADSAAAAETEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVU="
        const blipReversed = "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qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqr/+5JkQo/wEACAAyAACAIAEABkAAEAAAGkAAAAIAAANIAAAASqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq";
        let isStart = true;
        function findSpeechButton() {
            const iframe = doc.querySelector("#root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.block-container.st-emotion-cache-13ln4jf.ea3mdgi5 > div > div > div > div:nth-child(2) > iframe");
            if (iframe) {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const button = iframeDoc.querySelector("#root > div > button");
                return button;
            }
        }

        function checkForButton() {
            if (!findSpeechButton()) {
                setTimeout(checkForButton, 500); // Check again after 500ms if the button is not found
             }
        }

        checkForButton();
        doc.addEventListener('keyup', function (event) {
            if (event.key === ' ') {
                const button = findSpeechButton();
                button.click();
                if (isStart) {
                    new Audio("data:audio/wav;base64," + blip).play();
                } else {
                    new Audio("data:audio/wav;base64," + blipReversed).play();
                }
                isStart = !isStart;
            }
        });
    </script>
    """, height=0, width=0)

# display last chat message from history on app rerun
for i in range(len(st.session_state.messages)-2, len(st.session_state.messages)):
    if st.session_state.messages[i]["role"] != "system":
        with st.chat_message(st.session_state.messages[i]["role"]):
            st.markdown(st.session_state.messages[i]["content"])
