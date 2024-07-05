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
        "content": "You are a chatbot that interacts with blind and low-vision users. You should be able to generate responses in a way that they can be converted to speech and sound natural. They cannot be too long because the user cannot stop you from speaking. You should accept user's feedback regarding the quality of responses and ask for repeating the last question if you cannot understand it. You should also be able to ask for clarification if the user's input is ambiguous. The conversation should be as natural as possible."
        },
    ]

# simple frontend 
st.title("Blind and Low-Vision Assistant")
# st.header("Press the space and start speaking")

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
        autoplay_audio('feedback_response.mp3')
        st.write(st.session_state.stt_prompt_output)

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
                console.log('click')
                button.click();
            }
        });
    </script>
    """, height=0, width=0)

# display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
