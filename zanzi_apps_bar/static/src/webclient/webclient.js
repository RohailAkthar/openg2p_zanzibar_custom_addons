/** @odoo-module */

import {patch} from "@web/core/utils/patch";

import {WebClient} from "@web/webclient/webclient";
import {AppsBar} from "@zanzi_apps_bar/webclient/appsbar/appsbar";

patch(WebClient, {
    components: {
        ...WebClient.components,
        AppsBar,
    },
});
