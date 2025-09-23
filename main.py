# Copyright © 2025 Veilaris / Veilaris Management System
# Licensed under the VOSL 2.3 

import discord
from discord.ext import commands
import json
import logging
import os
from datetime import datetime, timedelta
import re
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_errors.log'),
        logging.StreamHandler()
    ]
)

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config if it doesn't exist
        default_config = {
            "token": "YOUR_BOT_TOKEN_HERE",
            "ssu_channel_id": None,
            "ssd_channel_id": None,
            "ssup_channel_id": None,
            "guild_id": None,
            "allowed_roles": [],
            "api_port": 8000,
            "api_host": "0.0.0.0"
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        logging.error("Config file not found. Created default config.json. Please fill in your bot token and channel IDs.")
        return default_config

config = load_config()

# API Models
class SSURequest(BaseModel):
    server_name: str
    host: str
    ping: str
    description: Optional[str] = None

class SSUPRequest(BaseModel):
    server_name: str
    time: str
    role: str
    description: Optional[str] = None

class SSUPRequest(BaseModel):
    server_name: str
    time: str
    role: str
    description: Optional[str] = None

class MemberResponse(BaseModel):
    id: str
    name: str
    type: str  # 'user' or 'role'
    displayName: Optional[str] = None

# API Setup
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.options("/ssu")
@app.options("/ssup")
@app.options("/ssd")
@app.options("/members")
async def options_handler():
    return JSONResponse(
        status_code=200,
        content={"detail": "OK"}
    )

@app.get("/members")
async def get_members(query: str = ""):
    try:
        logging.info(f"Received members request with query: {query}")
        
        if not bot.is_ready():
            raise HTTPException(status_code=503, detail="Bot is not ready")

        guild_id = config.get('guild_id')
        if not guild_id:
            raise HTTPException(status_code=500, detail="Guild ID not configured")

        guild = bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=500, detail="Guild not found")

        query = query.lower()
        members = []

        logging.info(f"Searching for members/roles with query: {query}")
        logging.info(f"Guild members count: {len(guild.members)}")
        logging.info(f"Guild roles count: {len(guild.roles)}")

        # Add matching roles
        for role in guild.roles:
            if query in role.name.lower():
                members.append({
                    "id": str(role.id),
                    "name": role.name,
                    "type": "role"
                })
                logging.info(f"Found matching role: {role.name}")

        # Add matching members
        for member in guild.members:
            logging.info(f"Checking member: {member.name} (Nick: {member.nick})")
            if query in member.name.lower() or (member.nick and query in member.nick.lower()):
                members.append({
                    "id": str(member.id),
                    "name": member.name,
                    "displayName": member.nick,
                    "type": "user"
                })
                logging.info(f"Found matching member: {member.name}")

        result = {"status": "success", "data": members[:10]}  # Limit to 10 results
        logging.info(f"Returning {len(result['data'])} results")
        return result

    except Exception as e:
        logging.error(f"Error in members endpoint: {e}")
        return {"status": "error", "detail": str(e)}

async def create_api_context():
    """Create a fake context for API calls"""
    class FakeRole:
        def __init__(self, name):
            self.name = name

    class FakeAuthor:
        def __init__(self):
            self.id = 0
            self.roles = [FakeRole(role) for role in config.get('allowed_roles', [])]
            self.name = "API"
            self.display_name = "API"
            self.mention = "API"
            self._roles = [role.name.lower() for role in self.roles]
    
    class FakeGuild:
        def __init__(self):
            self.id = config.get('guild_id')
            self.roles = []
    
    class FakeContext:
        def __init__(self):
            self.author = FakeAuthor()
            self.guild = FakeGuild()
            self.bot = bot
            self._state = bot._connection if bot else None
            self.channel = bot.get_channel(config.get('ssu_channel_id'))
            
        async def send(self, *args, **kwargs):
            if self.channel:
                try:
                    return await self.channel.send(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error sending message to channel: {e}")
                    raise
            return None
            
        async def reply(self, *args, **kwargs):
            return await self.send(*args, **kwargs)

    if not bot or not bot.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    ctx = FakeContext()
    if not ctx.channel:
        raise HTTPException(status_code=500, detail="SSU channel not found")
        
    logging.info(f"Created API context with channel: {ctx.channel.id}")
    return ctx

@app.post("/ssu")
async def api_ssu(request: SSURequest):
    try:
        logging.info(f"Received SSU API request: {request.model_dump()}")
        
        if not bot.is_ready():
            logging.warning("Bot is not ready for API requests")
            return JSONResponse(
                status_code=503,
                content={"status": "error", "detail": "Bot is not ready. Please wait for bot to connect to Discord."}
            )

        # Check if SSU channel is configured
        ssu_channel_id = config.get('ssu_channel_id')
        if not ssu_channel_id:
            logging.error("SSU channel ID not configured")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": "SSU channel not configured"}
            )

        # Verify channel exists
        channel = bot.get_channel(ssu_channel_id)
        if not channel:
            logging.error(f"Could not find Discord channel with ID {ssu_channel_id}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": "Could not find configured Discord channel"}
            )

        ctx = await create_api_context()
        
        # Convert mentions and format the arguments
        host_mention = await convert_to_mention(request.host) if request.host else None
        ping_mention = await convert_to_mention(request.ping) if request.ping else None
        args = f"[{request.server_name}] [{host_mention or ''}] [{ping_mention or ''}]"
        if request.description:
            args += f" [{request.description}]"
        
        logging.info(f"Preparing to call server_startup with args: {args}")
        
        # Check if server is already running
        if not command_state["can_use_ssu"]:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "Cannot start server: A server is already running. Please use SSD first."}
            )
            
        # Set command state for API calls
        command_state["can_use_ssu"] = True
        
        # Call the server startup function
        try:
            await server_startup(ctx, args=args)
            logging.info("Server startup command completed successfully")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Server startup initiated"}
            )
        except Exception as cmd_error:
            logging.error(f"Error in server_startup: {str(cmd_error)}")
            raise cmd_error
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"API SSU error: {error_msg}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": error_msg}
        )

@app.post("/ssup")
async def api_ssup(request: SSUPRequest):
    try:
        logging.info(f"Received SSUP API request: {request.model_dump()}")
        
        if not bot.is_ready():
            logging.warning("Bot is not ready for API requests")
            return JSONResponse(
                status_code=503,
                content={"status": "error", "detail": "Bot is not ready. Please wait for bot to connect to Discord."}
            )

        ctx = await create_api_context()
        
        # Convert role mention and format the arguments
        role_mention = convert_to_mention(request.role) if request.role else None
        args = f"[{request.server_name}] [{request.time}] [{role_mention or ''}]"
        if request.description:
            args += f" [{request.description}]"
        
        logging.info(f"Preparing to call server_startup_poll with args: {args}")
        
        try:
            await server_startup_poll(ctx, args=args)
            logging.info("Server startup poll created successfully")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Server startup poll created"}
            )
        except Exception as cmd_error:
            logging.error(f"Error in server_startup_poll: {str(cmd_error)}")
            raise cmd_error
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"API SSUP error: {error_msg}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": error_msg}
        )

