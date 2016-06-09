# Standard library imports.
import sys
import os

# Major package imports.
import wx
import numpy as np
from atrcopy import SegmentData, DefaultSegment

# Enthought library imports.
from traits.api import on_trait_change, Any, Bool, Int, Str, List, Event, Enum, Instance, File, Unicode, Property, provides
from pyface.key_pressed_event import KeyPressedEvent

# Local imports.
from omnivore import get_image_path
from omnivore.tasks.hex_edit.hex_editor import HexEditor
from omnivore.tasks.bitmap_edit.bitmap_editor import MainBitmapScroller, SelectMode, BitmapEditor
from omnivore.framework.document import Document
from omnivore.arch.machine import Machine, predefined
from omnivore.utils.wx.bitviewscroller import BitmapScroller
from omnivore.utils.command import Overlay
from omnivore.utils.searchutil import HexSearcher, CharSearcher
from omnivore.utils.drawutil import get_bounds
from omnivore.utils.sortutil import invert_rects
from omnivore.utils.jumpman import JumpmanLevelBuilder
from omnivore.tasks.hex_edit.commands import ChangeByteCommand, PasteCommand
from omnivore.framework.mouse_handler import MouseHandler

from commands import *

import logging
log = logging.getLogger(__name__)


class JumpmanLevelView(MainBitmapScroller):
    def __init__(self, *args, **kwargs):
        MainBitmapScroller.__init__(self, *args, **kwargs)
        self.level_builder = None

    def get_segment(self, editor):
        self.level_builder = JumpmanLevelBuilder(editor.document.user_segments)
        self.pick_buffer = editor.pick_buffer
        return editor.screen

    def clear_screen(self):
        self.segment[:] = 0
        self.pick_buffer[:] = -1

    def compute_image(self):
        if self.level_builder is None:
            return
        self.clear_screen()
        source = self.editor.segment
        start = source.start_addr
        if len(source) < 0x38:
            return
        index = source[0x38]*256 + source[0x37]
        log.debug("level def table: %x" % index)
        if index > start:
            index -= start
        if index < len(source):
            commands = source[index:index + 500]  # arbitrary max number of bytes
        else:
            commands = source[index:index]
        self.level_builder.draw_commands(self.segment, commands, current_segment=source, pick_buffer=self.pick_buffer)
        self.pick_buffer[self.pick_buffer >= 0] += index

    def get_image(self):
        self.compute_image()
        bitimage = MainBitmapScroller.get_image(self)
        self.mouse_mode.draw_overlay(bitimage)
        return bitimage

class JumpmanSelectMode(SelectMode):
    def draw_overlay(self, bitimage):
        return
    
    def get_xy(self, evt):
        c = self.canvas
        e = c.editor
        if e is not None:
            index, bit, inside = c.event_coords_to_byte(evt)
            r0, c0 = c.byte_to_row_col(index)
            x = c0 * 4 + (3 - bit)
            y = r0
            if y < e.antic_lines:
                pick = e.pick_buffer[x, y]
            else:
                pick = -1
            return index, x, y, pick
        return None, None, None, None


class AnticDSelectMode(JumpmanSelectMode):
    icon = "select.png"
    menu_item_name = "Select"
    menu_item_tooltip = "Select regions"

    def display_coords(self, evt, extra=None):
        c = self.canvas
        e = c.editor
        if e is not None:
            index, x, y, pick = self.get_xy(evt)
            msg = "x=%d (0x%x) y=%d (0x%x) index=%d (0x%x) pick=%d" % (x, x, y, y, index, index, pick)
            if extra:
                msg += " " + extra
            e.task.status_bar.message = msg

    def highlight_pick(self, evt):
        index, x, y, pick = self.get_xy(evt)
        if pick >= 0:
            e = self.canvas.editor
            e.index_clicked(pick, 0, None)
            e.select_range(pick, pick + 4)
            wx.CallAfter(e.index_clicked, pick, 0, None)

    def process_left_down(self, evt):
        self.highlight_pick(evt)
        self.display_coords(evt)

    def process_left_up(self, evt):
        self.display_coords(evt)

    def process_mouse_motion_down(self, evt):
        self.highlight_pick(evt)
        self.display_coords(evt)

    def process_mouse_motion_up(self, evt):
        self.display_coords(evt)


