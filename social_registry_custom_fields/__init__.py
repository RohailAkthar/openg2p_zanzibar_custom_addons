from odoo.fields import Field
if not hasattr(Field, "ondelete"):
    Field.ondelete = None

from . import models
