# API Endpoints Summary - Quick Reference

## All Available Endpoints

### Authentication (No Token Required)
1. `GET /api/` - Health check
2. `POST /api/auth/register` - Register new user
3. `POST /api/auth/login` - Login and get JWT token

### Instance Management (Token Required)
4. `POST /api/instances/` - Register AWS instance
5. `GET /api/instances/` - Get all user instances
6. `POST /api/instances/<instance_id>/monitor/start` - Start monitoring
7. `POST /api/instances/<instance_id>/monitor/stop` - Stop monitoring

### Metrics & Decisions (Token Required)
8. `GET /api/metrics/<instance_id>` - Get instance metrics
9. `GET /api/metrics/decisions/<instance_id>` - Get scaling decisions

---

## Quick Test Flow for Postman

### 1. Register User
**POST** `http://localhost:5000/api/auth/register`
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

### 2. Login
**POST** `http://localhost:5000/api/auth/login`
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```
**→ Copy the token from response**

### 3. Register Instance
**POST** `http://localhost:5000/api/instances/`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`
- `Content-Type: application/json`

**Body:**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "instance_type": "t2.micro",
  "region": "us-east-1"
}
```

### 4. Start Monitoring
**POST** `http://localhost:5000/api/instances/i-1234567890abcdef0/monitor/start`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`

### 5. Get Instances
**GET** `http://localhost:5000/api/instances/`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`

### 6. Get Metrics (wait 30+ seconds after starting monitoring)
**GET** `http://localhost:5000/api/metrics/i-1234567890abcdef0?limit=50`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`

### 7. Get Scaling Decisions (wait for metrics to accumulate)
**GET** `http://localhost:5000/api/metrics/decisions/i-1234567890abcdef0?limit=20`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`

### 8. Stop Monitoring
**POST** `http://localhost:5000/api/instances/i-1234567890abcdef0/monitor/stop`

**Headers:**
- `Authorization: Bearer YOUR_TOKEN_HERE`

---

## Important Notes

- **Token Format:** Always use `Bearer YOUR_TOKEN` in Authorization header
- **Token Expiry:** 24 hours
- **Metrics Collection:** Every 30 seconds (only for monitored instances)
- **Scaling Decisions:** Every 15 seconds (only for monitored instances)
- **Decision Logic:** CPU mean ± 31 threshold
- **Base URL:** `http://localhost:5000`

For detailed documentation, see API_DOCUMENTATION.md
