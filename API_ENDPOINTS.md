# API Endpoints Documentation

## Quick Reference

### Authentication (No Token Required)
1. `GET /api/` - Health check
2. `POST /api/auth/register` - Register new user
3. `POST /api/auth/login` - Login and get JWT token
4. `GET /api/auth/me` - Get current user information

### Instance Management (Token Required)
5. `POST /api/instances/` - Register AWS instance or mock instance
6. `GET /api/instances/` - Get all user instances
7. `PATCH /api/instances/<instance_id>/monitor/start` - Start monitoring
8. `PATCH /api/instances/<instance_id>/monitor/stop` - Stop monitoring

### Metrics & Decisions (Token Required)
9. `GET /api/metrics/<instance_id>` - Get instance metrics
10. `GET /api/metrics/decisions/<instance_id>` - Get scaling decisions
11. `POST /api/metrics/simulate` - Simulate metrics for testing (instant or prolonged)

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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

### 4. Get User Information
**GET** `/api/auth/me`

**Description:** Get current authenticated user's profile and statistics.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2026-01-22T05:16:25.123456",
  "instance_count": 5,
  "monitoring_count": 2
}
```

**Error Responses:**

*401 Unauthorized:*
```json
{
  "error": "Token is missing"
}
```

*401 Unauthorized - Expired:*
```json
{
  "error": "Token has expired"
}
```

---

### 5. Register Instance
**POST** `/api/instances/`

**Description:** Register an AWS EC2 instance or a mock instance for monitoring.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body (Real AWS Instance):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "instance_type": "t2.micro",
  "region": "us-east-1",
  "is_mock": false
}
```

**Request Body (Mock Instance):**
```json
{
  "instance_id": "mock-instance-1",
  "instance_type": "t2.micro",
  "region": "mock",
  "is_mock": true
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
    "is_mock": false,
    "cpu_capacity": 100.0,
    "memory_capacity": 100.0,
    "network_capacity": 100.0,
    "current_scale_level": 1
  }
}
```

**Notes:**
- `is_mock` defaults to `false` if not provided
- Mock instances generate metrics in the 40-50% utilization range
- Mock instances don't require AWS CLI configuration
- Capacity values start at 100.0 and change with scaling decisions

**Error Responses:**

*400 Bad Request:*
```json
{
  "error": "instance_id, instance_type, and region are required"
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

### 6. Get All Instances
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
      "is_mock": false,
      "cpu_capacity": 150.0,
      "memory_capacity": 150.0,
      "network_capacity": 150.0,
      "current_scale_level": 2,
      "created_at": "2026-01-22T05:16:25.123456"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "instance_id": "mock-instance-1",
      "instance_type": "t2.small",
      "region": "mock",
      "is_monitoring": false,
      "is_mock": true,
      "cpu_capacity": 100.0,
      "memory_capacity": 100.0,
      "network_capacity": 100.0,
      "current_scale_level": 1,
      "created_at": "2026-01-22T06:30:15.654321"
    }
  ]
}
```

---

### 7. Start Monitoring
**PATCH** `/api/instances/<instance_id>/monitor/start`

**Description:** Start monitoring an instance. Metrics will be collected every 30 seconds, and scaling decisions will be made every 15 seconds.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "message": "Monitoring started successfully"
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
  "error": "Monitoring is already active for this instance"
}
```

---

### 8. Stop Monitoring
**PATCH** `/api/instances/<instance_id>/monitor/stop`

**Description:** Stop monitoring an instance.

**Headers:**
- `Authorization: Bearer <token>`

**Success Response (200 OK):**
```json
{
  "message": "Monitoring stopped successfully"
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

### 9. Get Instance Metrics
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

### 10. Get Scaling Decisions
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
      "reason": "Sustained scale up: CPU > 90% for 85.0% of last 5 minutes (Current: 92.50%)"
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "timestamp": "2026-01-22T05:20:45.654321",
      "cpu_utilization": 45.2,
      "memory_usage": 62.8,
      "network_in": 1024000,
      "network_out": 512000,
      "decision": "no_action",
      "reason": "All metrics within acceptable range. Current: CPU: 45.20%, Memory: 62.80%"
    },
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440007",
      "timestamp": "2026-01-22T05:20:30.987654",
      "cpu_utilization": 8.3,
      "memory_usage": 15.1,
      "network_in": 512000,
      "network_out": 256000,
      "decision": "scale_down",
      "reason": "Sustained scale down: CPU < 10% AND Memory < 20% for 90.0% of last 5 minutes (Current: CPU=8.30%, Memory=15.10%)"
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

