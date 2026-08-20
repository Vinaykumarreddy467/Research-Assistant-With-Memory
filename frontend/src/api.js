const API_BASE = '/api';

export async function ingestUrl(url) {
  // Step 1: Send URL to n8n webhook
  const n8nResponse = await fetch('http://localhost:5678/webhook/ingest-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  if (!n8nResponse.ok) {
    throw new Error('Failed to ingest URL via n8n');
  }

  return await n8nResponse.json();
}

export async function querySources(question, topK = 5) {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
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
