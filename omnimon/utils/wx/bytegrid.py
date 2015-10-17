import sys
import wx

import wx.grid as Grid

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class ByteGridRenderer(Grid.PyGridCellRenderer):
    def __init__(self, table, color="black", font="", fontsize=8):
        """Render data in the specified color and font and fontsize"""
        Grid.PyGridCellRenderer.__init__(self)
        self.table = table
        self.color = color
        self.font = wx.Font(fontsize, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, font)
        self.selectedBrush = wx.Brush("blue", wx.SOLID)
        self.normalBrush = wx.Brush(wx.WHITE, wx.SOLID)
        self.colSize = None
        self.rowSize = 50

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        # Here we draw text in a grid cell using various fonts
        # and colors.  We have to set the clipping region on
        # the grid's DC, otherwise the text will spill over
        # to the next cell
        dc.SetClippingRect(rect)

        # clear the background
        dc.SetBackgroundMode(wx.SOLID)
        
        index = self.table.get_index(row, col)
        if not self.table.is_index_valid(index):
            dc.SetBrush(wx.Brush(wx.WHITE, wx.SOLID))
            dc.SetPen(wx.Pen(wx.WHITE, 1, wx.SOLID))
            dc.DrawRectangleRect(rect)
        else:
            start, end = grid.anchor_index, grid.end_index
            if start > end:
                start, end = end, start
#            print "r,c,index", row, col, index, "grid selection:", start, end
            is_in_range = start <= index <= end
            if is_in_range:
                dc.SetBrush(wx.Brush(wx.BLUE, wx.SOLID))
                dc.SetPen(wx.Pen(wx.BLUE, 1, wx.SOLID))
            else:
                dc.SetBrush(wx.Brush(wx.WHITE, wx.SOLID))
                dc.SetPen(wx.Pen(wx.WHITE, 1, wx.SOLID))
            dc.DrawRectangleRect(rect)

            text = self.table.GetValue(row, col)
            dc.SetBackgroundMode(wx.SOLID)

            # change the text background based on whether the grid is selected
            # or not
            if is_in_range:
                dc.SetBrush(self.selectedBrush)
                dc.SetTextBackground("blue")
            else:
                dc.SetBrush(self.normalBrush)
                dc.SetTextBackground("white")

            dc.SetTextForeground(self.color)
            dc.SetFont(self.font)
            dc.DrawText(text, rect.x+1, rect.y+1)

            # Okay, now for the advanced class :)
            # Let's add three dots "..."
            # to indicate that that there is more text to be read
            # when the text is larger than the grid cell

            width, height = dc.GetTextExtent(text)
            
            if width > rect.width-2:
                width, height = dc.GetTextExtent("...")
                x = rect.x+1 + rect.width-2 - width
                dc.DrawRectangle(x, rect.y+1, width+1, height)
                dc.DrawText("...", x, rect.y+1)

        dc.DestroyClippingRegion()


