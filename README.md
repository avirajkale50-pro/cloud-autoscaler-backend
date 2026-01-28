# Cloud Resource Autoscaler Backend

A Flask-based backend service that monitors AWS EC2 instances and mock instances, collects performance metrics, and makes intelligent autoscaling decisions based on CPU, memory, and network utilization.

## Table of Contents
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [Viewing Swagger Documentation](#viewing-swagger-documentation)
- [API Endpoints](#api-endpoints)
- [Testing with Postman](#testing-with-postman)
- [Scaling Logic](#scaling-logic)

---

## Setup and Installation

### Prerequisites
- **Python 3.8+**
- **PostgreSQL** or **TimescaleDB** (recommended for time-series data)
- **Git** (for cloning the repository)

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd cloud_resource_autoscaler/backend
```

#### 2. Create a Virtual Environment
```bash
python -m venv venv
```

#### 3. Activate the Virtual Environment
**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Configure Environment Variables
Create a `.env` file in the `backend` directory with the following content:

```env
DATABASE_URL="postgresql://username:password@host:port/database?sslmode=require"
JWT_SECRET_KEY="your-secret-key-change-in-production"
```

**Example:**
```env
DATABASE_URL="postgresql://admin:mypassword@localhost:5432/autoscaler?sslmode=require"
JWT_SECRET_KEY="my-super-secret-jwt-key-12345"
```

#### 6. Database Setup
The application will automatically create all required tables on first run. Ensure your PostgreSQL database is running and accessible.

---

## Running the Application

### Start the Server
```bash
python main.py
```

The server will start on **http://0.0.0.0:5000** (accessible from all network interfaces).

### Verify the Server is Running
Open your browser and navigate to:
```
http://localhost:5000/api/
```

You should see:
```json
{
  "message": "Cloud Resource Autoscaler API is running",
  "version": "1.0"
}
```

### Background Jobs
Once started, the application runs two background jobs:
- **Metrics Collection**: Every 30 seconds (for monitored instances)
- **Scaling Decisions**: Every 15 seconds (for monitored instances)

---

## Viewing Swagger Documentation

### Access Swagger UI
Once the server is running, open your browser and navigate to:

**🔗 http://localhost:5000/api/docs**

### Swagger Features
- ✅ **Interactive API Testing**: Execute API calls directly from the browser
- ✅ **Authentication Support**: Use the "Authorize" button to set your JWT token
- ✅ **Request/Response Examples**: View sample requests and responses for all endpoints
- ✅ **Schema Documentation**: Explore all data models and their properties

### How to Use Swagger UI

#### Step 1: Register a User
1. Expand `POST /api/auth/register`
2. Click **"Try it out"**
3. Enter your email and password in the request body
4. Click **"Execute"**

#### Step 2: Login and Get Token
1. Expand `POST /api/auth/login`
2. Click **"Try it out"**
3. Enter your credentials
4. Click **"Execute"**
5. **Copy the token** from the response

#### Step 3: Authorize
1. Click the **"Authorize"** button at the top right
2. Paste your token (without "Bearer" prefix)
3. Click **"Authorize"**
4. Click **"Close"**

#### Step 4: Test Protected Endpoints
Now you can test any endpoint that requires authentication!

---

## API Endpoints

### Quick Reference Table

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/` | Health check | ❌ No |
| `POST` | `/api/auth/register` | Register new user | ❌ No |
| `POST` | `/api/auth/login` | Login and get JWT token | ❌ No |
| `GET` | `/api/auth/me` | Get current user info | ✅ Yes |
| `POST` | `/api/instances/` | Register AWS/Mock instance | ✅ Yes |
| `GET` | `/api/instances/` | Get all user instances | ✅ Yes |
| `PATCH` | `/api/instances/<id>/monitor/start` | Start monitoring | ✅ Yes |
| `PATCH` | `/api/instances/<id>/monitor/stop` | Stop monitoring | ✅ Yes |
| `GET` | `/api/metrics/<id>` | Get instance metrics | ✅ Yes |
| `GET` | `/api/metrics/decisions/<id>` | Get scaling decisions | ✅ Yes |
| `POST` | `/api/metrics/simulate` | Simulate metrics (testing) | ✅ Yes |

---

### Detailed API Documentation

## 1. Health Check

**Endpoint:** `GET /api/`  
**Authorization:** Not required

**Response (200 OK):**
```json
{
  "message": "Cloud Resource Autoscaler API is running",
  "version": "1.0"
}
```

---

## 2. Register User

**Endpoint:** `POST /api/auth/register`  
**Authorization:** Not required

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

## 3. Login

**Endpoint:** `POST /api/auth/login`  
**Authorization:** Not required

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

## 4. Get User Information

**Endpoint:** `GET /api/auth/me`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

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

## 5. Register Instance

**Endpoint:** `POST /api/instances/`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**Request Body (Real AWS Instance):**
```json
{
  "instance_id": "i-1234567890abcdef0",
  "instance_type": "t2.micro",
  "region": "us-east-1",
  "is_mock": false
}
```

**Request Body (Mock Instance - No AWS Required):**
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

**Error Responses:**

*400 Bad Request:*
```json
{
  "error": "instance_id, instance_type, and region are required"
}
```

*409 Conflict:*
```json
{
  "error": "Instance already registered"
}
```

---

## 6. Get All Instances

**Endpoint:** `GET /api/instances/`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

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
    }
  ]
}
```

---

## 7. Start Monitoring

**Endpoint:** `PATCH /api/instances/<instance_id>/monitor/start`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

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

## 8. Stop Monitoring

**Endpoint:** `PATCH /api/instances/<instance_id>/monitor/stop`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Success Response (200 OK):**
```json
{
  "message": "Monitoring stopped successfully"
}
```

---

## 9. Get Instance Metrics

**Endpoint:** `GET /api/metrics/<instance_id>?limit=50`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

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
    }
  ]
}
```

---

## 10. Get Scaling Decisions

**Endpoint:** `GET /api/metrics/decisions/<instance_id>?limit=20`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

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
    }
  ]
}
```

---

## 11. Simulate Metrics

**Endpoint:** `POST /api/metrics/simulate`  
**Authorization:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

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

**Request Body (Prolonged Simulation - 10 minutes of high load):**
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
    "network_out": 1536000
  }
}
```

