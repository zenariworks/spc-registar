"""Gunicorn configuration for the bare-metal systemd deploy.

Read by /etc/systemd/system/spc-registar.service (ExecStart ... -c <this file>).
Docker deployments ignore this file — see docker-compose.prod.yml for the
in-container gunicorn command.
"""

bind = "0.0.0.0:9000"
workers = 3
worker_class = "sync"
timeout = 120
accesslog = "/var/log/spc-registar/access.log"
errorlog = "/var/log/spc-registar/error.log"
loglevel = "info"
chdir = "/root/projects/spc-registar-main/crkva"
