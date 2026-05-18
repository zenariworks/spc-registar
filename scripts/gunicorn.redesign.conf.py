"""Gunicorn config for the redesign deploy on port 8999."""
bind = "0.0.0.0:8999"
workers = 2
worker_class = "sync"
timeout = 120
accesslog = "/var/log/spc-registar-redesign/access.log"
errorlog = "/var/log/spc-registar-redesign/error.log"
loglevel = "info"