**Success Response - Prolonged (201 Created):**
```json
{
  "message": "Created 20 simulated metrics over 10 minutes",
  "metrics_created": 20,
  "duration_minutes": 10,
  "interval_seconds": 30
}
```

---

## Testing with Postman

### Step 1: Register and Login

1. **Register a user:**
   - Method: `POST`
   - URL: `http://localhost:5000/api/auth/register`
   - Body (JSON):
     ```json
     {
       "email": "test@example.com",
       "password": "testpass123"
     }
     ```

2. **Login:**
   - Method: `POST`
   - URL: `http://localhost:5000/api/auth/login`
   - Body (JSON):
     ```json
     {
       "email": "test@example.com",
       "password": "testpass123"
     }
     ```
   - **Copy the token from the response**

3. **Set Authorization Header:**
   - In Postman, go to the "Authorization" tab
   - Type: `Bearer Token`
   - Token: `<paste-your-token-here>`

### Step 2: Register and Monitor a Mock Instance

1. **Register a mock instance:**
   - Method: `POST`
   - URL: `http://localhost:5000/api/instances/`
   - Body (JSON):
     ```json
     {
       "instance_id": "mock-test-1",
       "instance_type": "t2.micro",
       "region": "mock",
       "is_mock": true
     }
     ```

2. **Start monitoring:**
   - Method: `PATCH`
   - URL: `http://localhost:5000/api/instances/mock-test-1/monitor/start`

3. **Wait 30 seconds** for metrics to be auto-generated

### Step 3: Test Scaling with Simulation

1. **Simulate high CPU for 10 minutes:**
   - Method: `POST`
   - URL: `http://localhost:5000/api/metrics/simulate`
   - Body (JSON):
     ```json
     {
       "instance_id": "mock-test-1",
       "cpu_utilization": 95.0,
       "memory_usage": 50.0,
       "duration_minutes": 10,
       "interval_seconds": 30
     }
     ```

2. **Wait 15 seconds** for the scaling decision job to run

