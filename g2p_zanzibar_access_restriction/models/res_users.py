from odoo import models, api, _
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class Groups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _update_user_groups_view(self):
        """Override to move specific categories out of the hidden 'xml4' group."""
        super()._update_user_groups_view()
        view = self.env.ref("base.user_groups_view", raise_if_not_found=False)
        if view and view.arch:
            try:
                arch = etree.fromstring(view.arch)
                # Find the group that Odoo core uses for boolean categories (xml4)
                # In Odoo 17, it's typically the last group and has groups="base.group_no_one"
                debug_groups = arch.xpath("//group[@groups='base.group_no_one']")
                if not debug_groups:
                    return

                # Target sections to make visible
                targets = ["OpenG2P Module Access", "OpenG2P Documents Module"]
                
                # Check each debug group (usually there's only one for xml4)
                for debug_group in debug_groups:
                    # Look for separators with these names
                    to_move = []
                    found_target = False
                    for child in debug_group:
                        if child.tag == "separator" and child.get("string") in targets:
                            found_target = True
                            to_move.append(child)
                            # Identify following groups for this separator
                            # Odoo usually adds 1 or 2 groups after a separator for boolean fields
                            current = child.getnext()
                            count = 0
                            while current is not None and current.tag == "group" and count < 2:
                                to_move.append(current)
                                current = current.getnext()
                                count += 1
                    
                    if to_move:
                        # Create a new group container without the base.group_no_one restriction
                        new_group = etree.Element("group", {"colspan": "4"})
                        for node in to_move:
                            new_group.append(node)
                        # Insert it before the debug group
                        debug_group.addprevious(new_group)
                
                # Write back the modified arch
                new_arch = etree.tostring(arch, encoding='unicode', pretty_print=True)
                view.sudo().write({'arch': new_arch})
            except Exception as e:
                _logger.error("Failed to post-process user groups view: %s", e)
