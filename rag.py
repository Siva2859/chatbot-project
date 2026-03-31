import streamlit as st

# ---------------- CACHE EMBEDDINGS ----------------

@st.cache_resource
def load_embeddings():
    """
    Load embedding model only once.
    This prevents reloading on every Streamlit rerun.
    """

    from langchain_community.embeddings import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en"   # faster embedding model
    )

    return embeddings


# ---------------- CREATE VECTOR STORE ----------------

def create_vector_store(pdf_path):
    """
    Create FAISS vector database from uploaded PDF
    """

    # Lazy imports (load only when needed)
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS

    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Split text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    texts = splitter.split_documents(documents)

    # Load cached embeddings
    embeddings = load_embeddings()

    # Create vector database
    vectorstore = FAISS.from_documents(texts, embeddings)

    return vectorstore