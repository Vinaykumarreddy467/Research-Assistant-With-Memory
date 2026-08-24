import { exportPdf } from '../api';

export default function ExportButton({ sessionHistory, sessionTitle }) {
  const handleExportPdf = async () => {
    if (!sessionHistory || sessionHistory.length === 0) return;
    try {
      const filename = sessionTitle || 'research-chat';
      await exportPdf(sessionHistory, filename);
    } catch (err) {
      alert('Failed to export PDF: ' + err.message);
    }
  };

  const handleExportJson = () => {
    if (!sessionHistory || sessionHistory.length === 0) return;
    try {
      const filename = sessionTitle || 'research-chat';
      const cleanName = filename.replace(/[^a-zA-Z0-9\s\-]/g, '').replace(/\s+/g, '-').substring(0, 50);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(sessionHistory, null, 2));
      const dlAnchorElem = document.createElement('a');
      dlAnchorElem.setAttribute("href",     dataStr     );
      dlAnchorElem.setAttribute("download", `${cleanName}.json`);
      dlAnchorElem.click();
    } catch (err) {
      alert('Failed to export JSON: ' + err.message);
    }
  };

  const isDisabled = !sessionHistory || sessionHistory.length === 0;

  return (
    <div style={{ display: 'flex', gap: '8px' }}>
      <button
        onClick={handleExportPdf}
        className="export-button"
        disabled={isDisabled}
      >
        📥 Export PDF
      </button>
      <button
        onClick={handleExportJson}
        className="export-button"
        disabled={isDisabled}
      >
        📋 Export JSON
      </button>
    </div>
  );
}
