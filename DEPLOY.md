# Backend deployment

Deploy the five backend services (gateway + 4 microservices) with **Docker Compose** locally or **Render** in the cloud.

Managed services you still need (not in Compose):

- MongoDB Atlas (`design_db`, `media_db`, `subscription_db`)
- Upstash Redis (design cache, presence, AI jobs)
- Upstash Vector (RAG)
- Cloudinary, DeepSeek, Stripe/Razorpay, Google OAuth

---

## 1. Prepare env files

Copy each `.env.example` to `.env` and fill in real values:

| Service | File |
|---|---|
| api-gateway | `api-gateway/.env` |
| design-service | `design-service/.env` |
| upload-service | `upload-service/.env` |
| subscription-service | `subscription-service/.env` |
| ai-service | `ai-service/.env` |

**Important for cloud / Compose without Kafka:**

```env
# ai-service/.env
KAFKA_DISABLED=true
```

Gateway service URLs use short names (`DESIGN`, `UPLOAD`, `SUBSCRIPTION`, `AI`) — not `DESIGN_SERVICE_URL`.

---

## 2. Docker Compose (local or VPS)

From this repo root:

```bash
docker compose up --build
```

- Gateway: `http://localhost:5000/health`
- Readiness (all services): `http://localhost:5000/ready`

Compose overrides internal URLs so services talk over the Docker network. Your `.env` files still supply Atlas, Upstash, Cloudinary, etc.

**First ai-service build** takes several minutes (sentence-transformers + rembg).

---

## 3. Render (Blueprint)

1. Push this repo to GitHub.
2. Render → **New** → **Blueprint** → connect the repo.
3. Render reads `render.yaml` and creates 5 web services.
4. In the Render dashboard, set secrets marked `sync: false`:
   - Gateway: `GOOGLE_CLIENT_ID`
   - Design: `MONGO_URI`, Upstash Redis
   - Upload: `MONGO_URI`, Cloudinary keys
   - Subscription: `MONGO_URI`, `FRONTEND_URL`, Stripe/Razorpay
   - AI: `DEEPSEEK_API_KEY`, Upstash Redis + Vector, optional `HF_TOKEN`
5. After deploy, copy the **public URL** of `canva-api-gateway` → set frontend `API_URL` on Vercel.

**Subscription redirects:** set `FRONTEND_URL` to your Vercel app, e.g. `https://your-app.vercel.app`.

**Google OAuth:** add your Vercel URL to authorized origins and redirect URIs in Google Cloud Console.

---

## 4. Frontend (Vercel)

| Variable | Value |
|---|---|
| `API_URL` | Render gateway URL, e.g. `https://canva-api-gateway.onrender.com` |
| `AUTH_URL` | Vercel app URL |
| `AUTH_SECRET` | same as local |
| `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` | same Google client |

Gateway must have the same `GOOGLE_CLIENT_ID` as the frontend OAuth client.

---

## 5. Health checks

| Service | Liveness | Readiness |
|---|---|---|
| api-gateway | `GET /health` | `GET /ready` (pings all 4 backends) |
| design / upload / subscription | `GET /health` | `GET /ready` (Mongo connected) |
| ai-service | `GET /health` | `GET /ready` (Redis + Vector) |

---

## 6. Kafka (optional)

- **Render / Compose default:** `KAFKA_DISABLED=true` — AI jobs run inline in ai-service.
- **Local dev with Redpanda:** `KAFKA_DISABLED=false`, run `npm run kafka:up` from `my-project` and `npm run dev:image-worker`.

Design-service Kafka events are optional; failures are logged only.

---

## 7. Build one service manually

```bash
# Node example
docker build -t canva-gateway ./api-gateway
docker run --rm -p 5000:5000 --env-file api-gateway/.env canva-gateway

# AI example (slow first build)
docker build -t canva-ai ./ai-service
docker run --rm -p 5004:5004 --env-file ai-service/.env -e KAFKA_DISABLED=true canva-ai
```

---

## Render free tier notes

- Services spin down after inactivity; first request may take ~30s.
- AI service image is large; upgrade plan if builds time out.
- Five separate web services = five free slots (gateway is the only public URL the frontend needs).
