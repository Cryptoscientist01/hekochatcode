module.exports = {
  apps: [
    {
      name: 'hekochat-backend',
      cwd: '/var/www/hekochat/backend',
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
      error_file: '/var/log/pm2/hekochat-error.log',
      out_file: '/var/log/pm2/hekochat-out.log',
      log_file: '/var/log/pm2/hekochat-combined.log',
      time: true
    }
  ]
};
