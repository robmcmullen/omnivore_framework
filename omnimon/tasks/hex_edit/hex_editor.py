# Standard library imports.
import sys
import os

# Major package imports.
import wx
import numpy as np

# Enthought library imports.
from traits.api import Any, Bool, Int, Str, List, Event, Enum, Instance, File, Unicode, Property, provides
from pyface.key_pressed_event import KeyPressedEvent

# Local imports.
from omnimon.framework.editor import FrameworkEditor
from omnimon.framework.document import Document
from grid_control import HexEditControl
from omnimon.utils.file_guess import FileMetadata
import omnimon.utils.wx.fonts as fonts
import omnimon.utils.colors as colors
from omnimon.utils.dis6502 import Atari800Disassembler
from omnimon.utils.binutil import known_segment_parsers, ATRSegmentParser, XexSegmentParser, DefaultSegment

from commands import PasteCommand


class HexEditor(FrameworkEditor):
    """ The toolkit specific implementation of a HexEditor.  See the
    IHexEditor interface for the API documentation.
    """

    #### 'IPythonEditor' interface ############################################

    obj = Instance(File)

    #### traits
    
    grid_range_selected = Bool
    
    segment_parser = Any
    
    segment_number = Int(0)
    
    ### View traits
    
    antic_font_data = Any
    
    antic_font = Any
    
    font_mode = Enum(2, 4, 5, 6, 7, 8, 9)
    
    playfield_colors = Any
    
    disassembler = Any
    
    segment = Any(None)
    
    highlight_color = Any((100, 200, 230))
    
    background_color = Any((255, 255, 255))
    
    text_color = Any((0, 0, 0))
    
    empty_color = Any(None)
    
    text_font_size = Int(9)
    
    text_font_face = Str("")
    
    text_font = Any(None)

    #### Events ####

    changed = Event

    key_pressed = Event(KeyPressedEvent)
    
    # Class attributes (not traits)
    
    font_list = None
    
    ##### Default traits
    
    def _disassembler_default(self):
        return Atari800Disassembler
    
    def _segment_default(self):
        return DefaultSegment()
    
    def _text_font_default(self):
        return wx.Font(self.text_font_size, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, self.text_font_face)
    
    def _antic_font_data_default(self):
        return fonts.A8DefaultFont
    
    def _font_mode_default(self):
        return 2  # Antic mode 2, Graphics 0
    
    def _playfield_colors_default(self):
        return colors.powerup_colors()

    ###########################################################################
    # 'FrameworkEditor' interface.
    ###########################################################################

    def create(self, parent):
        self.control = self._create_control(parent)
        self.init_fonts(self.window.application)
        self.task.fonts_changed = self.font_list

    def rebuild_document_properties(self):
        self.find_segment_parser([ATRSegmentParser, XexSegmentParser])
    
    def process_paste_data_object(self, data_obj):
        bytes = self.get_numpy_from_data_object(data_obj)
        cmd = PasteCommand(self.segment, self.anchor_start_index, self.anchor_end_index, bytes)
        self.process_command(cmd)
    
    def get_numpy_from_data_object(self, data_obj):
        if wx.DF_TEXT in data_obj.GetAllFormats():
            value = data_obj.GetText()
        else:
            value = data_obj.GetData()
        bytes = np.fromstring(value, dtype=np.uint8)
        return bytes
    
    def create_clipboard_data_object(self):
        if self.anchor_start_index != self.anchor_end_index:
            data = self.segment[self.anchor_start_index:self.anchor_end_index]
            data_obj = wx.CustomDataObject("numpy")
            data_obj.SetData(data.tostring())
            print "Created data obj", data_obj, "for", data
            return data_obj
        return None
    
    def get_supported_clipboard_data_objects(self):
        return [wx.CustomDataObject("numpy"), wx.TextDataObject()]

    def update_panes(self):
        self.segment = self.document.segments[self.segment_number]
        self.set_colors()
        self.refresh_panes()
        self.update_segments_ui()
    
    def update_segments_ui(self):
        self.segment_list.set_segments(self.document.segments, self.segment_number)
        self.task.segments_changed = self.document.segments
    
    def refresh_panes(self):
        self.control.recalc_view()
        self.disassembly.recalc_view()
        self.byte_graphics.recalc_view()
        self.font_map.recalc_view()
        self.memory_map.recalc_view()
    
    def set_colors(self):
        if self.empty_color is None:
            attr = self.control.GetDefaultAttributes()
            self.empty_color = attr.colBg.Get(False)
    
    def update_colors(self, colors):
        if len(colors) == 5:
            self.playfield_colors = colors
        else:
            self.playfield_colors = colors[4:9]
        self.set_font()
        self.refresh_panes()
    
    def update_fonts(self):
        self.font_map.Refresh()
        pane = self.window.get_dock_pane('hex_edit.font_map')
        pane.name = self.font_map.get_font_mapping_name()
        self.window._aui_manager.Update()
        
    @classmethod
    def init_fonts(cls, application):
        if cls.font_list is None:
            try:
                cls.font_list = application.get_bson_data("font_list")
            except IOError:
                # file not found
                cls.font_list = []
            except ValueError:
                # bad JSON format
                cls.font_list = []
    
    def remember_fonts(self):
        self.window.application.save_bson_data("font_list", self.font_list)
    
    def get_antic_font(self):
        return fonts.AnticFont(self.antic_font_data, self.font_mode, self.playfield_colors, self.highlight_color)
    
    def set_font(self, font=None, font_mode=None):
        print font
        if font is None:
            font = self.antic_font_data
        if font_mode is None:
            font_mode = self.font_mode
        self.font_mode = font_mode
        self.antic_font_data = font
        self.antic_font = self.get_antic_font()
        self.font_map.set_font()
        self.update_fonts()
    
    def load_font(self, filename):
        try:
            fh = open(filename, 'rb')
            data = fh.read() + "\0"*1024
            data = data[0:1024]
            font = {
                'name': os.path.basename(filename),
                'data': data,
                'char_w': 8,
                'char_h': 8,
                }
            self.set_font(font)
            self.font_list.append(font)
            self.remember_fonts()
            self.task.fonts_changed = self.font_list
        except:
            raise
    
    def get_font_from_selection(self):
        pass
    
    def set_disassembler(self, disassembler):
        self.disassembler = disassembler
        self.disassembly.recalc_view()
    
    def find_segment_parser(self, parsers):
        parser = self.document.parse_segments(parsers)
        self.segment_number = 0
        self.segment_parser = parser
        self.update_segments_ui()
        self.select_none(refresh=False)
    
    def set_segment_parser(self, parser):
        self.find_segment_parser([parser])
        self.update_panes()
    
    def view_segment_number(self, number):
        doc = self.document
        num = number if number < len(doc.segments) else 0
        if num != self.segment_number:
            new_segment = doc.segments[num]
            self.adjust_selection(self.segment, new_segment)
            self.segment = new_segment
            self.segment_number = num
            self.refresh_panes()
    
    def adjust_selection(self, current_segment, new_segment):
        """Adjust the selection of the current segment so that it is limited to the
        bounds of the new segment.
        
        If the current selection is entirely out of bounds of the new segment,
        all the selection indexes will be set to zero.
        """
        indexes = np.array([self.anchor_initial_start_index, self.anchor_start_index, self.anchor_initial_end_index, self.anchor_end_index], dtype=np.int64)
        
        # find byte index of view into master array
        current_offset = np.byte_bounds(current_segment.data)[0]
        new_offset = np.byte_bounds(new_segment.data)[0]
        
        delta = new_offset - current_offset
        indexes -= delta
        indexes.clip(0, len(new_segment), out=indexes)
        same = (indexes == indexes[0])
        if same.all():
            indexes = np.zeros(4, dtype=np.int64)
        self.anchor_initial_start_index, self.anchor_start_index, self.anchor_initial_end_index, self.anchor_end_index = list(indexes)
    
    def get_segment_from_selection(self):
        data = self.segment[self.anchor_start_index:self.anchor_end_index]
        segment = DefaultSegment(self.segment.start_addr + self.anchor_start_index, data)
        return segment
    
    def add_user_segment(self, segment):
        self.document.add_user_segment(segment)
        self.update_segments_ui()
    
    def ensure_visible(self, start, end):
        self.index_clicked(start, 0, None)
    
    def update_history(self):
