# Site-29 Server Management Bot API Documentation

<p align="center">
  <a href="https://github.com/ZOMPAZY/SCP-Roleplay-Server-Startup-Discord-Bot//blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-VOSL%202.3-7b42f6?style=flat&logoColor=white" alt="License">
  </a>
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/discord.py-2.3.2-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord.py">
  <img src="https://img.shields.io/badge/Bot%20Version-2.1.3-brightgreen?style=flat&logo=github" alt="Bot Version">
  <img src="https://img.shields.io/github/stars/zompazy/SCP-Roleplay-Server-Startup-Discord-Bot?style=flat&logo=github" alt="Stars">
  <img src="https://img.shields.io/github/issues/zompazy/SCP-Roleplay-Server-Startup-Discord-Bot?style=flat&logo=github" alt="Issues">
</p>

## Security Guide

### Authentication

The API supports multiple authentication methods to ensure secure access:

1. **API Key Authentication**
```http
Authorization: Bearer your-api-key-here
```

2. **Discord Bot Token**
```http
Authorization: Bot your-discord-bot-token
```

3. **OAuth2 Authentication**
For integrating with Discord's OAuth2 system:
```http
Authorization: Bearer discord-oauth-token
```

### Token Management

#### Generating API Keys
```bash
# Generate a new API key
curl -X POST http://localhost:8000/auth/keys \
-H "Authorization: Bot your-discord-bot-token" \
-H "Content-Type: application/json" \
-d '{"name": "My API Key", "permissions": ["read", "write"]}'
```

#### Revoking Tokens
```bash
# Revoke an API key
curl -X DELETE http://localhost:8000/auth/keys/{key_id} \
-H "Authorization: Bot your-discord-bot-token"
```

### Role-Based Access Control (RBAC)

The API implements a comprehensive RBAC system:

1. **Permission Levels**
   - `READ`: View-only access to endpoints
   - `WRITE`: Can make changes and execute commands
   - `ADMIN`: Full access including configuration
   - `SUPER_ADMIN`: Can manage other admins and tokens

2. **Role Hierarchy**
   ```json
   {
       "roles": {
           "super_admin": ["*"],
           "admin": ["read", "write", "config"],
           "moderator": ["read", "write"],
           "viewer": ["read"]
       }
   }
   ```

3. **Permission Checking**
   ```python
   # Example permission check
   @requires_permission('write')
   async def modify_resource():
       pass
   ```

### Security Best Practices

1. **Token Security**
   - Store tokens securely (use environment variables)
   - Rotate tokens regularly
   - Never commit tokens to version control
   - Use separate tokens for development/production

2. **Network Security**
   - Enable HTTPS in production
   - Use secure WebSocket connections
   - Implement IP whitelisting
   - Configure proper CORS settings

3. **Access Control**
   - Implement principle of least privilege
   - Regular permission audits
   - Monitor failed authentication attempts
   - Rate limit authentication endpoints

4. **Data Security**
   - Encrypt sensitive data
   - Sanitize user inputs
   - Validate all parameters
   - Implement request signing

### Security Configuration

```json
{
    "security": {
        "enable_https": true,
        "ssl_cert_path": "/path/to/cert.pem",
        "ssl_key_path": "/path/to/key.pem",
        "allowed_origins": ["https://yourdomain.com"],
        "rate_limit": {
            "enabled": true,
            "window": 3600,
            "max_requests": 1000
        },
        "ip_whitelist": ["10.0.0.0/24"],
        "token_expiry": 86400,
        "require_auth": true
    }
}
```

### Secure Setup Guide

1. **Enable HTTPS**
   ```bash
   # Generate self-signed certificate
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
   -keyout private.key -out certificate.crt
   ```

2. **Configure Firewall**
   ```bash
   # Allow only specific ports
   sudo ufw allow 443/tcp
   sudo ufw allow 8000/tcp
   ```

3. **Set Environment Variables**
   ```bash
   # Set sensitive configurations
   export BOT_TOKEN="your-token-here"
   export API_SECRET="your-secret-here"
   ```

### Security Headers

The API implements the following security headers:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

### Logging and Monitoring

1. **Security Logging**
   ```json
   {
       "security_logs": {
           "level": "INFO",
           "file": "/var/log/bot/security.log",
           "format": "%(asctime)s [%(levelname)s] %(message)s",
           "rotate": true,
           "max_size": "10MB"
       }
   }
   ```

2. **Audit Trail**
   ```json
   {
       "audit": {
           "enabled": true,
           "store": "database",
           "retention_days": 90,
           "sensitive_fields": [
               "token",
               "password",
               "api_key"
           ]
       }
   }
   ```

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

## Role Management

### Move Role Up
Move a role up in the role hierarchy.

**Endpoint:** `POST /roles/move-up`

**Request Body:**
```json
{
    "role": string,      // Role name or ID
    "positions": number  // Number of positions to move up
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "role": {
        "id": string,
        "name": string,
        "position": number
    }
}
```

