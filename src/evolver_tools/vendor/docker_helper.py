#!/usr/bin/env python3
"""docker-helper — Common Docker commands helper."""
import subprocess
import sys

TOOL_META = {
    "name": "docker-helper",
    "func": "main",
    "desc": "Docker command helper. Usage: docker-helper <command> [args]",
}

COMMANDS = {
    "ps": "docker ps",
    "images": "docker images",
    "stats": "docker stats --no-stream",
    "logs": "docker logs",
    "stop-all": "docker stop $(docker ps -q)",
    "rm-all": "docker rm $(docker ps -aq)",
    "rmi-none": "docker rmi $(docker images -f dangling=true -q)",
    "prune": "docker system prune -f",
    "prune-all": "docker system prune -af --volumes",
    "compose-ps": "docker compose ps",
    "top": "docker top",
    "inspect": "docker inspect",
    "network-ls": "docker network ls",
    "volume-ls": "docker volume ls",
    "clean": "docker system prune -f",
    "exec": "docker exec -it",
    "build": "docker build",
    "pull": "docker pull",
    "push": "docker push",
    "info": "docker info",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: docker-helper <command> [extra args...]")
        print("\nAvailable commands:")
        for cmd, desc in sorted(COMMANDS.items()):
            print(f"  {cmd:<15} {desc}")
        print()
        print("Examples:")
        print("  docker-helper ps")
        print("  docker-helper logs mycontainer")
        print("  docker-helper stop-all")
        return
    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Available: " + ", ".join(sorted(COMMANDS.keys())), file=sys.stderr)
        sys.exit(1)
    docker_cmd = COMMANDS[cmd]
    extra = args[1:]
    full_cmd = docker_cmd + " " + " ".join(extra) if extra else docker_cmd
    # Handle docker exec -it specially (needs pty, just show the command)
    if cmd == "exec":
        print(f"Run: {full_cmd}")
        print("Note: Use 'docker exec -it' directly for interactive sessions")
        return
    print(f"$ {full_cmd}")
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=False, timeout=60)
        if result.returncode != 0:
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print("Command timed out", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Docker not found. Is Docker installed?", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