class ByteGridTable(Grid.PyGridTableBase):
    column_labels = [""]
    column_sizes = [4]
    
    def __init__(self):
        Grid.PyGridTableBase.__init__(self)
        
        self._rows = 1
        self._cols = len(self.column_labels)
    
    def get_index(self, r, c):
        return r
    
    def is_index_valid(self, index):
        return index < self._rows
    
    def get_col_size(self, c):
        return self.column_sizes[c]
   
    def GetNumberRows(self):
        return self._rows

    def GetRowLabelValue(self, row):
        raise NotImplementedError

    def GetNumberCols(self):
        return self._cols

    def GetColLabelValue(self, col):
        return self.column_labels[col]
    
    def GetValue(self, row, col):
        raise NotImplementedError

    def SetValue(self, row, col, value):
        raise NotImplementedError

    def ResetViewProcessArgs(self, *args):
        pass

    def ResetView(self, grid, *args):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        oldrows=self._rows
        oldcols=self._cols
        self.ResetViewProcessArgs(*args)
        
        grid.BeginBatch()

        for current, new, delmsg, addmsg in [
            (oldrows, self._rows, Grid.GRIDTABLE_NOTIFY_ROWS_DELETED, Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (oldcols, self._cols, Grid.GRIDTABLE_NOTIFY_COLS_DELETED, Grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:

            if new < current:
                msg = Grid.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = Grid.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)
        grid.EndBatch()

        # update the scrollbars and the displayed part of the grid
        dc = wx.MemoryDC()
        dc.SetFont(grid.font)
        (width, height) = dc.GetTextExtent("M")
        grid.SetDefaultRowSize(height)
        grid.SetColMinimalAcceptableWidth(width)
        grid.SetRowMinimalAcceptableHeight(height + 1)

        for col in range(self._cols):
            # Can't share GridCellAttrs among columns; causes crash when
            # freeing them.  So, have to individually allocate the attrs for
            # each column
            hexattr = Grid.GridCellAttr()
            hexattr.SetFont(grid.font)
            hexattr.SetBackgroundColour("white")
            renderer = ByteGridRenderer(self)
            hexattr.SetRenderer(renderer)
            log.debug("hexcol %d width=%d" % (col,width))
            grid.SetColMinimalWidth(col, 0)
            grid.SetColSize(col, (width * self.get_col_size(col)) + 4)
            grid.SetColAttr(col, hexattr)

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        
        dc.SetFont(grid.label_font)
        (width, height) = dc.GetTextExtent("M")
        grid.SetColLabelSize(height + 4)
        digits = len(hex(self._rows)) - 2
        grid.SetRowLabelSize(width * digits + 4)
        
        grid.AdjustScrollbars()
        grid.ForceRefresh()

    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = Grid.GridTableMessage(self, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)


class HexDigitMixin(object):
    keypad=[ wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3, 
             wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7, 
             wx.WXK_NUMPAD8, wx.WXK_NUMPAD9
             ]
    
    def isValidHexDigit(self,key):
        return key in HexDigitMixin.keypad or (key>=ord('0') and key<=ord('9')) or (key>=ord('A') and key<=ord('F')) or (key>=ord('a') and key<=ord('f'))

    def getValidHexDigit(self,key):
        if key in HexDigitMixin.keypad:
            return chr(ord('0') + key - wx.WXK_NUMPAD0)
        elif (key>=ord('0') and key<=ord('9')) or (key>=ord('A') and key<=ord('F')) or (key>=ord('a') and key<=ord('f')):
            return chr(key)
        else:
            return None


class HexTextCtrl(wx.TextCtrl,HexDigitMixin):
    def __init__(self,parent,id,parentgrid):
        # Don't use the validator here, because apparently we can't
        # reset the validator based on the columns.  We have to do the
        # validation ourselves using EVT_KEY_DOWN.
        wx.TextCtrl.__init__(self,parent, id,
                             style=wx.TE_PROCESS_TAB|wx.TE_PROCESS_ENTER)
        log.debug("parent=%s" % parent)
        self.SetInsertionPoint(0)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.parentgrid=parentgrid
        self.setMode('hex')
        self.startValue=None

    def setMode(self, mode):
        self.mode=mode
        if mode=='hex':
            self.SetMaxLength(2)
            self.autoadvance=2
        elif mode=='char':
            self.SetMaxLength(1)
            self.autoadvance=1
        else:
            self.SetMaxLength(0)
            self.autoadvance=0
        self.userpressed=False

    def editingNewCell(self, value, mode='hex'):
        """
        Begin editing a new cell by determining the edit mode and
        setting the initial value.
        """
        # Set the mode before setting the value, otherwise OnText gets
        # triggered before self.userpressed is set to false.  When
        # operating in char mode (i.e. autoadvance=1), this causes the
        # editor to skip every other cell.
        self.setMode(mode)
        self.startValue=value
        self.SetValue(value)
        self.SetFocus()
        self.SetInsertionPoint(0)
        self.SetSelection(-1, -1) # select the text

    def insertFirstKey(self, key):
        """
        Check for a valid initial keystroke, and insert it into the
        text ctrl if it is one.

        @param key: keystroke
        @type key: int

        @returns: True if keystroke was valid, False if not.
        """
        ch=None
        if self.mode=='hex':
            ch=self.getValidHexDigit(key)
        elif key>=wx.WXK_SPACE and key<=255:
            ch=chr(key)

        if ch is not None:
            # set self.userpressed before SetValue, because it appears
            # that the OnText callback happens immediately and the
            # keystroke won't be flagged as one that the user caused.
            self.userpressed=True
            self.SetValue(ch)
            self.SetInsertionPointEnd()
            return True

        return False

    def OnKeyDown(self, evt):
        """
        Keyboard handler to process command keys before they are
        inserted.  Tabs, arrows, ESC, return, etc. should be handled
        here.  If the key is to be processed normally, evt.Skip must
        be called.  Otherwise, the event is eaten here.

        @param evt: key event to process
        """
        log.debug("key down before evt=%s" % evt.GetKeyCode())
        key=evt.GetKeyCode()
        
        if key==wx.WXK_TAB:
            wx.CallAfter(self.parentgrid.advanceCursor)
            return
        if key==wx.WXK_ESCAPE:
            self.SetValue(self.startValue)
            wx.CallAfter(self.parentgrid.abortEdit)
            return
        elif self.mode=='hex':
            if self.isValidHexDigit(key):
                self.userpressed=True
        elif self.mode!='hex':
            self.userpressed=True
        evt.Skip()
        
    def OnText(self, evt):
        """
        Callback used to automatically advance to the next edit field.
        If self.autoadvance > 0, this number is used as the max number
        of characters in the field.  Once the text string hits this
        number, the field is processed and advanced to the next
        position.
        
        @param evt: CommandEvent
        """
        log.debug("evt=%s str=%s cursor=%d" % (evt,evt.GetString(),self.GetInsertionPoint()))
        
        # NOTE: we check that GetInsertionPoint returns 1 less than
        # the desired number because the insertion point hasn't been
        # updated yet and won't be until after this event handler
        # returns.
        if self.autoadvance and self.userpressed:
            if len(evt.GetString())>=self.autoadvance and self.GetInsertionPoint()>=self.autoadvance-1:
                # FIXME: problem here with a bunch of really quick
                # keystrokes -- the interaction with the
                # underlyingSTCChanged callback causes a cell's
                # changes to be skipped over.  Need some flag in grid
                # to see if we're editing, or to delay updates until a
                # certain period of calmness, or something.
                wx.CallAfter(self.parentgrid.advanceCursor)


class HexCellEditor(Grid.PyGridCellEditor,HexDigitMixin):
    """
    Cell editor for the grid, based on GridCustEditor.py from the
    wxPython demo.
    """
    def __init__(self,grid):
        Grid.PyGridCellEditor.__init__(self)
        self.parentgrid=grid

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        log.debug("")
        self._tc = HexTextCtrl(parent, id, self.parentgrid)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        log.debug("rect=%s\n" % rect)
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        log.debug("show=%s, attr=%s" % (show, attr))
        Grid.PyGridCellEditor.Show(self, show, attr)

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        log.debug("MyCellEditor: PaintBackground\n")

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        log.debug("row,col=(%d,%d)" % (row, col))
        self.startValue = grid.GetTable().GetValue(row, col)
        mode='hex'
        table=self.parentgrid.table
        textcol=table.getTextCol(col)
        if textcol>=0:
            textfmt=table.types[textcol]
            if textfmt.endswith('s') or textfmt.endswith('c'):
                if table.sizes[textcol]==1:
                    mode='char'
                else:
                    mode='str'
            else:
                mode='text'
            log.debug("In value area! mode=%s" % mode)
        self._tc.editingNewCell(self.startValue,mode)

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        log.debug("row,col=(%d,%d)" % (row, col))
        changed = False

        val = self._tc.GetValue()
        
        if val != self.startValue:
            changed = True
            grid.GetTable().SetValue(row, col, val) # update the table

        self.startValue = ''
        self._tc.SetValue('')
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        log.debug("")
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        log.debug("keycode=%d" % (evt.GetKeyCode()))

        ## We can ask the base class to do it
        #return self.base_IsAcceptedKey(evt)

        # or do it ourselves
        return (not (evt.ControlDown() or evt.AltDown()) and
                evt.GetKeyCode() != wx.WXK_SHIFT)

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        log.debug("keycode=%d" % evt.GetKeyCode())
        key = evt.GetKeyCode()
        if not self._tc.insertFirstKey(key):
            evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        log.debug("")

    def Destroy(self):
        """final cleanup"""
        log.debug("")
        Grid.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        log.debug("")
        return HexCellEditor(self.parentgrid)

    
class ByteGrid(Grid.Grid):
    """
    View for editing in hexidecimal notation.
    """

    def __init__(self, parent, task, table):
        """Create the HexEdit viewer
        """
        Grid.Grid.__init__(self, parent, -1)
        self.task = task
        self.table = table
        self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
        self.label_font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.FONTWEIGHT_BOLD)
        self.SetLabelFont(self.label_font)

        # The second parameter means that the grid is to take
        # ownership of the table and will destroy it when done.
        # Otherwise you would need to keep a reference to it and call
        # its Destroy method later.
        self.SetTable(self.table, True)
        self.SetMargins(0,0)
        self.SetColMinimalAcceptableWidth(10)
        self.EnableDragGridSize(False)
        self.DisableDragRowSize()

        self.RegisterDataType(Grid.GRID_VALUE_STRING, None, None)
#        self.SetDefaultEditor(HexCellEditor(self))

        self.anchor_index = None
        self.end_index = None
        self.allow_range_select = True
        self.updateUICallback = None
        self.Bind(Grid.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftDown)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(Grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)
#        self.Bind(Grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
#        self.Bind(Grid.EVT_GRID_RANGE_SELECT, self.OnSelectRange)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Show(True)

    def OnRightDown(self, evt):
        log.debug(self.GetSelectedRows())

    def OnLeftDown(self, evt):
        c, r = (evt.GetCol(), evt.GetRow())
        self.ClearSelection()
        self.anchor_index = self.table.get_index(r, c)
        self.end_index = self.anchor_index
        print "down: cell", (c, r)
        evt.Skip()
        wx.CallAfter(self.ForceRefresh)
        wx.CallAfter(self.task.active_editor.byte_clicked, self.anchor_index, 0, self.table.segment.start_addr, self)
 
    def on_motion(self, evt):
        if self.anchor_index is not None and evt.LeftIsDown():
            x, y = evt.GetPosition()
            x, y = self.CalcUnscrolledPosition(x, y)
            r, c = self.XYToCell(x, y)
            index = self.table.get_index(r, c)
            if index != self.end_index:
                self.end_index = index
                wx.CallAfter(self.ForceRefresh)
                wx.CallAfter(self.task.active_editor.byte_clicked, self.end_index, 0, self.table.segment.start_addr, self)
            print "motion: x, y, index", x, y, index
        evt.Skip()

    def OnSelectCell(self, evt):
        print "cell selected:", evt.GetCol(), evt.GetRow()
        evt.Skip()

    def OnKeyDown(self, evt):
        log.debug("evt=%s" % evt)
        if evt.GetKeyCode() == wx.WXK_RETURN or evt.GetKeyCode()==wx.WXK_TAB:
            if evt.ControlDown():   # the edit control needs this key
                evt.Skip()
            else:
                self.DisableCellEditControl()
                if evt.ShiftDown():
                    (row,col)=self.table.getPrevCursorPosition(self.GetGridCursorRow(),self.GetGridCursorCol())
                else:
                    (row,col)=self.table.getNextCursorPosition(self.GetGridCursorRow(),self.GetGridCursorCol())
                self.SetGridCursor(row,col)
                self.MakeCellVisible(row,col)
        else:
            evt.Skip()

    def abortEdit(self):
        self.DisableCellEditControl()

    def advanceCursor(self):
        self.DisableCellEditControl()
        # FIXME: moving from the hex region to the value region using
        # self.MoveCursorRight(False) causes a segfault, so make sure
        # to stay in the same region
        (row,col)=self.table.getNextCursorPosition(self.GetGridCursorRow(),self.GetGridCursorCol())
        self.SetGridCursor(row,col)
        self.EnableCellEditControl()
    
    def pos_to_row(self, pos):
        addr = pos + self.table.start_addr
        addr_map = self.table.addr_to_lines
        if addr in addr_map:
            index = addr_map[addr]
        else:
            index = 0
            for a in range(addr - 1, addr - 5, -1):
                if a in addr_map:
                    index = addr_map[a]
                    break
        print "addr %s -> index=%d" % (addr, index)
        return index

    def select_pos(self, pos):
        print "make %s visible in disassembly!" % pos
        row = self.pos_to_row(pos)
        self.select_range(row, row)
        self.SetGridCursor(row, 0)
        self.MakeCellVisible(row, 0)
    
    def select_range(self, start, end):
        self.ClearSelection()
        self.anchor_index = start
        self.end_index = end
        self.ForceRefresh()
