{
    "name": "Social Registry Profile Custom",
    "version": "17.0.1.0.0",
    "category": "Custom",
    "summary": "Customizations for the Social Registry Profile",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_agent_portal_base",
        "web",
    ],
    "data": [
        "views/navbar.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "social_registry_profile_custom/static/src/css/navbar_custom.css",
        ],
        "web.assets_backend": [
            "social_registry_profile_custom/static/src/xml/user_menu.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
