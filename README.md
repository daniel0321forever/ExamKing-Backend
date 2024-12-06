# Preparation
### Install Redis server (Ubuntu)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server.service  # Enable Redis to start on boot
sudo systemctl start redis-server.service   # Start Redis immediately
```