import { useRef, useState } from 'react';
import { Icon } from './Icons.jsx';

export default function UploadPanel({ onUpload, uploading, summary }) {
  const input = useRef(null);
  const [file, setFile] = useState(null);

  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    await onUpload(file);
    setFile(null);
    if (input.current) input.current.value = '';
  }

  return (
    <section className="upload-panel" aria-labelledby="upload-heading">
      <div className="upload-art" aria-hidden="true"><Icon name="upload" size={26} /></div>
      <div className="upload-copy">
        <div className="eyebrow eyebrow--inverse">BANK STATEMENT</div>
        <h2 id="upload-heading">Bring payments into focus.</h2>
        <p>Upload a CSV to find likely capital call matches and review exceptions.</p>
        <form onSubmit={submit} className="upload-form">
          <label className="file-picker">
            <input
              ref={input}
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            <Icon name="upload" size={17} />
            <span>{file ? file.name : 'Choose CSV file'}</span>
          </label>
          <button className="button button--light" type="submit" disabled={!file || uploading}>
            {uploading ? 'Importing…' : 'Import statement'} <Icon name="arrow" size={17} />
          </button>
        </form>
        <p className="upload-hint">Columns: date, description, amount, type, reference</p>
      </div>

      {summary && (
        <div className="import-summary" role="status">
          <strong>Import complete</strong>
          <div className="import-totals">
            <span>{summary.imported} imported</span>
            <span>{summary.duplicates} duplicates</span>
            <span>{summary.errors.length} row errors</span>
          </div>
          {summary.errors.length > 0 && (
            <details>
              <summary>View row errors</summary>
              <ul>
                {summary.errors.map((error, index) => (
                  <li key={`${error.line}-${index}`}>
                    <b>Line {error.line}:</b> {error.message}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