3. **Check scaling decisions:**
   - Method: `GET`
   - URL: `http://localhost:5000/api/metrics/decisions/mock-test-1`

4. **Verify scale-up decision** was made

5. **Check instance capacity:**
   - Method: `GET`
   - URL: `http://localhost:5000/api/instances/`
   - Verify `cpu_capacity` increased to 150%

---

## Scaling Logic

The autoscaler uses a **3-tier priority system** to make intelligent scaling decisions based on CPU, Memory, and Network metrics.

### Decision Priority Levels

| Priority | Condition | Action | Duration Required |
|----------|-----------|--------|-------------------|
| **1** | CPU < 10% **AND** Memory < 20% | Scale Down | 5 minutes sustained |
| **2** | CPU > 90% **OR** Memory > 90% | Scale Up | 5 minutes sustained |
| **3** | IQR-based outlier detection | Scale Up/Down/No Action | Based on last 5 minutes |

---

### Priority 1: Sustained Scale Down

**Conditions:**
```
Sustained Usage Check (5 minutes):
- CPU Utilization < 10%
- AND Memory Usage < 20%
- Sustained for ≥80% of time window
```

**Formula:**
```
matching_count = count of metrics where (CPU < 10% AND Memory < 20%)
total_count = total metrics in last 5 minutes
percentage = (matching_count / total_count) × 100

Decision: Scale Down if percentage ≥ 80%
```

**Outcome:**
- **Decision**: `scale_down`
- **Metric Flagged**: `is_outlier = True`, `outlier_type = scale_down`
- **Capacity Change**: CPU, Memory, Network capacity × 0.67 (33% reduction)
- **Scale Level**: Decremented by 1

---

### Priority 2: Sustained Scale Up

**Conditions (Either/Or):**

**Option A: High CPU**
```
Sustained Usage Check (5 minutes):
- CPU Utilization > 90%
- Sustained for ≥80% of time window
```

**Option B: High Memory**
```
Sustained Usage Check (5 minutes):
- Memory Usage > 90%
- Sustained for ≥80% of time window
```

**Formula:**
```
matching_count = count of metrics where (CPU > 90% OR Memory > 90%)
total_count = total metrics in last 5 minutes
percentage = (matching_count / total_count) × 100

Decision: Scale Up if percentage ≥ 80%
```

**Outcome:**
- **Decision**: `scale_up`
- **Metric Flagged**: `is_outlier = True`, `outlier_type = scale_up`
- **Capacity Change**: CPU, Memory, Network capacity × 1.5 (50% increase)
- **Scale Level**: Incremented by 1

---

### Priority 3: IQR-Based Outlier Detection

**Prerequisites:**
- Minimum 4 non-outlier metrics in last 5 minutes
- If insufficient data → `no_action`

**IQR Formula (Applied to Each Metric):**

```
Step 1: Sort metric values in ascending order
Step 2: Calculate quartiles
  Q1 = value at position (n / 4)
  Q3 = value at position (3n / 4)

Step 3: Calculate Interquartile Range
  IQR = Q3 - Q1

Step 4: Calculate bounds
  Lower Bound = Q1 - (1.5 × IQR)
  Upper Bound = Q3 + (1.5 × IQR)

Step 5: Compare current value
  If current_value > Upper Bound → Vote for Scale Up
  If current_value < Lower Bound → Vote for Scale Down
  Otherwise → No vote
```

**Metric Analysis & Voting System:**

| Metric | Weight | Scale Up Condition | Scale Down Condition |
|--------|--------|-------------------|---------------------|
| **CPU Utilization** | 2 votes | `current_cpu > (Q3 + 1.5×IQR)` | `current_cpu < (Q1 - 1.5×IQR)` |
| **Memory Usage** | 2 votes | `current_memory > (Q3 + 1.5×IQR)` | `current_memory < (Q1 - 1.5×IQR)` |
| **Network In** | 1 vote | `current_net_in > (Q3 + 1.5×IQR)` | `current_net_in < (Q1 - 1.5×IQR)` |
| **Network Out** | 1 vote | `current_net_out > (Q3 + 1.5×IQR)` | `current_net_out < (Q1 - 1.5×IQR)` |