### Move Role Down
Move a role down in the role hierarchy.

**Endpoint:** `POST /roles/move-down`

**Request Body:**
```json
{
    "role": string,      // Role name or ID
    "positions": number  // Number of positions to move down
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "role": {
        "id": string,
        "name": string,
        "position": number
    }
}
```

### Change Role Color
Update the color of a role.

**Endpoint:** `POST /roles/color`

**Request Body:**
```json
{
    "role": string,     // Role name or ID
    "color": string     // Hex color code (e.g., "#FF0000")
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "role": {
        "id": string,
        "name": string,
        "color": string
    }
}
```

### Add Role
Create a new role.

**Endpoint:** `POST /roles/create`

**Request Body:**
```json
{
    "name": string,
    "color": string,          // Hex color code (optional)
    "position": number,       // Role position (optional)
    "permissions": number,    // Permission bitfield (optional)
    "mentionable": boolean,  // Whether the role can be mentioned (optional)
    "hoist": boolean         // Whether the role is displayed separately (optional)
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "role": {
        "id": string,
        "name": string,
        "color": string,
        "position": number,
        "permissions": number
    }
}
```

### Grant Admin
Grant administrative permissions to a role.

**Endpoint:** `POST /roles/grant-admin`

**Request Body:**
```json
{
    "role": string      // Role name or ID
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "role": {
        "id": string,
        "name": string,
        "permissions": number
    }
}
```

## Poll Management

### Update Poll (USSUP)
Manually update a server startup poll.

**Endpoint:** `POST /polls/update/{poll_id}`

**Parameters:**
- `poll_id`: The ID of the poll to update

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "poll": {
        "id": string,
        "server_name": string,
        "target_time": string,
        "time_remaining": string,
        "created_by": string,
        "role_ping": string,
        "description": string,
        "updated_at": string
    }
}
```

### Get Active Polls
Retrieve all currently active polls.

**Endpoint:** `GET /polls/active`

**Response:**
```json
{
    "status": "success" | "error",
    "data": {
        "active_polls": [
            {
                "id": string,
                "server_name": string,
                "target_time": string,
                "time_remaining": string,
                "created_by": string,
                "role_ping": string,
                "description": string,
                "created_at": string,
                "last_updated": string
            }
        ]
    }
}
```

### Cancel Poll
Cancel an active server startup poll.

**Endpoint:** `POST /polls/cancel/{poll_id}`

**Parameters:**
- `poll_id`: The ID of the poll to cancel

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string
}
```

### Poll Auto-Update Configuration
Configure auto-update settings for polls.

**Endpoint:** `POST /polls/config`

**Request Body:**
```json
{
    "update_interval": number,  // Update interval in seconds (default: 60)
    "auto_cancel": boolean,    // Whether to auto-cancel expired polls (default: true)
    "notification_threshold": number  // Minutes before expiry to send notification (default: 5)
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "config": {
        "update_interval": number,
        "auto_cancel": boolean,
        "notification_threshold": number
    }
}
```

### Poll Status
Get detailed status of a specific poll.

**Endpoint:** `GET /polls/{poll_id}`

**Parameters:**
- `poll_id`: The ID of the poll to check

**Response:**
```json
{
    "status": "success" | "error",
    "data": {
        "id": string,
        "server_name": string,
        "target_time": string,
        "time_remaining": string,
        "created_by": string,
        "role_ping": string,
        "description": string,
        "created_at": string,
        "last_updated": string,
        "votes": {
            "total": number,
            "positive": number,
            "negative": number
        },
        "state": "active" | "expired" | "cancelled" | "completed"
    }
}
```

## Configuration Management

### Get Current Configuration
Retrieve current bot configuration settings.

**Endpoint:** `GET /config`

**Response:**
```json
{
    "status": "success" | "error",
    "data": {
        "ssu_channel_id": string,
        "ssd_channel_id": string,
        "ssup_channel_id": string,
        "guild_id": string,
        "allowed_roles": string[],
        "api_host": string,
        "api_port": number,
        "auto_update_enabled": boolean,
        "admin_users": string[]
    }
}
```

### Update Channel Configuration
Configure channel settings for different commands.

**Endpoint:** `POST /config/channels`

**Request Body:**
```json
{
    "ssu_channel_id": string,   // Channel ID for SSU commands
    "ssd_channel_id": string,   // Channel ID for SSD commands
    "ssup_channel_id": string   // Channel ID for SSUP commands
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "channels": {
        "ssu_channel_id": string,
        "ssd_channel_id": string,
        "ssup_channel_id": string
    }
}
```

### Manage Role Permissions
Configure roles that can use bot commands.

**Endpoint:** `POST /config/roles`

