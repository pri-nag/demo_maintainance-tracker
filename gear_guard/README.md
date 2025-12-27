# GearGuard - Equipment Maintenance Tracker

## Overview

GearGuard is a comprehensive Odoo module for managing equipment maintenance. It connects Equipment → Maintenance Teams → Maintenance Requests with an intuitive workflow, Kanban board, and calendar scheduling.

## Features

### Core Features
- **Equipment Management**: Track all equipment with serial numbers, categories, locations, departments, and warranty info
- **Hierarchical Categories**: Organize equipment into parent/child categories
- **Maintenance Teams**: Organize technicians into teams for efficient task assignment
- **Maintenance Requests**: Create corrective and preventive maintenance requests with full lifecycle tracking

### Workflow & UI
- **Kanban Workflow**: Drag-and-drop interface with states: New → In Progress → Repaired (or Scrap)
- **Calendar View**: Schedule and visualize preventive maintenance
- **Smart Buttons**: Quick navigation between equipment and related maintenance requests
- **Dashboard**: Personal dashboard with quick filters
- **Bulk Operations**: Create multiple requests at once, bulk assign technicians

### Automation
- **Auto-fill**: Team and technician auto-populated from equipment
- **Scrap Logic**: Mark equipment as unusable and block new requests
- **Overdue Detection**: Automatic flagging of overdue preventive maintenance via daily cron job

### Reporting & Analytics
- **Pivot Reports**: Analysis by team, by category
- **Graph Views**: Bar, pie, and trend charts
- **Equipment Distribution**: Visual analysis of equipment across categories/teams

### Integration
- **REST API**: Full API access for external integrations
- **Smart Search (ML)**: Optional TF-IDF based similar issue search

## Installation

### Prerequisites

1. **Odoo 16.0 or 17.0** installed and running
2. **PostgreSQL 12+** database server
3. **Python 3.8+** with required Odoo dependencies

### Step 1: PostgreSQL Database Setup

#### Install PostgreSQL (if not installed)

**Windows:**
```powershell
# Download and install from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

#### Create Odoo Database User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create odoo user with password
CREATE USER odoo WITH CREATEDB PASSWORD 'odoo';

# Grant privileges
ALTER USER odoo WITH SUPERUSER;

# Exit psql
\q
```

#### Create Database for GearGuard

```bash
# Option 1: Using psql
sudo -u postgres createdb -O odoo gearguard_db

# Option 2: Using Odoo (recommended)
# Odoo will create the database automatically when you access the database manager
```

### Step 2: Configure Odoo

#### Edit odoo.conf

```ini
[options]
; Database settings
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
db_name = gearguard_db

; Addons path - add your custom addons folder
addons_path = /path/to/odoo/addons,/path/to/demo_maintainance-tracker

; Admin password for database management
admin_passwd = admin

; Server settings
http_port = 8069
```

### Step 3: Install GearGuard Module

1. **Copy the module** to your Odoo addons directory:
```powershell
# Windows PowerShell
Copy-Item -Recurse "gear_guard" "C:\odoo\custom_addons\"
```

```bash
# Linux/macOS
cp -r gear_guard /opt/odoo/custom_addons/
```

2. **Restart Odoo server:**
```powershell
# Windows
Restart-Service odoo
# Or restart manually from command line
python odoo-bin -c odoo.conf
```

```bash
# Linux
sudo systemctl restart odoo
# Or
./odoo-bin -c /etc/odoo/odoo.conf
```

3. **Update Apps List:**
   - Go to `http://localhost:8069`
   - Login as admin
   - Navigate to `Apps` menu
   - Click `Update Apps List`
   - Search for "GearGuard"
   - Click `Install`

### Step 4: Install with Demo Data (Recommended for Testing)

When installing, enable demo data to get sample categories, equipment, teams, and maintenance requests:

1. Create a new database with "Load demonstration data" checked
2. Install GearGuard module
3. Demo data will be automatically loaded

### Step 5: Install Optional ML Dependencies

For smart search functionality (TF-IDF similarity):

```powershell
# Windows
pip install scikit-learn numpy
```

```bash
# Linux/macOS
pip3 install scikit-learn numpy
```

---

## Quick Start with Docker (Alternative)

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  odoo:
    image: odoo:17.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./gear_guard:/mnt/extra-addons/gear_guard
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo

volumes:
  odoo-web-data:
  odoo-db-data:
```

Run with:
```bash
docker-compose up -d
```

---

## Database Management

### Backup Database

```bash
# Using pg_dump
pg_dump -U odoo -h localhost gearguard_db > gearguard_backup.sql

# Using Odoo Database Manager
# Go to http://localhost:8069/web/database/manager
# Click "Backup" next to your database
```

### Restore Database

```bash
# Using psql
psql -U odoo -h localhost gearguard_db < gearguard_backup.sql

# Using Odoo Database Manager
# Go to http://localhost:8069/web/database/manager
# Click "Restore Database"
```

### Upgrade Module After Changes

```bash
# Command line
./odoo-bin -c odoo.conf -u gear_guard -d gearguard_db

# Or from UI:
# Apps > GearGuard > Upgrade
```

---

## Troubleshooting

### Common Issues

**1. Module not appearing in Apps list:**
```bash
# Ensure addons_path includes your custom folder
# Restart Odoo and Update Apps List
./odoo-bin -c odoo.conf --update=gear_guard
```

**2. Database connection error:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection
psql -U odoo -h localhost -d gearguard_db
```

**3. Permission denied errors:**
```bash
# Grant proper permissions
sudo chown -R odoo:odoo /path/to/custom_addons/gear_guard
```

