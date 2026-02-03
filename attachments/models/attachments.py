from odoo import models, fields, api
from odoo.addons.g2p_document_field.image_field import DocumentImageField

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    nominee_image = DocumentImageField(
        string="Relative / Nominee Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_nominee_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )
    zan_image = DocumentImageField(
        string="Zan ID Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_zan_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )
    beneficiary_image = DocumentImageField(
        string="Beneficiary Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_beneficiary_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )

    def _get_nominee_image_tags(self):
        return self.env.ref("attachments.document_tag_nominee_photo")

    def _get_zan_image_tags(self):
        return self.env.ref("attachments.document_tag_zan_id_photo")

    def _get_beneficiary_image_tags(self):
        return self.env.ref("attachments.document_tag_beneficiary_photo")