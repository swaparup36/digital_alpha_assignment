import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api.js';
import { money, toCents } from './format.js';
import { Icon } from './components/Icons.jsx';
import LineItemPanel from './components/LineItemPanel.jsx';
import TransactionTable from './components/TransactionTable.jsx';
import UploadPanel from './components/UploadPanel.jsx';

const organizations = [
  { slug: 'northwind', name: 'Northwind Ventures' },
  { slug: 'bluebird', name: 'Bluebird Capital' },
];

export default function App() {
  const [organization, setOrganization] = useState('northwind');
  const [theme, setTheme] = useState(() => localStorage.getItem('clearline-theme') || 'light');
  const [transactions, setTransactions] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);
  const requestNumber = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('clearline-theme', theme);
  }, [theme]);

  const refresh = useCallback(async () => {
    const currentRequest = ++requestNumber.current;
    setLoading(true);
    setError('');
    try {
      const [nextTransactions, nextItems] = await Promise.all([
        api.transactions(organization), api.lineItems(organization),
      ]);
      if (currentRequest !== requestNumber.current) return;
      setTransactions(nextTransactions);
      setItems(nextItems);
    } catch (caught) {
      if (currentRequest === requestNumber.current) setError(caught.message);
    } finally {
      if (currentRequest === requestNumber.current) setLoading(false);
    }
  }, [organization]);

  useEffect(() => {
    requestNumber.current += 1;
    setTransactions([]);
    setItems([]);
    setSummary(null);
    refresh();
  }, [refresh]);

  async function upload(file) {
    setUploading(true);
    setError('');
    setSummary(null);
    try {
      const result = await api.importCsv(organization, file);
      setSummary(result);
      await refresh();
    } catch (caught) {
      setError(caught.message);
    } finally {
      setUploading(false);
    }
  }

  async function act(type, id) {
    setBusy(`${type}-${id}`);
    setError('');
    let actionError = null;
    try {
      await api[type](organization, id);
    } catch (caught) {
      actionError = caught.message;
    } finally {
      await refresh();
      if (actionError) setError(actionError);
      setBusy('');
    }
  }

  const stats = useMemo(() => ({
    incoming: transactions.filter((t) => t.type === 'credit').length,
    review: transactions.filter((t) => t.status === 'needs_review').length,
    reconciled: transactions.filter((t) => t.status === 'reconciled').length,
    funded: items.reduce((total, item) => total + toCents(item.amount_funded), 0n),
  }), [transactions, items]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><span /></div>
          <span>clearline<span className="brand-period">.</span></span>
        </div>

        <div className="topbar-actions">
          <span className="workspace-label">WORKSPACE</span>
          <select
            aria-label="Organization"
            value={organization}
            disabled={Boolean(busy) || uploading}
            onChange={(event) => setOrganization(event.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.slug} value={org.slug}>{org.name}</option>
            ))}
          </select>
          <button
            className="icon-button theme-button"
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            title={theme === 'light' ? 'Dark mode' : 'Light mode'}
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          >
            <Icon name={theme === 'light' ? 'moon' : 'sun'} size={19} />
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="page-heading">
          <div>
            <div className="eyebrow">OVERVIEW <span className="eyebrow-line" /> CAPITAL OPERATIONS</div>
            <h1>Reconciliation, made clear.</h1>
            <p>Match bank activity to capital calls with confidence.</p>
          </div>
          <div className="heading-note">
            <span className="live-dot" />
            {organizations.find((org) => org.slug === organization)?.name} workspace
          </div>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <Icon name="info" size={18} />
            <span>{error}</span>
            <button aria-label="Dismiss error" onClick={() => setError('')}>
              <Icon name="close" size={16} />
            </button>
          </div>
        )}

        <div className="overview-grid">
          <div className="stat-card">
            <span>Incoming payments</span><strong>{loading ? '-' : stats.incoming}</strong>
            <small>Credits in this workspace</small>
          </div>
          <div className="stat-card">
            <span>Needs attention</span><strong>{loading ? '-' : stats.review}</strong>
            <small>Payments awaiting review</small>
          </div>
          <div className="stat-card">
            <span>Reconciled</span><strong>{loading ? '-' : stats.reconciled}</strong>
            <small>Approved payments</small>
          </div>
          <div className="stat-card stat-card--funded">
            <span>Total funded</span><strong>{loading ? '-' : money(stats.funded)}</strong>
            <small>Across all capital calls</small>
          </div>
        </div>

        <UploadPanel onUpload={upload} uploading={uploading} summary={summary} />
        <div className="content-grid">
          <TransactionTable
            transactions={transactions}
            onAction={act}
            busy={busy}
            loading={loading}
            onRefresh={refresh}
          />
          <LineItemPanel items={items} loading={loading} />
        </div>
        <footer className="footer">
          <span>Clearline / Capital operations</span>
          <span>Review every match before funds are recorded.</span>
        </footer>
      </main>
    </div>
  );
}
