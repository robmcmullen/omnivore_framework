import sys

import wx

# Enthought library imports.
from envisage.ui.tasks.api import PreferencesPane, TaskFactory
from apptools.preferences.api import PreferencesHelper
from traits.api import Bool, Dict, Enum, List, Str, Unicode, Int, Font, Range, Tuple, Color, Any
from traitsui.api import FontEditor, HGroup, VGroup, Item, Label, \
    View, RangeEditor, ColorEditor

if sys.platform == "darwin":
    def_font = "10 point Monaco"
elif sys.platform == "win32":
    def_font = "10 point Lucida Console"
else:
    def_font = "10 point monospace"


class ByteEditPreferences(PreferencesHelper):
    """ The preferences helper for the Framework application.
    """

    #### 'PreferencesHelper' interface ########################################

    # The path to the preference node that contains the preferences.
    preferences_path = 'omnivore.task.byte_edit'

    #### Preferences ##########################################################

    map_width_low = 1
    map_width_high = 256
    map_width = Range(low=map_width_low, high=map_width_high, value=16)

    bitmap_width_low = 1
    bitmap_width_high = 16
    bitmap_width = Range(low=bitmap_width_low, high=bitmap_width_high, value=1)

    # Font used for hex/disassembly
    text_font = Font(def_font)

    header_font = Font(def_font + " bold")

    hex_grid_lower_case = Bool(True)

    assembly_lower_case = Bool(False)

    disassembly_column_widths = Tuple(0, 0, 0)

    background_color = Color(wx.WHITE)

    text_color = Color(wx.BLACK)

    highlight_color = Color(wx.Colour(100, 200, 230))

    data_color = Color(wx.Colour(224, 224, 224))

    empty_color = Color(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get(False))

    match_background_color = Color(wx.Colour(255, 255, 180))

    comment_background_color = Color(wx.Colour(255, 180, 200))

    diff_text_color = Color(wx.Colour(255, 0, 0))

    unfocused_cursor_color = Color(wx.Colour(128, 128, 128))
    
    row_header_bg_color = Color(wx.Colour(224, 224, 224))
    
    col_header_bg_color = Color(wx.Colour(224, 224, 224))

    col_label_border_width = Int(3)

    row_label_border_width = Int(3)

    row_height_extra_padding = Int(-3)

    base_cell_width_in_chars = Int(2)

    pixel_width_padding = Int(2)
    
    cursor_pen = Any

    selected_brush = Any
    
    selected_pen = Any
    
    normal_brush = Any
    
    normal_pen = Any
    
    data_brush = Any
    
    match_brush = Any
    
    match_pen = Any
    
    comment_brush = Any
    
    comment_pen = Any

    def _cursor_pen_default(self):
        return wx.Pen(self.unfocused_cursor_color, 1, wx.SOLID)

    def _selected_brush_default(self):
        return wx.Brush(self.highlight_color, wx.SOLID)

    def _selected_pen_default(self):
        return wx.Pen(self.highlight_color, 1, wx.SOLID)

    def _normal_brush_default(self):
        return wx.Brush(self.background_color, wx.SOLID)

    def _normal_pen_default(self):
        return wx.Pen(self.background_color, 1, wx.SOLID)

    def _data_brush_default(self):
        return wx.Brush(self.data_color, wx.SOLID)

    def _match_brush_default(self):
        return wx.Brush(self.match_background_color, wx.SOLID)

    def _match_pen_default(self):
        return wx.Pen(self.match_background_color, 1, wx.SOLID)

    def _comment_brush_default(self):
        return wx.Brush(self.comment_background_color, wx.SOLID)

    def _comment_pen_default(self):
        return wx.Pen(self.comment_background_color, 1, wx.SOLID)





class ByteEditPreferencesPane(PreferencesPane):
    """ The preferences pane for the Framework application.
    """

    #### 'PreferencesPane' interface ##########################################

    # The factory to use for creating the preferences model object.
    model_factory = ByteEditPreferences

    category = Str('Editors')

    #### 'FrameworkPreferencesPane' interface ################################

    # Note the quirk in the RangeEditor: specifying a custom editor is
    # supposed to take the defaults from the item name specified, but I
    # can't get it to work with only the "mode" parameter.  I have to specify
    # all the other params, and the low/high values have to be attributes
    # in ByteEditPreferences, not the values in the trait itself.  See
    # traitsui/editors/range_editor.py
    view = View(
        VGroup(HGroup(Item('map_width', editor=RangeEditor(mode="spinner", is_float=False, low_name='map_width_low', high_name='map_width_high')),
                      Label('Default Character Map Width (in bytes)'),
                      show_labels = False),
               HGroup(Item('bitmap_width', editor=RangeEditor(mode="spinner", is_float=False, low_name='bitmap_width_low', high_name='bitmap_width_high')),
                      Label('Default Bitmap Width (in bytes)'),
                      show_labels = False),
               HGroup(Item('text_font'),
                      Label('Hex Display Font'),
                      show_labels = False),
               HGroup(Item('header_font'),
                      Label('Column Header Font'),
                      show_labels = False),
               HGroup(Item('hex_grid_lower_case'),
                      Label('Use Lower Case for Hex Digits'),
                      show_labels = False),
               HGroup(Item('assembly_lower_case'),
                      Label('Use Lower Case for Assembler Mnemonics'),
                      show_labels = False),
               HGroup(Item('highlight_color', editor=ColorEditor(), style='custom'),
                      Label('Highlight Color'),
                      show_labels = False),
               label='Hex Editor'),
        resizable=True)
