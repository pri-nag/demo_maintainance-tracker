# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GearEquipment(models.Model):
    _name = 'gear.equipment'
    _description = 'Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Equipment Name',
        required=True,
        tracking=True,
    )
    serial_number = fields.Char(
        string='Serial Number',
        tracking=True,
    )
    category_id = fields.Many2one(
        comodel_name='gear.equipment.category',
        string='Category',
        tracking=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        tracking=True,
    )
    maintenance_team_id = fields.Many2one(
        comodel_name='gear.maintenance.team',
        string='Maintenance Team',
        tracking=True,
    )
    default_technician_id = fields.Many2one(
        comodel_name='res.users',
        string='Default Technician',
        tracking=True,
        domain="[('id', 'in', technician_domain_ids)]",
    )
    technician_domain_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_technician_domain_ids',
    )
    location = fields.Char(
        string='Location',
        tracking=True,
    )
    is_scrapped = fields.Boolean(
        string='Scrapped',
        default=False,
        tracking=True,
    )
    purchase_date = fields.Date(
        string='Purchase Date',
    )
    warranty_expiry_date = fields.Date(
        string='Warranty Expiry Date',
    )
    notes = fields.Text(
        string='Notes',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    
    # Smart button fields
    maintenance_request_count = fields.Integer(
        string='Maintenance Requests',
        compute='_compute_maintenance_request_count',
    )
    open_maintenance_request_count = fields.Integer(
        string='Open Maintenance Requests',
        compute='_compute_maintenance_request_count',
    )

    @api.depends('maintenance_team_id', 'maintenance_team_id.member_ids')
    def _compute_technician_domain_ids(self):
        for record in self:
            if record.maintenance_team_id and record.maintenance_team_id.member_ids:
                record.technician_domain_ids = record.maintenance_team_id.member_ids
            else:
                record.technician_domain_ids = self.env['res.users'].search([])

    def _compute_maintenance_request_count(self):
        for record in self:
            requests = self.env['gear.maintenance.request'].search([
                ('equipment_id', '=', record.id)
            ])
            record.maintenance_request_count = len(requests)
            record.open_maintenance_request_count = len(requests.filtered(
                lambda r: r.state in ['new', 'in_progress']
            ))

    @api.onchange('maintenance_team_id')
    def _onchange_maintenance_team_id(self):
        if self.maintenance_team_id:
            if self.maintenance_team_id.member_ids:
                self.default_technician_id = self.maintenance_team_id.member_ids[0]
            else:
                self.default_technician_id = False
        else:
            self.default_technician_id = False

    def action_view_maintenance_requests(self):
        """Smart button action to view related maintenance requests."""
        self.ensure_one()
        return {
            'name': _('Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'gear.maintenance.request',
            'view_mode': 'tree,kanban,form,calendar',
            'domain': [('equipment_id', '=', self.id)],
            'context': {
                'default_equipment_id': self.id,
                'default_team_id': self.maintenance_team_id.id,
                'default_assigned_user_id': self.default_technician_id.id,
            },
        }

    def action_create_maintenance_request(self):
        """Smart button action to create a new maintenance request."""
        self.ensure_one()
        if self.is_scrapped:
            raise UserError(_('Cannot create maintenance request for scrapped equipment.'))
        return {
            'name': _('Create Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'gear.maintenance.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_equipment_id': self.id,
                'default_team_id': self.maintenance_team_id.id,
                'default_assigned_user_id': self.default_technician_id.id,
            },
        }

    def action_scrap_equipment(self):
        """Mark equipment as scrapped."""
        self.ensure_one()
        self.write({'is_scrapped': True})
        self.message_post(body=_('Equipment has been marked as scrapped.'))
        return True

    def action_restore_equipment(self):
        """Restore scrapped equipment."""
        self.ensure_one()
        self.write({'is_scrapped': False})
        self.message_post(body=_('Equipment has been restored from scrapped status.'))
        return True
