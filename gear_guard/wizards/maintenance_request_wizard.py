# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaintenanceRequestWizard(models.TransientModel):
    _name = 'gear.maintenance.request.wizard'
    _description = 'Maintenance Request Wizard'

    equipment_ids = fields.Many2many(
        comodel_name='gear.equipment',
        string='Equipment',
        required=True,
        domain="[('is_scrapped', '=', False)]",
    )
    request_type = fields.Selection(
        selection=[
            ('corrective', 'Corrective'),
            ('preventive', 'Preventive'),
        ],
        string='Request Type',
        default='preventive',
        required=True,
    )
    name_template = fields.Char(
        string='Request Title Template',
        default='Scheduled Maintenance - {equipment}',
        required=True,
        help="Use {equipment} as placeholder for equipment name",
    )
    description = fields.Text(
        string='Description',
    )
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        required=True,
    )
    duration_hours = fields.Float(
        string='Duration (Hours)',
        default=1.0,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
    )

    def action_create_requests(self):
        """Create maintenance requests for selected equipment."""
        self.ensure_one()
        
        if not self.equipment_ids:
            raise UserError(_('Please select at least one equipment.'))
        
        MaintenanceRequest = self.env['gear.maintenance.request']
        created_requests = MaintenanceRequest
        
        for equipment in self.equipment_ids:
            if equipment.is_scrapped:
                continue
            
            name = self.name_template.replace('{equipment}', equipment.name)
            
            vals = {
                'name': name,
                'equipment_id': equipment.id,
                'team_id': equipment.maintenance_team_id.id if equipment.maintenance_team_id else False,
                'assigned_user_id': equipment.default_technician_id.id if equipment.default_technician_id else False,
                'request_type': self.request_type,
                'description': self.description,
                'scheduled_date': self.scheduled_date,
                'duration_hours': self.duration_hours,
                'priority': self.priority,
            }
            
            created_requests |= MaintenanceRequest.create(vals)
        
        if not created_requests:
            raise UserError(_('No maintenance requests were created.'))
        
        # Return action to view created requests
        return {
            'name': _('Created Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'gear.maintenance.request',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_requests.ids)],
            'context': {},
        }


class MaintenanceAssignWizard(models.TransientModel):
    _name = 'gear.maintenance.assign.wizard'
    _description = 'Bulk Assign Maintenance Requests'

    request_ids = fields.Many2many(
        comodel_name='gear.maintenance.request',
        string='Requests',
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name='gear.maintenance.team',
        string='Assign to Team',
    )
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assign to Technician',
        domain="[('id', 'in', available_user_ids)]",
    )
    available_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_available_user_ids',
    )
    scheduled_date = fields.Datetime(
        string='Reschedule To',
    )
    
    @api.depends('team_id')
    def _compute_available_user_ids(self):
        for record in self:
            if record.team_id and record.team_id.member_ids:
                record.available_user_ids = record.team_id.member_ids
            else:
                record.available_user_ids = self.env['res.users'].search([])

    def action_assign(self):
        """Bulk assign selected requests."""
        self.ensure_one()
        
        if not self.request_ids:
            raise UserError(_('No requests selected.'))
        
        vals = {}
        if self.team_id:
            vals['team_id'] = self.team_id.id
        if self.assigned_user_id:
            vals['assigned_user_id'] = self.assigned_user_id.id
        if self.scheduled_date:
            vals['scheduled_date'] = self.scheduled_date
        
        if vals:
            self.request_ids.write(vals)
        
        return {'type': 'ir.actions.act_window_close'}
