import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env if it exists
load_dotenv()

st.set_page_config(page_title="Private Audio Transcriber", layout="wide")

# Session state for persistence
if "models_list" not in st.session_state:
    st.session_state.models_list = []

with st.sidebar:
    st.header("⚙️ Connection Settings")
    
    # Pre-fill from .env if available, else empty string
    default_url = os.getenv("NAI_BASE_URL", "")
    default_key = os.getenv("NAI_API_KEY", "")
    
    input_url = st.text_input("Service URL", value=default_url, placeholder="https://nai.example.com/enterpriseai/v1")
    input_key = st.text_input("Access Key", value=default_key, type="password")
    
    if st.button("🔌 Connect & Sync Models"):
        if not input_url or not input_key:
            st.warning("Please provide both a URL and an API Key.")
        else:
            try:
                client = OpenAI(base_url=input_url, api_key=input_key)
                models_data = client.models.list()
                st.session_state.models_list = [m.id for m in models_data.data]
                st.success(f"Connected! {len(st.session_state.models_list)} models found.")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

    if st.session_state.models_list:
        st.divider()
        st.subheader("🎯 Model Selection")
        stt_choice = st.selectbox("Speech-to-Text (STT)", st.session_state.models_list)
        llm_choice = st.selectbox("Summarizer (LLM)", st.session_state.models_list)
        st.divider()
        st.subheader("🌐 Language Selection")
        audio_lang = st.selectbox("Audio Language", ["en", "fr", "es", "de"], index=0)

# --- Main Logic ---
st.title("🎙️ Audio Transcriber & Summarizer")

if not st.session_state.models_list:
    st.info("👈 Set your connection details in the sidebar to get started.")
else:
    uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "webm"])

    if uploaded_file and st.button("🚀 Process Audio", type="primary"):
        # Explicitly defining the client with the UI/Env values
        client = OpenAI(base_url=input_url, api_key=input_key)
        
        try:
            with st.status("Working...", expanded=True) as status:
                st.write("Transcribing...")
                transcript = client.audio.transcriptions.create(
                    model=stt_choice, 
                    file=uploaded_file,
                    language=audio_lang
                )
                text = transcript.text
                
                st.write("Summarizing...")
                summary = client.chat.completions.create(
                    model=llm_choice,
                    messages=[{"role": "user", "content": f"Summarize this: {text}"}]
                )
                final_summary = summary.choices[0].message.content
                status.update(label="Complete!", state="complete")

            col1, col2 = st.columns(2)
            col1.text_area("Transcript", text, height=400)
            col2.markdown(f"### Summary\n{final_summary}")
            
        except Exception as e:
            st.error(f"Error: {e}")