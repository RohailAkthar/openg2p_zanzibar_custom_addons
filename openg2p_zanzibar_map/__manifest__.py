{
    'name': 'OpenG2P map sampled ',
    'version': '1.0',
    'depends': ['base', 'web', 'mail', "g2p_social_registry",], 
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/admin_areas_menu.xml',
        'views/map_menu.xml',
        'views/res_users.xml',
        'views/web_layout.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'openg2p_zanzibar_map/static/src/css/dashboard.css',
            'openg2p_zanzibar_map/static/src/components/kpi/**/*',
            'openg2p_zanzibar_map/static/src/components/chart/**/*',
            'openg2p_zanzibar_map/static/src/components/map/**/*',
            'openg2p_zanzibar_map/static/src/js/minimal_mode_detection.js',
            'openg2p_zanzibar_map/static/src/js/dashboard.js',
            'openg2p_zanzibar_map/static/src/xml/dashboard.xml',
        ],
        'web.assets_frontend': [
            'openg2p_zanzibar_map/static/src/js/minimal_mode_detection.js',
        ],
    },
    'installable': True,
    'application': True,
}