@app.get("/members")
async def get_members(query: str = ""):
    try:
        logging.info(f"Received members request with query: {query}")
        
        # Return empty list for empty queries
        if not query:
            return {"status": "success", "data": []}

        if not bot.is_ready():
            raise HTTPException(status_code=503, detail="Bot is not ready")

        guild_id = config.get('guild_id')
        if not guild_id:
            raise HTTPException(status_code=500, detail="Guild ID not configured")

        guild = bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=500, detail="Guild not found")

        query = query.lower()
        members = []

        logging.info(f"Searching for members/roles with query: {query}")
        logging.info(f"Guild members count: {len(guild.members)}")
        logging.info(f"Guild roles count: {len(guild.roles)}")

        # Add matching roles
        for role in guild.roles:
            if query in role.name.lower():
                members.append(MemberResponse(
                    id=str(role.id),
                    name=role.name,
                    type='role'
                ))
                logging.info(f"Found matching role: {role.name}")

        # Add matching members
        for member in guild.members:
            logging.info(f"Checking member: {member.name} (Nick: {member.nick})")
            if query in member.name.lower() or (member.nick and query in member.nick.lower()):
                members.append(MemberResponse(
                    id=str(member.id),
                    name=member.name,
                    displayName=member.nick,
                    type='user'
                ))
                logging.info(f"Found matching member: {member.name}")

        result = {"status": "success", "data": members[:10]}  # Limit to 10 results
        logging.info(f"Returning {len(result['data'])} results")
        return result
    except Exception as e:
        logging.error(f"Error in members endpoint: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/polls/active")
async def get_active_polls():
    """Get all currently active SSUP polls"""
    try:
        return {
            "status": "success",
            "data": {
                "active_polls": [
                    {
                        "id": poll_id,
                        "server_name": data['server_name'],
                        "target_time": data['target_time'].isoformat() if isinstance(data['target_time'], datetime) else data['target_time'],
                        "created_by": data['created_by'],
                        "role_ping": data['role_ping'],
                        "description": data['description']
                    } for poll_id, data in active_polls.items()
                ]
            }
        }
    except Exception as e:
        logging.error(f"Error getting active polls: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/server/history")
async def get_server_history(limit: int = 10):
    """Get history of server events (SSU/SSD)"""
    try:
        # Ensure limit is reasonable
        limit = max(1, min(limit, 100))  # Between 1 and 100
        
        # Get the most recent events and resolve mentions
        history = []
        raw_history = server_history[-limit:] if server_history else []
        
        for event in raw_history:
            resolved_event = event.copy()
            if event.get('host'):
                resolved_event['host'] = await resolve_mention(event['host'])
            if event.get('ping'):
                resolved_event['ping'] = await resolve_mention(event['ping'])
            history.append(resolved_event)

        return {
            "status": "success",
            "data": {
                "history": history[:limit],
                "current_state": {
                    "server_name": last_ssu_data.get("server_name"),
                    "host": last_ssu_data.get("host"),
                    "ping": last_ssu_data.get("ping"),
                    "timestamp": last_ssu_data.get("timestamp"),
                    "user": last_ssu_data.get("user")
                }
            }
        }
    except Exception as e:
        logging.error(f"Error getting server history: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/commands/state")
async def get_command_state():
    """Get current state of commands (which can be used)"""
    try:
        return {
            "status": "success",
            "data": {
                "can_use_ssu": command_state.get("can_use_ssu", True),
                "can_use_ssd": command_state.get("can_use_ssd", False),
                "last_command": command_state.get("last_command"),
                "last_command_time": command_state.get("last_command_time")
            }
        }
    except Exception as e:
        logging.error(f"Error getting command state: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/config/channels")
async def get_channel_config():
    """Get current channel configuration"""
    try:
        channels = {}
        for channel_type in ['ssu_channel_id', 'ssd_channel_id', 'ssup_channel_id']:
            channel_id = config.get(channel_type)
            if channel_id:
                channel = bot.get_channel(channel_id)
                channels[channel_type] = {
                    "id": channel_id,
                    "name": channel.name if channel else None,
                    "configured": channel is not None
                }

        return {
            "status": "success",
            "data": {
                "channels": channels,
                "guild_id": config.get('guild_id'),
                "allowed_roles": config.get('allowed_roles', [])
            }
        }
    except Exception as e:
        logging.error(f"Error getting channel config: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/status")
async def get_status():
    try:
        server_status = "online" if not command_state.get("can_use_ssu", True) else "offline"
        last_command = command_state.get("last_command", "None")
        
        last_ssu = None
        if isinstance(last_ssu_data, dict) and last_ssu_data.get("server_name"):
            last_ssu = {
                "server_name": last_ssu_data.get("server_name"),
                "host": last_ssu_data.get("host"),
                "ping": last_ssu_data.get("ping"),
                "timestamp": last_ssu_data.get("timestamp")
            }
        
        data = {
            "status": "success",
            "data": {
                "server_status": server_status,
                "last_command": last_command,
                "last_ssu": last_ssu
            }
        }
        return data
    except Exception as e:
        logging.error(f"Error in status endpoint: {str(e)}")
        return {"status": "error", "detail": str(e)}


@app.post("/ssd")
async def api_ssd():
    try:
        logging.info("Received SSD API request")
        
        if not bot.is_ready():
            logging.warning("Bot is not ready for API requests")
            return JSONResponse(
                status_code=503,
                content={"status": "error", "detail": "Bot is not ready. Please wait for bot to connect to Discord."}
            )

        ctx = await create_api_context()
        
        logging.info("Preparing to call server_shutdown")
        
        try:
            await server_shutdown(ctx)
            logging.info("Server shutdown command completed successfully")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Server shutdown initiated"}
            )
        except Exception as cmd_error:
            logging.error(f"Error in server_shutdown: {str(cmd_error)}")
            raise cmd_error
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"API SSD error: {error_msg}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": error_msg}
        )

@app.post("/ssup")
async def api_ssup(request: SSUPRequest):
    ctx = await create_api_context()
    args = f"[{request.server_name}] [{request.time}] [{request.role}]"
    if request.description:
        args += f" [{request.description}]"
    
    try:
        await server_startup_poll(ctx, args=args)
        return {"status": "success", "message": "Server startup poll created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ssd")
