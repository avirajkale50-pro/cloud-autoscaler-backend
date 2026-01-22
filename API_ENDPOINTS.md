# API Endpoints Documentation

## Quick Reference

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
10. `POST /api/metrics/simulate` - Simulate metrics for testing

---

## Detailed API Documentation

### 1. Health Check
**GET** `/api/`

**Description:** Check if the API is running.

**Response (200 OK):**
```json
{
  "message": "Cloud Resource Autoscaler API is running",
  "version": "1.0"
}
```

---

### 2. Register User
**POST** `/api/auth/register`

**Description:** Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

*400 Bad Request - Missing fields:*
```json
{
  "error": "Email and password are required"
}
```

*409 Conflict - User already exists:*
```json
{
  "error": "User with this email already exists"
}
```

---

### 3. Login
**POST** `/api/auth/login`

**Description:** Authenticate and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

*400 Bad Request:*
```json
{
  "error": "Email and password are required"
}
```

*401 Unauthorized:*
```json
{
  "error": "Invalid credentials"
}
```

---

### 4. Register Instance
**POST** `/api/instances/`

**Description:** Register an AWS EC2 instance for monitoring.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "instance_type": "t2.micro",
  "region": "us-east-1"
}
```

**Success Response (201 Created):**
```json
{
  "message": "Instance registered successfully",
  "instance": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "instance_id": "i-1234567890abcdef0",
    "instance_type": "t2.micro",
    "region": "us-east-1",
    "is_monitoring": false,
    "created_at": "2026-01-22T05:16:25.123456"
  }
}
```

**Error Responses:**

*400 Bad Request:*
```json
{
  "error": "instance_id and region are required"
}
```

*401 Unauthorized:*
```json
{
  "error": "Token is missing or invalid"
}
```

*409 Conflict:*
```json
{
  "error": "Instance already registered"
}
```

---

### 5. Get All Instances
**GET** `/api/instances/`

**Description:** Retrieve all instances registered by the authenticated user.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "instances": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "instance_id": "i-1234567890abcdef0",
      "instance_type": "t2.micro",
      "region": "us-east-1",
      "is_monitoring": true,
      "created_at": "2026-01-22T05:16:25.123456"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "instance_id": "i-0987654321fedcba0",
      "instance_type": "t2.small",
      "region": "us-west-2",
      "is_monitoring": false,
      "created_at": "2026-01-22T06:30:15.654321"
    }
  ]
}
```

---

### 6. Start Monitoring
**POST** `/api/instances/<instance_id>/monitor/start`

**Description:** Start monitoring an instance. Metrics will be collected every 30 seconds, and scaling decisions will be made every 15 seconds.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "message": "Monitoring started for instance i-1234567890abcdef0"
}
```

**Error Responses:**

*404 Not Found:*
```json
{
  "error": "Instance not found"
}
```

*403 Forbidden:*
```json
{
  "error": "Unauthorized: You don't own this instance"
}
```

*400 Bad Request:*
```json
{
  "error": "Instance is already being monitored"
}
```

---

### 7. Stop Monitoring
**POST** `/api/instances/<instance_id>/monitor/stop`

**Description:** Stop monitoring an instance.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "message": "Monitoring stopped for instance i-1234567890abcdef0"
}
```

**Error Responses:**

*404 Not Found:*
```json
{
  "error": "Instance not found"
}
```

*403 Forbidden:*
```json
{
  "error": "Unauthorized: You don't own this instance"
}
```

---

### 8. Get Instance Metrics
**GET** `/api/metrics/<instance_id>?limit=50`

**Description:** Retrieve metrics for a specific instance.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional, default=100): Maximum number of metrics to return

**Success Response (200 OK):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "metrics": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "timestamp": "2026-01-22T05:20:30.123456",
      "cpu_utilization": 45.2,
      "memory_usage": 62.8,
      "network_in": 1024000,
      "network_out": 512000,
      "is_outlier": false,
      "outlier_type": null
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "timestamp": "2026-01-22T05:21:00.654321",
      "cpu_utilization": 92.5,
      "memory_usage": 68.3,
      "network_in": 2048000,
      "network_out": 1024000,
      "is_outlier": true,
      "outlier_type": "scale_up"
    }
  ]
}
```

**Error Responses:**

*404 Not Found:*
```json
{
  "error": "Instance not found"
}
```

*403 Forbidden:*
```json
{
  "error": "Unauthorized: You don't own this instance"
}
```

---

### 9. Get Scaling Decisions
**GET** `/api/metrics/decisions/<instance_id>?limit=20`

**Description:** Retrieve scaling decisions for a specific instance.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional, default=50): Maximum number of decisions to return

**Success Response (200 OK):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "decisions": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "timestamp": "2026-01-22T05:21:00.123456",
      "cpu_utilization": 92.5,
      "memory_usage": 68.3,
      "network_in": 2048000,
      "network_out": 1024000,
      "decision": "scale_up",
      "reason": "Immediate scale up: CPU utilization (92.50%) exceeds 90% threshold"
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "timestamp": "2026-01-22T05:20:45.654321",
      "cpu_utilization": 45.2,
      "memory_usage": 62.8,
      "network_in": 1024000,
      "network_out": 512000,
      "decision": "no_action",
      "reason": "CPU utilization (45.20%) is within acceptable IQR range (30.50% - 65.80%)"
    },
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440007",
      "timestamp": "2026-01-22T05:20:30.987654",
      "cpu_utilization": 8.3,
      "memory_usage": 55.1,
      "network_in": 512000,
      "network_out": 256000,
      "decision": "scale_down",
      "reason": "Immediate scale down: CPU utilization (8.30%) is below 10% threshold"
    }
  ]
}
```

