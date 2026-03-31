import streamlit as st
from chatbot import get_response
from rag import create_vector_store

st.set_page_config(page_title="AI Assistant", layout="wide")

st.title("🤖 AI Assistant")


# ---------------- SESSION STATE ----------------

if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if "search_index" not in st.session_state:
    st.session_state.search_index = 0


# ---------------- SIDEBAR ----------------

st.sidebar.title("💬 Chats")

for chat in st.session_state.chats:

    if st.sidebar.button(chat):
        st.session_state.current_chat = chat


if st.sidebar.button("➕ New Chat"):

    new_chat = f"Chat {len(st.session_state.chats)+1}"

    st.session_state.chats[new_chat] = []

    st.session_state.current_chat = new_chat


messages = st.session_state.chats[st.session_state.current_chat]


# ---------------- TOP BAR ----------------

col1, col2, col3 = st.columns(3)

with col1:

    if st.button("🧹 Clear Chat"):
        messages.clear()
        st.rerun()


with col2:

    st.download_button(
        "💾 Export Chat",
        str(messages),
        file_name="chat_history.txt"
    )


with col3:

    st.write("📊 Messages:", len(messages))


# ---------------- SEARCH ----------------

search_query = st.text_input("🔎 Search in chat")

search_results = []
target_message = None

if search_query:

    for i, msg in enumerate(messages):

        if search_query.lower() in msg["content"].lower():
            search_results.append(i)

    st.write(f"Matches found: {len(search_results)}")

    if search_results:

        col1, col2 = st.columns(2)

        if col1.button("⬅ Previous"):
            st.session_state.search_index = max(
                0,
                st.session_state.search_index - 1
            )

        if col2.button("Next ➡"):
            st.session_state.search_index = min(
                len(search_results) - 1,
                st.session_state.search_index + 1
            )

        target_message = search_results[
            st.session_state.search_index
        ]


# ---------------- DISPLAY CHAT ----------------

for i, msg in enumerate(messages):

    if i == target_message:
        st.markdown("<div id='target'></div>", unsafe_allow_html=True)

    with st.chat_message(msg["role"]):

        if msg["role"] == "user":

            if st.session_state.edit_index == i:

                new_text = st.text_area(
                    "Edit message",
                    value=msg["content"],
                    key=f"edit_{i}"
                )

                col1, col2 = st.columns(2)

                if col1.button("✔ Update", key=f"update_{i}"):

                    messages[i]["content"] = new_text

                    if i + 1 < len(messages):
                        messages.pop(i + 1)

                    response = get_response(messages)

                    messages.insert(
                        i + 1,
                        {
                            "role": "assistant",
                            "content": response
                        }
                    )

                    st.session_state.edit_index = None
                    st.rerun()

                if col2.button("Cancel", key=f"cancel_{i}"):

                    st.session_state.edit_index = None
                    st.rerun()

            else:

                col1, col2 = st.columns([10,1])

                with col1:

                    text = msg["content"]

                    if search_query and i in search_results:

                        text = text.replace(
                            search_query,
                            f"<mark>{search_query}</mark>"
                        )

                        st.markdown(text, unsafe_allow_html=True)

                    else:
                        st.markdown(text)

                with col2:

                    if st.button("✏️", key=f"editbtn_{i}"):

                        st.session_state.edit_index = i
                        st.rerun()

        else:

            text = msg["content"]

            if search_query and i in search_results:

                text = text.replace(
                    search_query,
                    f"<mark>{search_query}</mark>"
                )

                st.markdown(text, unsafe_allow_html=True)

            else:
                st.markdown(text)


# ---------------- AUTO SCROLL ----------------

if target_message is not None:

    st.markdown(
        """
        <script>
        const element = window.parent.document.getElementById("target");
        if (element){
            element.scrollIntoView({behavior: "smooth"});
        }
        </script>
        """,
        unsafe_allow_html=True
    )


# ---------------- TOOL MENU ----------------

col1, col2 = st.columns([1,8])

with col1:

    tool = st.selectbox(
        "➕",
        ["None","Upload PDF","Upload Image","Upload File"],
        label_visibility="collapsed"
    )

with col2:

    prompt = st.chat_input("Ask anything...")


# ---------------- FILE UPLOAD ----------------

if tool == "Upload PDF":

    uploaded_pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_pdf:

        with open("temp.pdf","wb") as f:
            f.write(uploaded_pdf.read())

        st.session_state.vectorstore = create_vector_store("temp.pdf")

        st.success("PDF uploaded successfully!")


if tool == "Upload Image":

    uploaded_image = st.file_uploader(
        "Upload Image",
        type=["png","jpg","jpeg"]
    )

    if uploaded_image:
        st.image(uploaded_image)


if tool == "Upload File":

    st.file_uploader("Upload File")


# ---------------- CHAT ----------------

if prompt:

    messages.append({
        "role":"user",
        "content":prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)


    # ---- RAG ----

    if st.session_state.vectorstore:

        docs = st.session_state.vectorstore.similarity_search(
            prompt,
            k=3
        )

        context = "\n".join([
            doc.page_content for doc in docs
        ])

        rag_prompt = f"""
Answer using the context below.

Context:
{context}

Question:
{prompt}
"""

        response = get_response([
            {"role":"user","content":rag_prompt}
        ])

    else:

        response = get_response(messages)


    with st.chat_message("assistant"):

        placeholder = st.empty()
        text = ""

        for word in response.split():

            text += word + " "
            placeholder.markdown(text)


    messages.append({
        "role":"assistant",
        "content":response
    })

    st.rerun()
    