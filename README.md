# 🐑 Adhahi Supply Chain Tracker

An end-to-end MVP that tracks the lifecycle of Eid Adhahi sheep from import to
delivery using **Ethereum (Sepolia testnet)** for tamper-evident data
integrity, plus QR codes for public verification, a mobile field app, and a
real-time admin dashboard.

```
Adhahi/
├── contracts/      Solidity smart contract + Hardhat 2 project
├── backend/        Django + DRF API + admin dashboard
├── mobile/         React Native (Expo SDK 51) app
└── docs/           Architecture & API notes
```

## High-level flow

1. **Admin** registers a sheep → backend creates a `Sheep` row, generates a
   QR code (`tag_id`), hashes the registration payload (SHA-256 over
   canonical JSON), and pushes the hash on-chain via `registerSheep`.
2. **Inspector / Transporter** add lifecycle events
   (`QUARANTINE`, `HEALTH_CHECK`, `TRANSPORTED`, `DELIVERED`). Each event
   payload is hashed, stored in DB, and anchored on-chain via `addEvent`.
3. **Public users / auditors** scan the QR code → mobile app calls
   `GET /api/sheep/<tag_id>/history/` and `…/verify/` to see the full
   timeline plus a per-record verification badge that re-computes the hash
   from the current DB row and compares it with the on-chain hash. Any
   mutation → instant `tampered: true`.

## What the verify endpoint actually proves

For every record (sheep registration + each event), `…/verify/` returns:

| Field                | Meaning                                                      |
|----------------------|--------------------------------------------------------------|
| `stored_hash`        | Hash committed at write time                                 |
| `recomputed_hash`    | Hash computed **right now** from the current DB row          |
| `anchored_on_chain`  | The stored hash exists in the Sepolia contract               |
| `data_matches_hash`  | `stored_hash == recomputed_hash` (no DB tampering)           |
| `verified`           | `anchored_on_chain AND data_matches_hash`                    |
| `tampered`           | `true` when the row was modified after anchoring             |

Hashed (protected) fields per event:
`tag_id, status, location, notes, latitude, longitude, actor, timestamp`.

## Quick start (3 terminals)

### A. Smart contract
```bash
cd contracts
npm install                 # Hardhat 2.22.10 (CommonJS)
cp .env.example .env        # SEPOLIA_RPC_URL + PRIVATE_KEY (64 hex chars)
npx hardhat compile
npx hardhat run scripts/deploy.js --network sepolia
# → copy the printed contract address into backend/.env (CONTRACT_ADDRESS)
```

Recommended free public RPC (no API key, no Infura):
`https://ethereum-sepolia-rpc.publicnode.com`

Faucet for free Sepolia ETH: https://sepoliafaucet.com

### B. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS
                            # set BLOCKCHAIN_DISABLED=True to run fully offline
python check_env.py         # validates RPC, chain id, balance, contract bytecode
python manage.py makemigrations tracker
python manage.py migrate

# Choose ONE seed strategy:
python manage.py seed_users   # users only — empty DB for live demos
python manage.py seed_demo    # users + 1 sheep + 5 anchored events (showcase)

python manage.py runserver 0.0.0.0:8000
```

Demo users (password = `password123`):

| username        | role         |
|-----------------|--------------|
| `admin1`        | admin        |
| `inspector1`   | inspector    |
| `transporter1`  | transporter  |

#### Re-anchor missing hashes
If a previous run failed to mine some transactions:
```bash
python manage.py reanchor             # publish only missing/unmined hashes
python manage.py reanchor --force     # re-publish everything (idempotent)
```

### C. Mobile
```bash
cd mobile
npm install
# set API base URL in src/config.js (default: http://10.0.2.2:8000 for Android emu)
npx expo start
```

The mobile app reads the user's role from the login response (no JWT decode
needed in React Native). Admins see the **Register Sheep** button;
inspectors/transporters see only the actions allowed by their role.

## Admin web dashboard

Open `http://localhost:8000/dashboard/` and log in with `admin1`. Includes:

