module.exports = {
  apps: [
    {
      name: 'aicompanion-backend',
      cwd: '/var/www/aicompanion/backend',
      script: 'venv/bin/uvicorn',
      args: 'server:app --host 127.0.0.1 --port 8001',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: '/var/log/pm2/aicompanion-error.log',
      out_file: '/var/log/pm2/aicompanion-out.log',
      log_file: '/var/log/pm2/aicompanion-combined.log',
      time: true
    }
  ]
};
