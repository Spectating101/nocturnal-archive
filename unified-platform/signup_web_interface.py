#!/usr/bin/env python3
"""
Web-based signup interface for R/SQL Assistant
Provides a user-friendly way to register and manage accounts
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from user_signup_manager import SignupManager

app = Flask(__name__)
manager = SignupManager()

# HTML template for the signup interface
SIGNUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>R/SQL Assistant - Sign Up</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .step {
            margin: 20px 0;
            padding: 20px;
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }
        .step h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .form-group {
            margin: 15px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #34495e;
        }
        input[type="email"], input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        button:hover {
            background-color: #2980b9;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .code-block {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
            overflow-x: auto;
        }
        .stats {
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .stats h3 {
            margin-top: 0;
            color: #27ae60;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 R/SQL Assistant - Beta Signup</h1>
        
        {% if message %}
            <div class="{{ message_type }}">{{ message }}</div>
        {% endif %}
        
        <div class="stats">
            <h3>📊 Beta Program Stats</h3>
            <p><strong>Total Users:</strong> {{ stats.total_users }}</p>
            <p><strong>Active Users:</strong> {{ stats.active_users }}</p>
            <p><strong>Completion Rate:</strong> {{ "%.1f"|format(stats.completion_rate) }}%</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Register Your Email</h3>
            <p>Enter your email address to get started with the R/SQL Assistant beta program.</p>
            
            <form method="POST" action="/register">
                <div class="form-group">
                    <label for="email">Email Address:</label>
                    <input type="email" id="email" name="email" required 
                           placeholder="your.email@university.edu">
                </div>
                <button type="submit">Register for Beta</button>
            </form>
        </div>
        
        {% if user_id %}
        <div class="step">
            <h3>Step 2: Create Groq Account</h3>
            <p>Now you need to create a free Groq account to get your API key.</p>
            
            <div class="code-block">
                <strong>Your User ID:</strong> {{ user_id }}<br>
                <strong>Your Email:</strong> {{ email }}
            </div>
            
            <ol>
                <li>Go to <a href="https://console.groq.com/keys" target="_blank">https://console.groq.com/keys</a></li>
                <li>Click "Sign Up" and use your email: <strong>{{ email }}</strong></li>
                <li>Complete email verification</li>
                <li>Log in and go to "API Keys"</li>
                <li>Click "Create API Key" and copy it</li>
            </ol>
        </div>
        
        <div class="step">
            <h3>Step 3: Activate Your Account</h3>
            <p>Enter your Groq API key to activate your account.</p>
            
            <form method="POST" action="/activate">
                <input type="hidden" name="user_id" value="{{ user_id }}">
                <div class="form-group">
                    <label for="api_key">Groq API Key:</label>
                    <input type="text" id="api_key" name="api_key" required 
                           placeholder="gsk_your_api_key_here">
                </div>
                <button type="submit">Activate Account</button>
            </form>
        </div>
        {% endif %}
        
        <div class="step">
            <h3>Step 4: Download and Install</h3>
            <p>Once your account is activated, download and install the R/SQL Assistant.</p>
            
            <div class="code-block">
# Download the assistant
git clone https://github.com/yourusername/r-sql-assistant.git
cd r-sql-assistant

# Run setup
./setup_rstudio_server.sh

# Start using
./run_rstudio_assistant.sh
            </div>
        </div>
        
        <div class="step">
            <h3>Need Help?</h3>
            <p>If you have any questions or need assistance:</p>
            <ul>
                <li>Check the <a href="/docs">documentation</a></li>
                <li>Contact support at: support@yourdomain.com</li>
                <li>Join our Discord community</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main signup page"""
    stats = manager.get_signup_stats()
    return render_template_string(SIGNUP_TEMPLATE, stats=stats)

@app.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    email = request.form.get('email')
    
    if not email:
        return render_template_string(SIGNUP_TEMPLATE, 
                                    message="Email is required", 
                                    message_type="error")
    
    try:
        user_id = manager.register_user(email)
        stats = manager.get_signup_stats()
        
        return render_template_string(SIGNUP_TEMPLATE, 
                                    user_id=user_id, 
                                    email=email, 
                                    stats=stats,
                                    message="Registration successful! Follow the steps below.", 
                                    message_type="success")
    except Exception as e:
        return render_template_string(SIGNUP_TEMPLATE, 
                                    message=f"Registration failed: {str(e)}", 
                                    message_type="error")

@app.route('/activate', methods=['POST'])
def activate():
    """Handle account activation"""
    user_id = request.form.get('user_id')
    api_key = request.form.get('api_key')
    
    if not user_id or not api_key:
        return render_template_string(SIGNUP_TEMPLATE, 
                                    message="User ID and API key are required", 
                                    message_type="error")
    
    try:
        if manager.add_api_key(user_id, api_key):
            stats = manager.get_signup_stats()
            return render_template_string(SIGNUP_TEMPLATE, 
                                        stats=stats,
                                        message="Account activated successfully! You can now use the R/SQL Assistant.", 
                                        message_type="success")
        else:
            return render_template_string(SIGNUP_TEMPLATE, 
                                        message="Failed to activate account. Please check your API key.", 
                                        message_type="error")
    except Exception as e:
        return render_template_string(SIGNUP_TEMPLATE, 
                                    message=f"Activation failed: {str(e)}", 
                                    message_type="error")

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    return jsonify(manager.get_signup_stats())

@app.route('/api/user/<user_id>')
def api_user_status(user_id):
    """API endpoint for user status"""
    status = manager.get_user_status(user_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    print("🌐 Starting R/SQL Assistant Signup Interface")
    print("📊 Access at: http://localhost:5000")
    print("📋 API endpoints:")
    print("  - GET /api/stats - Get signup statistics")
    print("  - GET /api/user/<user_id> - Get user status")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
