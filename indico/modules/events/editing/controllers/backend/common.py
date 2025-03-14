# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session

from indico.core import signals
from indico.modules.events.editing.controllers.base import RHEditableTypeEditorBase, RHEditingBase
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.schemas import EditingFileTypeSchema, EditingMenuItemSchema, EditingTagSchema
from indico.modules.events.editing.settings import editable_type_settings
from indico.util.signals import named_objects_from_signal


class RHEditingFileTypes(RHEditingBase):
    """Return all editing file types defined in the event for the editable type."""

    SERVICE_ALLOWED = True

    def _process_args(self):
        RHEditingBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]
        self.editing_file_types = EditingFileType.query.with_parent(self.event).filter_by(type=self.editable_type).all()

    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.editing_file_types)


class RHEditingTags(RHEditingBase):
    """Return all editing tags defined in the event."""

    SERVICE_ALLOWED = True

    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)


class RHMenuEntries(RHEditingBase):
    """Return the menu entries for the editing view."""

    def _process(self):
        menu_entries = sorted(
            named_objects_from_signal(signals.menu.items.send('event-editing-sidemenu', event=self.event)).values(),
            key=lambda x: (-x.weight, x.title),
        )
        is_editing_manager = self.event.can_manage(session.user, permission='editing_manager')
        show_editable_list = {
            et.name: (is_editing_manager or self.event.can_manage(session.user, et.editor_permission))
            for et in EditableType
        }
        return jsonify(
            items=EditingMenuItemSchema(many=True).dump(menu_entries),
            show_management_link=is_editing_manager,
            show_editable_list=show_editable_list
        )


class RHEditableCheckSelfAssign(RHEditableTypeEditorBase):
    """Check if editor is allowed to self-assign."""

    def _process(self):
        return jsonify(editable_type_settings[self.editable_type].get(self.event, 'self_assign_allowed'))
