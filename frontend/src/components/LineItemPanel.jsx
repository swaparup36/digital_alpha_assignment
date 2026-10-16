import { money, shortDate } from '../format.js';
import StatusBadge from './StatusBadge.jsx';

export default function LineItemPanel({ items, loading }) {
  return (
    <section className="card commitments" aria-labelledby="commitments-heading">
      <div className="section-head">
        <div>
          <div className="eyebrow">CAPITAL CALLS</div>
          <h2 id="commitments-heading">Investor commitments</h2>
          <p>Funding progress by line item.</p>
        </div>
      </div>

      {loading ? (
        <div className="state"><div className="spinner" />Loading commitments…</div>
      ) : items.length === 0 ? (
        <div className="state">
          <strong>No line items</strong>
          <span>Run the seed command to add demo commitments.</span>
        </div>
      ) : (
        <div className="commitment-list">
          {items.map((item) => {
            const progress = Math.min(
              100,
              Math.max(0, (Number(item.amount_funded) / Number(item.amount_called)) * 100),
            );
            return (
              <article className="commitment" key={item.id}>
                <div className="commitment-top">
                  <div>
                    <strong>{item.investor_name}</strong>
                    <span className="mono">
                      {item.expected_reference} · Call #{item.capital_call_number}
                    </span>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
                <div
                  className="progress-track"
                  role="progressbar"
                  aria-valuenow={progress}
                  aria-valuemin="0"
                  aria-valuemax="100"
                  aria-label={`${item.investor_name} funded`}
                >
                  <span style={{ width: `${progress}%` }} />
                </div>
                <div className="commitment-numbers">
                  <div><small>Called</small><strong>{money(item.amount_called)}</strong></div>
                  <div><small>Funded</small><strong>{money(item.amount_funded)}</strong></div>
                  <div><small>Remaining</small><strong>{money(item.amount_remaining)}</strong></div>
                </div>
                <div className="commitment-dates">
                  Called {shortDate(item.call_date)} <span>·</span> Due {shortDate(item.due_date)}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
