{
    "name": "MuK AppsBar",
    "summary": "Adds a sidebar to the main screen",
    "description": """
        This module adds a sidebar to the main screen. The sidebar has a list
        of all installed apps similar to the home menu to ease navigation.
    """,
    "version": "17.0.1.1.2",
    "category": "Tools/UI",
    "license": "LGPL-3",
    "author": "MuK IT",
    "website": "https://openg2p.org",
    "live_test_url": "https://mukit.at/demo",
    "contributors": [
        "Mathias Markl <mathias.markl@mukit.at>",
    ],
    "depends": [
        "base_setup",
        "web",
    ],
    "data": [
        "templates/webclient.xml",
        "views/res_users.xml",
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "zanzi_apps_bar/static/src/scss/variables.scss",
        ],
        "web._assets_backend_helpers": [
            "zanzi_apps_bar/static/src/scss/mixins.scss",
        ],
        "web.assets_web_dark": [
            (
                "after",
                "zanzi_apps_bar/static/src/scss/variables.scss",
                "zanzi_apps_bar/static/src/scss/variables.dark.scss",
            ),
        ],
        "web.assets_backend": [
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "zanzi_apps_bar/static/src/webclient/webclient.js",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.xml",
                "zanzi_apps_bar/static/src/webclient/webclient.xml",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "zanzi_apps_bar/static/src/webclient/menus/app_menu_service.js",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "zanzi_apps_bar/static/src/webclient/appsbar/appsbar.js",
            ),
            "zanzi_apps_bar/static/src/webclient/webclient.scss",
            "zanzi_apps_bar/static/src/webclient/appsbar/appsbar.xml",
            "zanzi_apps_bar/static/src/webclient/appsbar/appsbar.scss",
        ],
    },
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "_setup_module",
}