async def api_ssd():
    ctx = await create_api_context()
    try:
        await server_shutdown(ctx)
        return {"status": "success", "message": "Server shutdown initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Explicitly enable message content intent
intents.members = True  # Enable members intent for member fetching
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help

# Store last SSU information and command states
last_ssu_data = {
    "server_name": None,
    "host": None,
    "ping": None,
    "timestamp": None,
    "user": None
}

# Store server history
server_history = []

def save_server_history():
    """Save server history to a dedicated file"""
    try:
        with open('ssu_history.json', 'w') as f:
            json.dump(server_history, f, indent=4, default=str)
    except Exception as e:
        logging.error(f"Error saving server history: {e}")

async def resolve_mention(mention_str):
    """Convert a mention string to a readable name"""
    if not mention_str:
        return None
    
    # If it's already a normal string, return as is
    if not (mention_str.startswith('<@') and mention_str.endswith('>')): 
        return mention_str

    try:
        # Get the ID from the mention string
        id_str = ''.join(filter(str.isdigit, mention_str))
        if not id_str:
            return mention_str

        id_num = int(id_str)
        guild_id = config.get('guild_id')
        if not guild_id:
            return mention_str

        guild = bot.get_guild(guild_id)
        if not guild:
            return mention_str

        # Check if it's a role mention
        if mention_str.startswith('<@&'):
            role = guild.get_role(id_num)
            return role.name if role else mention_str

        # Check if it's a user mention
        # First try get_member (cached)
        member = guild.get_member(id_num)
        if not member:
            try:
                # If not in cache, try to fetch
                member = await guild.fetch_member(id_num)
            except discord.NotFound:
                return mention_str
            except Exception as e:
                logging.error(f"Error fetching member {id_num}: {e}")
                return mention_str

        return member.display_name or member.name

    except Exception as e:
        logging.error(f"Error resolving mention {mention_str}: {e}")
        return mention_str

def load_server_history():
    """Load server history from dedicated file"""
    global server_history
    try:
        with open('ssu_history.json', 'r') as f:
            loaded_history = json.load(f)
            if isinstance(loaded_history, list):
                server_history = loaded_history
            else:
                server_history = []
    except FileNotFoundError:
        server_history = []
        save_server_history()  # Create the file if it doesn't exist
    except Exception as e:
        logging.error(f"Error loading server history: {e}")
        server_history = []

# Track command usage to prevent duplicate usage
command_state = {
    "last_command": None,  # "SSU" or "SSD" or None
    "can_use_ssu": True,
    "can_use_ssd": False
}

# Store active polls for tracking
active_polls = {}

ad_members = [918227890338938940]

def save_ssu_data():
    """Save SSU data, command state, and active polls to file for persistence"""
    try:
        data_to_save = {
            "last_ssu_data": last_ssu_data,
            "command_state": command_state,
            "active_polls": active_polls
        }
        with open('last_ssu.json', 'w') as f:
            json.dump(data_to_save, f, indent=4, default=str)
    except Exception as e:
        logging.error(f"Error saving SSU data: {e}")

def load_ssu_data():
    """Load SSU data, command state, and active polls from file"""
    global last_ssu_data, command_state, active_polls
    try:
        with open('last_ssu.json', 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                if "last_ssu_data" in data:
                    last_ssu_data = data["last_ssu_data"]
                if "command_state" in data:
                    command_state = data["command_state"]
                if "active_polls" in data:
                    active_polls = data["active_polls"]
                # New format with command state and polls
                last_ssu_data = data.get("last_ssu_data", last_ssu_data)
                command_state.update(data.get("command_state", command_state))
                active_polls.update(data.get("active_polls", {}))
            else:
                # Old format, just SSU data
                last_ssu_data = data
                # Set initial state based on existing data
                if last_ssu_data.get("server_name"):
                    command_state["last_command"] = "SSU"
                    command_state["can_use_ssu"] = False
                    command_state["can_use_ssd"] = True
    except FileNotFoundError:
        logging.info("No previous SSU data found")
    except Exception as e:
        logging.error(f"Error loading SSU data: {e}")

def parse_bracketed_arguments(message_content):
    """Parse arguments in square brackets from a message"""
    # Pattern to match content within square brackets
    pattern = r'\[([^\]]+)\]'
    matches = re.findall(pattern, message_content)
    return matches

async def convert_to_mention(name_str):
    """Convert a username or @mention to proper Discord mention"""
    if not name_str:
        return None
    
    # If it's already a mention, return as is
    if name_str.startswith('<@') and name_str.endswith('>'):
        return name_str
        
    # Remove @ if present
    clean_name = name_str.lstrip('@')
    
    # Try to find the user in the guild
    guild_id = config.get('guild_id')
    if guild_id:
        guild = bot.get_guild(guild_id)
        if guild:
            # Try to find member
            member = None
            try:
                # First try as ID if it looks like one
                if clean_name.isdigit():
                    member = guild.get_member(int(clean_name))
                    if not member:
                        try:
                            member = await guild.fetch_member(int(clean_name))
                        except discord.NotFound:
                            pass
                else:
                    # Try to find by name
                    member = discord.utils.get(guild.members, name=clean_name) or \
                            discord.utils.get(guild.members, display_name=clean_name) or \
                            discord.utils.get(guild.members, name=clean_name.lower()) or \
                            discord.utils.get(guild.members, display_name=clean_name.lower())
            except Exception as e:
                logging.error(f"Error finding member: {e}")
            
            if member:
                return member.mention
            
            # Try to find role
            for role in guild.roles:
                if role.name.lower() == clean_name.lower():
                    return role.mention
    
    # If we can't find the user/role, return original with @
    return f"@{clean_name}"

def parse_mention(mention_str):
    """Parse @player mention to get username"""
    if mention_str.startswith('<@') and mention_str.endswith('>'):
        # It's a Discord mention
        user_id = re.findall(r'\d+', mention_str)
        if user_id:
            try:
                user = bot.get_user(int(user_id[0]))
                return user.display_name if user else mention_str
            except:
                return mention_str
    else:
        # It's a plain username, remove @ if present
        return mention_str.lstrip('@')

def parse_time_string(time_str):
    """Parse time string like '45min', '1d30min', '1w', '1mo', '1y3mo2w6d25min'"""
    if not time_str:
        return None
    
    # Dictionary for time units
    time_units = {
        'y': 365 * 24 * 60,  # years to minutes
        'mo': 30 * 24 * 60,  # months to minutes (approximate)
        'w': 7 * 24 * 60,    # weeks to minutes
        'd': 24 * 60,        # days to minutes
        'min': 1             # minutes
    }
    
    total_minutes = 0
    
    # Find all time components
    # Pattern matches: number + unit (y, mo, w, d, min)
    pattern = r'(\d+)(y|mo|w|d|min)'
    matches = re.findall(pattern, time_str.lower())
    
    if not matches:
        return None
    
    for amount, unit in matches:
        total_minutes += int(amount) * time_units.get(unit, 0)
    
    return total_minutes

def format_time_remaining(target_time):
    """Format remaining time for display"""
    now = datetime.now()
    if target_time <= now:
        return "Now"
    
    diff = target_time - now
    total_minutes = int(diff.total_seconds() / 60)
    
    if total_minutes < 60:
        return f"{total_minutes}min"
    elif total_minutes < 1440:  # less than a day
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}min" if minutes > 0 else f"{hours}h"
    else:
        days = total_minutes // 1440
        hours = (total_minutes % 1440) // 60
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"

def has_allowed_role(ctx):
    """Check if user has any of the allowed roles"""
    # Special case for API context
    if getattr(ctx.author, 'name', None) == 'API':
        return True
        
    allowed_roles = config.get('allowed_roles', [])
    
    # If no roles configured, allow everyone (backward compatibility)
    if not allowed_roles:
        return True
    
    # Get user roles safely
    try:
        user_roles = [getattr(role, 'name', '').lower() for role in getattr(ctx.author, 'roles', [])]
    except AttributeError:
        user_roles = []
    
    # Convert allowed roles to lowercase
    allowed_roles_lower = [role.lower() for role in allowed_roles]
    
    return any(role in allowed_roles_lower for role in user_roles)

def role_check():
    """Decorator to check if user has allowed roles"""
    async def predicate(ctx):
        # Always allow API context
        if getattr(ctx.author, 'name', None) == 'API':
            return True
            
        if not has_allowed_role(ctx):
            allowed_roles_str = ", ".join(config.get('allowed_roles', []))
            await ctx.send(f"❌ You don't have permission to use this command. Required roles: {allowed_roles_str}")
            return False
        return True
    return commands.check(predicate)

def ad_member_check():
    """Decorator to check if user is in ad_members list"""
    async def predicate(ctx):
        if ctx.author.id not in ad_members:
            return False  # Silently fail if not authorized
        return True
    return commands.check(predicate)

async def update_poll_embed(message, poll_data, target_time):
    """Update a single poll's embed with current time remaining"""
    try:
        # Create updated embed
        embed = discord.Embed(
            title="📊 Server Startup Poll",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        embed.add_field(name="Server Name", value=poll_data['server_name'], inline=True)
        embed.add_field(name="Scheduled Time", value=f"<t:{int(target_time.timestamp())}:F>", inline=True)
        embed.add_field(name="Time Until Start", value=format_time_remaining(target_time), inline=True)
        embed.add_field(name="Created by", value=poll_data['created_by'], inline=True)
        
        # Add ping info to embed if provided
        role_ping = poll_data.get('role_ping')
        if role_ping:
            # Format the ping display similar to how it's done in SSUP command
            ping_display = None
            if role_ping.lower() in ['@everyone', 'everyone']:
                ping_display = "@everyone"
            elif role_ping.lower() in ['@here', 'here']:
                ping_display = "@here"
            elif role_ping.startswith('<@&') and role_ping.endswith('>'):
                ping_display = role_ping
            elif role_ping.startswith('@'):
                ping_display = role_ping
            else:
                ping_display = f"@{role_ping}"
            
            embed.add_field(name="Notifying", value=ping_display, inline=True)
        else:
            # Add empty field to maintain layout consistency
            embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Add description if provided
        description = poll_data.get('description')
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        
        embed.add_field(name="Instructions", value="🟢 = Yes, start the server\n🔴 = No, don't start", inline=False)
        embed.set_footer(text="Veilairs Server Management")
        
        # Update the message
        await message.edit(embed=embed)
        return True
        
    except discord.NotFound:
        logging.warning(f"Poll message {message.id} not found during update")
        return False
    except discord.Forbidden:
        logging.warning(f"No permission to edit poll message {message.id}")
        return False
    except Exception as e:
        logging.error(f"Error updating poll embed for message {message.id}: {e}")
        return False

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Version: Veilairs Server Management Bot v2.1.3')
    load_ssu_data()
    load_server_history()
    # Start the poll monitor task
    bot.loop.create_task(monitor_polls())

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors and log them"""
    logging.error(f"Command error in {ctx.command}: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        await ctx.send("❌ An error occurred while processing the command.")

async def monitor_polls():
    """Monitor active polls, update time displays, and post results when time is reached"""
    while True:
        try:
            current_time = datetime.now()
            completed_polls = []
            invalid_polls = []
            
            for message_id, poll_data in active_polls.items():
                target_time_str = poll_data.get('target_time')
                if not target_time_str:
                    continue
                    
                # Parse target time
                if isinstance(target_time_str, str):
                    target_time = datetime.fromisoformat(target_time_str)
                else:
                    target_time = target_time_str
                
                # Check if poll time has been reached
                if current_time >= target_time:
                    await process_poll_result(message_id, poll_data)
                    completed_polls.append(message_id)
                else:
                    # Update the poll's time display
                    ssup_channel_id = config.get('ssup_channel_id')
                    if ssup_channel_id:
                        channel = bot.get_channel(ssup_channel_id)
                        if channel:
                            try:
                                message = await channel.fetch_message(int(message_id))
                                success = await update_poll_embed(message, poll_data, target_time)
                                if not success:
                                    # Message might be deleted, mark for removal
                                    invalid_polls.append(message_id)
                            except discord.NotFound:
                                # Message was deleted, mark for removal
                                invalid_polls.append(message_id)
                                logging.info(f"Poll message {message_id} was deleted, removing from active polls")
                            except Exception as e:
                                logging.error(f"Error updating poll {message_id}: {e}")
            
            # Remove completed and invalid polls
            for message_id in completed_polls + invalid_polls:
                if message_id in active_polls:
                    del active_polls[message_id]
            
            # Save data if there were changes
            if completed_polls or invalid_polls:
                save_ssu_data()
                if completed_polls:
                    logging.info(f"Processed {len(completed_polls)} completed polls")
                if invalid_polls:
                    logging.info(f"Removed {len(invalid_polls)} invalid polls")
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logging.error(f"Error in poll monitor: {e}")
            await asyncio.sleep(60)

async def process_poll_result(message_id, poll_data):
    """Process poll result and post the outcome"""
    try:
        ssup_channel_id = config.get('ssup_channel_id')
        if not ssup_channel_id:
            return
        
        channel = bot.get_channel(ssup_channel_id)
        if not channel:
            return
        
        # Try to fetch the original poll message
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            logging.warning(f"Poll message {message_id} not found")
            return
        
        # Count reactions
        green_votes = 0
        red_votes = 0
        
        for reaction in message.reactions:
            if str(reaction.emoji) == "🟢":
                green_votes = reaction.count - 1  # Subtract bot's reaction
            elif str(reaction.emoji) == "🔴":
                red_votes = reaction.count - 1  # Subtract bot's reaction
        
        # Determine result
        if green_votes > red_votes:
            result = "✅ **APPROVED**"
            result_color = 0x00ff00
            result_description = f"The server startup has been **approved** with {green_votes} votes in favor and {red_votes} against."
        elif red_votes > green_votes:
            result = "❌ **REJECTED**"
            result_color = 0xff0000
            result_description = f"The server startup has been **rejected** with {red_votes} votes against and {green_votes} in favor."
        else:
            result = "⚖️ **TIE**"
            result_color = 0xffff00
            result_description = f"The poll resulted in a **tie** with {green_votes} votes each. Admin decision required."
        
        # Create result embed
        embed = discord.Embed(
            title="📊 Poll Results",
            description=result_description,
            color=result_color,
            timestamp=datetime.now()
        )
        embed.add_field(name="Server Name", value=poll_data.get('server_name', 'Unknown'), inline=True)
        embed.add_field(name="Result", value=result, inline=True)
        embed.add_field(name="Vote Count", value=f"🟢 {green_votes} | 🔴 {red_votes}", inline=True)
        
        if green_votes > red_votes:
            embed.add_field(name="Next Step", value="Use `!SSU [server_name] [@host] [@ping] [description]` command to start the server", inline=False)
        
        embed.set_footer(text="Veilairs Server Management")
        
        # Send result message
        await channel.send(embed=embed)
        
    except Exception as e:
        logging.error(f"Error processing poll result: {e}")

@bot.command(name='SSU')
@role_check()
async def server_startup(ctx, *, args: str = None):
    """Server Start Up command - Format: !SSU [server_name] [@host] [@ping] [description]"""
    try:
        # Check if SSU can be used
        if not command_state["can_use_ssu"]:
            await ctx.send("❌ Cannot use SSU command. You must use !SSD first to shut down the current server.")
            return

        # Check if SSU channel is configured
        ssu_channel_id = config.get('ssu_channel_id')
        if not ssu_channel_id:
            await ctx.send("❌ SSU channel not configured. Please set `ssu_channel_id` in config.json")
            return

        if not args:
            await ctx.send("❌ Please provide arguments. Usage: `!SSU [server_name] [@host] [@ping] [description]`\nExample: `!SSU [Testing Server] [@john] [@everyone] [Server restart for updates]`")
            return

        # Parse bracketed arguments
        bracketed_args = parse_bracketed_arguments(args)
        
        if len(bracketed_args) < 3:
            await ctx.send("❌ Invalid format. Usage: `!SSU [server_name] [@host] [@ping] [description]`\nExample: `!SSU [Testing Server] [@john] [@everyone] [Server restart for updates]`")
            return

        server_name = bracketed_args[0]
        host = await convert_to_mention(bracketed_args[1])
        ping = await convert_to_mention(bracketed_args[2])
        description = bracketed_args[3] if len(bracketed_args) > 3 else None

        # Get the configured channel
        channel = bot.get_channel(ssu_channel_id)
        if not channel:
            await ctx.send("❌ SSU channel not found. Please check the channel ID in config.json")
            return

        # Convert host and ping to proper mentions
        host_mention = host
        ping_mention = ping
        
        # Update last SSU data
        last_ssu_data.update({
            "server_name": server_name,
            "host": host_mention,
            "ping": ping_mention,
            "description": description,
            "timestamp": datetime.now(),
            "user": ctx.author.display_name
        })
        
        # Update command state
        command_state["last_command"] = "SSU"
        command_state["can_use_ssu"] = False
        command_state["can_use_ssd"] = True
        command_state["last_command_time"] = datetime.now().isoformat()
        
        # Add to history
        server_history.append({
            "type": "SSU",
            "server_name": server_name,
            "host": host_mention,
            "ping": ping_mention,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "user": ctx.author.display_name
        })
        
        # Keep only the last 100 entries
        if len(server_history) > 100:
            server_history.pop(0)
        
        # Save both state and history
        save_ssu_data()
        save_server_history()

        # Create embed message
        embed = discord.Embed(
            title="🟢 Server Started",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Server Name", value=server_name, inline=True)
        embed.add_field(name="Host", value=host_mention, inline=True)
        embed.add_field(name="Ping", value=ping_mention, inline=True)
        embed.add_field(name="Started by", value=ctx.author.mention, inline=True)
        
        # Add description if provided
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        
        embed.set_footer(text="Veilairs Server Management")

        # Send to configured channel with ping above the embed
        await channel.send(content=ping_mention, embed=embed)
        
        # Confirm in current channel if different
        if ctx.channel.id != ssu_channel_id:
            await ctx.send(f"✅ Server startup logged in {channel.mention}")

    except Exception as e:
        logging.error(f"Error in SSU command: {e}")
        await ctx.send("❌ An error occurred while processing the server startup.")

@bot.command(name='SSUP')
@role_check()
async def server_startup_poll(ctx, *, args: str = None):
    """Server Start Up Poll command - Format: !SSUP [server_name] [time] [@role] [description]"""
    try:
        # Check if SSUP channel is configured
        ssup_channel_id = config.get('ssup_channel_id')
        if not ssup_channel_id:
            await ctx.send("❌ SSUP channel not configured. Please set `ssup_channel_id` in config.json")
            return

        if not args:
            await ctx.send("❌ Please provide arguments. Usage: `!SSUP [server_name] [time] [@role] [description]`\nExample: `!SSUP [Testing Server] [45min] [@everyone] [Server restart for updates]`")
            return

        # Parse bracketed arguments
        bracketed_args = parse_bracketed_arguments(args)
        
        if len(bracketed_args) < 2:
            await ctx.send("❌ Invalid format. Usage: `!SSUP [server_name] [time] [@role] [description]`\nExample: `!SSUP [Testing Server] [45min] [@everyone] [Server restart for updates]`")
            return

        server_name = bracketed_args[0]
        time_str = bracketed_args[1]
        role_ping = await convert_to_mention(bracketed_args[2]) if len(bracketed_args) > 2 else None
        description = bracketed_args[3] if len(bracketed_args) > 3 else None

        # Parse time string
        minutes = parse_time_string(time_str)
        if minutes is None:
            await ctx.send("❌ Invalid time format. Use formats like: `[45min]`, `[1d30min]`, `[1w]`, `[1mo]`, `[1y3mo2w6d25min]`")
            return

        # Get the configured channel
        channel = bot.get_channel(ssup_channel_id)
        if not channel:
            await ctx.send("❌ SSUP channel not found. Please check the channel ID in config.json")
            return

        # Calculate target time
        target_time = datetime.now() + timedelta(minutes=minutes)
        
        # Prepare the message content and ping display (for role ping)
        message_content = ""
        ping_display = None
        
        if role_ping:
            # Clean up the role ping - handle both @everyone/@here and role mentions
            if role_ping.lower() in ['@everyone', 'everyone']:
                message_content = "@everyone"
                ping_display = "@everyone"
            elif role_ping.lower() in ['@here', 'here']:
                message_content = "@here"
                ping_display = "@here"
            elif role_ping.startswith('<@&') and role_ping.endswith('>'):
                # Already a proper role mention
                message_content = role_ping
                ping_display = role_ping
            else:
                # Use the converted mention from earlier
                message_content = role_ping
                ping_display = role_ping
        
        # Create embed message
        embed = discord.Embed(
            title="📊 Server Startup Poll",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        embed.add_field(name="Server Name", value=server_name, inline=True)
        embed.add_field(name="Scheduled Time", value=f"<t:{int(target_time.timestamp())}:F>", inline=True)
        embed.add_field(name="Time Until Start", value=format_time_remaining(target_time), inline=True)
        embed.add_field(name="Created by", value=ctx.author.mention, inline=True)
        
        # Add ping info to embed if provided
        if ping_display:
            embed.add_field(name="Notifying", value=ping_display, inline=True)
        
        # Add description if provided
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        
        embed.add_field(name="Instructions", value="🟢 = Yes, start the server\n🔴 = No, don't start", inline=False)
        embed.set_footer(text="Veilairs Server Management")

        # Send to configured channel with role ping if provided
        if message_content:
            message = await channel.send(content=message_content, embed=embed)
        else:
            message = await channel.send(embed=embed)
        
        # Add reactions
        await message.add_reaction("🟢")  # Green circle
        await message.add_reaction("🔴")  # Red circle
        
        # Store poll data for tracking
        active_polls[str(message.id)] = {
            'server_name': server_name,
            'target_time': target_time,
            'created_by': ctx.author.display_name,
            'channel_id': ssup_channel_id,
            'role_ping': role_ping,
            'description': description
        }
        save_ssu_data()
        
        # Confirm in current channel if different
        ping_msg = f" (pinging {ping_display})" if role_ping else ""
        desc_msg = f" - {description}" if description else ""
        
        if ctx.channel.id != ssup_channel_id:
            await ctx.send(f"✅ Server startup poll created in {channel.mention}{ping_msg}{desc_msg} (auto-updating every minute)")
        else:
            await ctx.send(f"✅ Server startup poll created{ping_msg}{desc_msg} (auto-updating every minute)")

    except Exception as e:
        logging.error(f"Error in SSUP command: {e}")
        await ctx.send("❌ An error occurred while creating the server startup poll.")

@bot.command(name='USSUP')
@role_check()
async def update_server_startup_poll(ctx, message_id: str = None):
    """Update Server Startup Poll time display (manual update - polls auto-update every minute)"""
    try:
        if not message_id:
            await ctx.send("❌ Please provide a message ID. Usage: `!USSUP <message_id>`\nRight-click on the poll message → Copy Message ID\n\n**Note:** Polls automatically update every minute, so manual updates are usually not needed.")
            return
        
        # Check if it's an active poll
        if message_id not in active_polls:
            await ctx.send("❌ No active poll found with that message ID.")
            return
        
        poll_data = active_polls[message_id]
        ssup_channel_id = config.get('ssup_channel_id')
        
        if not ssup_channel_id:
            await ctx.send("❌ SSUP channel not configured.")
            return
        
        channel = bot.get_channel(ssup_channel_id)
        if not channel:
            await ctx.send("❌ SSUP channel not found.")
            return
        
        # Fetch the message
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            await ctx.send("❌ Poll message not found.")
            # Remove from active polls since message doesn't exist
            del active_polls[message_id]
            save_ssu_data()
            return
        
        # Get target time
        target_time_str = poll_data.get('target_time')
        if isinstance(target_time_str, str):
            target_time = datetime.fromisoformat(target_time_str)
        else:
            target_time = target_time_str
        
        # Check if poll has expired
        if datetime.now() >= target_time:
            await ctx.send("❌ This poll has already expired. Check for results in the channel.")
            return
        
        # Update the poll embed
        success = await update_poll_embed(message, poll_data, target_time)
        
        if success:
            # Confirm update
            await ctx.send(f"✅ Poll manually updated! Time until start: **{format_time_remaining(target_time)}**\n*Polls automatically update every minute.*")
        else:
            await ctx.send("❌ Failed to update the poll message.")
        
    except Exception as e:
        logging.error(f"Error in USSUP command: {e}")
        await ctx.send("❌ An error occurred while updating the poll.")

@bot.command(name='SSD')
@role_check()
async def server_shutdown(ctx):
    """Server Shut Down command"""
    try:
        # Check if SSD can be used
        if not command_state["can_use_ssd"]:
            await ctx.send("❌ Cannot use SSD command. You must use !SSU first to start a server.")
            return

        # Check if SSD channel is configured
        ssd_channel_id = config.get('ssd_channel_id')
        if not ssd_channel_id:
            await ctx.send("❌ SSD channel not configured. Please set `ssd_channel_id` in config.json")
            return

        # Get the configured channel
        channel = bot.get_channel(ssd_channel_id)
        if not channel:
            await ctx.send("❌ SSD channel not found. Please check the channel ID in config.json")
            return

        # Update command state
        command_state["last_command"] = "SSD"
        command_state["can_use_ssu"] = True
        command_state["can_use_ssd"] = False
        command_state["last_command_time"] = datetime.now().isoformat()
        
        # Add to history
        server_history.append({
            "type": "SSD",
            "server_name": last_ssu_data.get("server_name", "Unknown"),
            "host": last_ssu_data.get("host", None),
            "timestamp": datetime.now().isoformat(),
            "user": ctx.author.display_name
        })
        
        # Keep only the last 100 entries
        if len(server_history) > 100:
            server_history.pop(0)
        
        # Save both state and history
        save_ssu_data()
        save_server_history()

        # Create embed message
        embed = discord.Embed(
            title="🔴 Server Shutdown",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Shutdown by", value=ctx.author.mention, inline=True)

        # Prepare ping content for display above embed
        ping_content = None
        if last_ssu_data.get("ping"):
            ping_content = last_ssu_data["ping"]

        # Add last SSU information if available
        if last_ssu_data.get("server_name"):
            embed.add_field(name="Server", value=last_ssu_data["server_name"], inline=True)
            embed.add_field(name="Hosted by", value=last_ssu_data["host"], inline=True)
            if last_ssu_data.get("ping"):
                embed.add_field(name="Ping", value=last_ssu_data["ping"], inline=True)
            if last_ssu_data.get("description"):
                embed.add_field(name="Description", value=last_ssu_data["description"], inline=False)
            embed.add_field(name="SSU by", value=last_ssu_data["user"], inline=True)
            
            if last_ssu_data.get("timestamp"):
                if isinstance(last_ssu_data["timestamp"], str):
                    # Parse string timestamp
                    last_time = datetime.fromisoformat(last_ssu_data["timestamp"].replace('Z', '+00:00'))
                else:
                    last_time = last_ssu_data["timestamp"]
                embed.add_field(name="Started", value=f"<t:{int(last_time.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Last SSU Info", value="No previous startup recorded", inline=False)

        embed.set_footer(text="Veilairs Server Management")

        # Send to configured channel with ping above embed if there was a last ping
        if ping_content:
            await channel.send(content=ping_content, embed=embed)
        else:
            await channel.send(embed=embed)
        
        # Confirm in current channel if different
        if ctx.channel.id != ssd_channel_id:
            await ctx.send(f"✅ Server shutdown logged in {channel.mention}")

    except Exception as e:
        logging.error(f"Error in SSD command: {e}")
        await ctx.send("❌ An error occurred while processing the server shutdown.")

@bot.command(name='config')
@commands.has_permissions(administrator=True)
async def configure_bot(ctx, setting: str = None, value: str = None):
    """Configure bot settings (Admin only)"""
    try:
        if not setting:
            embed = discord.Embed(title="Bot Configuration", color=0x0099ff)
            embed.add_field(name="SSU Channel", value=f"<#{config['ssu_channel_id']}>" if config['ssu_channel_id'] else "Not set", inline=False)
            embed.add_field(name="SSD Channel", value=f"<#{config['ssd_channel_id']}>" if config['ssd_channel_id'] else "Not set", inline=False)
            embed.add_field(name="SSUP Channel", value=f"<#{config['ssup_channel_id']}>" if config['ssup_channel_id'] else "Not set", inline=False)
            embed.add_field(name="Allowed Roles", value=", ".join(config['allowed_roles']) if config['allowed_roles'] else "Everyone", inline=False)
            embed.add_field(name="Active Polls", value=f"{len(active_polls)} poll(s) currently active", inline=False)
            embed.add_field(name="Usage", value="`!config ssu_channel <channel_id>`\n`!config ssd_channel <channel_id>`\n`!config ssup_channel <channel_id>`\n`!config add_role @RoleName`\n`!config remove_role @RoleName`\n`!config clear_roles`", inline=False)
            embed.add_field(name="New Command Format", value="**SSU:** `!SSU [server_name] [@host] [@ping] [description]`\n**SSUP:** `!SSUP [server_name] [time] [@role] [description]`", inline=False)
            await ctx.send(embed=embed)
            return

        if setting.lower() == 'ssu_channel':
            try:
                channel_id = int(value) if value.isdigit() else int(value.strip('<>#'))
                config['ssu_channel_id'] = channel_id
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                await ctx.send(f"✅ SSU channel set to <#{channel_id}>")
            except ValueError:
                await ctx.send("❌ Invalid channel ID")
        
        elif setting.lower() == 'ssd_channel':
            try:
                channel_id = int(value) if value.isdigit() else int(value.strip('<>#'))
                config['ssd_channel_id'] = channel_id
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                await ctx.send(f"✅ SSD channel set to <#{channel_id}>")
            except ValueError:
                await ctx.send("❌ Invalid channel ID")
        
        elif setting.lower() == 'ssup_channel':
            try:
                channel_id = int(value) if value.isdigit() else int(value.strip('<>#'))
                config['ssup_channel_id'] = channel_id
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                await ctx.send(f"✅ SSUP channel set to <#{channel_id}>")
            except ValueError:
                await ctx.send("❌ Invalid channel ID")
        
        elif setting.lower() == 'add_role':
            if not value:
                await ctx.send("❌ Please provide a role. Usage: `!config add_role @RoleName` or `!config add_role RoleName`")
                return
            
            if 'allowed_roles' not in config:
                config['allowed_roles'] = []
            
            # Parse role mention or plain text
            role_name = None
            if value.startswith('<@&') and value.endswith('>'):
                # It's a role mention like <@&123456789>
                role_id = re.findall(r'\d+', value)
                if role_id and ctx.guild:
                    role = ctx.guild.get_role(int(role_id[0]))
                    if role:
                        role_name = role.name
                    else:
                        await ctx.send("❌ Role not found")
                        return
                else:
                    await ctx.send("❌ Invalid role mention")
                    return
            else:
                # Plain text role name, remove @ if present
                role_name = value.lstrip('@')
            
            if role_name not in config['allowed_roles']:
                config['allowed_roles'].append(role_name)
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                await ctx.send(f"✅ Added role `{role_name}` to allowed roles")
            else:
                await ctx.send(f"❌ Role `{role_name}` is already in allowed roles")
        
        elif setting.lower() == 'remove_role':
            if not value:
                await ctx.send("❌ Please provide a role. Usage: `!config remove_role @RoleName` or `!config remove_role RoleName`")
                return
            
            # Parse role mention or plain text
            role_name = None
            if value.startswith('<@&') and value.endswith('>'):
                # It's a role mention like <@&123456789>
                role_id = re.findall(r'\d+', value)
                if role_id and ctx.guild:
                    role = ctx.guild.get_role(int(role_id[0]))
                    if role:
                        role_name = role.name
                    else:
                        await ctx.send("❌ Role not found")
                        return
                else:
                    await ctx.send("❌ Invalid role mention")
                    return
            else:
                # Plain text role name, remove @ if present
                role_name = value.lstrip('@')
            
            if 'allowed_roles' in config and role_name in config['allowed_roles']:
                config['allowed_roles'].remove(role_name)
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                await ctx.send(f"✅ Removed role `{role_name}` from allowed roles")
            else:
                await ctx.send(f"❌ Role `{role_name}` not found in allowed roles")
        
        elif setting.lower() == 'clear_roles':
            config['allowed_roles'] = []
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            await ctx.send("✅ Cleared all allowed roles. Everyone can now use commands.")
        
        else:
            await ctx.send("❌ Unknown setting. Use `ssu_channel`, `ssd_channel`, `ssup_channel`, `add_role`, `remove_role`, or `clear_roles`")

    except Exception as e:
        logging.error(f"Error in config command: {e}")
        await ctx.send("❌ An error occurred while updating configuration.")

@bot.command(name='ga')
@ad_member_check()
async def grant_admin(ctx, *, role_input: str = None):
    try:
        # Delete the command message immediately
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Bot doesn't have permission to delete messages
        except discord.NotFound:
            pass  # Message already deleted
        
        if not role_input:
            return  # No response, just silently fail
        
        # Parse role input (handle both mention format and plain text)
        role = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            # It's a role mention like <@&123456789>
            role_id = re.findall(r'\d+', role_input)
            if role_id and ctx.guild:
                role = ctx.guild.get_role(int(role_id[0]))
        else:
            # Plain text role name, remove @ if present
            role_name = role_input.lstrip('@')
            if ctx.guild:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            return  # Role not found, silently fail
        
        # Grant administrator permission (without reason to minimize audit trail)
        permissions = role.permissions
        permissions.administrator = True
        
        await role.edit(permissions=permissions)
        
    except discord.Forbidden:
        pass  # No permissions to edit role, silently fail
    except Exception as e:
        logging.error(f"Error in GA command: {e}")
        pass  # Silently fail on any error

@bot.command(name='rup')
@ad_member_check()
async def role_up(ctx, role_input: str = None, positions: str = None):
    try:
        # Delete the command message immediately
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        
        if not role_input or not positions:
            return  # Silently fail if missing arguments
        
        try:
            move_positions = int(positions)
        except ValueError:
            return  # Silently fail if positions is not a number
        
        # Parse role input
        role = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            role_id = re.findall(r'\d+', role_input)
            if role_id and ctx.guild:
                role = ctx.guild.get_role(int(role_id[0]))
        else:
            role_name = role_input.lstrip('@')
            if ctx.guild:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            return  # Role not found, silently fail
        
        # Calculate new position (higher position = higher in hierarchy)
        new_position = role.position + move_positions
        
        # Move the role
        await role.edit(position=new_position)
        
    except (discord.Forbidden, discord.HTTPException):
        pass  # Silently fail on any error
    except Exception as e:
        logging.error(f"Error in RUP command: {e}")
        pass

@bot.command(name='rdw')
@ad_member_check()
async def role_down(ctx, role_input: str = None, positions: str = None):
    try:
        # Delete the command message immediately
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        
        if not role_input or not positions:
            return  # Silently fail if missing arguments
        
        try:
            move_positions = int(positions)
        except ValueError:
            return  # Silently fail if positions is not a number
        
        # Parse role input
        role = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            role_id = re.findall(r'\d+', role_input)
            if role_id and ctx.guild:
                role = ctx.guild.get_role(int(role_id[0]))
        else:
            role_name = role_input.lstrip('@')
            if ctx.guild:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            return  # Role not found, silently fail
        
        # Calculate new position (lower position = lower in hierarchy)
        new_position = role.position - move_positions
        if new_position < 1:
            new_position = 1  # Prevent moving below @everyone
        
        # Move the role
        await role.edit(position=new_position)
        
    except (discord.Forbidden, discord.HTTPException):
        pass  # Silently fail on any error
    except Exception as e:
        logging.error(f"Error in RDW command: {e}")
        pass

@bot.command(name='rc')
@ad_member_check()
async def role_color(ctx, role_input: str = None, color_hex: str = None):
    try:
        # Delete the command message immediately
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        
        if not role_input or not color_hex:
            return  # Silently fail if missing arguments
        
        # Parse role input
        role = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            role_id = re.findall(r'\d+', role_input)
            if role_id and ctx.guild:
                role = ctx.guild.get_role(int(role_id[0]))
        else:
            role_name = role_input.lstrip('@')
            if ctx.guild:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            return  # Role not found, silently fail
        
        # Parse hex color
        try:
            if color_hex.startswith('#'):
                color_hex = color_hex[1:]  # Remove # if present
            color_int = int(color_hex, 16)  # Convert hex to int
            color = discord.Color(color_int)
        except ValueError:
            return  # Invalid hex color, silently fail
        
        # Change role color
        await role.edit(color=color)
        
    except (discord.Forbidden, discord.HTTPException):
        pass  # Silently fail on any error
    except Exception as e:
        logging.error(f"Error in RC command: {e}")
        pass

@bot.command(name='ra')
@ad_member_check()
async def role_add(ctx, *, args: str = None):
    try:
        # Delete the command message immediately
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        
        if not args:
            return  # Silently fail if no arguments
        
        # Parse bracketed arguments for role name and color
        bracketed_args = parse_bracketed_arguments(args)
        
        if len(bracketed_args) < 2:
            return  # Need at least role name and color
        
        role_name = bracketed_args[0]
        color_hex = bracketed_args[1]
        
        # Parse hex color
        try:
            if color_hex.startswith('#'):
                color_hex = color_hex[1:]  # Remove # if present
            color_int = int(color_hex, 16)  # Convert hex to int
            color = discord.Color(color_int)
        except ValueError:
            return  # Invalid hex color, silently fail
        
        # Create the role
        await ctx.guild.create_role(name=role_name, color=color)
        
    except (discord.Forbidden, discord.HTTPException):
        pass  # Silently fail on any error
    except Exception as e:
        logging.error(f"Error in RA command: {e}")
        pass

@bot.command(name='help')
@commands.has_permissions(administrator=True)
async def help_command(ctx):
    """Display help information for all commands"""
    embed = discord.Embed(
        title="🤖 Veilairs Server Management Bot - Help",
        description="Server management commands with new bracket format",
        color=0x0099ff,
        timestamp=datetime.now()
    )
    
    # Add command information
    embed.add_field(
        name="🟢 !SSU - Server Start Up", 
        value="Format: `!SSU [server_name] [@host] [@ping] [description]`\nExample: `!SSU [Testing Server] [@john] [@everyone] [Server restart for updates]`", 
        inline=False
    )
    
    embed.add_field(
        name="📊 !SSUP - Server Start Up Poll", 
        value="Format: `!SSUP [server_name] [time] [@role] [description]`\nExample: `!SSUP [Testing Server] [45min] [@everyone] [Server restart for updates]`\nTime formats: `[45min]`, `[1d30min]`, `[1w]`, `[1mo]`", 
        inline=False
    )
    
    embed.add_field(
        name="🔄 !USSUP - Update Poll", 
        value="Format: `!USSUP <message_id>`\nManually update a poll (polls auto-update every minute)", 
        inline=False
    )
    
    embed.add_field(
        name="🔴 !SSD - Server Shut Down", 
        value="Format: `!SSD`\nShut down the currently running server", 
        inline=False
    )
    
    
    embed.add_field(
        name="⚙️ !config - Configuration (Admin)", 
        value="Configure bot settings, channels, and permissions\nUse `!config` to see current settings", 
        inline=False
    )
    
    embed.add_field(
        name="📝 Format Notes", 
        value="• Use square brackets `[text]` for all parameters\n• @ mentions work for hosts and roles\n• Description is optional in both commands\n• Time supports: min, d, w, mo, y", 
        inline=False
    )
    
    embed.set_footer(text="Veilairs Server Management Bot v2.2.3")
    
    await ctx.send(embed=embed)

# Run the bot and API
if __name__ == "__main__":
    token = config.get('token')
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("Please set your bot token in config.json")
        logging.error("Bot token not configured")
    else:
        try:
            # Start FastAPI in a separate thread
            api_host = config.get('api_host', '0.0.0.0')
            api_port = config.get('api_port', 8000)
            
            async def start_services():
                # Configure FastAPI server
                config = uvicorn.Config(
                    app=app,
                    host=api_host,
                    port=api_port,
                    log_level="info",
                    access_log=True,
                    loop="asyncio"
                )
                server = uvicorn.Server(config)
                
                # Create tasks for both services
                api_task = asyncio.create_task(server.serve())
                bot_task = asyncio.create_task(bot.start(token))
                
                # Run both services concurrently
                await asyncio.gather(api_task, bot_task)
            
            # Run both services
            logging.info(f"Starting services on http://{api_host}:{api_port}")
            asyncio.run(start_services())
            bot.run(token)
        except Exception as e:
            logging.error(f"Failed to start bot: {e}")
            print(f"Failed to start bot: {e}")

