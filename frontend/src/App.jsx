import { useState, useEffect, useCallback } from 'react';
import UrlIngestForm from './components/UrlIngestForm';
import ChatWindow from './components/ChatWindow';
import SourcesList from './components/SourcesList';
import ExportButton from './components/ExportButton';
import { getSources, getProvider } from './api';
import './App.css';

export default function App() {
  const [sources, setSources] = useState([]);
  const [provider, setProvider] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
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

  useEffect(() => {
    fetchSources();
    fetchProvider();
  }, [refreshTrigger, fetchSources, fetchProvider]);

  const handleIngestSuccess = () => {
    setRefreshTrigger((prev) => prev + 1);
    fetchSources();
  };

  const handleNewMessage = (exchange) => {
    setSessionHistory((prev) => [...prev, exchange]);
  };

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
          <SourcesList sources={sources} />
        </aside>

        <main className="main-content">
          <UrlIngestForm onIngestSuccess={handleIngestSuccess} />
          <ChatWindow
            refreshTrigger={refreshTrigger}
            onNewMessage={handleNewMessage}
          />
        </main>
      </div>
    </div>
  );
}
