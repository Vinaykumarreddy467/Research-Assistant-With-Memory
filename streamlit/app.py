import os
import requests
import streamlit as st
from datetime import datetime
from urllib.parse import urlparse

# Page configuration
st.set_page_config(
    page_title="Research Assistant with Memory",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .provider-tag {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #22c55e20;
        color: #22c55e;
        border: 1px solid #22c55e40;
    }
    .citation-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 0.85rem;
    }
    .citation-title {
        color: #3b82f6;
        font-weight: 600;
        text-decoration: none;
    }
    .citation-title:hover {
        text-decoration: underline;
    }
    .citation-snippet {
        color: #94a3b8;
        font-style: italic;
        margin-top: 4px;
    }
    .stChatMessage {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper functions for API calls
def check_backend_health():
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return res.status_code == 200
    except Exception:
        return False

def get_provider_info():
    try:
        res = requests.get(f"{BACKEND_URL}/provider", timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {"active": "offline"}

def fetch_sources():
    try:
        res = requests.get(f"{BACKEND_URL}/sources", timeout=5)
        if res.status_code == 200:
            return res.json().get("sources", [])
    except Exception as e:
        st.sidebar.error(f"Error fetching sources: {e}")
    return []

def fetch_sessions():
    try:
        res = requests.get(f"{BACKEND_URL}/sessions", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def create_session(title="New Conversation", source_url=None):
    try:
        res = requests.post(
            f"{BACKEND_URL}/sessions",
            json={"title": title, "source_url": source_url},
            timeout=5,
        )
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to create session: {e}")
    return None

def delete_session(session_id):
    try:
        res = requests.delete(f"{BACKEND_URL}/sessions/{session_id}", timeout=5)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Failed to delete session: {e}")
        return False

def fetch_session_messages(session_id):
    try:
        res = requests.get(f"{BACKEND_URL}/sessions/{session_id}/messages", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def ingest_url(url):
    try:
        res = requests.post(
            f"{BACKEND_URL}/ingest-url",
            json={"url": url},
            timeout=25,
        )
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"detail": str(e)}

def query_assistant(question, session_id=None, top_k=5):
    try:
        res = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question, "session_id": session_id, "top_k": top_k},
            timeout=60,
        )
        if res.status_code == 200:
            return res.json()
        else:
            err = res.json()
            return {"error": err.get("detail", "Query failed")}
    except Exception as e:
        return {"error": str(e)}

def export_pdf(session_history):
    try:
        res = requests.post(
            f"{BACKEND_URL}/export-pdf",
            json={"session_history": session_history},
            timeout=15,
        )
        if res.status_code == 200:
            return res.content
    except Exception as e:
        st.error(f"Failed to export PDF: {e}")
    return None


# Initialize session state
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

if "sessions" not in st.session_state:
    st.session_state.sessions = []

# Fetch initial backend status
backend_ok = check_backend_health()
provider_data = get_provider_info() if backend_ok else {"active": "offline"}

# --- Sidebar ---
with st.sidebar:
    st.title("📚 Research Assistant")
    
    if not backend_ok:
        st.warning(f"⚠️ FastAPI Backend not reachable at `{BACKEND_URL}`. Make sure it's running via `uvicorn main:app --port 8000`.")
    else:
        active_p = provider_data.get("active", "unknown")
        st.markdown(f"**Provider**: <span class='provider-tag'>{active_p.upper()}</span>", unsafe_allow_html=True)
    
    st.divider()

    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        time_str = datetime.now().strftime("%H:%M")
        new_sess = create_session(f"Chat - {time_str}")
        if new_sess:
            st.session_state.active_session_id = new_sess["id"]
            st.rerun()

    # Conversations Section
    st.subheader("Conversations")
    sessions = fetch_sessions() if backend_ok else []
    
    if sessions:
        if not st.session_state.active_session_id or not any(s["id"] == st.session_state.active_session_id for s in sessions):
            st.session_state.active_session_id = sessions[0]["id"]

        for sess in sessions:
            col1, col2 = st.columns([0.85, 0.15])
            is_active = sess["id"] == st.session_state.active_session_id
            btn_label = f"💬 {sess['title']}" if not is_active else f"👉 **{sess['title']}**"
            
            with col1:
                if st.button(btn_label, key=f"sess_{sess['id']}", use_container_width=True):
                    st.session_state.active_session_id = sess["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{sess['id']}", help="Delete chat"):
                    delete_session(sess["id"])
                    if st.session_state.active_session_id == sess["id"]:
                        st.session_state.active_session_id = None
                    st.rerun()
    else:
        st.info("No active conversations. Click 'New Chat' to start.")

    st.divider()

    # Sources Knowledge Base
    st.subheader("Knowledge Sources")
    sources = fetch_sources() if backend_ok else []
    
    if sources:
        for src in sources:
            hostname = urlparse(src['url']).netloc or src['url']
            title = src.get('title') or hostname
            with st.expander(f"📄 {title[:24]}"):
                st.caption(f"**URL**: [{src['url']}]({src['url']})")
                st.caption(f"**Chunks**: {src.get('chunk_count', 0)}")
                if st.button("Start scoped chat", key=f"src_chat_{src['url']}"):
                    new_sess = create_session(f"Chat: {hostname}", source_url=src["url"])
                    if new_sess:
                        st.session_state.active_session_id = new_sess["id"]
                        st.rerun()
    else:
        st.caption("No sources ingested yet.")


# --- Main Content Area ---
st.markdown("<div class='main-header'><span>🧠</span> Grounded Research Assistant</div>", unsafe_allow_html=True)
st.caption("Ingest web URLs into your persistent vector memory and ask grounded, citation-backed questions.")

# URL Ingestion Bar
with st.container():
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        ingest_input = st.text_input(
            "Add URL to knowledge base",
            placeholder="https://en.wikipedia.org/wiki/Artificial_intelligence",
            label_visibility="collapsed",
        )
    with col2:
        ingest_btn = st.button("Ingest URL", type="primary", use_container_width=True)

    if ingest_btn and ingest_input:
        with st.spinner("Fetching and indexing webpage content..."):
            success, res = ingest_url(ingest_input)
            if success:
                st.success(f"✅ Ingested successfully! ({res.get('chunks_added', 0)} chunks indexed)")
                # Automatically scope a new chat or reload
                hostname = urlparse(ingest_input).netloc or ingest_input
                new_sess = create_session(f"Chat: {hostname}", source_url=ingest_input)
                if new_sess:
                    st.session_state.active_session_id = new_sess["id"]
                st.rerun()
            else:
                st.error(f"❌ Ingestion failed: {res.get('detail', 'Unknown error')}")

st.divider()

# Ensure we have an active session
if not st.session_state.active_session_id and backend_ok:
    default_sess = create_session("General Chat")
    if default_sess:
        st.session_state.active_session_id = default_sess["id"]

# Load chat history for the active session
messages = []
if st.session_state.active_session_id and backend_ok:
    messages = fetch_session_messages(st.session_state.active_session_id)

# PDF Export Action Bar
if messages:
    pdf_col1, pdf_col2 = st.columns([0.8, 0.2])
    with pdf_col2:
        history_for_export = []
        for i in range(0, len(messages), 2):
            q_msg = messages[i] if i < len(messages) else None
            a_msg = messages[i+1] if i+1 < len(messages) else None
            if q_msg and q_msg.get("role") == "user":
                history_for_export.append({
                    "question": q_msg.get("content", ""),
                    "answer": a_msg.get("content", "") if a_msg else "",
                    "citations": a_msg.get("citations", []) if a_msg else [],
                })
        
        if history_for_export:
            pdf_bytes = export_pdf(history_for_export)
            if pdf_bytes:
                st.download_button(
                    label="📥 Export PDF",
                    data=pdf_bytes,
                    file_name=f"research_session_{st.session_state.active_session_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

# Display Messages
if not messages:
    st.info("💡 Ask any question about your ingested documents below. Citations and source URLs will be linked automatically.")
else:
    for msg in messages:
        role = msg.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))
            
            # Show citations if present
            citations = msg.get("citations", [])
            if citations:
                st.markdown("**Citations & Sources:**")
                for cite in citations:
                    url = cite.get("url", "")
                    snippet = cite.get("snippet", "")
                    hostname = urlparse(url).netloc or url
                    st.markdown(
                        f"""
                        <div class="citation-card">
                            🔗 <a class="citation-title" href="{url}" target="_blank">{hostname}</a>
                            <div class="citation-snippet">"{snippet}"</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# Chat Input
user_query = st.chat_input("Ask a question about your ingested sources...")
if user_query:
    if not backend_ok:
        st.error("Cannot query: backend is not reachable.")
    else:
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_query)

        # Call query endpoint
        with st.chat_message("assistant"):
            with st.spinner("Searching sources & generating grounded response..."):
                response = query_assistant(
                    question=user_query,
                    session_id=st.session_state.active_session_id,
                )

                if "error" in response:
                    st.error(f"Query error: {response['error']}")
                else:
                    st.markdown(response.get("answer", ""))
                    citations = response.get("citations", [])
                    if citations:
                        st.markdown("**Citations & Sources:**")
                        for cite in citations:
                            url = cite.get("url", "")
                            snippet = cite.get("snippet", "")
                            hostname = urlparse(url).netloc or url
                            st.markdown(
                                f"""
                                <div class="citation-card">
                                    🔗 <a class="citation-title" href="{url}" target="_blank">{hostname}</a>
                                    <div class="citation-snippet">"{snippet}"</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
        st.rerun()
