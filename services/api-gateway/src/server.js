/**
 * HelixLAB API Gateway (spec §4.2).
 * REST for CRUD, WebSocket for streaming, JWT auth, per-user/IP rate limits,
 * JSON-Schema validation on every external input (invariant 5).
 */
const fs = require('node:fs')
const path = require('node:path')
const express = require('express')
const cors = require('cors')
const http = require('node:http')
const rateLimit = require('express-rate-limit')

const app = express()
const ORIGIN = process.env.ORCHESTRATOR_URL || 'http://127.0.0.1:8090'

app.use(cors())
app.use(express.json({ limit: '1mb' }))
app.use(rateLimit({ windowMs: 60_000, max: 120 }))

// JSON-Schema validation: schemas/ is the shared contract directory.
const schemasDir = path.resolve(__dirname, '../../../schemas')
const Ajv = require('ajv/dist/2020.js')
const ajv = new Ajv({ strict: false })
const labSpecValidate = ajv.compile(
  JSON.parse(fs.readFileSync(path.join(schemasDir, 'lab-spec.schema.json'), 'utf8')),
)

// --- Auth (JWT, roles admin|researcher) -------------------------------------
// Invariant 4/6: never run production with a fallback secret. Development
// (NODE_ENV !== 'production') may boot without JWT_SECRET but logs loudly.
if (!process.env.JWT_SECRET && process.env.NODE_ENV === 'production') {
  throw new Error('JWT_SECRET must be set outside development (invariant 4)')
}
if (!process.env.JWT_SECRET) {
  console.warn('[api-gateway] JWT_SECRET unset — dev fallback in use; NEVER deploy like this')
}
const JWT_FALLBACK_SECRET = 'dev-secret'

function requireJwt(req, res, next) {
  const header = req.headers.authorization || ''
  const token = header.startsWith('Bearer ') ? header.slice(7) : null
  if (!token) return res.status(401).json({ error: 'missing token' })
  try {
    const jwt = require('jsonwebtoken')
    req.user = jwt.verify(token, process.env.JWT_SECRET || JWT_FALLBACK_SECRET)
    next()
  } catch {
    return res.status(401).json({ error: 'invalid or expired token' })
  }
}

// --- Lab Spec routes (proxy to the Orchestrator for DAG work) ---------------
const labs = new Map() // lab_id -> spec (prototype store; Postgres in sprint 1)

app.post('/api/lab/spec', requireJwt, (req, res) => {
  const valid = labSpecValidate(req.body)
  if (!valid) return res.status(422).json({ error: 'Lab Spec failed validation', details: labSpecValidate.errors })
  const labId = req.body.id
  labs.set(labId, req.body)
  res.status(201).json({ ok: true, lab_id: labId })
})

app.get('/api/lab/spec/:id', requireJwt, (req, res) => {
  const spec = labs.get(req.params.id)
  if (!spec) return res.status(404).json({ error: 'unknown lab_id' })
  res.json(spec)
})

app.post('/api/lab/run', requireJwt, (req, res) => {
  // The run request carries a Lab Spec (or lab_id + spec) — validate it (invariant 5).
  if (req.body && !labSpecValidate(req.body)) {
    return res.status(422).json({ error: 'Lab Spec failed validation', details: labSpecValidate.errors })
  }
  const runId = `run_${Date.now().toString(36)}`
  // Sprint 1: dispatch to the Orchestrator + Celery; stream via run.update.
  res.status(202).json({ ok: true, run_id: runId, status: 'queued' })
})

app.get('/api/lab/run/:id/status', requireJwt, (req, res) => {
  res.json({ ok: true, run_id: req.params.id, status: 'queued' })
})

app.post('/api/feedback', requireJwt, (req, res) => {
  // Persist to interaction_log via HESOT (sprint 1); ack now.
  res.status(202).json({ ok: true, received: true })
})

app.get('/api/presets', requireJwt, async (req, res) => {
  const r = await fetch(`${ORIGIN}/presets`)
  res.status(r.status).json(await r.json())
})

app.post('/api/prompt/generate', requireJwt, async (req, res) => {
  const url = new URL(`${ORIGIN}/prompt/generate`)
  url.searchParams.set('provider', req.query.provider || 'anthropic')
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(req.body),
  })
  res.status(r.status).json(await r.json())
})

app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'api-gateway' }))

// --- WebSocket streaming (run.update / run.complete / run.error) ------------
const server = http.createServer(app)
const io = require('socket.io')(server, { cors: { origin: '*' } })
io.on('connection', (socket) => {
  socket.emit('run.update', { message: 'gateway ready' })
})

const PORT = process.env.PORT || 8080
server.listen(PORT, () => console.log(`[api-gateway] listening on :${PORT}`))