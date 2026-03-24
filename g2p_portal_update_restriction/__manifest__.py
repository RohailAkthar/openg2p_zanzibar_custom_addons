{
    'name': 'G2P Portal Update Restriction',
    'version': '1.0',
    'category': 'OpenG2P/Portal',
    'summary': 'Restrict portal update functionality to specific users.',
    'description': """
This module adds a new security group "Reg portal update access" to control access
to the update functionality for individuals in the registration portal.
    """,
    'author': 'OpenG2P',
    'website': 'https://openg2p.org',
    'depends': [
        'g2p_registration_portal_base',
        'g2p_zanzibar_draft_publish',
        'g2p_social_registry_model',
    ],
    'data': [
        'security/security.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
