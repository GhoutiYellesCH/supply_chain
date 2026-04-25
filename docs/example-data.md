# Example API calls

Assumes backend at `http://localhost:8000` and you have run `seed_demo`.

## 1. Login (admin)
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"password123"}'
```
Response:
```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi...",
  "role": "admin",
  "username": "admin1"
}
```
Export token:
```bash
export TOKEN="eyJhbGciOi..."
```

## 2. Register a sheep (admin only)
```bash
curl -X POST http://localhost:8000/api/sheep/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "Australia",
    "import_date": "2026-04-25",
    "batch_number": "BATCH-2026-007"
  }'
```

## 3. List sheep
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/sheep/
```

## 4. Add lifecycle event (inspector)
```bash
curl -X POST http://localhost:8000/api/sheep/ADH-XXXXXXXXXX/event/ \
  -H "Authorization: Bearer $INSPECTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "quarantine",
    "location": "Quarantine Yard A",
    "notes": "21-day observation started"
  }'
```

## 5. Public timeline
```bash
curl http://localhost:8000/api/sheep/ADH-XXXXXXXXXX/history/
```

## 6. Blockchain verification
```bash
curl http://localhost:8000/api/sheep/ADH-XXXXXXXXXX/verify/
```
```json
{
  "tag_id": "ADH-XXXXXXXXXX",
  "verified": true,
  "blockchain_disabled": false,
  "records": [
    { "type": "registration", "hash": "0x…", "tx": "0x…", "verified": true, "chain_meta": { "timestamp": 1745577600, "sender": "0x…" } },
    { "type": "event", "status": "imported", "hash": "0x…", "tx": "0x…", "verified": true },
    ...
  ]
}
```

## 7. QR code (PNG)
Open in a browser:
```
http://localhost:8000/api/sheep/ADH-XXXXXXXXXX/qrcode/
```
