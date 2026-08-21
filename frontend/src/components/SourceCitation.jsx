export default function SourceCitation({ citation }) {
  let hostname;
  try {
    hostname = new URL(citation.url).hostname;
  } catch {
    hostname = citation.url;
  }

  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="source-citation"
      title={`Evidence from source: "${citation.snippet}"`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '3px 8px',
        borderRadius: '12px',
        backgroundColor: 'var(--bg-tertiary)',
        border: '1px solid var(--border)',
        color: 'var(--accent)',
        textDecoration: 'none',
        fontSize: '0.75rem',
        margin: '2px',
        transition: 'all 0.2s ease',
      }}
    >
      📄 {hostname}
    </a>
  );
}
