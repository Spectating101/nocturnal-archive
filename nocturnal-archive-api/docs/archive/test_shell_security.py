#!/usr/bin/env python3
"""
Comprehensive shell security test matrix
Tests command validation with edge cases and malicious patterns
"""

import sys
sys.path.append('src')
from src.services.secure_shell import SecureShell

def test_shell_security():
    """Test shell command validation with comprehensive test cases"""
    shell = SecureShell()
    
    # Test cases: (command, should_be_allowed, description)
    test_cases = [
        # Safe commands
        ("ls", True, "Basic directory listing"),
        ("pwd", True, "Print working directory"),
        ("cat file.txt", True, "Read file"),
        ("git status", True, "Git status"),
        ("python --version", True, "Python version check"),
        ("R --version", True, "R version check"),
        ("at 5pm", True, "Schedule command"),
        ("echo 'hello'", True, "Echo command"),
        ("head -n 10 file.txt", True, "Head command with args"),
        ("grep 'pattern' file.txt", True, "Grep with args"),
        
        # Dangerous commands - should be blocked
        ("rm -rf /", False, "Delete everything"),
        ("rm -r /", False, "Delete recursively"),
        ("sudo su", False, "Switch to root"),
        ("sudo rm -rf /", False, "Sudo delete"),
        ("chmod 777 /", False, "Make everything writable"),
        ("chown root /", False, "Change ownership"),
        ("dd if=/dev/zero of=/dev/sda", False, "Destroy disk"),
        ("mkfs.ext4 /dev/sda", False, "Format disk"),
        ("mount /dev/sda /mnt", False, "Mount filesystem"),
        ("umount /", False, "Unmount root"),
        ("reboot", False, "Reboot system"),
        ("shutdown -h now", False, "Shutdown system"),
        ("halt", False, "Halt system"),
        ("poweroff", False, "Power off"),
        ("init 0", False, "Init level 0"),
        ("init 6", False, "Init level 6"),
        ("kill -9 1", False, "Kill init process"),
        ("killall -9 init", False, "Kill all init"),
        ("pkill -9 init", False, "Kill processes"),
        ("xkill", False, "X kill"),
        
        # Network commands - should be blocked
        ("curl http://example.com", False, "HTTP request"),
        ("wget http://example.com", False, "Download file"),
        ("ssh user@host", False, "SSH connection"),
        ("scp file user@host:", False, "SCP transfer"),
        ("rsync -av / user@host:/", False, "Rsync everything"),
        ("nc -l 8080", False, "Netcat listener"),
        ("netcat -l 8080", False, "Netcat listener alt"),
        ("telnet host 80", False, "Telnet connection"),
        ("ftp host", False, "FTP connection"),
        ("sftp user@host", False, "SFTP connection"),
        
        # Code execution - should be blocked
        ("python -c \"import os; os.system('rm -rf /')\"", False, "Python code execution"),
        ("perl -e \"system('rm -rf /')\"", False, "Perl code execution"),
        ("ruby -e \"system('rm -rf /')\"", False, "Ruby code execution"),
        ("node -e \"require('child_process').exec('rm -rf /')\"", False, "Node.js code execution"),
        ("bash -c \"rm -rf /\"", False, "Bash code execution"),
        ("sh -c \"rm -rf /\"", False, "Shell code execution"),
        ("zsh -c \"rm -rf /\"", False, "Zsh code execution"),
        ("fish -c \"rm -rf /\"", False, "Fish code execution"),
        ("tcsh -c \"rm -rf /\"", False, "Tcsh code execution"),
        ("csh -c \"rm -rf /\"", False, "Csh code execution"),
        
        # System services - should be blocked
        ("service apache2 restart", False, "Service restart"),
        ("systemctl restart apache2", False, "Systemctl restart"),
        ("systemd-analyze", False, "Systemd analyze"),
        ("crontab -e", False, "Edit crontab"),
        ("crontab -l", False, "List crontab"),
        ("at 5pm < script.sh", False, "Schedule script"),
        ("batch < script.sh", False, "Batch job"),
        ("nohup command &", False, "Background job"),
        ("screen -S session", False, "Screen session"),
        ("tmux new-session", False, "Tmux session"),
        
        # Unicode and encoding tricks - should be blocked
        ("rm -rf /tmp/\u0000", False, "Unicode null byte"),
        ("rm -rf /tmp/\u200b", False, "Zero-width space"),
        ("rm -rf /tmp/\u202e", False, "Right-to-left override"),
        ("rm -rf /tmp/\u202d", False, "Left-to-right override"),
        
        # Semicolon and command chaining - should be blocked
        ("ls; rm -rf /", False, "Semicolon chaining"),
        ("pwd && rm -rf /", False, "Logical AND"),
        ("ls || rm -rf /", False, "Logical OR"),
        ("ls | rm -rf /", False, "Pipe to dangerous command"),
        
        # Backticks and subshells - should be blocked
        ("rm -rf `echo /`", False, "Backticks subshell"),
        ("rm -rf $(echo /)", False, "Dollar subshell"),
        ("rm -rf $(echo /; echo /tmp)", False, "Complex subshell"),
        
        # Environment variable tricks - should be blocked
        ("$PATH", False, "Environment variable expansion"),
        ("${PATH}", False, "Brace expansion"),
        ("rm -rf $HOME", False, "Home directory via env"),
        ("rm -rf ${HOME}", False, "Home directory via brace"),
        
        # Background and job control - should be blocked
        ("rm -rf / &", False, "Background job"),
        ("rm -rf / &&", False, "Background with AND"),
        ("rm -rf / ||", False, "Background with OR"),
        ("rm -rf / ;", False, "Background with semicolon"),
        
        # Redirects and file operations - should be blocked
        ("rm -rf / > /dev/null", False, "Redirect to null"),
        ("rm -rf / 2> /dev/null", False, "Redirect stderr"),
        ("rm -rf / &> /dev/null", False, "Redirect both"),
        ("rm -rf / >> log.txt", False, "Append to log"),
        ("rm -rf / < input.txt", False, "Read from file"),
        
        # Fork bombs and resource exhaustion - should be blocked
        (":(){ :|:& };:", False, "Fork bomb"),
        ("python -c \"while True: pass\"", False, "Infinite loop"),
        ("python -c \"import os; os.fork()\"", False, "Fork process"),
        ("python -c \"a='x'*10**9\"", False, "Memory bomb"),
        
        # Path traversal and directory tricks - should be blocked
        ("rm -rf ../", False, "Parent directory"),
        ("rm -rf ../../", False, "Grandparent directory"),
        ("rm -rf ./../", False, "Current to parent"),
        ("rm -rf /tmp/../", False, "Path traversal"),
        ("rm -rf /tmp/../../", False, "Double path traversal"),
        
        # Symbolic links and special files - should be blocked
        ("rm -rf /proc/", False, "Delete proc filesystem"),
        ("rm -rf /sys/", False, "Delete sys filesystem"),
        ("rm -rf /dev/", False, "Delete device files"),
        ("rm -rf /etc/", False, "Delete system config"),
        ("rm -rf /var/", False, "Delete variable data"),
        ("rm -rf /usr/", False, "Delete user programs"),
        ("rm -rf /bin/", False, "Delete binaries"),
        ("rm -rf /sbin/", False, "Delete system binaries"),
        ("rm -rf /lib/", False, "Delete libraries"),
        ("rm -rf /lib64/", False, "Delete 64-bit libraries"),
    ]
    
    print("🧪 COMPREHENSIVE SHELL SECURITY TEST MATRIX")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for command, should_be_allowed, description in test_cases:
        result = shell._is_safe_command(command)
        status = "✅" if result == should_be_allowed else "❌"
        
        if result == should_be_allowed:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} {command:<40} | {description}")
    
    print("=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Shell security is bulletproof!")
        return True
    else:
        print(f"⚠️  {failed} TESTS FAILED - Shell security needs attention")
        return False

if __name__ == "__main__":
    test_shell_security()
