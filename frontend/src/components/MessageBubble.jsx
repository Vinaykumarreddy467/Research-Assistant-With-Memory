import SourceCitation from './SourceCitation';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">
        {message.text}
      </div>
      {message.citations && message.citations.length > 0 && (
        <div className="citations">
          <span className="citations-label">Sources:</span>
          {message.citations.map((cite, i) => (
            <SourceCitation key={i} citation={cite} />
          ))}
        </div>
      )}
      {message.provider && (
        <div className="provider-badge">
          via {message.provider}
        </div>
      )}
    </div>
  );
}
