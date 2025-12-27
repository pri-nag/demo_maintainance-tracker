# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GearMaintenanceTeam(models.Model):
    _name = 'gear.maintenance.team'
    _description = 'Maintenance Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Team Name',
        required=True,
        tracking=True,
    )
    member_ids = fields.Many2many(
        comodel_name='res.users',
        relation='gear_maintenance_team_users_rel',
        column1='team_id',
        column2='user_id',
        string='Team Members',
        tracking=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    description = fields.Text(
        string='Description',
    )
    
    # Computed fields for smart buttons
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
    )
    maintenance_request_count = fields.Integer(
        string='Maintenance Requests',
        compute='_compute_maintenance_request_count',
    )
    open_request_count = fields.Integer(
        string='Open Requests',
        compute='_compute_maintenance_request_count',
    )

    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = self.env['gear.equipment'].search_count([
                ('maintenance_team_id', '=', record.id)
            ])

    def _compute_maintenance_request_count(self):
        for record in self:
            requests = self.env['gear.maintenance.request'].search([
                ('team_id', '=', record.id)
            ])
            record.maintenance_request_count = len(requests)
            record.open_request_count = len(requests.filtered(
                lambda r: r.state in ['new', 'in_progress']
            ))

    def action_view_equipment(self):
        """Smart button action to view related equipment."""
        self.ensure_one()
        return {
            'name': _('Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'gear.equipment',
            'view_mode': 'tree,form',
            'domain': [('maintenance_team_id', '=', self.id)],
            'context': {
                'default_maintenance_team_id': self.id,
            },
        }

    def action_view_maintenance_requests(self):
        """Smart button action to view related maintenance requests."""
        self.ensure_one()
        return {
            'name': _('Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'gear.maintenance.request',
            'view_mode': 'tree,kanban,form,calendar',
            'domain': [('team_id', '=', self.id)],
            'context': {
                'default_team_id': self.id,
            },
        }