**Decision Logic:**
```
Total Scale Up Votes = sum of all scale up votes
Total Scale Down Votes = sum of all scale down votes

If scale_up_votes ≥ 2:
  Decision = scale_up
  
Else If scale_down_votes ≥ 2:
  Decision = scale_down
  
Else:
  Decision = no_action
```

---

### Example Calculations

**Example 1: CPU-Based Scale Up (IQR)**

Historical CPU values (last 5 min): `[45, 48, 50, 52, 55, 58, 60, 62]`

```
Step 1: Sort values (already sorted)
Step 2: Calculate quartiles
  n = 8
  Q1 = values[8/4] = values[2] = 50
  Q3 = values[3×8/4] = values[6] = 60

Step 3: IQR = 60 - 50 = 10

Step 4: Bounds
  Lower Bound = 50 - (1.5 × 10) = 35
  Upper Bound = 60 + (1.5 × 10) = 75

Step 5: Current CPU = 78%
  78 > 75 → Scale Up Vote (+2)
```

**Example 2: Network-Based Scale Down (IQR)**

Historical Network In values (bytes): `[5000, 5200, 5500, 5800, 6000, 6200, 6500]`

```
Step 1: Sort values (already sorted)
Step 2: Calculate quartiles
  n = 7
  Q1 = values[7/4] = values[1] = 5200
  Q3 = values[3×7/4] = values[5] = 6200

Step 3: IQR = 6200 - 5200 = 1000

Step 4: Bounds
  Lower Bound = 5200 - (1.5 × 1000) = 3700
  Upper Bound = 6200 + (1.5 × 1000) = 7700

Step 5: Current Network In = 3000 bytes
  3000 < 3700 → Scale Down Vote (+1)
```

**Example 3: Combined Decision**

Current Metrics:
- CPU: 78% → Above upper bound → +2 scale up votes
- Memory: 45% → Within bounds → 0 votes
- Network In: 3000 bytes → Below lower bound → +1 scale down vote
- Network Out: 4500 bytes → Within bounds → 0 votes

Vote Tally:
- Scale Up Votes: 2
- Scale Down Votes: 1

**Decision:** `scale_up` (scale_up_votes ≥ 2)

---

### Capacity Adjustment Formulas

**Scale Up:**
```
new_cpu_capacity = current_cpu_capacity × 1.5
new_memory_capacity = current_memory_capacity × 1.5
new_network_capacity = current_network_capacity × 1.5
new_scale_level = current_scale_level + 1
```

**Scale Down:**
```
new_cpu_capacity = current_cpu_capacity × 0.67
new_memory_capacity = current_memory_capacity × 0.67
new_network_capacity = current_network_capacity × 0.67
new_scale_level = current_scale_level - 1
```

**Note:** 0.67 is approximately the inverse of 1.5, ensuring symmetric scaling.

---

### Instance Capacity Tracking

| Field | Initial Value | Scale Up | Scale Down |
|-------|---------------|----------|------------|
| `cpu_capacity` | 100.0% | ×1.5 | ×0.67 |
| `memory_capacity` | 100.0% | ×1.5 | ×0.67 |
| `network_capacity` | 100.0% | ×1.5 | ×0.67 |
| `current_scale_level` | 1 | +1 | -1 |

**Example Progression:**
- Initial: Level 1, Capacity 100%
- After scale up: Level 2, Capacity 150%
- After another scale up: Level 3, Capacity 225%
- After scale down: Level 2, Capacity 150%

---

### Outlier Flagging

Metrics are flagged as outliers when:
- Priority 1 condition met → `is_outlier = True`, `outlier_type = 'scale_down'`
- Priority 2 condition met → `is_outlier = True`, `outlier_type = 'scale_up'`

**Impact:** Flagged metrics are excluded from future mean calculations and IQR analysis to prevent skewing the baseline.

---

### Time Windows

| Parameter | Duration | Purpose |
|-----------|----------|---------|
| **Sustained Check** | 5 minutes | Verify high/low usage is persistent, not a spike |
| **IQR Historical Data** | 5 minutes | Calculate baseline behavior for outlier detection |
| **Minimum Data Points** | 3 (sustained), 4 (IQR) | Ensure statistical validity |
| **Decision Frequency** | Every 15 seconds | How often scaling decisions are evaluated |