### 11. Simulate Metrics
**POST** `/api/metrics/simulate`

**Description:** Create simulated metrics for testing the autoscaling system. Supports both instant simulation (single metric) and prolonged simulation (multiple metrics over time).

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body (Instant Simulation):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "cpu_utilization": 95.5,
  "memory_usage": 70.2,
  "network_in": 3072000,
  "network_out": 1536000
}
```

**Request Body (Prolonged Simulation):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "cpu_utilization": 95.5,
  "memory_usage": 70.2,
  "network_in": 3072000,
  "network_out": 1536000,
  "duration_minutes": 10,
  "interval_seconds": 30
}
```

**Parameters:**
- `instance_id` (required): Instance to simulate metrics for
- `cpu_utilization` (optional): CPU percentage (0-100)
- `memory_usage` (optional): Memory percentage (0-100)
- `network_in` (optional): Network in bytes
- `network_out` (optional): Network out bytes
- `duration_minutes` (optional): Duration for prolonged simulation
- `interval_seconds` (optional, default=30): Interval between metrics

**Success Response - Instant (201 Created):**
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

**Success Response - Prolonged (201 Created):**
```json
{
  "message": "Created 20 simulated metrics over 10 minutes",
  "metrics_created": 20,
  "duration_minutes": 10,
  "interval_seconds": 30,
  "sample_metrics": [
    {
      "timestamp": "2026-01-22T05:12:15.123456",
      "cpu_utilization": 95.5,
      "memory_usage": 70.2
    },
    {
      "timestamp": "2026-01-22T05:12:45.123456",
      "cpu_utilization": 95.5,
      "memory_usage": 70.2
    },
    {
      "timestamp": "2026-01-22T05:13:15.123456",
      "cpu_utilization": 95.5,
      "memory_usage": 70.2
    }
  ]
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

The system uses a three-tier decision logic with **sustained usage checks**:

### Priority 1: Sustained Scale Down
- **Trigger:** CPU < 10% **AND** Memory < 20% for **80%+ of last 5 minutes**
- **Action:** Scale down and update capacity
- **Capacity Change:** Decrease by 33% (multiply by 0.67)
- **Scale Level:** Decremented by 1
- **Flag:** Metric is marked as outlier with type `scale_down`

### Priority 2: Sustained Scale Up
- **Trigger:** CPU > 90% **OR** Memory > 90% for **80%+ of last 5 minutes**
- **Action:** Scale up and update capacity
- **Capacity Change:** Increase by 50% (multiply by 1.5)
- **Scale Level:** Incremented by 1
- **Flag:** Metric is marked as outlier with type `scale_up`

### Priority 3: IQR-Based Outlier Detection
For normal conditions (not meeting sustained thresholds), the system uses the Interquartile Range (IQR) method:

1. Collect metrics from the last 5 minutes (excluding flagged outliers)
2. Calculate Q1 (25th percentile) and Q3 (75th percentile) for each metric
3. Calculate IQR = Q3 - Q1
4. Determine bounds:
   - Lower bound = Q1 - 1.5 × IQR
   - Upper bound = Q3 + 1.5 × IQR
5. Voting system:
   - CPU and Memory: 2 votes each
   - Network In/Out: 1 vote each
6. Make decision:
   - **Scale up** if total scale-up votes ≥ 2
   - **Scale down** if total scale-down votes ≥ 2
   - **No action** otherwise

**Important Notes:**
- Sustained usage requires 80% of metrics in the 5-minute window to meet the threshold
- Metrics flagged as outliers are excluded from future IQR calculations
- Capacity tracking allows monitoring of instance resource changes over time

---

## Instance Capacity Tracking

Each instance tracks its current capacity across three dimensions:

| Field | Description | Initial Value | Scale Up | Scale Down |
|-------|-------------|---------------|----------|------------|
| `cpu_capacity` | CPU processing capacity (%) | 100.0 | ×1.5 | ×0.67 |
| `memory_capacity` | Memory capacity (%) | 100.0 | ×1.5 | ×0.67 |
| `network_capacity` | Network bandwidth capacity (%) | 100.0 | ×1.5 | ×0.67 |
| `current_scale_level` | Number of scale operations | 1 | +1 | -1 |

**Example Progression:**
- Initial: Level 1, Capacity 100%
- After scale up: Level 2, Capacity 150%
- After another scale up: Level 3, Capacity 225%
- After scale down: Level 2, Capacity 150%

---

## Mock Instances

Mock instances allow testing without AWS CLI configuration:

**Benefits:**
- No AWS credentials required
- Consistent metrics in 40-50% utilization range
- Perfect for demos and development
- Same API interface as real instances

**Usage:**
1. Register with `"is_mock": true`
2. Start monitoring as normal
3. Metrics are auto-generated every 30 seconds
4. Scaling decisions work identically to real instances

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
| `is_outlier` | Boolean | Whether this metric triggered scaling |
| `outlier_type` | String | Type: 'scale_up', 'scale_down', or null |

---

## Testing Flow with Postman

### Step 1: Register and Login
1. Register a user: `POST /api/auth/register`
2. Login: `POST /api/auth/login`
3. Copy the token from the response
4. Get user info: `GET /api/auth/me` (with token)

### Step 2: Register Mock Instance (No AWS Required)
1. Register a mock instance: `POST /api/instances/`
   ```json
   {
     "instance_id": "mock-test-1",
     "instance_type": "t2.micro",
     "region": "mock",
     "is_mock": true
   }
   ```
2. Start monitoring: `PATCH /api/instances/mock-test-1/monitor/start`
3. Wait 30 seconds for metrics to be generated

### Step 3: Test Prolonged Simulation
1. Simulate sustained high CPU for 10 minutes:
   ```json
   {
     "instance_id": "mock-test-1",
     "cpu_utilization": 95.0,
     "memory_usage": 50.0,
     "duration_minutes": 10,
     "interval_seconds": 30
   }
   ```
2. Wait 15 seconds for scaling decision
3. Check decisions: `GET /api/metrics/decisions/mock-test-1`
4. Verify scale-up decision was made
5. Check instance: `GET /api/instances/`
6. Verify capacity increased to 150%

### Step 4: Check Results
1. View metrics: `GET /api/metrics/mock-test-1`
2. View scaling decisions: `GET /api/metrics/decisions/mock-test-1`
3. Verify sustained usage triggered scaling
4. Check capacity changes in instance details

---

## Important Notes

- **Token Format:** Always use `Bearer <token>` in Authorization header
- **Token Expiry:** 24 hours
- **Metrics Collection:** Every 30 seconds (only for monitored instances)
- **Scaling Decisions:** Every 15 seconds (only for monitored instances)
- **Base URL:** `http://localhost:5000`
- **Sustained Usage:** Requires 80% of metrics in 5-minute window
- **Mock Instances:** Generate metrics in 40-50% range automatically
- **Capacity Tracking:** Updates automatically with scaling decisions
- **HTTP Methods:** Start/Stop monitoring use PATCH (not POST)
