import streamlit as st
from langchain_community.vectorstores.weaviate import Weaviate

from japanese_rag.util.langchain import get_llm, get_memory, \
    invoke, get_retriever, get_openai_models, clear_memory
from japanese_rag.util.streamlit import get_credentials

MODELS = get_openai_models()

st.set_page_config(page_title="Chat", page_icon="🇯🇵", layout="wide")
st.title("🇯🇵 Chat")

weaviate_client = get_credentials()

# LLM
model_col, clear_col = st.columns([3,1])

with model_col:
    model_name: str = st.selectbox("Model", options=MODELS, label_visibility="collapsed")  # type: ignore

with clear_col:
    if st.button("Clear chat history", use_container_width=True):
        clear_memory()
        st.session_state.sources = []
        st.rerun()

# Weaviate data
retriever: Weaviate = get_retriever(weaviate_client)

# Chat memory
memory, loaded_memory = get_memory()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["content"] != "":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Accept user input
if prompt := st.chat_input("Please explain ... to me."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Display assistant response in chat message container
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = invoke(prompt, get_llm(model_name), retriever, memory, loaded_memory)
                st.session_state.messages.append({"role": "assistant", "content": response["answer"].content})
                st.markdown(response["answer"].content)

                st.session_state.sources = list(set([doc.metadata["source"] for doc in response["docs"]]))

if "sources" in st.session_state and len(st.session_state.sources) > 0:
    with st.expander("Sources"):
        for source in st.session_state.sources:
            st.write(source)
