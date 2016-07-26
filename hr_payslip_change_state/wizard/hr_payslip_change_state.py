# -*- coding: utf-8 -*-
# © 2016 - Eficent http://www.eficent.com/
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp import netsvc


class HrPaySlipChangeState(models.TransientModel):

    _name = "hr.payslip.change.state"
    _description = "Change state of a payslip"

    state = fields.Selection([
            ('draft', 'Set to Draft'),
            ('verify', 'Compute Sheet'),
            ('done', 'Confirm'),
            ('cancel', 'Cancel Payslip'),
        ], 'Action',
            help='* When the payslip is created the status is \'Draft\'.\
            \n* If the payslip is under verification, the status is '
                 '\'Waiting\'. \
            \n* If the payslip is confirmed then status is set to \'Done\'.\
            \n* When user cancel payslip the status is \'Rejected\'.')

    @api.multi
    def change_state_confirm(self):
        record_ids = self.env.context.get('active_ids', False)
        payslip_obj = self.env['hr.payslip']
        new_state = self.state
        records = payslip_obj.browse(record_ids)
        wf_service = netsvc.LocalService("workflow")

        for rec in records:
            if new_state == 'draft':
                if rec.state == 'cancel':
                    wf_service.trg_validate(self.env.uid,'hr.payslip',
                                            rec.id, 'draft', self.env.cr)
                else:
                    raise Warning(_("Only rejected payslips can be reset to "
                                    "draft, the payslip %s is in "
                                    "%s state" % (rec.name, rec.state)))
            elif new_state == 'verify':
                if rec.state == 'draft':
                    rec.compute_sheet()
                else:
                    raise Warning(_("Only draft payslips can be verified,"
                                    "the payslip %s is in "
                                    "%s state" % (rec.name, rec.state)))
            elif new_state == 'done':
                if rec.state in ('verify', 'draft'):
                    wf_service.trg_validate(self.env.uid, 'hr.payslip',
                                            rec.id, 'hr_verify_sheet',
                                            self.env.cr)
                else:
                    raise Warning(_("Only payslips in states verify or draft "
                                    "can be confirmed, the payslip %s is in "
                                    "%s state" % (rec.name, rec.state)))
            elif new_state == 'cancel':
                if rec.state != 'cancel':
                    wf_service.trg_validate(self.env.uid, 'hr.payslip',
                                            rec.id,'cancel_sheet',self.env.cr)
                else:
                    raise Warning(_("The payslip %s is already canceled "
                                    "please deselect it" % rec.name))

        return {
            'domain': "[('id','in', ["+','.join(map(str, record_ids))+"])]",
            'name': _('Payslips'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }