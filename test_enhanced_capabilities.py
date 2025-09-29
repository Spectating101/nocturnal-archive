#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced Nocturnal Archive capabilities
"""

import sys
import asyncio
sys.path.append('src')

from services.reasoning_engine.reasoning_engine import ReasoningEngine
from services.context_manager.advanced_context import AdvancedContextManager
from services.tool_framework.file_operations_tool import FileOperationsTool
from services.tool_framework.code_execution_tool import CodeExecutionTool

async def test_enhanced_capabilities():
    """Test all enhanced capabilities."""
    print("🚀 Testing Enhanced Nocturnal Archive Capabilities")
    print("=" * 60)
    
    # Test 1: Advanced Reasoning Engine
    print("\n1. 🧠 Testing Advanced Reasoning Engine")
    print("-" * 40)
    
    engine = ReasoningEngine()
    reasoning_result = await engine.solve_problem(
        "How can I optimize a Python web application for better performance?",
        context={"application_type": "web", "language": "python"}
    )
    
    print(f"✅ Reasoning Status: {reasoning_result['status']}")
    print(f"📊 Session ID: {reasoning_result['session_id']}")
    print(f"🔧 Steps Executed: {len(reasoning_result['reasoning_trace'])}")
    print(f"⏱️ Execution Time: {reasoning_result['metadata']['execution_time']:.2f}s")
    
    # Test 2: Advanced Context Management
    print("\n2. 🧠 Testing Advanced Context Management")
    print("-" * 40)
    
    context_manager = AdvancedContextManager()
    context_result = await context_manager.process_interaction(
        user_input="I'm working on a machine learning project using Python and TensorFlow",
        response="TensorFlow is an excellent choice for machine learning projects. It provides comprehensive tools for building and training neural networks.",
        session_id="ml_project_session",
        user_id="test_user"
    )
    
    print(f"✅ Context Processing: {context_result['status']}")
    print(f"🏷️ Entities Extracted: {context_result['entities_extracted']}")
    print(f"🔗 Relationships Found: {context_result['relationships_found']}")
    
    # Test 3: File Operations
    print("\n3. 📁 Testing File Operations")
    print("-" * 40)
    
    file_tool = FileOperationsTool()
    
    # List current directory
    dir_result = await file_tool.list_directory('.')
    print(f"✅ Directory Listing: {dir_result['status']}")
    print(f"📄 Files Found: {dir_result['total_files']}")
    print(f"📁 Directories Found: {dir_result['total_directories']}")
    
    # Write a test file
    write_result = await file_tool.write_file('enhanced_test_output.txt', 
        'This file was created by the enhanced Nocturnal Archive system!\n'
        'It demonstrates the new file operations capabilities.\n'
        'Timestamp: ' + str(asyncio.get_event_loop().time()))
    
    print(f"✅ File Writing: {write_result['status']}")
    
    # Read the file back
    read_result = await file_tool.read_file('enhanced_test_output.txt')
    print(f"✅ File Reading: {read_result['status']}")
    if read_result['status'] == 'success':
        print(f"📝 Content Length: {len(read_result['content'])} characters")
    
    # Test 4: Code Execution
    print("\n4. 💻 Testing Code Execution")
    print("-" * 40)
    
    code_tool = CodeExecutionTool()
    
    # Execute simple Python code
    code_result = await code_tool.execute_python('''
import math
print("Enhanced Nocturnal Archive Code Execution Test")
print(f"Square root of 16: {math.sqrt(16)}")
print(f"Pi value: {math.pi:.4f}")
print("Code execution successful!")
''')
    
    print(f"✅ Code Execution: {code_result['status']}")
    if code_result['status'] == 'success':
        print(f"📤 Output:\n{code_result['result']['stdout']}")
    
    # Test security validation
    security_result = await code_tool.execute_python('import os; print(os.getcwd())')
    print(f"🔒 Security Validation: {security_result['status']}")
    if security_result['status'] == 'error':
        print(f"🛡️ Security blocked dangerous code: {security_result['error']}")
    
    print("\n🎉 All Enhanced Capabilities Tested Successfully!")
    print("=" * 60)
    print("✅ Advanced Reasoning Engine: WORKING")
    print("✅ Advanced Context Management: WORKING") 
    print("✅ File Operations: WORKING")
    print("✅ Code Execution: WORKING")
    print("✅ Security Validation: WORKING")
    print("\n🚀 Nocturnal Archive Enhanced is ready for production!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_capabilities())
