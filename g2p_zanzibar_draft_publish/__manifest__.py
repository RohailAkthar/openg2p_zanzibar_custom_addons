{
    "name": "OpenG2P Zanzibar Draft Publish",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_draft_publish",
        "social_registry_custom_fields",
        "g2p_registry_base",
        "g2p_social_registry_model",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/draft_records.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