class PeanutCheckMode(JumpmanSelectMode):
    icon = "jumpman_peanut_check.png"
    menu_item_name = "Peanut Check"
    menu_item_tooltip = "Check for valid peanut positions"

    def __init__(self, *args, **kwargs):
        JumpmanSelectMode.__init__(self, *args, **kwargs)
        self.mouse_down = (0, 0)
        self.batch = None

    def get_harvest_offset(self):
        source = self.canvas.editor.segment
        if len(source) < 0x47:
            hx = hy = 0, 0
        else:
            hx = source[0x46]
            hy = source[0x47]
        return hx, hy

    def draw_overlay(self, bitimage):
        hx, hy = self.get_harvest_offset()
        w = 160
        h = 88
        bad = (203, 144, 161)
        orig = bitimage.copy()
        
        # Original (slow) algorithm to determine bad locations:
        #
        # def is_allergic(x, y, hx, hy):
        #     return (x + 0x30 + hx) & 0x1f < 7 or (2 * y + 0x20 + hy) & 0x1f < 5
        #
        # Note that in the originial 6502 code, the y coord is in player
        # coords, which is has twice the resolution of graphics 7. That's the
        # factor of two in the y part. Simplifying, the bad locations can be
        # defined in sets of 32 columns and 16 rows:
        #
        # x: 16 - hx, 16 - hx + 6 inclusive
        # y: 0 - hy/2, 0 - hy/2 + 2 inclusive
        hx = hx & 0x1f
        hy = (hy & 0x1f) / 2
        startx = (16 - hx) & 0x1f
        starty = (0 - hy) & 0xf

        # Don't know how to set multiple ranges simultaneously in numpy, so use
        # a slow python loop
        for x in range(startx, startx + 7):
            x = x & 0x1f
            bitimage[0:h:, x::32] = orig[0:h:, x::32] / 8 + bad
        for y in range(starty, starty + 3):
            y = y & 0xf
            bitimage[y:h:16,:] = orig[y:h:16,:] / 8 + bad

    def display_coords(self, evt, extra=None):
        c = self.canvas
        e = c.editor
        if e is not None:
            hx, hy = self.get_harvest_offset()
            msg = "harvest offset: x=%d (0x%x) y=%d (0x%x)" % (hx, hx, hy, hy)
            e.task.status_bar.message = msg

    def change_harvest_offset(self, evt, start=False):
        c = self.canvas
        e = c.editor
        if e is None:
            return
        index, x, y, pick = self.get_xy(evt)
        if start:
            self.batch = Overlay()
            hx, hy = self.get_harvest_offset()
            self.mouse_down = hx + x, hy + y
        else:
            dx = (self.mouse_down[0] - x) & 0x1f
            dy = (self.mouse_down[1] - y) & 0x1f
            self.display_coords(evt)
            values = [dx, dy]
            source = self.canvas.editor.segment
            cmd = ChangeByteCommand(source, 0x46, 0x48, values)
            e.process_command(cmd, self.batch)
        self.display_coords(evt)

    def process_left_down(self, evt):
        self.change_harvest_offset(evt, True)

    def process_left_up(self, evt):
        c = self.canvas
        e = c.editor
        if e is None:
            return
        e.end_batch()
        self.batch = None

        # Force updating of the hex view
        e.document.change_count += 1
        e.refresh_panes()

    def process_mouse_motion_down(self, evt):
        self.change_harvest_offset(evt)

    def process_mouse_motion_up(self, evt):
        self.display_coords(evt)


