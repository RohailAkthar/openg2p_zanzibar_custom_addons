{
    "name": "G2P Zanzibar: Access Restriction",
    "version": "17.0.1.0.0",
    "category": "G2P",
    "summary": "Restrict Archive and Disable features to Super Admin",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_registry_individual",
        "social_registry_custom_fields",
    ],
    "data": [
        "security/zanzibar_security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
