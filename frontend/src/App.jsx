import React, { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'
import RevealCanvas from './components/RevealCanvas.jsx'
import Breakglass from './components/Breakglass.jsx'

function usePoll(fn, ms, deps = []) {
  const [data, setData] = useState(null)
  const [live, setLive] = useState(true)
  useEffect(() => {
    let on = true
    const tick = () => fn().then(d => on && (setData(d), setLive(true)))
                          .catch(() => on && setLive(false))
    tick(); const id = setInterval(tick, ms)
    return () => { on = false; clearInterval(id) }
  }, deps)
  return [data, live]
}

function StatsPanel() {
  const [stats] = usePoll(() => api.stats(), 1500)
  const [truth] = usePoll(() => api.truth(), 1500)
  const eps = stats?.epsilon_remaining ?? 0
  return (
    <div className="panel">
      <div className="panel-h"><h2>Zone A · privacy-preserved analytics</h2><span className="idx">ε-DP</span></div>
      <div className="readout">
        <div className="cell">
          <div className="k">REPORTED (NOISED)</div>
          <div className="v amber">{stats?.suppressed ? '—' : Math.round(stats?.value ?? 0)}</div>
        </div>
        <div className="cell">
          <div className="k">TRUE COUNT (DEMO ONLY)</div>
          <div className="v">{truth?.true_count ?? 0}</div>
        </div>
      </div>
      <div className="panel-b">
        <div className="k lbl">PRIVACY BUDGET REMAINING — {eps.toFixed(1)} / 10.0 ε</div>
        <div className="bar"><i style={{ width: `${(eps / 10) * 100}%` }} /></div>
        <div className="lbl" style={{ marginTop: 8 }}>
          The gap between reported and true is calibrated Laplace noise — enough that
          no single person's presence is detectable.
        </div>
      </div>
    </div>
  )
}

function PrivacyGauge() {
  const [ps] = usePoll(() => api.privacyScore(), 2000)
  const pct = Math.round((ps?.score ?? 1) * 100)
  return (
    <div className="panel">
      <div className="panel-h"><h2>Privacy auditor · adversarial re-ID</h2><span className="idx">RED-TEAM</span></div>
      <div className="panel-b gauge">
        <div className="pct">{pct}%</div>
        <div className="meta">
          re-identification resistance<br />
          <b style={{ color: 'var(--bone)' }}>{ps?.attempts ?? 0}</b> attacks ·
          <b style={{ color: 'var(--bone)' }}> {ps?.successful_reids ?? 0}</b> succeeded<br />
          our own model attacks the redacted feed and fails
        </div>
      </div>
    </div>
  )
}

function AlertsFeed() {
  const [alerts] = usePoll(() => api.alerts(), 1500)
  return (
    <div className="panel">
      <div className="panel-h"><h2>Safety brain · anomaly stream</h2><span className="idx">AUTOENCODER</span></div>
      <div className="panel-b">
        {(alerts ?? []).map((a, i) => (
          <div className="alert" key={i}>
            <span className={'badge ' + a.type}>{a.type}</span>
            <span style={{ color: 'var(--mute)' }}>{a.zone}</span>
            <span style={{ marginLeft: 'auto', color: 'var(--mute)' }}>score {a.score}</span>
          </div>
        ))}
        <div className="lbl" style={{ marginTop: 8 }}>Detected from movement &amp; density — never identity.</div>
      </div>
    </div>
  )
}

function Ledger({ refresh }) {
  const [entries] = usePoll(() => api.audit(), 2500, [refresh])
  const [head] = usePoll(() => api.auditHead(), 2500, [refresh])
  return (
    <div className="panel">
      <div className="panel-h"><h2>Transparency ledger</h2>
        <span className={'verify ' + (head?.verified ? 'ok' : 'bad')}>
          {head?.verified ? 'CHAIN VERIFIED' : 'TAMPERED'}</span></div>
      <div className="panel-b" style={{ maxHeight: 230, overflow: 'auto' }}>
        {(entries ?? []).slice().reverse().map(e => (
          <div className="row" key={e.seq}>
            <span className="seq">#{e.seq}</span>
            <span>
              <span className={'act-' + e.action}>{e.action}</span>
              {e.reason ? <span style={{ color: 'var(--mute)' }}> — {e.reason}</span> : null}
              <div className="hash">{e.entry_hash}</div>
            </span>
            <span style={{ color: 'var(--mute)' }}>{e.approvers?.join(', ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Ask() {
  const [q, setQ] = useState('How many people in zone A?')
  const [a, setA] = useState(null)
  const ask = () => api.ask(q).then(setA).catch(e => setA({ answer: String(e) }))
  return (
    <div className="panel">
      <div className="panel-h"><h2>Private insight assistant</h2><span className="idx">DP-BOUND</span></div>
      <div className="panel-b">
        <div className="ask-row">
          <input className="txt" value={q} onChange={e => setQ(e.target.value)}
                 onKeyDown={e => e.key === 'Enter' && ask()} />
          <button className="btn" onClick={ask}>Ask</button>
        </div>
        {a && <div className="ans">{a.answer}</div>}
        <div className="lbl" style={{ marginTop: 8 }}>
          Can only ever read differentially-private aggregates — structurally incapable of returning a person.
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [truth] = usePoll(() => api.truth(), 1500)
  const [root, live] = usePoll(() => api.stats(), 3000)
  const [refresh, setRefresh] = useState(0)
  const bump = useCallback(() => setRefresh(x => x + 1), [])

  return (
    <div className="wrap">
      <div className="mast">
        <div>
          <h1>OBSC<span className="o">U</span>RA</h1>
          <div className="tag">SEE THE THREAT. NOT THE PERSON.</div>
        </div>
        <div className="stamp">Classified // Privacy-Preserved</div>
      </div>
      <div className="ticker">
        <span><span className={'dot ' + (live ? 'live' : 'down')} />
          {live ? 'PIPELINE LIVE' : 'BACKEND OFFLINE — start uvicorn'}</span>
        <span>ZONE A · <b>{truth?.true_count ?? 0}</b> present</span>
        <span>MODE · <b>synthetic feed</b> (toggle real video in reveal)</span>
        <span>VORTEX · Codorra 2026</span>
      </div>

      <div className="grid">
        <div className="col">
          <div className="panel">
            <div className="panel-h"><h2>Edge anonymization · live reveal</h2><span className="idx">DRAG TO WIPE</span></div>
            <RevealCanvas count={truth?.true_count ?? 8} />
          </div>
          <StatsPanel />
          <Ask />
        </div>
        <div className="col">
          <PrivacyGauge />
          <AlertsFeed />
          <Breakglass onChange={bump} />
          <Ledger refresh={refresh} />
        </div>
      </div>

      <div className="footer">
        <span>OBSCURA · public safety that cannot become mass surveillance</span>
        <span>Team VORTEX — Raktim · Nipun · Juhi · Pronov</span>
      </div>
    </div>
  )
}
