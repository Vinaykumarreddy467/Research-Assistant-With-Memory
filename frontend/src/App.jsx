import { useState, useEffect, useCallback } from 'react';
import UrlIngestForm from './components/UrlIngestForm';
import ChatWindow from './components/ChatWindow';
import SourcesList from './components/SourcesList';
import ExportButton from './components/ExportButton';
import { getSources, getProvider, getSessions, createSession, deleteSession } from './api';
import './App.css';

export default function App() {
  const [sources, setSources] = useState([]);
  const [provider, setProvider] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);

  const fetchSources = useCallback(async () => {
    try {
      const data = await getSources();
      setSources(data.sources);
    } catch (err) {
      console.error('Failed to fetch sources:', err);
    }
  }, []);

  const fetchProvider = useCallback(async () => {
    try {
      const data = await getProvider();
      setProvider(data);
    } catch (err) {
      console.error('Failed to fetch provider:', err);
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data);
      if (data.length === 0) {
        const defaultSession = await createSession('General Chat');
        setSessions([defaultSession]);
        setActiveSessionId(defaultSession.id);
      } else if (!activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  }, [activeSessionId]);

  useEffect(() => {
    fetchSources();
    fetchProvider();
    fetchSessions();
  }, [refreshTrigger, fetchSources, fetchProvider, fetchSessions]);

  const handleNewChat = async () => {
    try {
      const title = `Chat - ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      const newSession = await createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch (err) {
      console.error('Failed to create new chat:', err);
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      const updated = sessions.filter((s) => s.id !== sessionId);
      setSessions(updated);
      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          setActiveSessionId(updated[0].id);
        } else {
          setActiveSessionId(null);
          setRefreshTrigger((prev) => prev + 1); // Trigger default session creation
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSelectSource = async (url) => {
    const existing = sessions.find((s) => s.source_url === url);
    if (existing) {
      setActiveSessionId(existing.id);
    } else {
      try {
        const hostname = new URL(url).hostname;
        const title = `Chat: ${hostname}`;
        const newSession = await createSession(title, url);
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
      } catch (err) {
        console.error('Failed to create URL-scoped chat:', err);
      }
    }
  };

  const handleIngestSuccess = (url) => {
    setRefreshTrigger((prev) => prev + 1);
    fetchSources();
    if (url) {
      handleSelectSource(url);
    }
  };

  const handleMessagesChange = useCallback((loadedMessages) => {
    const history = [];
    for (let i = 0; i < loadedMessages.length; i++) {
      const msg = loadedMessages[i];
      if (msg.role === 'user') {
        const nextMsg = loadedMessages[i + 1];
        if (nextMsg && nextMsg.role === 'assistant') {
          history.push({
            question: msg.content || msg.text || '',
            answer: nextMsg.content || nextMsg.text || '',
            citations: nextMsg.citations || [],
          });
          i++;
        } else {
          history.push({
            question: msg.content || msg.text || '',
            answer: '',
            citations: [],
          });
        }
      }
    }
    setSessionHistory(history);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Research Assistant</h1>
        <div className="header-right">
          {provider && (
            <span className={`provider-indicator ${provider.active}`}>
              {provider.active === 'groq' ? '⚡ Groq' : '🏠 Ollama'}
            </span>
          )}
          <ExportButton sessionHistory={sessionHistory} />
        </div>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <button className="new-chat-btn" onClick={handleNewChat}>
            ➕ New Chat
          </button>

          <div className="sessions-list">
            <h3>Conversations</h3>
            <ul>
              {sessions.map((session) => (
                <li
                  key={session.id}
                  className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                  onClick={() => setActiveSessionId(session.id)}
                >
                  <span className="session-title" title={session.title}>
                    {session.title}
                  </span>
                  <button
                    className="session-delete-btn"
                    onClick={(e) => handleDeleteSession(session.id, e)}
                  >
                    🗑️
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <SourcesList sources={sources} onSelectSource={handleSelectSource} />
        </aside>

        <main className="main-content">
          <UrlIngestForm onIngestSuccess={handleIngestSuccess} />
          <ChatWindow
            activeSessionId={activeSessionId}
            onMessagesChange={handleMessagesChange}
            refreshTrigger={refreshTrigger}
          />
        </main>
      </div>
    </div>
  );
}
