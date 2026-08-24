import { useState } from 'react';
import { ingestUrl } from '../api';

export default function UrlIngestForm({ onIngestSuccess }) {
  const [activeTab, setActiveTab] = useState('url'); // 'url' or 'file'
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await ingestUrl(url);
      setMessage({ type: 'success', text: `Ingested webpage! ${result.chunks_added || 0} chunks added.` });
      onIngestSuccess?.(url);
      setUrl('');
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleFileIngest = async (file) => {
    if (!file) return;
    const allowed = ['text/plain', 'text/markdown', 'text/x-markdown'];
    const isText = allowed.includes(file.type) || file.name.endsWith('.txt') || file.name.endsWith('.md');
    
    if (!isText) {
      setMessage({ type: 'error', text: 'Unsupported file type. Please upload a .txt or .md file.' });
      return;
    }

    setLoading(true);
    setMessage(null);

    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target.result;
      const fakeUrl = `file://${file.name}`;
      
      try {
        const response = await fetch('/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: file.name,
            raw_text: text,
            url: fakeUrl
          })
        });

        if (!response.ok) {
          throw new Error('Failed to ingest document');
        }

        const result = await response.json();
        setMessage({ type: 'success', text: `Ingested document! ${result.chunks_added || 0} chunks added.` });
        onIngestSuccess?.(fakeUrl);
      } catch (err) {
        setMessage({ type: 'error', text: err.message });
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      setMessage({ type: 'error', text: 'Error reading file content.' });
      setLoading(false);
    };

    reader.readAsText(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileIngest(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileIngest(e.target.files[0]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      <div className="ingest-tabs">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
          onClick={() => { setActiveTab('url'); setMessage(null); }}
        >
          🌐 Index Web URL
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'file' ? 'active' : ''}`}
          onClick={() => { setActiveTab('file'); setMessage(null); }}
        >
          📁 Index Document File
        </button>
      </div>

      <div className="ingest-form-container">
        {activeTab === 'url' ? (
          <form onSubmit={handleUrlSubmit} className="ingest-form">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a URL to add to knowledge base..."
              disabled={loading}
              required
            />
            <button type="submit" className="primary-btn" disabled={loading}>
              {loading ? 'Ingesting...' : 'Add URL'}
            </button>
          </form>
        ) : (
          <div
            className={`file-drop-area ${dragActive ? 'drag-over' : ''}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload-input').click()}
          >
            <input
              type="file"
              id="file-upload-input"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              accept=".txt,.md"
              disabled={loading}
            />
            <span>📥</span>
            <p>{loading ? 'Uploading & indexing...' : 'Drag & drop a .txt or .md file, or click to browse'}</p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Note: PDF parsing is supported via the Streamlit interface.
            </span>
          </div>
        )}
        {message && (
          <div className={`message ${message.type}`}>{message.text}</div>
        )}
      </div>
    </div>
  );
}
