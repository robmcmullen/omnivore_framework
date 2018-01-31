import os
import sys

import wx

from traits.api import on_trait_change, Bool

from atrcopy import match_bit_mask, comment_bit_mask, user_bit_mask, selected_bit_mask, diff_bit_mask

from ..ui.segment_grid import SegmentGridControl
from omnivore.utils.wx import compactgrid as cg
from omnivore8bit.arch.disasm import get_style_name

from ..byte_edit.actions import GotoIndexAction
from ..byte_edit.commands import ChangeByteCommand

from . import SegmentViewer

import logging
log = logging.getLogger(__name__)


class SegmentTable(cg.HexTable):
    def __init__(self, linked_base):
        self.segment = linked_base.segment
        cg.HexTable.__init__(self, self.segment.data, self.segment.style, 16, self.segment.start_addr, col_widths=None, start_offset_mask=0x0f)

    def get_label_at_index(self, index):
        # Can't just return hex value of index because some segments (like the
        # raw sector segment) use different labels
        return self.segment.label(index, True)


class HexEditControl(SegmentGridControl):
    """
    View for editing in hexidecimal notation.
    """
    short_name = "hex"

    def recalc_view(self):
        table = SegmentTable(self.segment_viewer.linked_base)
        self.main.recalc_view(table, self.segment_viewer.linked_base.cached_preferences)

    def change_value(self, row, col, text):
        """Called after editor has provided a new value for a cell.
        
        Can use this to override the default handler.  Return True if the grid
        should be updated, or False if the value is invalid or the grid will
        be updated some other way.
        """
        try:
            val = int(text,16)
            if val >= 0 and val < 256:
                start, end = self.table.get_index_range(row, col)
                if self.table.is_index_valid(start):
                    cmd = ChangeByteCommand(self.table.segment, start, end, val)
                    self.linked_base.editor.process_command(cmd)
        except ValueError:
            pass
        return False

    def get_goto_actions(self, r, c):
        actions = []
        addr_dest = self.table.get_addr_dest(r, c)
        actions.extend(self.segment_viewer.linked_base.get_goto_actions_other_segments(addr_dest))
        index, _ = self.table.get_index_range(r, c)
        actions.extend(self.segment_viewer.linked_base.get_goto_actions_same_byte(index))
        return actions

    def get_popup_actions(self, r, c, inside):
        if not inside:
            actions = []
        else:
            actions = self.get_goto_actions(r, c)
            if actions:
                actions.append(None)
        actions.extend(self.segment_viewer.common_popup_actions())
        return actions


class HexEditViewer(SegmentViewer):
    name = "hex"

    pretty_name = "Hex"

    has_hex = True

    @classmethod
    def create_control(cls, parent, linked_base):
        return HexEditControl(parent, linked_base.segment, linked_base, linked_base.cached_preferences)

    def recalc_data_model(self):
        """Rebuild the data model after a document formatting (or other
        structural change) or loading a new document.
        """
        self.control.recalc_view()

    def update_carets(self, flags):
        self.control.caret_indexes_to_display_coords()