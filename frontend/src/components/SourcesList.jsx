export default function SourcesList({ sources, onSelectSource }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="sources-list empty">
        <h3>Sources</h3>
        <p>No sources ingested yet.</p>
      </div>
    );
  }

  const getHostname = (url) => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  return (
    <div className="sources-list">
      <h3>Sources ({sources.length})</h3>
      <ul>
        {sources.map((source, i) => (
          <li key={i} className="clickable" onClick={() => onSelectSource?.(source.url)}>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%', overflow: 'hidden' }}>
              <span style={{ color: 'var(--accent)', fontSize: '0.875rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {getHostname(source.url)}
              </span>
              <span className="source-meta">
                {source.chunk_count} chunks
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
