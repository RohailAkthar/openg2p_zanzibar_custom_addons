{
    'name': 'Non-Persistent Sessions',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Makes login sessions non-persistent (expire on browser close)',
    'description': """
        This module overrides the session cookie behavior to ensure that
        the session_id cookie is a session-only cookie.
        This means that when the user closes their browser, they will be
        logged out and asked for credentials upon returning.
    """,
    'author': 'OpenG2P',
    'depends': ['base', 'web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'g2p_session_non_persistent/static/src/js/session_tab_logout.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
