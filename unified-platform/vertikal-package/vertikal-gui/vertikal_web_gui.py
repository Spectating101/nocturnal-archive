#!/usr/bin/env python3
"""
Vertikal Web GUI - Browser-based interface for the terminal assistant
"""

import os
import sys
import subprocess
import threading
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class VertikalWebGUI:
    def __init__(self, port=8080):
        self.port = port
        self.project_root = Path.cwd()
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.process = None
        self.output_buffer = []
        self.server = None
        
    def start_server(self):
        """Start the web server"""
        handler = self.create_handler()
        self.server = HTTPServer(('localhost', self.port), handler)
        
        print(f"🌐 Starting Vertikal Web GUI on http://localhost:{self.port}")
        print("📱 Open your browser and go to the URL above")
        
        # Open browser automatically
        webbrowser.open(f'http://localhost:{self.port}')
        
        # Start server in thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server_thread
    
    def create_handler(self):
        """Create HTTP request handler"""
        gui = self
        
        class VertikalHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.serve_main_page()
                elif self.path == '/api/status':
                    self.serve_status()
                elif self.path == '/api/output':
                    self.serve_output()
                else:
                    self.send_error(404)
            
            def do_POST(self):
                if self.path == '/api/setup':
                    self.handle_setup()
                elif self.path == '/api/start':
                    self.handle_start()
                elif self.path == '/api/stop':
                    self.handle_stop()
                elif self.path == '/api/message':
                    self.handle_message()
                else:
                    self.send_error(404)
            
            def serve_main_page(self):
                """Serve the main HTML page"""
                html = gui.get_main_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())
            
            def serve_status(self):
                """Serve status information"""
                status = gui.get_status()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
            
            def serve_output(self):
                """Serve output buffer"""
                output = gui.get_output()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(output).encode())
            
            def handle_setup(self):
                """Handle setup requests"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                gui.api_key = data.get('api_key', '')
                gui.project_root = Path(data.get('project_root', '.'))
                
                # Set environment variable
                os.environ['GROQ_API_KEY'] = gui.api_key
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            
            def handle_start(self):
                """Handle start requests"""
                gui.start_assistant()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'started'}).encode())
            
            def handle_stop(self):
                """Handle stop requests"""
                gui.stop_assistant()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'stopped'}).encode())
            
            def handle_message(self):
                """Handle message requests"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                message = data.get('message', '')
                gui.send_message(message)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'sent'}).encode())
        
        return VertikalHandler
    
    def get_main_html(self):
        """Get the main HTML page"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vertikal Assistant</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 20px;
        }}
        .setup-section {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .setup-section h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .form-group {{
            margin-bottom: 15px;
        }}
        .form-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .form-group input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }}
        .btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }}
        .btn:hover {{
            background: #0056b3;
        }}
        .btn-success {{
            background: #28a745;
        }}
        .btn-success:hover {{
            background: #1e7e34;
        }}
        .btn-danger {{
            background: #dc3545;
        }}
        .btn-danger:hover {{
            background: #c82333;
        }}
        .status-section {{
            background: #e9ecef;
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .output-section {{
            border: 1px solid #ced4da;
            border-radius: 5px;
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: #2c3e50;
            color: #ecf0f1;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        .input-section {{
            display: flex;
            gap: 10px;
        }}
        .input-section input {{
            flex: 1;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }}
        .status-online {{ background: #28a745; }}
        .status-offline {{ background: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Vertikal Assistant</h1>
            <p>File-aware ChatGPT for RStudio and Data Analysis</p>
        </div>
        
        <div class="content">
            <div class="setup-section">
                <h3>Setup</h3>
                <div class="form-group">
                    <label for="apiKey">Groq API Key:</label>
                    <input type="password" id="apiKey" placeholder="Enter your Groq API key" value="{self.api_key}">
                    <button class="btn" onclick="window.open('https://console.groq.com/', '_blank')">Get Free Key</button>
                </div>
                <div class="form-group">
                    <label for="projectRoot">Project Directory:</label>
                    <input type="text" id="projectRoot" placeholder="Enter project directory path" value="{self.project_root}">
                </div>
                <button class="btn" onclick="saveSetup()">Save Setup</button>
                <button class="btn" onclick="testSetup()">Test Setup</button>
            </div>
            
            <div class="status-section">
                <h3>Status <span id="statusIndicator" class="status-indicator status-offline"></span></h3>
                <div id="statusText">Ready to start</div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <button class="btn btn-success" onclick="startAssistant()">🚀 Start Assistant</button>
                <button class="btn btn-danger" onclick="stopAssistant()">⏹️ Stop Assistant</button>
            </div>
            
            <div class="output-section" id="output">
                <div>🤖 Vertikal Assistant Web GUI</div>
                <div>📁 Project: {self.project_root}</div>
                <div>💡 Enter your API key and click "Start Assistant" to begin!</div>
                <div></div>
            </div>
            
            <div class="input-section">
                <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                <button class="btn" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        function saveSetup() {{
            const apiKey = document.getElementById('apiKey').value;
            const projectRoot = document.getElementById('projectRoot').value;
            
            fetch('/api/setup', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ api_key: apiKey, project_root: projectRoot }})
            }})
            .then(response => response.json())
            .then(data => {{
                updateStatus('Setup saved successfully');
            }})
            .catch(error => {{
                updateStatus('Setup failed: ' + error);
            }});
        }}
        
        function testSetup() {{
            updateStatus('Testing setup...');
            // Add test logic here
            updateStatus('Setup test completed');
        }}
        
        function startAssistant() {{
            fetch('/api/start', {{ method: 'POST' }})
            .then(response => response.json())
            .then(data => {{
                isRunning = true;
                updateStatus('Assistant started');
                updateStatusIndicator(true);
                startOutputPolling();
            }})
            .catch(error => {{
                updateStatus('Failed to start: ' + error);
            }});
        }}
        
        function stopAssistant() {{
            fetch('/api/stop', {{ method: 'POST' }})
            .then(response => response.json())
            .then(data => {{
                isRunning = false;
                updateStatus('Assistant stopped');
                updateStatusIndicator(false);
            }})
            .catch(error => {{
                updateStatus('Failed to stop: ' + error);
            }});
        }}
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addOutput('👤 You: ' + message);
            input.value = '';
            
            fetch('/api/message', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ message: message }})
            }})
            .then(response => response.json())
            .then(data => {{
                // Message sent
            }})
            .catch(error => {{
                addOutput('❌ Error sending message: ' + error);
            }});
        }}
        
        function handleKeyPress(event) {{
            if (event.key === 'Enter') {{
                sendMessage();
            }}
        }}
        
        function updateStatus(message) {{
            const statusText = document.getElementById('statusText');
            statusText.textContent = message;
        }}
        
        function updateStatusIndicator(online) {{
            const indicator = document.getElementById('statusIndicator');
            indicator.className = 'status-indicator ' + (online ? 'status-online' : 'status-offline');
        }}
        
        function addOutput(text) {{
            const output = document.getElementById('output');
            const div = document.createElement('div');
            div.textContent = text;
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }}
        
        function startOutputPolling() {{
            if (!isRunning) return;
            
            fetch('/api/output')
            .then(response => response.json())
            .then(data => {{
                if (data.output) {{
                    addOutput(data.output);
                }}
                setTimeout(startOutputPolling, 1000);
            }})
            .catch(error => {{
                setTimeout(startOutputPolling, 1000);
            }});
        }}
        
        // Initial status check
        fetch('/api/status')
        .then(response => response.json())
        .then(data => {{
            updateStatus(data.status || 'Ready');
        }});
    </script>
</body>
</html>
        """
    
    def get_status(self):
        """Get current status"""
        return {
            'status': 'Ready' if not self.process else 'Running',
            'api_key_set': bool(self.api_key),
            'project_root': str(self.project_root)
        }
    
    def get_output(self):
        """Get output buffer"""
        if self.output_buffer:
            output = '\n'.join(self.output_buffer)
            self.output_buffer.clear()
            return {'output': output}
        return {'output': ''}
    
    def start_assistant(self):
        """Start the vertikal assistant"""
        if self.process:
            return
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Start vertikal process
            self.process = subprocess.Popen(
                ['vertikal', '--project-root', '.'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start output reader thread
            output_thread = threading.Thread(target=self.read_output)
            output_thread.daemon = True
            output_thread.start()
            
        except Exception as e:
            self.output_buffer.append(f"❌ Error starting assistant: {e}")
    
    def read_output(self):
        """Read output from assistant process"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_buffer.append(line.rstrip())
        except Exception as e:
            self.output_buffer.append(f"❌ Error reading output: {e}")
    
    def stop_assistant(self):
        """Stop the assistant"""
        if self.process:
            self.process.terminate()
            self.process = None
            self.output_buffer.append("⏹️ Assistant stopped")
    
    def send_message(self, message):
        """Send message to assistant"""
        if not self.process:
            return
        
        try:
            self.process.stdin.write(message + '\n')
            self.process.stdin.flush()
            self.output_buffer.append(f"👤 You: {message}")
        except Exception as e:
            self.output_buffer.append(f"❌ Error sending message: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vertikal Web GUI")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    args = parser.parse_args()
    
    gui = VertikalWebGUI(port=args.port)
    
    try:
        server_thread = gui.start_server()
        print("🌐 Web GUI is running!")
        print("📱 Open your browser and go to the URL above")
        print("⏹️ Press Ctrl+C to stop")
        
        # Keep main thread alive
        server_thread.join()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        if gui.server:
            gui.server.shutdown()

if __name__ == "__main__":
    main()
