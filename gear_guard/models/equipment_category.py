# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GearEquipmentCategory(models.Model):
    _name = 'gear.equipment.category'
    _description = 'Equipment Category'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
    )
    description = fields.Text(
        string='Description',
    )
    parent_id = fields.Many2one(
        comodel_name='gear.equipment.category',
        string='Parent Category',
        index=True,
        ondelete='cascade',
    )
    child_ids = fields.One2many(
        comodel_name='gear.equipment.category',
        inverse_name='parent_id',
        string='Child Categories',
    )
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    color = fields.Integer(
        string='Color',
    )

    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = self.env['gear.equipment'].search_count([
                ('category_id', '=', record.id)
            ])

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise models.ValidationError(_('You cannot create recursive categories.'))

    def name_get(self):
        result = []
        for record in self:
            if record.parent_id:
                name = f"{record.parent_id.name} / {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result
