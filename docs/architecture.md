# Architecture

```
┌─────────────────┐   JWT   ┌───────────────────────┐   web3.py   ┌────────────────────────┐
│  Mobile (Expo)  │ ──────▶ │  Django REST API      │ ──────────▶ │  AdhahiSupplyChain.sol │
│  - Login        │         │  - Sheep / Event CRUD │             │  Ethereum Sepolia      │
│  - Dashboard    │         │  - SHA-256 hashing    │             │  Stores only bytes32   │
│  - QR scan      │ ◀────── │  - Role perms         │ ◀────────── │  + timestamp + sender  │
│  - Timeline     │  JSON   │  - QR generator       │   verify    └────────────────────────┘
└─────────────────┘         └───────────┬───────────┘
                                        │ ORM
                                        ▼
                                   SQLite/Postgres
```

## Hashing

For every event the backend builds a canonical JSON payload, e.g.:
```json
{
  "type": "event",
  "tag_id": "ADH-ABCDEF1234",
  "status": "quarantine",
  "location": "Quarantine Yard A",
  "notes": "21-day observation",
  "actor": "inspector1",
  "timestamp": "2026-04-25T10:15:00+00:00"
}
```
`SHA-256(canonical_json)` → `0x…` hex → sent to contract as `bytes32`.

## Why only hashes on-chain?

* **Privacy:** no PII ever leaves the backend.
* **Cost:** gas stays tiny and constant per event.
* **Integrity:** any tamper with DB breaks the hash match → `verifyEvent()` returns false.

## Roles & permissions

| Role        | Can do                                                |
|-------------|-------------------------------------------------------|
| admin       | Register sheep, any status update, view everything    |
| inspector   | Add `quarantine` / `health_check` / `issue`           |
| transporter | Add `transported` / `delivered`                       |
| public      | Scan QR → read-only timeline + verification badge     |

## Extending

* Swap SQLite → Postgres via `DATABASES` env.
* Add push notifications (Expo push tokens saved per user).
* IPFS pinning for photos, with the CID included in the hashed payload.
