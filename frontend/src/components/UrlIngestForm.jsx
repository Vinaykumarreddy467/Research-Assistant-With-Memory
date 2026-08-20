import { useState } from 'react';
import { ingestUrl } from '../api';

export default function UrlIngestForm({ onIngestSuccess }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await ingestUrl(url);
      setMessage({ type: 'success', text: `Ingested! ${result.chunks_added || ''} chunks added.` });
      setUrl('');
      onIngestSuccess?.();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="ingest-form">
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Paste a URL to add to knowledge base..."
        disabled={loading}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Ingesting...' : 'Add URL'}
      </button>
      {message && (
        <div className={`message ${message.type}`}>{message.text}</div>
      )}
    </form>
  );
}
