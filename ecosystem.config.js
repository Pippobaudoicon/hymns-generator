module.exports = {
  apps: [{
    name: 'italian-hymns-api',
    script: '.venv/bin/gunicorn',
    args: '-k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120',
    cwd: '/var/www/lds/hymns-generator',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      DEBUG: 'false',
      HOST: '0.0.0.0',
      PORT: '8000'
    },
    env_development: {
      NODE_ENV: 'development',
      DEBUG: 'true',
      HOST: '0.0.0.0',
      PORT: '8000'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true,
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