**Request Body:**
```json
{
    "action": "add" | "remove" | "clear",
    "role": string,   // Required for add/remove actions
    "permissions": {  // Optional permissions configuration
        "can_use_ssu": boolean,
        "can_use_ssd": boolean,
        "can_use_ssup": boolean,
        "can_configure": boolean
    }
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "allowed_roles": string[]
}
```

### Admin User Management
Manage users with administrative access.

**Endpoint:** `POST /config/admins`

**Request Body:**
```json
{
    "action": "add" | "remove",
    "user_id": string
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "admin_users": string[]
}
```

### Bot Settings Configuration
Configure general bot settings.

**Endpoint:** `POST /config/settings`

**Request Body:**
```json
{
    "auto_update_enabled": boolean,       // Enable/disable auto-updates
    "command_prefix": string,            // Set command prefix
    "api_host": string,                 // API host address
    "api_port": number,                 // API port number
    "logging_level": "INFO" | "DEBUG" | "WARNING" | "ERROR",
    "timezone": string                  // e.g., "UTC", "America/New_York"
}
```

**Response:**
```json
{
    "status": "success" | "error",
    "detail": string,
    "settings": {
        "auto_update_enabled": boolean,
        "command_prefix": string,
        "api_host": string,
        "api_port": number,
        "logging_level": string,
        "timezone": string
    }
}
```

## Error Handling

### Status Codes

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: Request succeeded
- `201 Created`: Resource successfully created
- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Request conflicts with current state
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Bot not ready or maintenance mode

### Error Response Format

All error responses follow this standardized format:

```json
{
    "status": "error",
    "error": {
        "code": string,         // Error code
        "message": string,      // Human-readable error message
        "details": object,      // Additional error details (optional)
        "correlation_id": string // Unique error ID for tracking
    },
    "timestamp": string        // ISO 8601 timestamp
}
```

### Common Error Codes

#### Authentication & Authorization
- `AUTH_001`: Missing authentication token
- `AUTH_002`: Invalid authentication token
- `AUTH_003`: Token expired
- `AUTH_004`: Insufficient permissions
- `AUTH_005`: Rate limit exceeded

#### Server Management
- `SSU_001`: Server already running
- `SSU_002`: Invalid server name format
- `SSU_003`: Invalid host mention format
- `SSU_004`: Invalid ping mention format
- `SSD_001`: No server currently running
- `SSD_002`: Server shutdown in progress

#### Poll Management
- `POLL_001`: Invalid poll ID
- `POLL_002`: Poll already expired
- `POLL_003`: Invalid time format
- `POLL_004`: Poll update failed
- `POLL_005`: Maximum active polls reached

#### Role Management
- `ROLE_001`: Role not found
- `ROLE_002`: Invalid role position
- `ROLE_003`: Cannot modify higher role
- `ROLE_004`: Invalid role color format
- `ROLE_005`: Role name already exists

#### Configuration
- `CONFIG_001`: Invalid channel ID
- `CONFIG_002`: Channel not found
- `CONFIG_003`: Invalid configuration value
- `CONFIG_004`: Configuration update failed

### Rate Limiting

The API implements rate limiting to prevent abuse:

1. **Global Limits**
   - 1000 requests per hour per IP
   - 100 requests per minute per IP

2. **Endpoint-Specific Limits**
   - SSU/SSD: 10 requests per minute
   - Polls: 30 requests per minute
   - Configuration: 60 requests per minute
   - Role Management: 30 requests per minute

3. **Rate Limit Response**
```json
{
    "status": "error",
    "error": {
        "code": "AUTH_005",
        "message": "Rate limit exceeded",
        "details": {
            "limit": number,
            "remaining": number,
            "reset": number,
            "retry_after": number
        }
    }
}
```

### Error Handling Best Practices

1. **Always Check Response Status**
   - Verify HTTP status code first
   - Check response body for detailed error information
   - Log correlation_id for debugging

2. **Implement Retry Logic**
   - Use exponential backoff for retries
   - Honor retry_after headers
   - Set maximum retry attempts
   - Don't retry on validation errors (400)

3. **Handle Rate Limits**
   - Track remaining limits
   - Implement request queuing
   - Add delays between requests
   - Use bulk endpoints when available

4. **Error Recovery**
   - Implement graceful degradation
   - Cache successful responses
   - Provide meaningful user feedback
   - Maintain audit logs of failures

### Error Recovery Examples

```python
import requests
from time import sleep
from datetime import datetime

def make_api_request(endpoint, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(f"http://localhost:8000{endpoint}", json=data)
            
            if response.status_code == 200:
                return response.json()
                
            elif response.status_code == 429:
                # Handle rate limiting
                retry_after = int(response.headers.get('Retry-After', 60))
                sleep(retry_after)
                continue
                
            elif response.status_code >= 500:
                # Server error, retry with exponential backoff
                sleep(2 ** attempt)
                continue
                
            else:
                # Client error, don't retry
                error_data = response.json()
                raise Exception(f"API Error: {error_data['error']['message']}")
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            sleep(2 ** attempt)
            continue
```

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
