import streamlit as st
import streamlit_shortcuts
from openai import OpenAI
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
# import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='study.log', encoding='utf-8', level=logging.INFO)

# model = whisper.load_model("base")

def record_audio():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    with microphone as source:
        audio_data = recognizer.listen(source)
        return audio_data

def recognize_speech(audio_data):
    recognizer = sr.Recognizer()
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except:
        return "Say that you didn't understand my last question and ask for repeating it."
    # with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as temp_audio_file:
    #     temp_audio_file.write(audio_data.get_wav_data())
    #     temp_audio_file.flush()
    # model = whisper.load_model("base")
    # result = model.transcribe(temp_audio_file.name)
    # return result["text"]

st.title("Blind and Low-Vision Assistant")
st.header("Press the space and start speaking")

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set gpt-4o
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
        "role": "system",
        "content": "You are a chatbot that interacts with blind and low-vision users. You should be able to generate responses in a way that they can be converted to speech and sound natural. They cannot be too long because the user cannot stop you from speaking. You should accept user's feedback regarding the quality of responses and ask for repeating the last question if you cannot understand it. You should also be able to ask for clarification if the user's input is ambiguous. The conversation should be as natural as possible."
        },
    ]

# Accept user input
# if prompt := st.chat_input("What is up?"):
def space_callback():
    sound = AudioSegment.from_mp3("feedback_response_start_talking.mp3")
    play(sound)
    # start = time.time()
    audio_data = record_audio()
    # end = time.time()
    # print('RECORD AUDIO TIME:', end - start)
    sound = AudioSegment.from_mp3("feedback_response.mp3")
    play(sound)
    # start = time.time()
    user_input = recognize_speech(audio_data)
    # end = time.time()
    # print('RECOGNIZE SPEECH TIME:', end - start)
    prompt = user_input
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    logger.info('USER:' + prompt)

    # start = time.time()
    # Display assistant response in chat message container
    stream = client.chat.completions.create(
        model = st.session_state["openai_model"],
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
    )
    response = stream.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": response})
    logger.info('ASSISTANT:' + response)
    # end = time.time()
    # print('DISPLAYING ASSISTANT MESSAGE TIME:', end - start)

    # start = time.time()
    # Text-to-speech
    with client.audio.speech.with_streaming_response.create(
        model = "tts-1",
        voice = "alloy",
        input = response,
    ) as audio_response:
    # audio_response = gTTS(text=response)
        with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as temp_audio_file:
            audio_response.stream_to_file(temp_audio_file.name)
            temp_audio_file.flush()
    # end = time.time()
    # print('TEXT TO SPEECH TIME:', end - start)
    sound = AudioSegment.from_mp3(temp_audio_file.name)
    play(sound)

streamlit_shortcuts.button('START', on_click=space_callback, shortcut=' ')

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])