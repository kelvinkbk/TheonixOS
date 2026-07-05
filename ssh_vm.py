import paramiko
import sys
import os

if len(sys.argv) < 2:
    print("Usage: python ssh_vm.py 'command'")
    sys.exit(1)

host = '192.168.177.128'
port = 22
user = 'k'
password = 'kk'
command = sys.argv[1]

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, password=password, timeout=10)
    
    stdin, stdout, stderr = client.exec_command(command)
    
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if out:
        print(out, end='')
    if err:
        print(err, end='', file=sys.stderr)
        
    exit_status = stdout.channel.recv_exit_status()
    client.close()
    sys.exit(exit_status)
except Exception as e:
    print(f"SSH Error: {e}", file=sys.stderr)
    sys.exit(1)
