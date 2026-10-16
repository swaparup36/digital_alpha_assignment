export function toCents(value) {
  if (typeof value === 'bigint') return value;
  const text = String(value ?? 0);
  const negative = text.startsWith('-');
  const [whole, fraction = ''] = (negative ? text.slice(1) : text).split('.');
  const cents = BigInt(whole || '0') * 100n + BigInt(`${fraction}00`.slice(0, 2));
  return negative ? -cents : cents;
}

export function money(value) {
  const cents = toCents(value);
  const sign = cents < 0n ? '-' : '';
  const absolute = cents < 0n ? -cents : cents;
  const dollars = (absolute / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const rest = (absolute % 100n).toString().padStart(2, '0');
  return `${sign}$${dollars}.${rest}`;
}

export function shortDate(value) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(`${value}T00:00:00Z`));
}

export function statusLabel(status) {
  return {
    suggested: 'Suggested',
    needs_review: 'Needs review',
    reconciled: 'Reconciled',
    ignored: 'Ignored',
    open: 'Open',
    partially_funded: 'Partially funded',
    funded: 'Funded',
  }[status] || status;
}
