import os

import streamlit as st
from openai import NotFoundError

from japanese_rag.util.weaviate import get_weaviate_client
import openai

def get_credentials():
    openai_api_key = st.session_state.get("OPENAI_API_KEY") if st.session_state.get("OPENAI_API_KEY") else st.secrets["OPENAI_API_KEY"]
    weaviate_url = st.session_state.get("WEAVIATE_URL") if st.session_state.get("WEAVIATE_URL") else st.secrets["WEAVIATE_URL"]
    weaviate_api_key = st.session_state.get("WEAVIATE_API_KEY") if st.session_state.get("WEAVIATE_API_KEY") else st.secrets["WEAVIATE_API_KEY"]

    if not openai_api_key:
        st.warning(
            "Enter a valid OpenAI API key under the 'APIs' tab."
        )

    if not weaviate_api_key:
        st.warning(
            "Enter your Weaviate API key under the 'APIs' tab."
        )

    # https://jp-test-om5t4vwr.weaviate.network
    if not weaviate_url:
        st.warning(
            "Enter your Weaviate API URL under the 'APIs' tab."
        )

    if not openai_api_key or not weaviate_api_key or not weaviate_url:
        st.stop()

    os.environ['OPENAI_API_KEY'] = openai_api_key

    # Todo: Check weaviate & openai key / url validity and exit if fail
    weaviate_client = get_weaviate_client(weaviate_url, weaviate_api_key)

    if not weaviate_client:
        st.error(
            "Failed to create Weaviate API client with the provided credentials. Check your credentials and try again."
        )
        st.stop()

    return weaviate_client