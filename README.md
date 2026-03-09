# NewTab

A modern, customizable homepage manager with flip-card navigation and dynamic page management.

![NewTab Screenshot](https://img.shields.io/badge/Flask-Python-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-green)

## Features

- 🎴 **Modern Flip Cards** - Premium glassmorphism interface with integrated tool labels
- 📑 **Dynamic Pages** - Create custom pages and assign cards to multiple pages
- 🔍 **Unified Search** - Sleek, single-pill search bar for a cleaner aesthetic
- 🎨 **Customizable Cards** - Set custom images, colors, and multiple links per card
- 📱 **Centered Responsive Layout** - Advanced CSS Grid with centered flex balancing for perfectly aligned rows
- ⚡ **Smart Pagination** - Smooth link pagination for cards with many URLs

## Included Presets

The application comes with over 60 built-in presets for popular DevOps and IT tools, including:

**Cloud & Infrastructure:** AWS, Azure, Google Cloud, DigitalOcean, Kubernetes, OpenShift, Docker, Terraform, VMware, Nutanix, Dell, Windows, Red Hat

**DevOps & CI/CD:** Jenkins, GitLab, GitHub, Azure DevOps, ArgoCD, Nexus, Kasten, Veeam

**Databases & Storage:** PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch, MinIO S3, NetApp

**Monitoring & Logging:** Grafana, Prometheus, Splunk, Uptime Kuma, LiveNX, Tufin, Monitor

**Security & Networking:** Cisco, Cisco ISE, Check Point, Palo Alto, CyberArk, Cybereason, McAfee, Trellix, Prisma Cloud, HAProxy, Nginx, Apache, Traefik, phpIPAM

**Productivity & Tools:** Outlook, Exchange, SharePoint, Wiki.js, Jira, Confluence, Swagger, Postman, Home Assistant, WordPress, Keycloak, ADFS, OmniSSA Horizon, Stratodesk, Chrome, Docs, ServiceNow

## Quick Start

### Using Docker Compose

```bash
docker-compose up -d
```

The app will be available at `http://localhost:5000`

### Using Docker Hub

```bash
docker pull devopsteamsdb/devopsteamsdb:newtab_latest
docker run -p 5000:5000 -v $(pwd)/data:/app/data devopsteamsdb/devopsteamsdb:newtab_latest
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment (development/production) | development |

### Data Persistence

The application uses a single volume mount for user data persistence:

- `./data:/app/data`

The `data` directory is structured as follows:
- `data/database/data.json` - Stores cards, pages, and settings
- `data/uploads/` - Stores uploaded card images

### System Presets

System presets are stored in `config/presets.json`. Code changes to presets are built into the image, but you can override them by mounting a local config directory if needed:
- `./config:/app/config`

## Admin Panel

Access the admin panel at `/admin` to:
- Add/Edit/Delete cards
- Manage pages
- Configure search bar settings

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

## CI/CD

GitHub Actions workflow automatically:
- Builds Docker image on push to main
- Pushes to Docker Hub with date and `latest` tags
- Creates GitHub release with Docker image artifact

### Required Secrets

- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_PASSWORD` - Docker Hub password/token

## License

MIT License
