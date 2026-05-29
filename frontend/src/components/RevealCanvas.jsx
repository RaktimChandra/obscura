import React, { useRef, useEffect, useState } from 'react'
import { api } from '../api.js'

// Animated plaza: left of the wipe = RAW (faces + ID tags exposed),
// right of the wipe = OBSCURA (faces replaced by redaction bars, only skeletons
// and counts remain). Tied to the live true head-count from the backend.
// "Use real feed" attempts the MJPEG stream and falls back to the simulation
// (with a notice) if the real CV path isn't configured.
export default function RevealCanvas({ count }) {
  const canvasRef = useRef(null)
  const figs = useRef([])
  const wipeRef = useRef(0.5)
  const [wipe, setWipe] = useState(0.5)
  const [real, setReal] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => { wipeRef.current = wipe }, [wipe])

  // keep figure population in step with the live count (capped for clarity)
  useEffect(() => {
    const target = Math.max(3, Math.min(28, count || 8))
    const arr = figs.current
    while (arr.length < target) {
      arr.push({ x: Math.random(), y: 0.25 + Math.random() * 0.6,
        vx: (Math.random() - 0.5) * 0.0016, vy: (Math.random() - 0.5) * 0.0012,
        id: 1000 + Math.floor(Math.random() * 8999) })
    }
    while (arr.length > target) arr.pop()
  }, [count])

  // draw loop — re-inits whenever we return to simulation mode
  useEffect(() => {
    if (real) return                       // real mode shows <img> streams instead
    const cv = canvasRef.current
    if (!cv) return
    const ctx = cv.getContext('2d')
    let raf
    const draw = () => {
      const dpr = window.devicePixelRatio || 1
      const w = cv.clientWidth, h = 340
      if (cv.width !== w * dpr) { cv.width = w * dpr; cv.height = h * dpr }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)
      ctx.strokeStyle = '#1a1a18'; ctx.lineWidth = 1
      for (let gx = 0; gx < w; gx += 38) { ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke() }
      for (let gy = 0; gy < h; gy += 38) { ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke() }
      const split = wipeRef.current * w
      figs.current.forEach(f => {
        f.x += f.vx; f.y += f.vy
        if (f.x < 0.02 || f.x > 0.98) f.vx *= -1
        if (f.y < 0.2 || f.y > 0.9) f.vy *= -1
        const px = f.x * w, py = f.y * h
        const exposed = px < split
        ctx.strokeStyle = exposed ? '#6b6457' : '#3f3f3a'; ctx.lineWidth = 2
        ctx.beginPath(); ctx.moveTo(px, py + 6); ctx.lineTo(px, py + 26); ctx.stroke()
        ctx.beginPath(); ctx.moveTo(px - 7, py + 34); ctx.lineTo(px, py + 26); ctx.lineTo(px + 7, py + 34); ctx.stroke()
        if (exposed) {
          ctx.fillStyle = '#c9a888'; ctx.beginPath(); ctx.arc(px, py, 7, 0, 7); ctx.fill()
          ctx.strokeStyle = '#d6453d'; ctx.lineWidth = 1; ctx.strokeRect(px - 10, py - 10, 20, 20)
          ctx.fillStyle = '#d6453d'; ctx.font = '9px IBM Plex Mono'
          ctx.fillText('ID:' + f.id, px + 12, py - 4)
        } else {
          ctx.fillStyle = '#000'; ctx.fillRect(px - 9, py - 8, 18, 16)
          ctx.fillStyle = '#76b06a'; ctx.fillRect(px - 9, py - 8, 18, 2)
          ctx.fillStyle = '#2f7d4f'
          ;[[px, py + 12], [px - 7, py + 34], [px + 7, py + 34]].forEach(([dx, dy]) => {
            ctx.beginPath(); ctx.arc(dx, dy, 1.6, 0, 7); ctx.fill() })
        }
      })
      ctx.fillStyle = '#f2a900'; ctx.fillRect(split - 1, 0, 2, h)
      ctx.fillStyle = '#d6453d'; ctx.font = '11px IBM Plex Mono'
      ctx.fillText('● RAW FEED — IDENTITIES EXPOSED', 12, 20)
      ctx.fillStyle = '#76b06a'
      ctx.fillText('OBSCURA — REDACTED ●', w - 168, 20)
      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(raf)
  }, [real])

  const exposed = figs.current.filter(f => f.x < wipe).length

  const enableReal = () => { setNotice(''); setReal(true) }
  const failReal = () => {
    setReal(false)
    setNotice('Real video feed not configured — showing simulation. Set OBSCURA_VIDEO and add the model files to enable it.')
  }

  return (
    <div className="reveal-wrap">
      {real ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: '#26261f' }}>
          <img src={api.base + '/video/raw'} alt="raw" style={{ width: '100%', display: 'block', background: '#070708' }}
               onError={failReal} />
          <img src={api.base + '/video/redacted'} alt="redacted" style={{ width: '100%', display: 'block', background: '#070708' }}
               onError={failReal} />
        </div>
      ) : (
        <canvas ref={canvasRef} className="scene" style={{ height: 340 }} />
      )}
      {!real && (
        <input className="slider" type="range" min="0" max="1" step="0.01"
               value={wipe} onChange={e => setWipe(+e.target.value)} />
      )}
      <div className="reveal-foot">
        <div className="expose">
          <span><span className="lbl">RAW EXPOSED</span><br /><span className="num raw">{real ? '—' : exposed}</span></span>
          <span><span className="lbl">OBSCURA EXPOSED</span><br /><span className="num safe">0</span></span>
        </div>
        <button className="btn ghost" onClick={() => (real ? setReal(false) : enableReal())}>
          {real ? 'Use simulation' : 'Use real feed'}
        </button>
      </div>
      {notice && <div className="lbl" style={{ padding: '0 14px 12px', color: 'var(--amber)' }}>{notice}</div>}
    </div>
  )
}
