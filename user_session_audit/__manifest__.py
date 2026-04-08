{
    'name': 'User Session Audit',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'Track user login/logout sessions and activity without external dependencies.',
    'description': """
        This module provides independent tracking of user sessions, 
        including login/logout times, session duration, IP addresses, 
        and user agents.
    """,
    'author': 'Rohail Akthar',
    'depends': ['base', 'web', 'g2p_zanzibar_access_restriction'],
    'data': [
        'security/ir.model.access.csv',
        'views/user_session_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