class JumpmanEditor(BitmapEditor):
    """ The toolkit specific implementation of a HexEditor.  See the
    IHexEditor interface for the API documentation.
    """
    ##### class attributes
    
    valid_mouse_modes = [AnticDSelectMode, PeanutCheckMode]
    
    ##### Default traits
    
    def _machine_default(self):
        return Machine(name="Jumpman", bitmap_renderer=predefined['bitmap_renderer'][2])

    def _map_width_default(self):
        return 40
    
    def _draw_pattern_default(self):
        return [0]

    ###########################################################################
    # 'FrameworkEditor' interface.
    ###########################################################################

    def process_extra_metadata(self, doc, e):
        HexEditor.process_extra_metadata(self, doc, e)
        pass
    
    @on_trait_change('machine.bitmap_change_event')
    def update_bitmap(self):
        self.hex_edit.recalc_view()
        self.bitmap.recalc_view()
    
    @on_trait_change('machine.font_change_event')
    def update_fonts(self):
        pass
    
    @on_trait_change('machine.disassembler_change_event')
    def update_disassembler(self):
        pass
    
    def reconfigure_panes(self):
        self.hex_edit.recalc_view()
        self.bitmap.recalc_view()
    
    def refresh_panes(self):
        self.hex_edit.refresh_view()
        self.bitmap.refresh_view()
    
    def rebuild_document_properties(self):
        self.bitmap.set_mouse_mode(AnticDSelectMode)
    
    def copy_view_properties(self, old_editor):
        self.find_segment(segment=old_editor.segment)
    
    def view_segment_set_width(self, segment):
        self.bitmap_width = 40
        colors = segment[0x2e:0x33].copy()
        # on some levels, the bombs are set to color 0 because they are cycled
        # to produce a glowing effect, but that's not visible here so we force
        # it to be bright white
        fg = colors[0:4]
        fg[fg == 0] = 15
        self.machine.update_colors(colors)
    
    def update_mouse_mode(self):
        self.bitmap.set_mouse_mode(self.mouse_mode)
        self.bitmap.refresh_view()
    
    def set_current_draw_pattern(self, pattern, control):
        try:
            iter(pattern)
        except TypeError:
            self.draw_pattern = [pattern]
        else:
            self.draw_pattern = pattern
        if control != self.tile_map:
            self.tile_map.clear_tile_selection()
        if control != self.character_set:
            self.character_set.clear_tile_selection()
    
    def highlight_selected_ranges(self):
        HexEditor.highlight_selected_ranges(self)

    def mark_index_range_changed(self, index_range):
        pass
    
    def perform_idle(self):
        pass
    
    def process_paste_data_object(self, data_obj, cmd_cls=None):
        # Don't use bitmap editor's paste, we want it to paste in hex
        return HexEditor.process_paste_data_object(self, data_obj, cmd_cls)
    
    def create_clipboard_data_object(self):
        # Don't use bitmap editor's clipboard, we want hex bytes
        return HexEditor.create_clipboard_data_object(self)
    
    def get_extra_segment_savers(self, segment):
        return []
    
    ###########################################################################
    # Trait handlers.
    ###########################################################################


    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_control(self, parent):
        """ Creates the toolkit-specific control for the widget. """

        # Base-class constructor.
        self.bitmap = JumpmanLevelView(parent, self.task)

        self.antic_lines = 90
        data = np.zeros(40 * self.antic_lines, dtype=np.uint8)
        data[::41] = 255
        r = SegmentData(data)
        self.screen = DefaultSegment(r, 0x7000)
        self.pick_buffer = np.zeros((160, self.antic_lines), dtype=np.int32)

        ##########################################
        # Events.
        ##########################################

        # Get related controls
        self.segment_list = self.window.get_dock_pane('jumpman.segments').control
        self.undo_history = self.window.get_dock_pane('jumpman.undo').control
        self.hex_edit = self.window.get_dock_pane('jumpman.hex').control

        # Load the editor's contents.
        self.load()

        return self.bitmap

    #### wx event handlers ####################################################
    
    def index_clicked(self, index, bit, control):
        self.cursor_index = index
        if control != self.hex_edit:
            self.hex_edit.select_index(index)
        self.can_copy = (self.anchor_start_index != self.anchor_end_index)
