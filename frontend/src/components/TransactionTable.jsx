import { useState } from 'react';
import { money, shortDate } from '../format.js';
import { Icon } from './Icons.jsx';
import StatusBadge from './StatusBadge.jsx';

const filters = [
  ['all', 'All activity'],
  ['suggested', 'Suggested'],
  ['needs_review', 'Needs review'],
  ['reconciled', 'Reconciled'],
  ['ignored', 'Ignored'],
];

function MatchDetails({ transaction, onAction, busy }) {
  const proposed = transaction.matches.filter((match) => match.status === 'proposed');
  if (!transaction.matches.length) {
    return <span className="muted">{transaction.review_reason || 'No match suggested'}</span>;
  }
  return (
    <div className="match-list">
      {transaction.matches.map((match) => (
        <div className="match-entry" key={match.id}>
          <div className="match-identity">
            <strong>{match.investor_name}</strong>
            <span className="mono">
              {match.expected_reference} · Call #{match.capital_call_number}
            </span>
          </div>
          <p>{match.reason}</p>
          {match.status === 'proposed' && (
            <div className="match-actions">
              <button
                className="button button--approve"
                disabled={Boolean(busy)}
                onClick={() => onAction('approve', match.id)}
              >
                <Icon name="check" size={15} /> Approve
              </button>
              <button
                className="button button--subtle"
                disabled={Boolean(busy)}
                onClick={() => onAction('reject', match.id)}
              >
                Reject
              </button>
            </div>
          )}
          {match.status !== 'proposed' && (
            <span className={`match-outcome match-outcome--${match.status}`}>
              {match.status}
            </span>
          )}
        </div>
      ))}
      {transaction.review_reason && <p className="review-note">{transaction.review_reason}</p>}
      {proposed.length > 1 && (
        <p className="review-note">Review all candidates before approving one.</p>
      )}
    </div>
  );
}

export default function TransactionTable({ transactions, onAction, busy, loading, onRefresh }) {
  const [filter, setFilter] = useState('all');
  const visible = filter === 'all' ? transactions : transactions.filter((transaction) => transaction.status === filter);
  return (
    <section className="card transactions" aria-labelledby="activity-heading">
      <div className="section-head">
        <div>
          <div className="eyebrow">RECONCILIATION QUEUE</div>
          <h2 id="activity-heading">Bank activity</h2>
          <p>Review incoming wires and keep funding up to date.</p>
        </div>
        <button
          className="icon-button refresh-button"
          aria-label="Refresh data"
          title="Refresh data"
          onClick={onRefresh}
          disabled={loading}
        >
          <Icon name="refresh" size={19} />
        </button>
      </div>
      <div className="filter-bar" role="group" aria-label="Filter transactions">
        {filters.map(([value, label]) => (
          <button
            key={value}
            className={`filter ${filter === value ? 'filter--active' : ''}`}
            onClick={() => setFilter(value)}
          >
            {label}
            <span>
              {value === 'all'
                ? transactions.length
                : transactions.filter((transaction) => transaction.status === value).length}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="state"><div className="spinner" />Loading transactions…</div>
      ) : visible.length === 0 ? (
        <div className="state">
          <div className="state-icon"><Icon name="bank" size={25} /></div>
          <strong>No transactions here yet</strong>
          <span>
            {filter === 'all'
              ? 'Upload a statement to start reconciling.'
              : 'Try another status filter.'}
          </span>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date / reference</th><th>Bank description</th><th>Amount</th>
                <th>Status</th><th>Suggested match & reason</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((transaction) => (
                <tr key={transaction.id}>
                  <td className="nowrap">
                    <strong>{shortDate(transaction.date)}</strong>
                    <span className="table-sub mono">{transaction.reference}</span>
                  </td>
                  <td className="description-cell">
                    {transaction.description}
                    <span className="table-sub">
                      {transaction.type === 'debit' ? 'Outgoing debit' : 'Incoming credit'}
                    </span>
                  </td>
                  <td className={`amount-cell ${transaction.type === 'debit' ? 'amount-cell--debit' : ''}`}>
                    {money(transaction.amount)}
                  </td>
                  <td><StatusBadge status={transaction.status} /></td>
                  <td className="suggestion-cell">
                    <MatchDetails transaction={transaction} onAction={onAction} busy={busy} />
                  </td>
                  <td>
                    {transaction.type === 'credit'
                      && ['suggested', 'needs_review'].includes(transaction.status)
                      && (
                        <button
                          className="text-button"
                          disabled={Boolean(busy)}
                          onClick={() => onAction('ignore', transaction.id)}
                        >
                          Ignore
                        </button>
                      )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