**4. Module import errors:**
```bash
# Check Python dependencies
pip install -r /path/to/odoo/requirements.txt
```

---

## Dependencies

### Required
- `base`
- `hr`
- `mail`

### Optional (for ML features)
```bash
pip install scikit-learn numpy
```

## Module Structure

```
gear_guard/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── api.py
├── data/
│   ├── cron.xml
│   └── demo_data.xml
├── models/
│   ├── __init__.py
│   ├── equipment.py
│   ├── equipment_category.py
│   ├── maintenance_request.py
│   └── maintenance_team.py
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml
├── static/
│   └── description/
│       └── icon.png
├── utils/
│   ├── __init__.py
│   └── ml_utils.py
├── views/
│   ├── dashboard_views.xml
│   ├── equipment_category_views.xml
│   ├── equipment_views.xml
│   ├── maintenance_request_views.xml
│   ├── maintenance_team_views.xml
│   ├── menus.xml
│   └── report_views.xml
├── wizards/
│   ├── __init__.py
│   ├── maintenance_request_wizard.py
│   └── wizard_views.xml
└── README.md
```

## Data Models

### gear.equipment.category
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Category name (required) |
| code | Char | Category code |
| parent_id | Many2one → self | Parent category |
| description | Text | Category description |

### gear.equipment
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Equipment name (required) |
| serial_number | Char | Serial number |
| category_id | Many2one → gear.equipment.category | Equipment category |
| department_id | Many2one → hr.department | Department |
| maintenance_team_id | Many2one → gear.maintenance.team | Assigned maintenance team |
| default_technician_id | Many2one → res.users | Default technician |
| location | Char | Physical location |
| is_scrapped | Boolean | Whether equipment is scrapped |
| purchase_date | Date | Purchase date |
| warranty_expiry_date | Date | Warranty expiry |

### gear.maintenance.team
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Team name (required) |
| member_ids | Many2many → res.users | Team members |
| description | Text | Team description |

### gear.maintenance.request
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Request title (required) |
| description | Text | Detailed description |
| equipment_id | Many2one → gear.equipment | Related equipment (required) |
| team_id | Many2one → gear.maintenance.team | Assigned team |
| assigned_user_id | Many2one → res.users | Assigned technician |
| request_type | Selection | corrective / preventive |
| scheduled_date | Datetime | Scheduled date |
| duration_hours | Float | Estimated duration |
| state | Selection | new / in_progress / repaired / scrap |
| is_overdue | Boolean (computed) | Whether request is overdue |
| priority | Selection | 0-Low, 1-Normal, 2-High, 3-Urgent |

## Workflow

1. **Create Categories**: Organize equipment into categories (optional)
2. **Create Teams**: Set up maintenance teams with technicians
3. **Create Equipment**: Add equipment with team and default technician assignment
4. **Create Maintenance Request**: Use smart button or menu; team/technician auto-filled from equipment
5. **Track Progress**: Use Kanban view to move requests through states
6. **Complete or Scrap**: Mark as repaired or scrap the equipment
7. **Preventive Schedule**: Use calendar view for scheduling preventive maintenance

## API Endpoints

All endpoints require user authentication.

### Equipment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/equipment` | List all equipment |
| GET | `/api/equipment/<id>` | Get equipment details |

Query parameters for list: `include_scrapped`, `team_id`, `department_id`, `limit`, `offset`

### Maintenance Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/maintenance-request` | Create new request |
| GET | `/api/maintenance-requests` | List requests with filters |

Query parameters: `equipment_id`, `team_id`, `state`, `request_type`, `overdue_only`, `limit`, `offset`

### Similar Issues (ML)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/maintenance/similar-issues?q=<query>` | Find similar past issues |

### Teams & Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/maintenance-teams` | List all teams |
| GET | `/api/maintenance/stats` | Get overall statistics |

### Example API Usage

```python
# Create maintenance request
import requests

response = requests.post(
    'http://localhost:8069/api/maintenance-request',
    json={
        'name': 'Fix broken motor',
        'equipment_id': 1,
        'description': 'Motor making grinding noise',
        'request_type': 'corrective',
        'priority': '2'
    },
    headers={'Content-Type': 'application/json'},
    auth=('admin', 'admin')
)
```

## Cron Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Update Overdue Status | Daily | Flags overdue preventive maintenance requests |

## Wizards

### Bulk Create Maintenance Requests
Create multiple maintenance requests for selected equipment at once.

### Bulk Assign
Assign team/technician to multiple requests simultaneously.

## Security

| Group | Equipment | Teams | Requests | Categories |
|-------|-----------|-------|----------|------------|
| User | Read | Read | Read/Write/Create | Read |
| System | Full | Full | Full | Full |

## Smart Search (ML)

The module includes optional TF-IDF based similarity search:
- Finds similar past maintenance issues
- Helps technicians learn from previous solutions
- Falls back to keyword search if ML libraries unavailable

To enable, install:
```bash
pip install scikit-learn numpy
```

## Menus

```
GearGuard
├── Maintenance
│   ├── My Dashboard
│   ├── Maintenance Requests
│   ├── Open Requests
│   ├── Overdue Requests
│   ├── Maintenance Calendar
│   └── Bulk Create Requests
├── Equipment
│   ├── Equipment
│   └── Scrapped Equipment
├── Reporting
│   ├── Analysis by Team
│   ├── Analysis by Category
│   └── Equipment Distribution
└── Configuration
    ├── Maintenance Teams
    └── Equipment Categories
```

## Configuration

### Adding Module Icon
Create a 128x128 PNG icon at:
```
gear_guard/static/description/icon.png
```

## Compatibility

- Odoo 16.0
- Odoo 17.0

## License

LGPL-3

## Author

GearGuard Team
