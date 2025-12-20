module.exports = {
  apps: [{
    name: 'hymns-generator',
    script: 'app.py',
    cwd: '/var/www/lds/hymns-generator',
    interpreter: '.venv/bin/python',
    args: '--workers 4',
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
