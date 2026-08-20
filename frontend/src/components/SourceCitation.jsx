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
      title={citation.snippet}
    >
      {hostname}
    </a>
  );
}
