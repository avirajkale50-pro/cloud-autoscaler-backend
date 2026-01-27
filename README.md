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

The system uses a three-tier decision logic with sustained usage checks:

### Priority 1: Sustained Scale Down
- **Trigger:** CPU < 10% **AND** Memory < 20% for **80%+ of last 5 minutes**
- **Action:** Scale down
- **Capacity Change:** Decrease by 33% (multiply by 0.67)
- **Scale Level:** Decremented by 1

### Priority 2: Sustained Scale Up
- **Trigger:** CPU > 90% **OR** Memory > 90% for **80%+ of last 5 minutes**
- **Action:** Scale up
- **Capacity Change:** Increase by 50% (multiply by 1.5)
- **Scale Level:** Incremented by 1

### Priority 3: IQR-Based Outlier Detection
For normal conditions (not meeting sustained thresholds):
1. Collect metrics from last 5 minutes (excluding flagged outliers)
2. Calculate Q1 (25th percentile) and Q3 (75th percentile)
3. Calculate IQR = Q3 - Q1
4. Determine bounds: Lower = Q1 - 1.5×IQR, Upper = Q3 + 1.5×IQR
5. Voting system:
   - CPU and Memory: 2 votes each
   - Network In/Out: 1 vote each
6. Decision:
   - **Scale up** if total scale-up votes ≥ 2
   - **Scale down** if total scale-down votes ≥ 2
   - **No action** otherwise

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
