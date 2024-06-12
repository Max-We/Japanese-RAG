import shutil

import streamlit as st

from japanese_rag.util.file_util import unzip_folder
from japanese_rag.util.langchain import load_documents, chunk_documents, create_embeddings, WEAVIATE_INDEX_NAME, \
    get_retriever
from japanese_rag.util.streamlit import get_credentials

DATA_DIR = "./data"

st.set_page_config(page_title="Data", page_icon="🇯🇵", layout="wide")
st.title("📁 Data")

weaviate_client = get_credentials()

with st.form("uploader", clear_on_submit=True, border=False):
    st.markdown("Upload a `.zip`-archive containing the `.txt.`-files that you want to index. You can upload as many archives as you want to and the uploaded documents will be concatenated to the existing DB documents.")
    uploaded_file = st.file_uploader(
        label="File Uploader",
        type=["zip"],
        help="Upload an archive containing the files in .txt format!",
    )

    upl_description_col, upl_submit_btn_col = st.columns([3, 1])

    with upl_description_col:
        st.markdown("Once you have selected a file, you can save the data into the DB by clicking the 'Submit' button.")

    with upl_submit_btn_col:
        submitted = st.form_submit_button("Submit", use_container_width=True)

    if uploaded_file and submitted:
        try:
            unzip_folder(uploaded_file, DATA_DIR)
        except Exception as e:
            st.error("Error reading file. Make sure the file is not corrupted or encrypted")
            st.stop()

        with st.spinner("Indexing document... This may take a while"):
            docs = load_documents(DATA_DIR)
            chunks = chunk_documents(docs)
            db = create_embeddings(weaviate_client, chunks)
            retriever = db.as_retriever()

        st.success(f"Loaded {len(docs)} documents in {len(chunks)} chunks.")

st.divider()

# display the data in a table

st.markdown("### Sources")


# Function to fetch all "source" values
def fetch_all_sources(client, className="Japanese"):
    unique_sources = set()  # Using a set to store unique "source" values
    offset = 0
    batch_size = 100  # Adjust based on your needs and Weaviate's performance

    while True:
        query = f"""
        {{
          Get {{
            {className}(limit: {batch_size}, offset: {offset}) {{
              source
            }}
          }}
        }}
        """
        results = client.query.raw(query)

        if "data" not in results:
            return None

        # Break if no more data is returned
        if not results['data']['Get'][className]:
            break

        # Extract "source" and add to the set
        for item in results['data']['Get'][className]:
            if item['source'] is not None:  # Ensure source is not None
                unique_sources.add(item['source'])

        offset += batch_size  # Increase offset for next batch

    return list(unique_sources)  # Convert set to list


# Fetch unique "source" values
unique_sources = fetch_all_sources(weaviate_client, "Japanese")

if unique_sources is None:
    st.markdown("Your Weaviate DB is currently empty. Upload some data via the File Uploader above.")
else:
    st.markdown("Your Weaviate DB contains the following documents.")
    st.table(unique_sources)

st.divider()

st.markdown("### Delete data")

description_col, del_btn_col = st.columns([3,1])

with description_col:
    st.markdown("If you wish to flush all records in the Vector DB, press the big red button.")

with del_btn_col:
    if st.button("Delete existing data", type="primary", use_container_width=True):
        with st.spinner("Deleting..."):
            weaviate_client.schema.delete_class(WEAVIATE_INDEX_NAME)
            weaviate_client.schema.create_class({ "class": WEAVIATE_INDEX_NAME })
            shutil.rmtree(DATA_DIR)
        st.rerun()
