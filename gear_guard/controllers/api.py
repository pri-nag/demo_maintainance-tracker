# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request, Response


class GearGuardAPI(http.Controller):
    """REST API Controller for GearGuard module."""

    def _json_response(self, data, status=200):
        """Helper method to return JSON response."""
        return Response(
            json.dumps(data, default=str),
            status=status,
            content_type='application/json'
        )

    def _error_response(self, message, status=400):
        """Helper method to return error response."""
        return self._json_response({'error': message}, status=status)

    # ==================== Equipment Endpoints ====================

    @http.route('/api/equipment', type='http', auth='user', methods=['GET'], csrf=False)
    def get_equipment_list(self, **kwargs):
        """
        GET /api/equipment
        Returns list of all equipment.
        Query params:
            - include_scrapped: boolean (default: false)
            - team_id: integer (filter by team)
            - department_id: integer (filter by department)
            - limit: integer (default: 100)
            - offset: integer (default: 0)
        """
        try:
            include_scrapped = kwargs.get('include_scrapped', 'false').lower() == 'true'
            team_id = kwargs.get('team_id')
            department_id = kwargs.get('department_id')
            limit = int(kwargs.get('limit', 100))
            offset = int(kwargs.get('offset', 0))

            domain = []
            if not include_scrapped:
                domain.append(('is_scrapped', '=', False))
            if team_id:
                domain.append(('maintenance_team_id', '=', int(team_id)))
            if department_id:
                domain.append(('department_id', '=', int(department_id)))

            equipment = request.env['gear.equipment'].sudo().search(
                domain, limit=limit, offset=offset, order='name'
            )
            total_count = request.env['gear.equipment'].sudo().search_count(domain)

            data = {
                'status': 'success',
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'data': [{
                    'id': eq.id,
                    'name': eq.name,
                    'serial_number': eq.serial_number,
                    'location': eq.location,
                    'is_scrapped': eq.is_scrapped,
                    'department': {
                        'id': eq.department_id.id,
                        'name': eq.department_id.name,
                    } if eq.department_id else None,
                    'maintenance_team': {
                        'id': eq.maintenance_team_id.id,
                        'name': eq.maintenance_team_id.name,
                    } if eq.maintenance_team_id else None,
                    'default_technician': {
                        'id': eq.default_technician_id.id,
                        'name': eq.default_technician_id.name,
                    } if eq.default_technician_id else None,
                    'purchase_date': eq.purchase_date,
                    'warranty_expiry_date': eq.warranty_expiry_date,
                    'open_maintenance_requests': eq.open_maintenance_request_count,
                } for eq in equipment]
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)

    @http.route('/api/equipment/<int:equipment_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_equipment_detail(self, equipment_id, **kwargs):
        """
        GET /api/equipment/<id>
        Returns detailed information for a specific equipment.
        """
        try:
            equipment = request.env['gear.equipment'].sudo().browse(equipment_id)
            
            if not equipment.exists():
                return self._error_response('Equipment not found', status=404)

            # Get maintenance requests for this equipment
            maintenance_requests = request.env['gear.maintenance.request'].sudo().search([
                ('equipment_id', '=', equipment_id)
            ], order='scheduled_date desc', limit=10)

            data = {
                'status': 'success',
                'data': {
                    'id': equipment.id,
                    'name': equipment.name,
                    'serial_number': equipment.serial_number,
                    'location': equipment.location,
                    'is_scrapped': equipment.is_scrapped,
                    'active': equipment.active,
                    'notes': equipment.notes,
                    'department': {
                        'id': equipment.department_id.id,
                        'name': equipment.department_id.name,
                    } if equipment.department_id else None,
                    'maintenance_team': {
                        'id': equipment.maintenance_team_id.id,
                        'name': equipment.maintenance_team_id.name,
                        'members': [{
                            'id': m.id,
                            'name': m.name,
                        } for m in equipment.maintenance_team_id.member_ids]
                    } if equipment.maintenance_team_id else None,
                    'default_technician': {
                        'id': equipment.default_technician_id.id,
                        'name': equipment.default_technician_id.name,
                    } if equipment.default_technician_id else None,
                    'purchase_date': equipment.purchase_date,
                    'warranty_expiry_date': equipment.warranty_expiry_date,
                    'maintenance_request_count': equipment.maintenance_request_count,
                    'open_maintenance_request_count': equipment.open_maintenance_request_count,
                    'recent_maintenance_requests': [{
                        'id': req.id,
                        'name': req.name,
                        'state': req.state,
                        'request_type': req.request_type,
                        'scheduled_date': req.scheduled_date,
                        'is_overdue': req.is_overdue,
                    } for req in maintenance_requests]
                }
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)

    # ==================== Maintenance Request Endpoints ====================

    @http.route('/api/maintenance-request', type='json', auth='user', methods=['POST'], csrf=False)
    def create_maintenance_request(self, **kwargs):
        """
        POST /api/maintenance-request
        Creates a new maintenance request.
        
        JSON Body:
        {
            "name": "Request Title (required)",
            "equipment_id": 1 (required),
            "description": "Description text",
            "request_type": "corrective" or "preventive",
            "scheduled_date": "2025-01-15 10:00:00",
            "priority": "0", "1", "2", or "3",
            "team_id": 1 (optional, auto-filled from equipment),
            "assigned_user_id": 1 (optional, auto-filled from equipment)
        }
        """
        try:
            data = request.jsonrequest

            # Validate required fields
            if not data.get('name'):
                return {'status': 'error', 'message': 'name is required'}
            if not data.get('equipment_id'):
                return {'status': 'error', 'message': 'equipment_id is required'}

            # Check if equipment exists and is not scrapped
            equipment = request.env['gear.equipment'].sudo().browse(data['equipment_id'])
            if not equipment.exists():
                return {'status': 'error', 'message': 'Equipment not found'}
            if equipment.is_scrapped:
                return {'status': 'error', 'message': 'Cannot create request for scrapped equipment'}

            # Prepare values
            vals = {
                'name': data['name'],
                'equipment_id': data['equipment_id'],
                'description': data.get('description', ''),
                'request_type': data.get('request_type', 'corrective'),
                'priority': data.get('priority', '1'),
            }

            # Auto-fill team and technician from equipment if not provided
            if data.get('team_id'):
                vals['team_id'] = data['team_id']
            elif equipment.maintenance_team_id:
                vals['team_id'] = equipment.maintenance_team_id.id

            if data.get('assigned_user_id'):
                vals['assigned_user_id'] = data['assigned_user_id']
            elif equipment.default_technician_id:
                vals['assigned_user_id'] = equipment.default_technician_id.id

            if data.get('scheduled_date'):
                vals['scheduled_date'] = data['scheduled_date']

            # Create the maintenance request
            maintenance_request = request.env['gear.maintenance.request'].sudo().create(vals)

            return {
                'status': 'success',
                'message': 'Maintenance request created successfully',
                'data': {
                    'id': maintenance_request.id,
                    'name': maintenance_request.name,
                    'equipment_id': maintenance_request.equipment_id.id,
                    'equipment_name': maintenance_request.equipment_id.name,
                    'team_id': maintenance_request.team_id.id if maintenance_request.team_id else None,
                    'team_name': maintenance_request.team_id.name if maintenance_request.team_id else None,
                    'assigned_user_id': maintenance_request.assigned_user_id.id if maintenance_request.assigned_user_id else None,
                    'assigned_user_name': maintenance_request.assigned_user_id.name if maintenance_request.assigned_user_id else None,
                    'state': maintenance_request.state,
                    'request_type': maintenance_request.request_type,
                    'scheduled_date': str(maintenance_request.scheduled_date) if maintenance_request.scheduled_date else None,
                }
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/maintenance-requests', type='http', auth='user', methods=['GET'], csrf=False)
    def get_maintenance_requests(self, **kwargs):
        """
        GET /api/maintenance-requests
        Returns list of maintenance requests.
        Query params:
            - equipment_id: integer
            - team_id: integer
            - state: string (new, in_progress, repaired, scrap)
            - request_type: string (corrective, preventive)
            - overdue_only: boolean
            - limit: integer (default: 100)
            - offset: integer (default: 0)
        """
        try:
            equipment_id = kwargs.get('equipment_id')
            team_id = kwargs.get('team_id')
            state = kwargs.get('state')
            request_type = kwargs.get('request_type')
            overdue_only = kwargs.get('overdue_only', 'false').lower() == 'true'
            limit = int(kwargs.get('limit', 100))
            offset = int(kwargs.get('offset', 0))

            domain = []
            if equipment_id:
                domain.append(('equipment_id', '=', int(equipment_id)))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            if state:
                domain.append(('state', '=', state))
            if request_type:
                domain.append(('request_type', '=', request_type))
            if overdue_only:
                domain.append(('is_overdue', '=', True))

            requests = request.env['gear.maintenance.request'].sudo().search(
                domain, limit=limit, offset=offset, order='scheduled_date desc'
            )
            total_count = request.env['gear.maintenance.request'].sudo().search_count(domain)

            data = {
                'status': 'success',
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'data': [{
                    'id': req.id,
                    'name': req.name,
                    'description': req.description,
                    'equipment': {
                        'id': req.equipment_id.id,
                        'name': req.equipment_id.name,
                    },
                    'team': {
                        'id': req.team_id.id,
                        'name': req.team_id.name,
                    } if req.team_id else None,
                    'assigned_user': {
                        'id': req.assigned_user_id.id,
                        'name': req.assigned_user_id.name,
                    } if req.assigned_user_id else None,
                    'state': req.state,
                    'request_type': req.request_type,
                    'priority': req.priority,
                    'scheduled_date': req.scheduled_date,
                    'completion_date': req.completion_date,
                    'duration_hours': req.duration_hours,
                    'is_overdue': req.is_overdue,
                } for req in requests]
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)

    # ==================== Similar Issues Endpoint (ML) ====================

    @http.route('/api/maintenance/similar-issues', type='http', auth='user', methods=['GET'], csrf=False)
    def get_similar_issues(self, **kwargs):
        """
        GET /api/maintenance/similar-issues?q=<query>
        Returns similar past maintenance requests using TF-IDF similarity.
        Falls back to keyword search if ML libraries unavailable.
        
        Query params:
            - q: search query (required)
            - limit: maximum results (default: 5)
        """
        try:
            query = kwargs.get('q', '')
            limit = int(kwargs.get('limit', 5))

            if not query:
                return self._error_response('Query parameter "q" is required', status=400)

            # Use the model's find_similar_issues method
            similar_issues = request.env['gear.maintenance.request'].sudo().find_similar_issues(
                query=query,
                limit=limit
            )

            data = {
                'status': 'success',
                'query': query,
                'count': len(similar_issues),
                'data': similar_issues
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)

    # ==================== Maintenance Teams Endpoint ====================

    @http.route('/api/maintenance-teams', type='http', auth='user', methods=['GET'], csrf=False)
    def get_maintenance_teams(self, **kwargs):
        """
        GET /api/maintenance-teams
        Returns list of all maintenance teams.
        """
        try:
            teams = request.env['gear.maintenance.team'].sudo().search([], order='name')

            data = {
                'status': 'success',
                'count': len(teams),
                'data': [{
                    'id': team.id,
                    'name': team.name,
                    'description': team.description,
                    'member_count': len(team.member_ids),
                    'members': [{
                        'id': m.id,
                        'name': m.name,
                    } for m in team.member_ids],
                    'equipment_count': team.equipment_count,
                    'open_request_count': team.open_request_count,
                } for team in teams]
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)

    # ==================== Statistics Endpoint ====================

    @http.route('/api/maintenance/stats', type='http', auth='user', methods=['GET'], csrf=False)
    def get_maintenance_stats(self, **kwargs):
        """
        GET /api/maintenance/stats
        Returns overall maintenance statistics.
        """
        try:
            MaintRequest = request.env['gear.maintenance.request'].sudo()
            Equipment = request.env['gear.equipment'].sudo()

            data = {
                'status': 'success',
                'data': {
                    'equipment': {
                        'total': Equipment.search_count([]),
                        'active': Equipment.search_count([('is_scrapped', '=', False)]),
                        'scrapped': Equipment.search_count([('is_scrapped', '=', True)]),
                    },
                    'maintenance_requests': {
                        'total': MaintRequest.search_count([]),
                        'new': MaintRequest.search_count([('state', '=', 'new')]),
                        'in_progress': MaintRequest.search_count([('state', '=', 'in_progress')]),
                        'repaired': MaintRequest.search_count([('state', '=', 'repaired')]),
                        'scrap': MaintRequest.search_count([('state', '=', 'scrap')]),
                        'overdue': MaintRequest.search_count([('is_overdue', '=', True)]),
                        'corrective': MaintRequest.search_count([('request_type', '=', 'corrective')]),
                        'preventive': MaintRequest.search_count([('request_type', '=', 'preventive')]),
                    }
                }
            }
            return self._json_response(data)

        except Exception as e:
            return self._error_response(str(e), status=500)