#        history = document.undo_stack.serialize()
#        self.window.application.save_log(str(history), "command_log", ".log")
        self.undo_history.update_history()

    ###########################################################################
    # Trait handlers.
    ###########################################################################


    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_control(self, parent):
        """ Creates the toolkit-specific control for the widget. """

        # Base-class constructor.
        print "CONSTRUCTOR!!!"
        self.control = HexEditControl(parent, self.task)
        self.antic_font = self.get_antic_font()

        ##########################################
        # Events.
        ##########################################

        # Get related controls
        self.disassembly = self.window.get_dock_pane('hex_edit.disasmbly_pane').control
        self.byte_graphics = self.window.get_dock_pane('hex_edit.byte_graphics').control
        self.font_map = self.window.get_dock_pane('hex_edit.font_map').control
        self.memory_map = self.window.get_dock_pane('hex_edit.memory_map').control
        self.segment_list = self.window.get_dock_pane('hex_edit.segments').control
        self.undo_history = self.window.get_dock_pane('hex_edit.undo').control

        # Load the editor's contents.
        self.load()

        return self.control

    #### wx event handlers ####################################################
    
    def index_clicked(self, index, bit, control):
        if control != self.control:
            self.control.select_index(index)
        if control != self.disassembly:
            self.disassembly.select_index(index)
        if control != self.byte_graphics:
            self.byte_graphics.select_index(index)
        if control != self.font_map:
            self.font_map.select_index(index)
        if control != self.memory_map:
            self.memory_map.select_index(index)
        self.can_copy = (self.anchor_start_index != self.anchor_end_index)
