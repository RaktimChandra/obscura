// All backend calls go through here. In dev, Vite proxies /api -> :8000.
// If you serve the built app elsewhere, set VITE_API_BASE.
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function j(path, opts) {
  const r = await fetch(BASE + path, opts)
  if (!r.ok) throw new Error(path + ' -> ' + r.status)
  return r.json()
}
const post = (p, body) =>
  j(p, { method: 'POST', headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(body) })

export const api = {
  base: BASE,
  stats: (zone = 'zone-A') => j(`/stats?zone=${zone}`),
  truth: (zone = 'zone-A') => j(`/truth?zone=${zone}`),
  alerts: () => j('/alerts'),
  privacyScore: () => j('/privacy-score'),
  audit: () => j('/audit'),
  auditHead: () => j('/audit/head'),
  demoRecords: () => j('/demo/records'),
  ask: (question) => post('/ask', { question }),
  bgRequest: (record_id, reason, requester) =>
    post('/breakglass/request', { record_id, reason, requester }),
  bgShare: (request_id, holder_id, share) =>
    post('/breakglass/share', { request_id, holder_id, share }),
}
