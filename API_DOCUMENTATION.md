# Site-29 Server Management Bot API Documentation

![Version](https://img.shields.io/badge/version-2.1.3-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-ff69b4)

## Overview

The Site-29 Server Management Bot API provides programmatic access to server management operations, allowing you to control server startups, shutdowns, and create polls through RESTful endpoints. This API mirrors the functionality of the Discord bot commands but enables integration with external systems and automation tools.

## Base URL

```
http://{host}:{port}
```

The host and port are configurable in `config.json`:
```json
{
    "api_host": "0.0.0.0",
    "api_port": 8000
}
```

## Endpoints

### Start Server (SSU)

Initiates a server startup sequence.

**Endpoint:** `POST /ssu`

**Request Body:**
```json
{
    "server_name": "string",
    "host": "string",
    "ping": "string",
    "description": "string (optional)"
}
```

**Parameters:**
- `server_name`: Name of the server to start
- `host`: Username or mention of the person hosting
- `ping`: Target group to notify (@everyone, @role, etc.)
- `description`: Optional description of the startup

**Example Request:**
```bash
curl -X POST http://localhost:8000/ssu \
-H "Content-Type: application/json" \
-d '{
    "server_name": "Testing Server",
    "host": "@john",
    "ping": "@everyone",
    "description": "Server restart for updates"
}'
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Server startup initiated"
}
```

### Create Server Startup Poll (SSUP)

Creates a poll for server startup approval.

**Endpoint:** `POST /ssup`

**Request Body:**
```json
{
    "server_name": "string",
    "time": "string",
    "role": "string",
    "description": "string (optional)"
}
```

**Parameters:**
- `server_name`: Name of the server for the poll
- `time`: Time until server start (e.g., "45min", "1d30min", "1w")
- `role`: Target role/group for the poll
- `description`: Optional description of the startup poll

**Time Format Options:**
- Minutes: `45min`
- Hours and Minutes: `2h30min`
- Days: `2d`
- Weeks: `1w`
- Months: `1mo`
- Combined: `1d12h30min`

**Example Request:**
```bash
curl -X POST http://localhost:8000/ssup \
-H "Content-Type: application/json" \
-d '{
    "server_name": "Testing Server",
    "time": "45min",
    "role": "@everyone",
    "description": "Scheduled maintenance restart"
}'
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Server startup poll created"
}
```

### Server Shutdown (SSD)

Initiates a server shutdown sequence.

**Endpoint:** `POST /ssd`

**Request Body:** None required

**Example Request:**
```bash
curl -X POST http://localhost:8000/ssd
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Server shutdown initiated"
}
```

## Error Responses

All endpoints return standard HTTP error codes along with a JSON response body:

```json
{
    "detail": "Error message description"
}
```

Common error codes:
- `400 Bad Request`: Invalid request body or parameters
- `500 Internal Server Error`: Server-side processing error

## State Management

The API maintains the same state management as the Discord bot:
- Only one server can be running at a time
- SSU cannot be used while a server is running
- SSD cannot be used unless a server is running
- Active polls are tracked and updated automatically

## Security Considerations

- The API runs on the same host as the Discord bot
- Consider implementing additional authentication if exposing to external networks
- Use HTTPS if deploying in a production environment
- Configure firewall rules to restrict access to the API port

## Examples

### Python Example

```python
import requests
import json

base_url = "http://localhost:8000"

# Start a server
ssu_data = {
    "server_name": "Test Server",
    "host": "@admin",
    "ping": "@everyone",
    "description": "Test startup"
}
response = requests.post(f"{base_url}/ssu", json=ssu_data)
print(response.json())

# Create a startup poll
ssup_data = {
    "server_name": "Test Server",
    "time": "30min",
    "role": "@everyone",
    "description": "Scheduled restart"
}
response = requests.post(f"{base_url}/ssup", json=ssup_data)
print(response.json())
```

### JavaScript Example

```javascript
const axios = require('axios');

const baseUrl = 'http://localhost:8000';

// Start a server
const ssuData = {
    server_name: 'Test Server',
    host: '@admin',
    ping: '@everyone',
    description: 'Test startup'
};

axios.post(`${baseUrl}/ssu`, ssuData)
    .then(response => console.log(response.data))
    .catch(error => console.error(error));

// Create a startup poll
const ssupData = {
    server_name: 'Test Server',
    time: '30min',
    role: '@everyone',
    description: 'Scheduled restart'
};

axios.post(`${baseUrl}/ssup`, ssupData)
    .then(response => console.log(response.data))
    .catch(error => console.error(error));
```

## Support

For issues, feature requests, or questions, please:
1. Check the existing GitHub issues
2. Create a new issue with detailed information
3. Include relevant error messages and request/response data

## License

Licensed under the VOSL 2.3 
Copyright © 2025 Veilaris / Veilaris Management System
