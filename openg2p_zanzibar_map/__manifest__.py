{
    'name': 'OpenG2P map sampled ',
    'version': '1.0',
    'depends': ['base', 'mail', "g2p_social_registry",], 
    'data': [
        # 'security/ir.model.access.csv',
        'data/admin_location.xml',
        'views/admin_areas_menu.xml',
        'views/map_menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'openg2p_zanzibar_map/static/src/css/dashboard.css',
            'openg2p_zanzibar_map/static/src/components/kpi/**/*',
            'openg2p_zanzibar_map/static/src/components/chart/**/*',
            'openg2p_zanzibar_map/static/src/components/map/**/*',
            'openg2p_zanzibar_map/static/src/js/dashboard.js',
            'openg2p_zanzibar_map/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}