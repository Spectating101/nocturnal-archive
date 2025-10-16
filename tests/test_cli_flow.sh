#!/bin/bash
# Test the CLI setup flow with auto-registration

# Generate unique test email
TEST_EMAIL="cli_test_$(date +%s)@example.com"
TEST_PASSWORD="CliTest123!"

echo "============================================================"
echo "🧪 Testing Cite-Agent CLI Setup Flow"
echo "============================================================"
echo ""
echo "📧 Test email: $TEST_EMAIL"
echo "🔐 Test password: $TEST_PASSWORD"
echo ""

# Remove any existing config
rm -rf ~/.nocturnal_archive/ ~/.cite_agent/

echo "🔄 Running cite-agent --setup with auto-registration..."
echo ""

# Run setup (this should auto-register if user doesn't exist)
echo -e "$TEST_EMAIL\n$TEST_PASSWORD" | cite-agent --setup

echo ""
echo "============================================================"
echo "✅ Setup completed!"
echo "============================================================"
