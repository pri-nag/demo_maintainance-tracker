# -*- coding: utf-8 -*-
{
    'name': 'GearGuard - Equipment Maintenance Tracker',
    'version': '17.0.1.0.0',
    'category': 'Maintenance',
    'summary': 'Equipment maintenance management with smart tracking',
    'description': """
        GearGuard - Equipment Maintenance Tracker
        ==========================================
        
        Features:
        - Equipment management with team assignment
        - Maintenance request workflow (Kanban & Calendar)
        - Preventive and corrective maintenance tracking
        - Smart buttons for quick navigation
        - Automated overdue detection via cron
        - REST API for external integrations
        - Optional ML-based similar issue search
    """,
    'author': 'GearGuard',
    'website': 'https://www.gearguard.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/cron.xml',
        'views/menus.xml',
        'views/equipment_category_views.xml',
        'views/equipment_views.xml',
        'views/maintenance_team_views.xml',
        'views/maintenance_request_views.xml',
        'views/dashboard_views.xml',
        'views/report_views.xml',
        'wizards/wizard_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
