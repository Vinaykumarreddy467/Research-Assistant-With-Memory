const API_BASE = '/api';
const N8N_WEBHOOK = 'http://localhost:5678/webhook/ingest-url';

export async function ingestUrl(url) {
  // Try n8n first, fall back to backend direct ingest
  try {
    const n8nResponse = await fetch(N8N_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(180000),
    });

    if (n8nResponse.ok) {
      return await n8nResponse.json();
    }
  } catch {
    // n8n not available, fall through to backend
  }

  // Fallback: fetch URL content ourselves and send to backend
  const response = await fetch(`${API_BASE}/ingest-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error('Failed to ingest URL');
  }

  return await response.json();
}

export async function querySources(question, topK = 5, sessionId = null) {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error('Query failed');
  }

  return await response.json();
}

export async function getSources() {
  const response = await fetch(`${API_BASE}/sources`);
  if (!response.ok) {
    throw new Error('Failed to fetch sources');
  }
  return await response.json();
}

export async function getProvider() {
  const response = await fetch(`${API_BASE}/provider`);
  if (!response.ok) {
    throw new Error('Failed to fetch provider info');
  }
  return await response.json();
}

export async function exportPdf(sessionHistory) {
  const response = await fetch(`${API_BASE}/export-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_history: sessionHistory }),
  });

  if (!response.ok) {
    throw new Error('PDF export failed');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'session-export.pdf';
  a.click();
  window.URL.revokeObjectURL(url);
}

export async function getSessions() {
  const response = await fetch(`${API_BASE}/sessions`);
  if (!response.ok) {
    throw new Error('Failed to fetch sessions');
  }
  return await response.json();
}

export async function createSession(title, sourceUrl = null) {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, source_url: sourceUrl }),
  });
  if (!response.ok) {
    throw new Error('Failed to create session');
  }
  return await response.json();
}

export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
  return await response.json();
}

export async function getSessionMessages(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
  if (!response.ok) {
    throw new Error('Failed to fetch session messages');
  }
  return await response.json();
}
