import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const HOLDERS = ['police', 'oversight_officer', 'judiciary']

// The accountable de-anonymization flow: open a request, then collect a quorum
// of holder shares. No single party can unlock; every unlock is audited.
export default function Breakglass({ onChange }) {
  const [records, setRecords] = useState(null)
  const [recordId, setRecordId] = useState('')
  const [reason, setReason] = useState('Court order #2026-0441')
  const [req, setReq] = useState(null)
  const [submitted, setSubmitted] = useState([])
  const [status, setStatus] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.demoRecords().then(r => {
      setRecords(r)
      const first = Object.values(r)[0]
      if (first) setRecordId(first.record_id)
    }).catch(() => {})
  }, [])

  const shareFor = (holder) => {
    if (!records) return null
    const rec = Object.values(records).find(x => x.record_id === recordId)
    return rec ? rec.holder_shares[holder] : null
  }

  const open = async () => {
    setErr(''); setSubmitted([]); setStatus(null)
    try {
      const r = await api.bgRequest(recordId, reason, 'police')
      setReq(r); setStatus(r)
    } catch (e) { setErr(String(e)) }
  }

  const submit = async (holder) => {
    if (!req) return
    try {
      const r = await api.bgShare(req.request_id, holder, shareFor(holder))
      setSubmitted(s => [...new Set([...s, holder])])
      setStatus(r)
      if (r.status === 'unlocked') onChange && onChange()
    } catch (e) { setErr(String(e)) }
  }

  return (
    <div className="panel">
      <div className="panel-h"><h2>Accountable break-glass</h2><span className="idx">2-OF-3</span></div>
      <div className="panel-b">
        <div className="field">
          <label>SEALED RECORD</label>
          <select className="txt" value={recordId} onChange={e => setRecordId(e.target.value)}>
            {records && Object.entries(records).map(([k, v]) =>
              <option key={v.record_id} value={v.record_id}>{k} · {v.record_id}</option>)}
          </select>
        </div>
        <div className="field">
          <label>JUSTIFICATION (written to public ledger)</label>
          <input className="txt" value={reason} onChange={e => setReason(e.target.value)} />
        </div>
        {!req
          ? <button className="btn" onClick={open}>Open de-anonymization request</button>
          : <>
              <div className="quorum">request {req.request_id} · {submitted.length}/{status?.shares_required ?? 2} shares</div>
              <div className="holders">
                {HOLDERS.map(h => (
                  <div key={h} className={'holder' + (submitted.includes(h) ? ' in' : '')}>
                    {h.replace('_', ' ')}
                    <br />
                    <button className="btn ghost" style={{ marginTop: 6, width: '100%' }}
                            disabled={submitted.includes(h) || status?.status === 'unlocked'}
                            onClick={() => submit(h)}>
                      {submitted.includes(h) ? 'share given' : 'submit share'}
                    </button>
                  </div>
                ))}
              </div>
            </>}
        {status?.status === 'unlocked' &&
          <div className="reveal-box">UNLOCKED → {status.revealed}<br />
            <span style={{ color: 'var(--mute)' }}>↳ event appended to audit ledger</span></div>}
        {status && status.status !== 'unlocked' && req &&
          <div className="quorum">status: {status.status} — need {(status.shares_required - status.shares_collected)} more</div>}
        {err && <div className="quorum" style={{ color: 'var(--red)' }}>{err}</div>}
      </div>
    </div>
  )
}
