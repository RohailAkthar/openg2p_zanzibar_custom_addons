{
    "name": "G2P Individual Custom UI",
    "version": "1.0",
    "category": "Registry",
    "summary": "Custom UI changes for Individual form (image size and name fields width)",
    "description": "Extends the Individual form view to increase image size and field widths",
    "author": "Your Name",
    "depends": [
        "g2p_registry_individual",
        "social_registry_custom_fields",
        "g2p_enumerator",
    ],
    "data": [
        "views/individual_form_custom.xml",
        "views/res_users_views_extension.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_registry_individual_custom_ui/static/src/css/hide_new_button.css",
            "g2p_registry_individual_custom_ui/static/src/js/user_menu.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

