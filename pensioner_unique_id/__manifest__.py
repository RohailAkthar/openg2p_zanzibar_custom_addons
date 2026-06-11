# -*- coding: utf-8 -*-
{
    'name': 'Pensioner Unique ID Generation',
    'version': '17.0.1.0.0',
    'category': 'G2P',
    'summary': 'Generate 10-digit unique random Pensioner IDs for imported and draft-approved records',
    'author': 'Admin',
    'website': 'https://openg2p.org',
    'license': 'LGPL-3',
    'depends': [
        'g2p_social_registry',
        'social_registry_custom_fields',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
