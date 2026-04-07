module.exports = {
  apps: [
    {
      name: "clarmi-imessage-agent",
      script: "dist/index.js",
      cwd: __dirname,
      watch: false,
      autorestart: true,
      max_restarts: 50,
      restart_delay: 5000,
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};
