export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="sources-list empty">
        <h3>Sources</h3>
        <p>No sources ingested yet.</p>
      </div>
    );
  }

  return (
    <div className="sources-list">
      <h3>Sources ({sources.length})</h3>
      <ul>
        {sources.map((source, i) => (
          <li key={i}>
            <a href={source.url} target="_blank" rel="noopener noreferrer">
              {new URL(source.url).hostname}
            </a>
            <span className="source-meta">
              {source.chunk_count} chunks
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
