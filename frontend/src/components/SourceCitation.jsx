export default function SourceCitation({ citation }) {
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="source-citation"
      title={citation.snippet}
    >
      {new URL(citation.url).hostname}
    </a>
  );
}
