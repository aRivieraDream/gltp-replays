# Deployment Guide

This guide outlines the deployment process for the replay service on a VM. You only need to run this once when setting up the VM for the first time. Once you have webhooks setup, the service will update automatically. Local testing can be done using the instructions in README.md

## Prerequisites

- A Linux server (tested on Ubuntu)
- Root access
- Git installed

## Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/aRivieraDream/gltp-replays
   cd replay-service
   ```

2. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

The deployment script will:
- Install required packages (Docker, Docker Compose, Certbot)
- Set up the application directory structure
- Configure Nginx as a reverse proxy
- Set up automatic backups
- Configure the webhook handler for automatic deployments
- Start the application containers

The process should take 10-15 minutes to install everything

## Post-Deployment

After running the deployment script:

1. Log out and log back in for Docker group changes to take effect
2. The application will be accessible at `http://<server-ip>`
3. Daily backups will be stored in `/backup/`
4. Deployment logs are available at `/var/log/webhook-deployments.log`

## Automatic Deployments

The service is configured to automatically deploy when changes are pushed to the main branch:

1. Set up a GitHub webhook:
   - Go to your repository settings
   - Add a webhook pointing to `http://<server-ip>/webhook`
   - Select "application/json" as the content type
   - Choose the "push" event

2. When changes are pushed:
   - The webhook handler will automatically pull the latest changes
   - Rebuild and restart the containers
   - Log the deployment in `/var/log/webhook-deployments.log`
   - Automatically rollback if the deployment fails

## SSL Setup

To enable HTTPS:

1. Point your domain to the server's IP address
2. Run Certbot to obtain SSL certificates:
   ```bash
   sudo certbot certonly --standalone -d your-domain.com
   ```
3. Update the Nginx configuration in `nginx/conf.d/default.conf` with your domain
4. Restart the containers:
   ```bash
   docker-compose restart
   ```

## Monitoring

- View deployment logs:
  ```bash
  cat /var/log/webhook-deployments.log
  ```
- Check container status:
  ```bash
  docker-compose ps
  ```
- View application logs:
  ```bash
  docker-compose logs
  ```

## Backup and Restore

- Daily backups are automatically created at midnight
- Backups are stored in `/backup/` with timestamps
- To restore from a backup:
  ```bash
  tar -xzf /backup/replay-data-<timestamp>.tar.gz -C /path/to/restore
  ```

## Troubleshooting

1. If the application is not accessible:
   - Check container status: `docker-compose ps`
   - View logs: `docker-compose logs`
   - Verify Nginx configuration: `nginx -t`

2. If automatic deployments fail:
   - Check webhook logs: `cat /var/log/webhook-deployments.log`
   - Verify webhook configuration in GitHub
   - Check container logs: `docker-compose logs`

3. If backups fail:
   - Check cron logs: `grep CRON /var/log/syslog`
   - Verify backup directory permissions
   - Check available disk space: `df -h`
