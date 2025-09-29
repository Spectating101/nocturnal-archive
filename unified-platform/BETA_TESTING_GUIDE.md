# R/SQL Assistant Beta Testing Guide

## Quick Start for Beta Testing

### For Administrators (You)

#### 1. Deploy the Server
```bash
# Get 5 Groq API keys from https://console.groq.com/keys
# Configure them in .env file
cp env_example.txt .env
nano .env

# Deploy server
./deploy_server.sh
```

#### 2. Monitor the System
```bash
# Check server status
./monitor.sh

# View real-time logs
sudo journalctl -u r-sql-assistant -f
```

### For Beta Users

#### 1. Install Client
```bash
# Download the client setup script
# Run setup (no API keys needed!)
./setup_client.sh
```

#### 2. Start Using
```bash
# Launch the assistant
./run_assistant.sh

# Or find "R/SQL Assistant Client" in your app launcher
```

## Beta Testing Plan

### Phase 1: Soft Launch (Week 1)
- **Users:** 10-15 power users
- **Goal:** Test server stability and basic functionality
- **Duration:** 1 week

### Phase 2: Expanded Beta (Week 2-3)
- **Users:** 30-50 users
- **Goal:** Test load balancing and API key rotation
- **Duration:** 2 weeks

### Phase 3: Full Beta (Week 4-6)
- **Users:** 75 users
- **Goal:** Full system testing and feedback collection
- **Duration:** 3 weeks

## Monitoring Checklist

### Daily Checks
- [ ] Server is running: `sudo systemctl status r-sql-assistant`
- [ ] API keys are healthy: `./monitor.sh`
- [ ] No error spikes in logs: `sudo journalctl -u r-sql-assistant --since "1 day ago"`
- [ ] Usage within limits: Check `/stats` endpoint

### Weekly Checks
- [ ] Reset daily limits: `curl -X POST http://localhost:8000/admin/reset-daily-limits`
- [ ] Review usage patterns: Analyze `/stats` data
- [ ] Check for API key rotation issues
- [ ] Review user feedback

## Expected Performance

### For 75 Beta Users
- **Requests per day:** ~1,875 (25 per user average)
- **Peak requests per minute:** ~40
- **API key utilization:** ~13% of daily limits
- **Response time:** <2 seconds average

### Scaling Triggers
- **Add more API keys** if daily usage >80% of limits
- **Increase server workers** if response time >5 seconds
- **Implement caching** if same questions repeated frequently

## User Feedback Collection

### Feedback Channels
1. **In-app feedback:** Add feedback command to client
2. **Email surveys:** Weekly feedback requests
3. **Usage analytics:** Track popular questions and patterns
4. **Support tickets:** Monitor error reports

### Key Metrics to Track
- User satisfaction scores
- Most common questions/use cases
- Performance issues
- Feature requests
- Error rates

## Troubleshooting Common Issues

### Server Issues
```bash
# Server won't start
sudo systemctl restart r-sql-assistant
sudo journalctl -u r-sql-assistant --since "10 minutes ago"

# API key errors
curl http://localhost:8000/status
# Check for unhealthy keys and reset if needed
```

### Client Issues
```bash
# Connection problems
curl http://your-server-ip:8000/
# Check if server is accessible from client

# Slow responses
./monitor.sh
# Check server load and API key health
```

## Success Criteria

### Technical Success
- [ ] 99%+ uptime during beta
- [ ] <3 second average response time
- [ ] No API key exhaustion
- [ ] Successful load balancing

### User Success
- [ ] 80%+ user satisfaction
- [ ] <5% error rate
- [ ] Positive feedback on ease of use
- [ ] Requests for production deployment

## Post-Beta Planning

### Based on Results
1. **If successful:** Plan production deployment
2. **If issues found:** Address and re-test
3. **If scaling needed:** Implement additional infrastructure

### Production Readiness
- [ ] Security hardening
- [ ] HTTPS implementation
- [ ] User authentication
- [ ] Advanced monitoring
- [ ] Backup and disaster recovery

## Contact Information

### For Beta Users
- **Support:** [Your support email]
- **Documentation:** This guide and server deployment guide
- **Status Page:** [Your status page URL]

### For Administrators
- **Monitoring:** `./monitor.sh`
- **Logs:** `sudo journalctl -u r-sql-assistant`
- **Emergency:** Server restart procedures in deployment guide
