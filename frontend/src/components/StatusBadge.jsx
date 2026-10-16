import { statusLabel } from '../format.js';

export default function StatusBadge({ status }) {
  return <span className={`status status--${status}`}><span className="status-dot" />{statusLabel(status)}</span>;
}