**Error Responses:**

*404 Not Found:*
```json
{
  "error": "Instance not found"
}
```

*403 Forbidden:*
```json
{
  "error": "Unauthorized: You don't own this instance"
}
```

---

### 10. Simulate Metrics
**POST** `/api/metrics/simulate`

**Description:** Create simulated metrics for testing the autoscaling system. This is useful for testing scaling decisions without waiting for real AWS metrics.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "cpu_utilization": 95.5,
  "memory_usage": 70.2,
  "network_in": 3072000,
  "network_out": 1536000
}
```

**Success Response (201 Created):**
```json
{
  "message": "Simulated metric created successfully",
  "metric": {
    "id": "dd0e8400-e29b-41d4-a716-446655440008",
    "instance_id": "i-1234567890abcdef0",
    "timestamp": "2026-01-22T05:22:15.123456",
    "cpu_utilization": 95.5,
    "memory_usage": 70.2,
    "network_in": 3072000,
    "network_out": 1536000,
    "is_outlier": false,
    "outlier_type": null
  }
}
```

**Error Responses:**

*400 Bad Request:*
```json
{
  "error": "instance_id is required"
}
```

*404 Not Found:*
```json
{
  "error": "Instance not found"
}
```

*403 Forbidden:*
```json
{
  "error": "Unauthorized: You don't own this instance"
}
```

*500 Internal Server Error:*
```json
{
  "error": "Failed to create metric: <error details>"
}
```

---

## Scaling Decision Logic

The system uses a three-tier decision logic:

### Priority 1: Immediate Scale Down
- **Trigger:** CPU utilization < 10%
- **Action:** Scale down immediately
- **Flag:** Metric is marked as outlier with type `scale_down`

### Priority 2: Immediate Scale Up
- **Trigger:** CPU utilization > 90%
- **Action:** Scale up immediately
- **Flag:** Metric is marked as outlier with type `scale_up`

### Priority 3: IQR-Based Outlier Detection
For normal conditions (10% ≤ CPU ≤ 90%), the system uses the Interquartile Range (IQR) method:

1. Collect CPU values from the last 5 minutes (excluding flagged outliers)
2. Calculate Q1 (25th percentile) and Q3 (75th percentile)
3. Calculate IQR = Q3 - Q1
4. Determine bounds:
   - Lower bound = Q1 - 1.5 × IQR
   - Upper bound = Q3 + 1.5 × IQR
5. Make decision:
   - **Scale up** if current CPU > upper bound
   - **Scale down** if current CPU < lower bound
   - **No action** if within bounds

**Important:** Metrics flagged as outliers (from immediate thresholds) are excluded from future mean calculations to prevent skewing the baseline.

---

## Metrics Table Schema

The `metrics` table includes the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `instance_id` | String | Foreign key to instances table |
| `timestamp` | DateTime | When the metric was recorded |
| `cpu_utilization` | Float | CPU usage percentage (0-100) |
| `memory_usage` | Float | Memory usage percentage (0-100) |
| `network_in` | BigInteger | Network bytes in |
| `network_out` | BigInteger | Network bytes out |
| `is_outlier` | Boolean | Whether this metric triggered immediate scaling |
| `outlier_type` | String | Type of outlier: 'scale_up', 'scale_down', or null |

---

## Testing Flow with Postman

### Step 1: Register and Login
1. Register a user: `POST /api/auth/register`
2. Login: `POST /api/auth/login`
3. Copy the token from the response

### Step 2: Register Instance
1. Register an instance: `POST /api/instances/`
2. Use the token in the Authorization header

### Step 3: Test Simulate Endpoint
1. Create a normal metric: `POST /api/metrics/simulate`
   ```json
   {"instance_id": "i-xxx", "cpu_utilization": 50.0}
   ```
2. Create a high CPU metric: `POST /api/metrics/simulate`
   ```json
   {"instance_id": "i-xxx", "cpu_utilization": 95.0}
   ```
3. Create a low CPU metric: `POST /api/metrics/simulate`
   ```json
   {"instance_id": "i-xxx", "cpu_utilization": 5.0}
   ```

### Step 4: Check Results
1. View metrics: `GET /api/metrics/<instance_id>`
2. View scaling decisions: `GET /api/metrics/decisions/<instance_id>`
3. Verify that high/low CPU metrics are flagged as outliers

---

## Important Notes

- **Token Format:** Always use `Bearer <token>` in Authorization header
- **Token Expiry:** 24 hours
- **Metrics Collection:** Every 30 seconds (only for monitored instances)
- **Scaling Decisions:** Every 15 seconds (only for monitored instances)
- **Base URL:** `http://localhost:5000`
- **Outlier Exclusion:** Flagged metrics are excluded from future mean calculations
