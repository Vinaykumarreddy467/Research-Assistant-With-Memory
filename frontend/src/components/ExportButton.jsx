import { exportPdf } from '../api';

export default function ExportButton({ sessionHistory, sessionTitle }) {
  const handleExport = async () => {
    if (!sessionHistory || sessionHistory.length === 0) return;
    try {
      const filename = sessionTitle || 'research-chat';
      await exportPdf(sessionHistory, filename);
    } catch (err) {
      alert('Failed to export PDF: ' + err.message);
    }
  };

  return (
    <button
      onClick={handleExport}
      className="export-button"
      disabled={!sessionHistory || sessionHistory.length === 0}
    >
      Download PDF
    </button>
  );
}
