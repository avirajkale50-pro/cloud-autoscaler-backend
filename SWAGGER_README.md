# Swagger API Documentation

The backend now includes interactive Swagger/OpenAPI documentation!

## Accessing Swagger UI

Once the server is running, visit:

**http://localhost:5000/api/docs**

## Features

- **Interactive Testing**: Test all API endpoints directly from the browser
- **Authentication**: Use the "Authorize" button to set your Bearer token
- **Request/Response Examples**: See example requests and responses for each endpoint
- **Schema Documentation**: View all data models and their properties

## Quick Start

1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000/api/docs
   ```

3. Test the API:
   - Click on any endpoint to expand it
   - Click "Try it out"
   - Fill in the parameters
   - Click "Execute"

## Authentication Flow

1. **Register a user**: Use `POST /api/auth/register`
2. **Login**: Use `POST /api/auth/login` and copy the token
3. **Authorize**: Click the "Authorize" button at the top
4. **Enter token**: Paste the token (without "Bearer" prefix)
5. **Test protected endpoints**: All authenticated endpoints will now work

## Files

- `swagger.yaml` - OpenAPI 3.0 specification
- `static/swagger.yaml` - Copy served by Flask
- Swagger UI served at `/api/docs`

## Updating Documentation

If you modify the API, update `swagger.yaml` and copy it to the static folder:
```bash
cp swagger.yaml static/
```

The changes will be reflected immediately (no server restart needed).
