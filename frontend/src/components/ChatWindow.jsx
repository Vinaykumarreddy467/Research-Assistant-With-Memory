import { useState, useRef, useEffect } from 'react';
import { querySources, getSessionMessages } from '../api';
import MessageBubble from './MessageBubble';

export default function ChatWindow({ activeSessionId, onMessagesChange, refreshTrigger }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load message history when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      onMessagesChange?.([]);
      return;
    }

    const loadHistory = async () => {
      setHistoryLoading(true);
      try {
        const data = await getSessionMessages(activeSessionId);
        const formatted = data.map((msg) => ({
          role: msg.role,
          text: msg.content,
          citations: msg.citations || [],
          provider: msg.provider || null,
          foundInSources: msg.role === 'assistant' ? (msg.citations && msg.citations.length > 0) : null,
        }));
        setMessages(formatted);
        onMessagesChange?.(formatted);
      } catch (err) {
        console.error('Failed to load chat history:', err);
      } finally {
        setHistoryLoading(false);
      }
    };

    loadHistory();
  }, [activeSessionId, onMessagesChange]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !activeSessionId) return;

    const userMessage = { role: 'user', text: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    onMessagesChange?.(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      const result = await querySources(input, 5, activeSessionId);
      const assistantMessage = {
        role: 'assistant',
        text: result.answer,
        citations: result.citations,
        provider: result.provider,
        foundInSources: result.found_in_sources,
      };
      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      onMessagesChange?.(finalMessages);
    } catch (err) {
      const errorMessage = { role: 'assistant', text: `Error: ${err.message}` };
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      onMessagesChange?.(finalMessages);
    } finally {
      setLoading(false);
    }
  };

  if (!activeSessionId) {
    return (
      <div className="chat-window">
        <div className="messages">
          <div className="empty-state">
            <h2>No Active Chat</h2>
            <p>Select or create a conversation in the sidebar to start chatting.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {historyLoading ? (
          <div className="empty-state">
            <p>Loading conversation history...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-state">
            <h2>Research Assistant</h2>
            <p>Ask questions about your sources. Follow-up queries will remember prior conversation context.</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))
        )}
        {loading && (
          <div className="message-bubble assistant loading">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your sources..."
          disabled={loading || historyLoading}
        />
        <button type="submit" disabled={loading || historyLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
