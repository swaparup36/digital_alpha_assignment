async function request(path, organization, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: { 'X-Organization': organization, ...options.headers },
    });
  } catch {
    throw new Error('Cannot reach the server. Check that the Django API is running.');
  }

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status}).`);
  }
  return body;
}

export const api = {
  transactions: (organization) => request('/transactions/', organization),
  lineItems: (organization) => request('/line-items/', organization),
  importCsv: (organization, file) => {
    const form = new FormData();
    form.append('file', file);
    return request('/imports/', organization, { method: 'POST', body: form });
  },
  approve: (organization, id) => request(`/matches/${id}/approve/`, organization, { method: 'POST' }),
  reject: (organization, id) => request(`/matches/${id}/reject/`, organization, { method: 'POST' }),
  ignore: (organization, id) => request(`/transactions/${id}/ignore/`, organization, { method: 'POST' }),
};
