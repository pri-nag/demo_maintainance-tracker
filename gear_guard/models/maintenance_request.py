# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class GearMaintenanceRequest(models.Model):
    _name = 'gear.maintenance.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(
        string='Request Title',
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        tracking=True,
    )
    equipment_id = fields.Many2one(
        comodel_name='gear.equipment',
        string='Equipment',
        required=True,
        tracking=True,
        domain="[('is_scrapped', '=', False)]",
    )
    team_id = fields.Many2one(
        comodel_name='gear.maintenance.team',
        string='Maintenance Team',
        tracking=True,
    )
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned Technician',
        tracking=True,
        domain="[('id', 'in', available_technician_ids)]",
    )
    available_technician_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_available_technician_ids',
    )
    request_type = fields.Selection(
        selection=[
            ('corrective', 'Corrective'),
            ('preventive', 'Preventive'),
        ],
        string='Request Type',
        default='corrective',
        required=True,
        tracking=True,
    )
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True,
    )
    completion_date = fields.Datetime(
        string='Completion Date',
        tracking=True,
    )
    duration_hours = fields.Float(
        string='Duration (Hours)',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('repaired', 'Repaired'),
            ('scrap', 'Scrap'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
        group_expand='_expand_states',
    )
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True,
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
        tracking=True,
    )
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    
    # Related fields for display
    equipment_location = fields.Char(
        related='equipment_id.location',
        string='Equipment Location',
        readonly=True,
    )
    equipment_serial = fields.Char(
        related='equipment_id.serial_number',
        string='Serial Number',
        readonly=True,
    )
    equipment_category_id = fields.Many2one(
        related='equipment_id.category_id',
        string='Equipment Category',
        readonly=True,
        store=True,
    )

    @api.model
    def _expand_states(self, states, domain, order):
        """Expand all states for Kanban grouping."""
        return [key for key, val in self._fields['state'].selection]

    @api.depends('team_id', 'team_id.member_ids')
    def _compute_available_technician_ids(self):
        for record in self:
            if record.team_id and record.team_id.member_ids:
                record.available_technician_ids = record.team_id.member_ids
            else:
                record.available_technician_ids = self.env['res.users'].search([])

    @api.depends('request_type', 'scheduled_date', 'state')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for record in self:
            if (record.request_type == 'preventive' and 
                record.scheduled_date and 
                record.state not in ['repaired', 'scrap'] and
                record.scheduled_date < now):
                record.is_overdue = True
            else:
                record.is_overdue = False

    @api.depends('state', 'is_overdue', 'priority')
    def _compute_color(self):
        for record in self:
            if record.is_overdue:
                record.color = 1  # Red
            elif record.state == 'scrap':
                record.color = 5  # Purple
            elif record.state == 'repaired':
                record.color = 10  # Green
            elif record.state == 'in_progress':
                record.color = 4  # Blue
            elif record.priority == '3':
                record.color = 2  # Orange
            else:
                record.color = 0  # Default

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        """Auto-fill team and technician from equipment."""
        if self.equipment_id:
            if self.equipment_id.is_scrapped:
                raise UserError(_('Cannot create maintenance request for scrapped equipment.'))
            self.team_id = self.equipment_id.maintenance_team_id
            self.assigned_user_id = self.equipment_id.default_technician_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'equipment_id' in vals and vals.get('equipment_id'):
                equipment = self.env['gear.equipment'].browse(vals['equipment_id'])
                if equipment.is_scrapped:
                    raise UserError(_('Cannot create maintenance request for scrapped equipment.'))
                if not vals.get('team_id') and equipment.maintenance_team_id:
                    vals['team_id'] = equipment.maintenance_team_id.id
                if not vals.get('assigned_user_id') and equipment.default_technician_id:
                    vals['assigned_user_id'] = equipment.default_technician_id.id
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'scrap':
            for record in self:
                record.equipment_id.write({'is_scrapped': True})
                record.equipment_id.message_post(
                    body=_('Equipment marked as scrapped from maintenance request: %s') % record.name
                )
        if 'state' in vals and vals['state'] == 'repaired':
            vals['completion_date'] = fields.Datetime.now()
        return super().write(vals)

    def action_start(self):
        """Move request to in_progress state."""
        for record in self:
            if record.state == 'new':
                record.write({'state': 'in_progress'})

    def action_repair(self):
        """Move request to repaired state."""
        for record in self:
            if record.state in ['new', 'in_progress']:
                record.write({
                    'state': 'repaired',
                    'completion_date': fields.Datetime.now(),
                })

    def action_scrap(self):
        """Move request to scrap state and mark equipment as scrapped."""
        for record in self:
            record.write({'state': 'scrap'})

    def action_reset_to_new(self):
        """Reset request to new state."""
        for record in self:
            record.write({
                'state': 'new',
                'completion_date': False,
            })

    @api.model
    def cron_update_overdue_status(self):
        """Cron job to update overdue status for preventive maintenance requests."""
        now = fields.Datetime.now()
        overdue_requests = self.search([
            ('request_type', '=', 'preventive'),
            ('scheduled_date', '<', now),
            ('state', 'not in', ['repaired', 'scrap']),
            ('is_overdue', '=', False),
        ])
        overdue_requests.write({'is_overdue': True})
        
        # Also update requests that are no longer overdue (edge case)
        not_overdue_requests = self.search([
            ('is_overdue', '=', True),
            '|',
            ('state', 'in', ['repaired', 'scrap']),
            ('scheduled_date', '>=', now),
        ])
        not_overdue_requests.write({'is_overdue': False})
        
        return True

    @api.model
    def find_similar_issues(self, query, limit=5):
        """
        Find similar maintenance requests using TF-IDF and cosine similarity.
        Falls back to ORM search if ML libraries are not available.
        """
        if not query:
            return []

        all_requests = self.search([
            ('state', '=', 'repaired'),
            ('description', '!=', False),
        ], limit=500)

        if not all_requests:
            return []

        if ML_AVAILABLE and len(all_requests) >= 2:
            try:
                descriptions = [r.description or '' for r in all_requests]
                descriptions.append(query)
                
                vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=1000,
                    ngram_range=(1, 2),
                )
                tfidf_matrix = vectorizer.fit_transform(descriptions)
                
                query_vector = tfidf_matrix[-1]
                doc_vectors = tfidf_matrix[:-1]
                
                similarities = cosine_similarity(query_vector, doc_vectors).flatten()
                
                top_indices = similarities.argsort()[-limit:][::-1]
                
                result = []
                for idx in top_indices:
                    if similarities[idx] > 0.1:
                        request = all_requests[idx]
                        result.append({
                            'id': request.id,
                            'name': request.name,
                            'description': request.description,
                            'similarity_score': float(similarities[idx]),
                            'equipment_name': request.equipment_id.name,
                            'state': request.state,
                        })
                return result
            except Exception:
                pass

        # Fallback to ORM search
        words = query.lower().split()
        domain = [('state', '=', 'repaired')]
        for word in words[:3]:
            domain.append('|')
            domain.append(('name', 'ilike', word))
            domain.append(('description', 'ilike', word))
        
        if len(domain) > 1:
            similar_requests = self.search(domain, limit=limit)
            return [{
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'similarity_score': 0.5,
                'equipment_name': r.equipment_id.name,
                'state': r.state,
            } for r in similar_requests]
        
        return []
