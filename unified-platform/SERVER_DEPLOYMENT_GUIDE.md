# R/SQL Assistant Server Deployment Guide

## Overview

This guide helps you deploy the R/SQL Assistant with server-based API key rotation for beta testing with 50-100 users.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client 1      │    │                  │    │   Groq API      │
│   Client 2      │───▶│  Server with     │───▶│   Key 1         │
│   Client 3      │    │  API Key         │    │   Key 2         │
│   ...           │    │  Rotation        │    │   Key 3         │
│   Client 100    │    │                  │    │   Key 4         │
└─────────────────┘    └──────────────────┘    │   Key 5         │
                                               └─────────────────┘
```

## Beta Testing Recommendations

### **Recommended Setup:**
- **Beta Users:** 75 users
- **API Keys:** 2-3 Groq API keys (FREE TIER!)
- **Server:** Single server instance
- **Load Balancing:** Round-robin with health checks

### **API Key Requirements:**

| Component | Count | Purpose |
|-----------|-------|---------|
| Primary Key | 1 | Handle all load (576 user capacity) |
| Backup Key | 1 | Failover and redundancy |
| **Total** | **2** | **More than enough!** |

### **Capacity Planning:**

| Metric | Per User | 75 Users | Free Tier Capacity |
|--------|----------|----------|-------------------|
| Requests/day | 25 | 1,875 | 14,400 per key |
| Requests/min | 0.5 | 37.5 | 30 per key |
| **Safety Margin** | | | **576 users per key!** |

## Server Deployment

### 1. Prerequisites

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip curl

# CentOS/RHEL
sudo yum install python3 python3-pip curl
```

### 2. Get API Keys

1. Visit [Groq Console](https://console.groq.com/keys)
2. Create 5 API keys
3. Note: Free tier gives 14,400 requests/day per key

### 3. Configure Environment

```bash
# Copy example configuration
cp env_example.txt .env

# Edit with your API keys
nano .env
```

**Required .env configuration:**
```bash
# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=1

# API Keys (2 keys are more than enough for 75 users!)
# Each free tier key can handle 576 users
GROQ_API_KEY_1=gsk_your_first_key_here
GROQ_API_KEY_2=gsk_your_second_key_here
```

### 4. Deploy Server

```bash
# Run deployment script
./deploy_server.sh
```

The script will:
- Create virtual environment
- Install dependencies
- Create systemd service
- Start the server
- Enable auto-start on boot

### 5. Verify Deployment

```bash
# Check server status
curl http://localhost:8000/

# Check API key status
curl http://localhost:8000/status

# View logs
sudo journalctl -u r-sql-assistant -f
```

## Client Setup

### For Beta Users

Users no longer need individual API keys! They just need to connect to your server.

```bash
# Run client setup
./setup_client.sh
```

The script will:
- Install client dependencies
- Configure server URL
- Create launcher script
- Set up desktop entry

### Client Configuration

Users can set their server URL:
```bash
# In their .env file
ASSISTANT_SERVER_URL=http://your-server-ip:8000
USER_ID=their_user_id
```

## Monitoring & Management

### Health Checks

```bash
# Server health
curl http://localhost:8000/status

# Usage statistics
curl http://localhost:8000/stats

# API key health
curl -X POST http://localhost:8000/admin/health-check
```

### Daily Management

```bash
# Reset daily limits (run daily at midnight)
curl -X POST http://localhost:8000/admin/reset-daily-limits

# View server logs
sudo journalctl -u r-sql-assistant --since "1 hour ago"

# Restart server
sudo systemctl restart r-sql-assistant
```

### Monitoring Dashboard

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor.sh - Simple monitoring script

echo "=== R/SQL Assistant Server Status ==="
echo "Time: $(date)"
echo ""

# Server health
echo "Server Status:"
curl -s http://localhost:8000/status | jq '.server_status'

# API Key Status
echo ""
echo "API Key Status:"
curl -s http://localhost:8000/status | jq '.api_keys[] | {key_id, requests_today, is_healthy}'

# Usage Stats
echo ""
echo "Usage Statistics:"
curl -s http://localhost:8000/stats | jq '.request_stats'
```

## Scaling for Production

### For 100+ Users

1. **Add More API Keys (Still Free!):**
   ```bash
   # Add to .env - each key handles 576 users
   GROQ_API_KEY_3=gsk_your_third_key
   GROQ_API_KEY_4=gsk_your_fourth_key
   ```

2. **Increase Server Workers:**
   ```bash
   # In .env
   SERVER_WORKERS=2
   ```

3. **Load Balancer (Optional):**
   - Use nginx or HAProxy
   - Multiple server instances
   - Database for session management

### For 500+ Users

1. **Database Integration:**
   - Store user sessions
   - Track usage patterns
   - Implement rate limiting per user

2. **Caching:**
   - Redis for response caching
   - Reduce API calls for common questions

3. **Multiple Servers:**
   - Deploy on multiple machines
   - Load balancer distribution
   - Geographic distribution

## Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check logs
sudo journalctl -u r-sql-assistant

# Check API keys
grep GROQ_API_KEY .env

# Test manually
source server_venv/bin/activate
python server.py
```

**API key errors:**
```bash
# Check key health
curl http://localhost:8000/status

# Reset unhealthy keys
curl -X POST http://localhost:8000/admin/health-check
```

**Client connection issues:**
```bash
# Test server connectivity
curl http://your-server-ip:8000/

# Check firewall
sudo ufw status
sudo ufw allow 8000
```

### Performance Tuning

**For high load:**
```bash
# Increase workers
SERVER_WORKERS=4

# Adjust rate limits
GROQ_API_KEY_1_RATE_LIMIT=60

# Monitor system resources
htop
iostat -x 1
```

## Security Considerations

1. **API Key Protection:**
   - Store keys in environment variables
   - Use secrets management in production
   - Rotate keys regularly

2. **Network Security:**
   - Use HTTPS in production
   - Implement authentication
   - Rate limit per IP/user

3. **Monitoring:**
   - Log all requests
   - Monitor for abuse
   - Set up alerts

## Cost Estimation

### Groq API Costs (75 beta users)

| Tier | Requests/Day | Cost/Month | Notes |
|------|--------------|------------|-------|
| **Free** | **14,400/key** | **$0** | **2 keys = 28,800 requests/day** |
| **Free** | **14,400/key** | **$0** | **Can handle 1,152 users!** |

### Server Costs

| Provider | Instance | Cost/Month | Notes |
|----------|----------|------------|-------|
| DigitalOcean | $10 droplet | $10 | Sufficient for 75 users |
| AWS | t3.micro | $8.50 | Free tier eligible |
| Google Cloud | e2-micro | $6.50 | Free tier eligible |

**Total estimated cost: $10-20/month for server hosting (API calls are FREE!)**

## Next Steps

1. **Deploy server** using this guide
2. **Test with small group** (5-10 users)
3. **Monitor performance** and adjust
4. **Scale up** to full beta (75 users)
5. **Gather feedback** and iterate
6. **Plan production** deployment

## Support

For issues or questions:
- Check server logs: `sudo journalctl -u r-sql-assistant`
- Monitor API usage: `curl http://localhost:8000/stats`
- Test connectivity: `curl http://localhost:8000/status`
