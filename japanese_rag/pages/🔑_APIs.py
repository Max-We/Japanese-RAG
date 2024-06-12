import openai
import streamlit as st


st.set_page_config(page_title="APIs", page_icon="🇯🇵", layout="wide")
st.title("🔑 APIs")

st.markdown("""
                The credentials entered here will be used to authenticate with the OpenAI and Weaviate APIs.
                
                These values override the environment secrets set in the Streamlit console and are lost as soon as the app restarts.
                It is therefore recommended to change the secrets in the Streamlit console if you want to persist the changes over longer periods.
            """
        )

open_ai_key_input = st.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="Paste your OpenAI API key here (sk-...)",
    value=st.session_state["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.session_state else None,
)

# Validate OpenAI API key
open_ai_key_is_valid = True
if open_ai_key_input:
    try:
        openai.api_key = open_ai_key_input

        models = openai.models.list()
        openai.chat.completions.create(
            model=models.data[0].id,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,

        )
    except openai.AuthenticationError:
        openai.api_key = None
        st.warning(
            "Your OpenAI API key is invalid and will not be saved. Please enter a valid key."
        )
        open_ai_key_is_valid = False

weaviate_key_input = st.text_input(
    "Weaviate API Key",
    type="password",
    placeholder="Paste your Weaviate API key here",
    value=st.session_state["WEAVIATE_API_KEY"] if "WEAVIATE_API_KEY" in st.session_state else None,
)

weaviate_url_input = st.text_input(
    "Weaviate URL",
    placeholder="Paste your Weaviate URL here",
    value=st.session_state["WEAVIATE_URL"] if "WEAVIATE_URL" in st.session_state else None,
)

# Set states
st.session_state.OPENAI_API_KEY = open_ai_key_input if open_ai_key_is_valid else None
st.session_state.WEAVIATE_URL = weaviate_url_input
st.session_state.WEAVIATE_API_KEY = weaviate_key_input