---

### Decision Flow Chart

```
┌─────────────────────────────────────┐
│   Get Latest Metric for Instance    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Priority 1: Check Sustained Low    │
│  CPU < 10% AND Memory < 20%         │
│  (5 min, ≥80% of time)              │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │    Yes    │──────────────────► SCALE DOWN
         └───────────┘
               │ No
               ▼
┌─────────────────────────────────────┐
│  Priority 2: Check Sustained High   │
│  CPU > 90% OR Memory > 90%          │
│  (5 min, ≥80% of time)              │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │    Yes    │──────────────────► SCALE UP
         └───────────┘
               │ No
               ▼
┌─────────────────────────────────────┐
│  Priority 3: IQR Analysis           │
│  Calculate Q1, Q3, IQR for each     │
│  metric from last 5 min             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Compare Current vs Bounds          │
│  Count votes for each metric        │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │ Up ≥ 2?   │──────────────────► SCALE UP
         └───────────┘
               │ No
         ┌─────┴─────┐
         │ Down ≥ 2? │──────────────────► SCALE DOWN
         └───────────┘
               │ No
               ▼
          NO ACTION
```

---

### Scaling Decision Scenarios

| Scenario | CPU | Memory | Network In | Network Out | Votes | Decision |
|----------|-----|--------|------------|-------------|-------|----------|
| Extreme Low | <10% | <20% | - | - | N/A | **Scale Down** (Priority 1) |
| Extreme High | >90% | - | - | - | N/A | **Scale Up** (Priority 2) |
| Extreme High | - | >90% | - | - | N/A | **Scale Up** (Priority 2) |
| High CPU Only | >Q3+1.5×IQR | Normal | Normal | Normal | 2 up | **Scale Up** (Priority 3) |
| Low CPU Only | <Q1-1.5×IQR | Normal | Normal | Normal | 2 down | **Scale Down** (Priority 3) |
| High CPU + Net | >Q3+1.5×IQR | Normal | >Q3+1.5×IQR | Normal | 3 up | **Scale Up** (Priority 3) |
| Low All Metrics | <Q1-1.5×IQR | <Q1-1.5×IQR | <Q1-1.5×IQR | <Q1-1.5×IQR | 6 down | **Scale Down** (Priority 3) |
| Mixed Signals | >Q3+1.5×IQR | Normal | <Q1-1.5×IQR | Normal | 2 up, 1 down | **Scale Up** (Priority 3) |
| All Normal | Normal | Normal | Normal | Normal | 0 | **No Action** |

---

## Mock Instances

Mock instances allow testing without AWS credentials:

**Benefits:**
- ✅ No AWS CLI configuration required
- ✅ Consistent metrics in 40-50% utilization range
- ✅ Perfect for demos and development
- ✅ Same API interface as real instances

**Usage:**
1. Register with `"is_mock": true`
2. Start monitoring as normal
3. Metrics are auto-generated every 30 seconds
4. Scaling decisions work identically to real instances

---

## Important Notes

- **Token Format:** Always use `Bearer <token>` in Authorization header
- **Token Expiry:** 24 hours
- **Metrics Collection:** Every 30 seconds (only for monitored instances)
- **Scaling Decisions:** Every 15 seconds (only for monitored instances)
- **Base URL:** `http://localhost:5000`
- **Sustained Usage:** Requires 80% of metrics in 5-minute window
- **CORS:** Enabled for all origins

---

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check `.env` file has correct `DATABASE_URL`
- Ensure database exists and is accessible

### Token Errors
- Ensure token is not expired (24-hour lifetime)
- Verify token is included in `Authorization` header as `Bearer <token>`
- Check `JWT_SECRET_KEY` is set in `.env`

### No Metrics Being Collected
- Verify instance monitoring is started
- Check logs in `logs/` directory
- For AWS instances, ensure AWS credentials are configured
- For mock instances, verify `is_mock: true` was set during registration

---

## Project Structure

```
backend/
├── api/                    # API route handlers
├── repo/                   # Database models and repository
├── service/                # Business logic (monitoring, scaling)
├── util/                   # Utilities (logging, auth)
├── static/                 # Static files (swagger.yaml)
├── logs/                   # Application logs
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

---
