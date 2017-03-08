# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Feb 23, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

{
    'name': "Construction",
    'summary': "This is a module for construction",
    'description': """This module can be used in construction industry""",
    'author': "ϰhalid Said (Kerbrose)",
    'license': "AGPL-3",
    'website': "https://gitlab.com/kerbrose/odoo-arabia",
    'category': 'Specific Industry Applications',
    'sequence': 13,
    'version': '10.0.0.1',
    'depends': ['base_setup',
                'account_accountant',
                'account_analytic_default',
                'purchase',
                ],
    'data': ['security/construction_security.xml',
             'security/ir.model.access.csv',
             'views/account_invoice.xml',
             'views/account_invoice_line.xml',
             'views/assets.xml',
             'views/construction_views.xml',
             'views/construction_master_format_view.xml',
             ],
    'demo': [ ],
    'application': True,
    'installable': True,
}