{
    "name": "Social Registry Custom Fields",
    "version": "17.0.1.0.0",
    "category": "G2P",
    "summary": "Custom fields for Social Registry",
    "author": "Admin",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_social_registry",
        "g2p_registry_individual",
        "g2p_draft_publish",
    ],
    "data": [
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "social_registry_custom_fields/static/src/css/hide_systray.css",
        ],
    },
    "installable": True,
    "application": False,
}