* KPI cards (total sheep, total events, **unverified count**)
* Doughnut chart by status, bar chart by origin country
* Timeline (last 7 days) line chart
* Sheep table with search
* Recent events table with per-event verification badges
* Auto-refresh every 30s

## API summary

| Method | Endpoint                          | Auth                    | Purpose                                 |
|--------|-----------------------------------|-------------------------|-----------------------------------------|
| POST   | `/api/auth/login/`                | public                  | JWT pair (returns `role` + `username`)  |
| POST   | `/api/sheep/`                     | admin                   | Register sheep + QR + chain anchor      |
| GET    | `/api/sheep/`                     | any logged              | List sheep                              |
| GET    | `/api/sheep/<tag_id>/`            | public                  | Sheep details                           |
| POST   | `/api/sheep/<tag_id>/event/`      | inspector / transporter | Add lifecycle event (anchored)          |
| GET    | `/api/sheep/<tag_id>/history/`    | public                  | Full timeline                           |
| GET    | `/api/sheep/<tag_id>/verify/`     | public                  | Recompute + on-chain integrity check    |
| GET    | `/api/sheep/<tag_id>/qrcode/`     | public                  | PNG QR code                             |
| GET    | `/api/dashboard/stats/`           | admin                   | Aggregated stats for the dashboard      |

## Architecture & hardening notes

* **Hardhat 2.22.10** (CommonJS) — pinned because v3 broke the project's
  ESM/CJS setup. `hardhat.config.js` validates the private key format
  *before* attaching the `sepolia` network so a missing/short key gives a
  clear error instead of HH8.
* **web3.py 6.20.1** with a custom `BlockchainService`:
  * Local **nonce tracking** (`_next_nonce`) prevents
    "replacement transaction underpriced" on rapid sends.
  * **Gas price ×1.5** bump for faster mining on Sepolia.
  * Compatible with both `raw_transaction` and `rawTransaction`
    attribute names across web3.py versions.
  * `wait_receipt` flag — API calls wait, batch seed/reanchor jobs
    fire-and-forget so they never time out.
* **JWT** — `RoleTokenObtainPairSerializer` injects `role` + `username`
  claims into the token *and* the login response body.
  `SECRET_KEY` is a 50-byte `secrets.token_urlsafe` value (no
  `InsecureKeyLengthWarning`).
* **Hashing** — SHA-256 over canonical JSON
  (`json.dumps(payload, sort_keys=True, separators=(",",":"))`) so any
  byte-level mutation flips the hash.
* **Verification** — `SheepVerifyView` recomputes the hash from the
  current DB row and compares with the anchored hash. Tampering is
  detected even if the chain still contains the original commitment.

## Tamper-detection demo (live)

After running `seed_demo`, open a Django shell and mutate any anchored
field, e.g.:

```python
python manage.py shell
>>> from tracker.models import SheepEvent
>>> ev = SheepEvent.objects.first()
>>> ev.location = "Black Market Branch"; ev.save()
```

Then:

```bash
curl -s http://localhost:8000/api/sheep/<TAG>/verify/ | jq
```

→ that record now reports `verified: false`, `tampered: true`,
`data_matches_hash: false`. The dashboard's **Unverified** KPI turns red.

Restore a clean state for the next demo:

```bash
rm db.sqlite3 && python manage.py migrate && python manage.py seed_users
```

## Security

* JWT auth (SimpleJWT) with role claims.
* Role-based permissions (`IsAdmin`, `IsInspector`, `IsTransporter`).
* Public endpoints are explicitly read-only.
* Blockchain only stores **32-byte hashes**, never PII or business data.
* `check_env.py` script validates the deployment environment before going
  live (RPC reachable, correct chain id `11155111`, funded wallet,
  contract bytecode + ABI compatibility).

See `docs/architecture.md` for diagrams & rationale.
