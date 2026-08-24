import os
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from urllib.parse import urlparse

# Page configuration
st.set_page_config(
    page_title="Antigravity | Grounded RAG Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS styling for premium SaaS dashboard feel
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap');

    /* Global Typography & Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }

    /* Glassmorphic Container Card */
    .premium-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: rgba(168, 85, 247, 0.35);
        box-shadow: 0 12px 40px rgba(168, 85, 247, 0.15);
    }

    /* Metric Cards styling */
    .metric-card-premium {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card-premium:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
    }
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #c084fc 0%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 5px 0;
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Citation cards inside chats */
    .citation-card-premium {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 12px 16px;
        margin-top: 8px;
        margin-bottom: 8px;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .citation-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }
    .citation-badge {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .citation-title-premium {
        font-family: 'Outfit', sans-serif;
        font-size: 0.9rem;
        color: #f1f5f9;
        font-weight: 600;
        text-decoration: none;
    }
    .citation-title-premium:hover {
        color: #3b82f6;
        text-decoration: underline;
    }
    .citation-snippet-premium {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.4;
        border-left: 2px solid #8b5cf6;
        padding-left: 10px;
        margin-top: 5px;
        font-style: italic;
    }

    /* Hero Landing Dashboard */
    .hero-section {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        backdrop-filter: blur(10px);
    }
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 8px 0;
        background: linear-gradient(135deg, #c084fc 0%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem;
        font-weight: 400;
        color: #94a3b8;
        margin: 0 0 18px 0;
    }

    /* Sidebar tweaks */
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
    .provider-tag-offline {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #ef444420;
        color: #ef4444;
        border: 1px solid #ef444440;
    }

    /* Chat bubble alignment rules */
    div[data-testid="stChatMessage"] {
        width: 85% !important;
        margin-bottom: 15px !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px) !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatar"] img[alt="user"]),
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        margin-left: auto !important;
        background-color: rgba(99, 102, 241, 0.12) !important;
        border: 1px solid rgba(99, 102, 241, 0.22) !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatar"] img[alt="assistant"]),
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        margin-right: auto !important;
        background-color: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
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

def ingest_text(title, text, url):
    try:
        res = requests.post(
            f"{BACKEND_URL}/ingest",
            json={"title": title, "raw_text": text, "url": url},
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


# Initialize session state variables
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

if "sessions" not in st.session_state:
    st.session_state.sessions = []

# Fetch active configurations
backend_ok = check_backend_health()
provider_data = get_provider_info() if backend_ok else {"active": "offline"}
sources = fetch_sources() if backend_ok else []
sessions = fetch_sessions() if backend_ok else []

# --- Sidebar Redesign ---
with st.sidebar:
    # Logo and App Identifier
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px;">
            <span style="font-size: 2.2rem;">🧠</span>
            <div>
                <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.3rem; background: linear-gradient(135deg, #c084fc 0%, #60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Antigravity</h3>
                <span style="color: #64748b; font-size: 0.75rem; font-weight: 500;">Research Assistant v1.2</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Active Connection State Banner
    if not backend_ok:
        st.markdown(
            """
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 10px; margin-bottom: 15px;">
                <span style="color: #ef4444; font-size: 0.8rem; font-weight: 600;">⚠️ Backend Offline</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        active_p = provider_data.get("active", "unknown")
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 500;">LLM Gateway</span>
                <span class="provider-tag">{active_p.upper()}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;'>Workspace Navigation</p>", unsafe_allow_html=True)
    
    # Selectable navigation options
    page = st.selectbox(
        "Navigation Selector",
        ["🏠 Dashboard", "💬 Research Chat", "📥 Ingestion Center"],
        label_visibility="collapsed",
    )
    
    st.divider()

    # RAG Settings Panel
    with st.expander("⚙️ RAG Engine Settings"):
        top_k = st.slider("Top K Context Chunks", min_value=1, max_value=10, value=5, help="Number of semantic fragments sent to the LLM context window.")

    st.divider()

    # Active chat creator
    if st.button("➕ New Conversation", use_container_width=True):
        time_str = datetime.now().strftime("%H:%M")
        new_sess = create_session(f"Chat - {time_str}")
        if new_sess:
            st.session_state.active_session_id = new_sess["id"]
            st.rerun()

    # Chat Conversations List with Live Filtering Search
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;'>Active Conversations</p>", unsafe_allow_html=True)
    search_query = st.text_input("Search chats", placeholder="🔍 Search conversations...", label_visibility="collapsed")
    
    filtered_sessions = sessions
    if search_query:
        filtered_sessions = [s for s in sessions if search_query.lower() in s["title"].lower()]

    if filtered_sessions:
        if not st.session_state.active_session_id or not any(s["id"] == st.session_state.active_session_id for s in sessions):
            st.session_state.active_session_id = sessions[0]["id"]

        for sess in filtered_sessions:
            col1, col2 = st.columns([0.85, 0.15])
            is_active = sess["id"] == st.session_state.active_session_id
            
            # Formatted list buttons
            if is_active:
                btn_label = f"👉 {sess['title']}"
            else:
                btn_label = f"💬 {sess['title']}"

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
        st.info("No matching conversations found.")

    st.divider()

    # Sidebar Knowledge Sources Summary
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;'>Knowledge Base</p>", unsafe_allow_html=True)
    if sources:
        for src in sources:
            hostname = urlparse(src['url']).netloc or src['url']
            title = src.get('title') or hostname
            with st.expander(f"📄 {title[:22]}"):
                st.caption(f"**URL**: [{src['url']}]({src['url']})")
                st.caption(f"**Chunks**: {src.get('chunk_count', 0)}")
                if st.button("Start scoped chat", key=f"src_chat_{src['url']}", use_container_width=True):
                    new_sess = create_session(f"Chat: {hostname}", source_url=src["url"])
                    if new_sess:
                        st.session_state.active_session_id = new_sess["id"]
                        st.rerun()
    else:
        st.caption("No sources ingested yet.")

    # Sidebar Footer
    st.markdown(
        """
        <div style="position: relative; bottom: 0; width: 100%; text-align: center; color: #64748b; font-size: 0.7rem; margin-top: 30px;">
            Antigravity System Engine • Running Locally
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Page Routing ---

# 🏠 Page 1: Landing Dashboard & Analytics
if page == "🏠 Dashboard":
    # Hero Landing Banner
    st.markdown(
        """
        <div class="hero-section">
            <h1 class="hero-title">Grounded Research Assistant</h1>
            <p class="hero-subtitle">Redefining local document understanding with robust citations and multi-turn chat persistence.</p>
            <div style="display: flex; gap: 10px;">
                <span style="background: rgba(34, 197, 94, 0.1); color: #10b981; border: 1px solid rgba(34, 197, 94, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">🟢 Systems Online</span>
                <span style="background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">⚡ Groq Primary</span>
                <span style="background: rgba(139, 92, 246, 0.1); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">🛡️ Ollama Fallback</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core system metrics
    st.markdown("<div class='section-header'>📊 Workspace Metrics</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            f"""
            <div class="metric-card-premium">
                <div style="font-size: 1.8rem; margin-bottom: 5px;">📄</div>
                <div class="metric-value">{len(sources)}</div>
                <div class="metric-label">Ingested Sources</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        total_chunks = sum(src.get('chunk_count', 0) for src in sources)
        st.markdown(
            f"""
            <div class="metric-card-premium">
                <div style="font-size: 1.8rem; margin-bottom: 5px;">🧩</div>
                <div class="metric-value">{total_chunks}</div>
                <div class="metric-label">Vector Chunks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"""
            <div class="metric-card-premium">
                <div style="font-size: 1.8rem; margin-bottom: 5px;">💬</div>
                <div class="metric-value">{len(sessions)}</div>
                <div class="metric-label">Conversations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[3]:
        active_engine = provider_data.get("active", "OFFLINE").upper()
        text_color = "#10b981" if active_engine != "OFFLINE" else "#ef4444"
        st.markdown(
            f"""
            <div class="metric-card-premium">
                <div style="font-size: 1.8rem; margin-bottom: 5px;">🚀</div>
                <div class="metric-value" style="color: {text_color}; background: none; -webkit-text-fill-color: {text_color}; font-size: 1.8rem; margin-top: 10px; margin-bottom: 8px;">{active_engine}</div>
                <div class="metric-label">Gateway Engine</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Beautiful Plotly charts and statistics
    if sources:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("<div class='section-header'>📈 Source Categories</div>", unsafe_allow_html=True)
            # Domain distribution pie chart
            domains = []
            for src in sources:
                parsed = urlparse(src['url'])
                domain = parsed.netloc or parsed.path
                if domain.startswith("file://"):
                    domain = "Local Files"
                elif not domain:
                    domain = "Direct Input"
                domains.append(domain)
            
            df_domains = pd.DataFrame(domains, columns=["Source Domain"]).value_counts().reset_index()
            df_domains.columns = ["Source Domain", "Document Count"]
            
            fig_pie = px.pie(
                df_domains,
                values="Document Count",
                names="Source Domain",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f8fafc",
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            st.markdown("<div class='section-header'>📊 Volume by Source</div>", unsafe_allow_html=True)
            # Horizontal bar chart of sources by chunk size
            src_titles = [src.get('title') or urlparse(src['url']).netloc or src['url'] for src in sources]
            src_chunks = [src.get('chunk_count', 0) for src in sources]
            
            df_chunks = pd.DataFrame({
                "Document Name": [t[:30] + "..." if len(t) > 30 else t for t in src_titles],
                "Vector Chunks": src_chunks,
            })
            df_chunks = df_chunks.sort_values(by="Vector Chunks", ascending=True).tail(8)
            
            fig_bar = px.bar(
                df_chunks,
                x="Vector Chunks",
                y="Document Name",
                orientation="h",
                color="Vector Chunks",
                color_continuous_scale=px.colors.sequential.Purples,
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f8fafc",
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False,
            )
            fig_bar.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            fig_bar.update_yaxes(showgrid=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Ingest documents or URLs in the Ingestion Center to view knowledge analytics.")


# 💬 Page 2: ChatGPT-style Research Chat Interface
elif page == "💬 Research Chat":
    # Ensure active session
    if not st.session_state.active_session_id and backend_ok:
        default_sess = create_session("General Chat")
        if default_sess:
            st.session_state.active_session_id = default_sess["id"]
            st.rerun()

    # Load messages
    messages = []
    active_session = None
    if st.session_state.active_session_id and backend_ok:
        messages = fetch_session_messages(st.session_state.active_session_id)
        active_session = next((s for s in sessions if s["id"] == st.session_state.active_session_id), None)

    # Chat Header Section
    header_col1, header_col2 = st.columns([0.6, 0.4])
    with header_col1:
        if active_session:
            st.markdown(f"<h2 style='margin: 0; font-family: Outfit; font-weight: 700; color: #f8fafc;'>💬 {active_session['title']}</h2>", unsafe_allow_html=True)
            if active_session.get("source_url"):
                st.markdown(
                    f"<span style='background: rgba(139, 92, 246, 0.12); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.25); padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>Scoped Search: {active_session['source_url']}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Searching across entire knowledge base.")
    
    with header_col2:
        # Action bar buttons side-by-side
        if messages:
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
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    pdf_bytes = export_pdf(history_for_export)
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Export PDF",
                            data=pdf_bytes,
                            file_name=f"research_session_{st.session_state.active_session_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                with btn_col2:
                    json_data = json.dumps(messages, indent=2)
                    st.download_button(
                        label="📋 Export JSON",
                        data=json_data,
                        file_name=f"research_session_{st.session_state.active_session_id}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

    st.divider()

    # Compile unique citations bibliography for the active chat session
    cited_sources = {}
    for msg in messages:
        if msg.get("role") == "assistant":
            for cite in msg.get("citations", []):
                url = cite.get("url", "")
                if url:
                    hostname = urlparse(url).netloc or url
                    if url.startswith("file://"):
                        hostname = url.replace("file://", "")
                    cited_sources[url] = hostname
    
    if cited_sources:
        with st.expander("📚 Bibliography (Sources Cited in this Chat)"):
            st.markdown("<p style='font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px;'>The following sources were referenced to construct responses in this session:</p>", unsafe_allow_html=True)
            for url, name in cited_sources.items():
                st.markdown(f"- **[{name}]({url})**")

    # Message Display Pane
    if not messages:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 40px; margin-top: 30px;">
                <span style="font-size: 3rem;">💡</span>
                <h3 style="margin-top: 15px; color: #f8fafc;">Start Grounded Research</h3>
                <p style="color: #94a3b8; max-width: 500px; margin: 10px auto;">Ask a question below. The assistant will retrieve relevant chunks from your index and construct a response complete with citations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for msg in messages:
            role = msg.get("role", "assistant")
            avatar = "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""))
                
                # Render citation cards below assistant replies
                citations = msg.get("citations", [])
                if citations:
                    st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #8b5cf6; margin-top: 15px; margin-bottom: 5px; text-transform: uppercase;'>Linked Citations & Sources</p>", unsafe_allow_html=True)
                    for cite in citations:
                        url = cite.get("url", "")
                        snippet = cite.get("snippet", "")
                        hostname = urlparse(url).netloc or url
                        
                        # Shorten local file names
                        if url.startswith("file://"):
                            hostname = url.replace("file://", "")
                        
                        st.markdown(
                            f"""
                            <div class="citation-card-premium">
                                <div class="citation-header">
                                    <span class="citation-badge">Source</span>
                                    <a class="citation-title-premium" href="{url}" target="_blank">{hostname}</a>
                                </div>
                                <div class="citation-snippet-premium">"{snippet}"</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    # Chat Query Input
    user_query = st.chat_input("Ask a question about your ingested documents...")
    if user_query:
        if not backend_ok:
            st.error("Cannot query: backend is not reachable.")
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_query)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Analyzing semantic vectors and compiling response..."):
                    response = query_assistant(
                        question=user_query,
                        session_id=st.session_state.active_session_id,
                        top_k=top_k,
                    )

                    if "error" in response:
                        st.error(f"Generation failed: {response['error']}")
                    else:
                        st.markdown(response.get("answer", ""))
                        
                        citations = response.get("citations", [])
                        if citations:
                            st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #8b5cf6; margin-top: 15px; margin-bottom: 5px; text-transform: uppercase;'>Linked Citations & Sources</p>", unsafe_allow_html=True)
                            for cite in citations:
                                url = cite.get("url", "")
                                snippet = cite.get("snippet", "")
                                hostname = urlparse(url).netloc or url
                                
                                if url.startswith("file://"):
                                    hostname = url.replace("file://", "")

                                st.markdown(
                                    f"""
                                    <div class="citation-card-premium">
                                        <div class="citation-header">
                                            <span class="citation-badge">Source</span>
                                            <a class="citation-title-premium" href="{url}" target="_blank">{hostname}</a>
                                        </div>
                                        <div class="citation-snippet-premium">"{snippet}"</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
            st.rerun()


# 📥 Page 3: Ingestion Center Form & Dropzone
elif page == "📥 Ingestion Center":
    st.markdown("<h2 style='font-family: Outfit; font-weight: 700; color: #f8fafc;'>📥 Knowledge Ingestion Center</h2>", unsafe_allow_html=True)
    st.caption("Expand the vector memory by indexing web pages or local text/PDF documents.")
    
    st.divider()

    # Setup layout
    col1, col2 = st.columns(2)

    with col1:
        # URL Ingestion Form
        st.markdown(
            """
            <div class="premium-card">
                <h4 style="margin-top:0; color: #c084fc;">🌐 Ingest Web URL</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Scrapes and cleans main body content, and indexes generated embeddings directly.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        with st.form("url_ingest_form"):
            url_input = st.text_input("Enter Web URL", placeholder="https://example.com/topic")
            url_submit = st.form_submit_button("Index Webpage", use_container_width=True)
            
            if url_submit and url_input:
                with st.spinner("Running ingestion script..."):
                    success, res = ingest_url(url_input)
                    if success:
                        st.success(f"✅ Indexed successfully! Added {res.get('chunks_added', 0)} chunks.")
                        st.rerun()
                    else:
                        st.error(f"❌ Ingestion failed: {res.get('detail', 'Unknown connection error')}")

    with col2:
        # Document File Ingestion Form
        st.markdown(
            """
            <div class="premium-card">
                <h4 style="margin-top:0; color: #60a5fa;">📁 Upload Document</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Ingest plain text, markdown files, or extract and chunk PDF files locally.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        uploaded_file = st.file_uploader(
            "Upload TXT, MD, or PDF",
            type=["txt", "md", "pdf"],
            label_visibility="collapsed",
        )
        
        if uploaded_file is not None:
            file_name = uploaded_file.name
            st.info(f"Loaded: `{file_name}` ({uploaded_file.size} bytes)")
            
            if st.button("Index Document", type="primary", use_container_width=True):
                with st.spinner("Parsing and chunking document contents..."):
                    text = ""
                    parse_ok = True
                    
                    if file_name.endswith(".pdf"):
                        try:
                            import pypdf
                            reader = pypdf.PdfReader(uploaded_file)
                            text = ""
                            for page in reader.pages:
                                page_txt = page.extract_text()
                                if page_txt:
                                    text += page_txt + "\n"
                            
                            if not text.strip():
                                parse_ok = False
                                st.error("Parsed PDF content appears empty or non-extractable.")
                        except Exception as e:
                            parse_ok = False
                            st.error(f"Failed to extract PDF: {e}")
                    else:
                        # Direct text reader (txt or md)
                        try:
                            text = uploaded_file.read().decode("utf-8")
                        except Exception as e:
                            parse_ok = False
                            st.error(f"Failed to read file: {e}")

                    if parse_ok and text.strip():
                        # Call backend ingest directly
                        fake_url = f"file://{file_name}"
                        success, res = ingest_text(
                            title=file_name,
                            text=text,
                            url=fake_url,
                        )
                        if success:
                            st.success(f"✅ Ingested file successfully! Added {res.get('chunks_added', 0)} chunks.")
                            # Create a new conversation scoped to this file
                            new_sess = create_session(f"Chat: {file_name}", source_url=fake_url)
                            if new_sess:
                                st.session_state.active_session_id = new_sess["id"]
                            st.rerun()
                        else:
                            st.error(f"❌ Ingestion failed: {res.get('detail', 'Unknown error')}")
