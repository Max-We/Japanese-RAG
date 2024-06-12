import streamlit as st

from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI, ChatOpenAI
from langchain_community.vectorstores import Weaviate
from langchain.memory import ConversationBufferMemory
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableSequence
from langchain_core.messages import get_buffer_string
from langchain_core.prompts import format_document

from japanese_rag.util.prompt import DEFAULT_DOCUMENT_PROMPT, CONDENSE_QUESTION_PROMPT, ANSWER_PROMPT

import openai as opeanai_openai

WEAVIATE_INDEX_NAME = "Japanese"
def load_documents(directory):
    text_loader_kwargs={'autodetect_encoding': True}
    loader = DirectoryLoader(
      directory,
      glob="**/*.txt",
      use_multithreading=True,
      silent_errors=True,
      loader_kwargs=text_loader_kwargs,
      loader_cls=TextLoader
    )

    return loader.load()

def chunk_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return text_splitter.split_documents(documents)

def create_embeddings(client, chunks):
    return Weaviate.from_documents(
        chunks,
        client=client,
        index_name=WEAVIATE_INDEX_NAME,
        embedding=OpenAIEmbeddings(),
        by_text=False,
    )

def get_retriever(client) -> VectorStore:
    db = Weaviate(
        client=client,
        index_name=WEAVIATE_INDEX_NAME,
        text_key="text",
        embedding=OpenAIEmbeddings(),
        by_text=False,
        attributes=["text", "source"]
    )
    return db.as_retriever()

def get_llm(model_name):
    return ChatOpenAI(model_name=model_name)

def get_memory():
    if "memory" not in st.session_state or "loaded_memory" not in st.session_state:
        memory = ConversationBufferMemory(
            return_messages=True, output_key="answer", input_key="question"
        )
        loaded_memory = RunnablePassthrough.assign(
            chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
        )

        st.session_state.loaded_memory = loaded_memory
        st.session_state.memory = memory

        return memory, loaded_memory
    else:
        return st.session_state.memory, st.session_state.loaded_memory

def clear_memory():
    if "memory" in st.session_state:
        st.session_state["memory"].clear()
    st.session_state.messages = []

def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)

def create_chain(llm, retriever, memory):
    # Now we calculate the standalone question
    standalone_question = {
        "standalone_question": {
            "question": lambda x: x["question"],
            "chat_history": lambda x: get_buffer_string(x["chat_history"]),
        }
        | CONDENSE_QUESTION_PROMPT
        | llm
        | StrOutputParser(),
    }
    # Now we retrieve the documents
    retrieved_documents = {
        "docs": itemgetter("standalone_question") | retriever,
        "question": lambda x: x["standalone_question"],
    }
    # Now we construct the inputs for the final prompt
    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
    }
    # And finally, we do the part that returns the answers
    answer = {
        "answer": final_inputs | ANSWER_PROMPT | llm,
        "docs": itemgetter("docs"),
    }
    # And now we put it all together!
    final_chain = memory | standalone_question | retrieved_documents | answer
    return final_chain

def invoke(question, llm, retriever, memory: ConversationBufferMemory, loaded_memory):
    chain: RunnableSequence = create_chain(llm, retriever, loaded_memory)
    inputs = {"question": question}
    result = chain.invoke(inputs)

    memory.save_context(inputs, {"answer": result["answer"].content})
    return result

def get_openai_models():
    try:
        # List all available OpenAI models
        models = opeanai_openai.models.list()

        # Filter the models to get the ones used for instruction-following
        return [model.id for model in models.data if "gpt" in model.id]
    except Exception:
        return ["gpt-3.5-turbo"]
