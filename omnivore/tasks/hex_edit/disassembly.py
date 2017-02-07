import os
import sys
import wx

from atrcopy import match_bit_mask, comment_bit_mask, data_bit_mask, selected_bit_mask

from omnivore.utils.wx.bytegrid import ByteGridTable, ByteGrid, HexTextCtrl, HexCellEditor

from actions import GotoIndexAction
from commands import MiniAssemblerCommand

import logging
log = logging.getLogger(__name__)


class DisassemblyTable(ByteGridTable):
    column_labels = ["Bytes", "Disassembly", "Comment"]
    column_sizes = [11, 18, 30]
    
    def __init__(self):
        ByteGridTable.__init__(self)
        self.lines = None
        self._rows = 0
        self.index_to_row = []
        self.start_addr = 0
        self.chunk_size = 256
        self.disassembler = None
        self.use_labels_on_operands = False

    def set_editor(self, editor):
        self.editor = editor
        self.segment = segment = self.editor.segment
        self.lines = None
        self.index_to_row = []
        self._rows = 0
        self.disassembler = editor.machine.get_disassembler(editor.task.hex_grid_lower_case, editor.task.assembly_lower_case)
        disasm = self.disassembler.fast
        disasm.add_antic_dl_processor(1)
        disasm.add_data_processor(64)
        disasm.add_antic_dl_processor(65)
        self.hex_lower = editor.task.hex_grid_lower_case
        self.start_addr = segment.start_addr
        self.restart_disassembly(0)
    
    def restart_disassembly(self, index):
        pc = self.segment.start_addr
        self.lines = None

        # old format: (addr, bytes, opstr, comment, count, flag)
        self.disassembler.set_pc(self.segment, pc)
        last_pc = pc + len(self.segment)
        disasm = self.disassembler.fast
        r = self.segment.get_entire_style_ranges(data=True, user=1)
        info = disasm.get_all(self.segment.rawdata.unindexed_view, pc, 0, r)
        self.index_to_row = info.index
        self.lines = info
        self._rows = info.num_instructions
        self.jump_targets = info.labels
    
    def set_grid_cell_attr(self, grid, col, attr):
        ByteGridTable.set_grid_cell_attr(self, grid, col, attr)
        if col == 1:
            attr.SetReadOnly(False)
        else:
            attr.SetReadOnly(True)
    
    def get_index_range(self, r, c):
        try:
            try:
                line = self.lines[r]
            except IndexError:
                line = self.lines[-1]
            except TypeError:
                return 0, 0
            index = line.pc - self.start_addr
            return index, index + line.num_bytes
        except IndexError:
            return 0, 0
    
    def is_index_valid(self, index):
        return self._rows > 0 and index < len(self.segment)
    
    def get_row_col(self, index):
        try:
            row = self.index_to_row[index]
        except:
            row = self.index_to_row[-1]
        return row, 1

    def get_next_cursor_pos(self, row, col):
        col += 1
        if col >= self._cols:
            if row < self._rows - 1:
                row += 1
                col = 1
            else:
                col = self._cols - 1
        return (row, col)

    def get_next_editable_pos(self, row, col):
        if col < 1:
            col = 1
        else:
            col = 1
            row += 1
        return (row, col)
   
    def get_prev_cursor_pos(self, row, col):
        col -= 1
        if col < 1:
            if row > 0:
                row -= 1
                col = self._cols - 1
            else:
                col = 1
        return (row, col)
   
    def get_page_index(self, index, segment_page_size, dir, grid):
        r, c = self.get_row_col(index)
        vr = grid.get_num_visible_rows() - 1
        r += (dir * vr)
        if r < 0:
            r = 0
        index, _ = self.get_index_range(r, 0)
        return index
    
    def get_pc(self, row):
        try:
            row = self.lines[row]
            return row.pc
        except IndexError:
            return 0
    
    def get_addr_dest(self, row):
        index, _ = self.get_index_range(row, 0)
        index_addr = self.get_pc(row)
        d = self.editor.machine.get_disassembler(False, False)
        d.set_pc(self.segment.data[index:], index_addr)
        args = d.disasm()
        return args[-1]

    def get_comments(self, index, line=None):
        if line is None:
            row = self.index_to_row[index]
            line = self.lines[row]
        comments = []
        c = line.instruction
        if ";" in c:
            _, c = c.split(";", 1)
            comments.append(c)
        for i in range(line.num_bytes):
            c = self.segment.get_comment(index + i)
            if c:
                comments.append(c)
        return " ".join(comments)

    def get_operand_label(self, operand, operand_labels_start_pc, operand_labels_end_pc, offset_operand_labels):
        """Find the label that the operand points to.
        """
        dollar = operand.find("$")
        if dollar >=0 and "#" not in operand:
            print operand, dollar, operand_labels_start_pc, operand_labels_end_pc,
            text_hex = operand[dollar+1:dollar+1+4]
            if len(text_hex) > 2 and text_hex[2] in "0123456789abcdefABCDEF":
                size = 4
            else:
                size = 2
            print text_hex, size,
            target_pc = int(text_hex[0:size], 16)
            print target_pc
            if target_pc >= operand_labels_start_pc and target_pc <= operand_labels_end_pc:
                #print operand, dollar, text_hex, target_pc, operand_labels_start_pc, operand_labels_end_pc
                label = offset_operand_labels.get(target_pc, "L" + text_hex)
                operand = operand[0:dollar] + label + operand[dollar+1+size:]
                return operand, target_pc, label
        return operand, -1, ""

    def get_value_style_lower(self, row, col, operand_labels_start_pc=-1, operand_labels_end_pc=-1, extra_labels={}, offset_operand_labels={}):
        line = self.lines[row]
        pc = line.pc
        index = pc - self.start_addr
        style = 0
        count = line.num_bytes
        for i in range(count):
            style |= self.segment.style[index + i]
        if col == 0:
            if self.hex_lower:
                text = " ".join("%02x" % self.segment[index + i] for i in range(count))
            else:
                text = " ".join("%02X" % self.segment[index + i] for i in range(count))
        elif col == 2:
            if (style & comment_bit_mask):
                text = self.get_comments(index, line)
            elif ";" in line.instruction:
                _, text = line.instruction.split(";", 1)
            else:
                text = ""
        else:
            if self.jump_targets[pc]:
                text = ("L%04X" % pc)
            else:
                text = extra_labels.get(pc, "     ")
            operand = line.instruction.rstrip()
            if count > 1 and operand_labels_start_pc >= 0:
                operand, target_pc, label = self.get_operand_label(operand, operand_labels_start_pc, operand_labels_end_pc, offset_operand_labels)
            text += " " + operand
        return text, style
    
    get_value_style_upper = get_value_style_lower

    def get_prior_valid_opcode_start(self, target_pc):
        index = target_pc - self.start_addr
        row = self.index_to_row[index]
        while index > 0:
            row_above = self.index_to_row[index - 1]
            if row_above < row:
                break
            index -= 1
        return index + self.start_addr
    
    def get_style_override(self, row, col, style):
        if self.lines[row].flag:
            return style|comment_bit_mask
        return style

    def get_label_at_index(self, index):
        row = self.index_to_row[index]
        return self.get_label_at_row(row)
    
    def get_label_at_row(self, row):
        addr = self.get_pc(row)
        if self.get_value_style == self.get_value_style_lower:
            return "%04x" % addr
        return "%04X" % addr

    def GetRowLabelValue(self, row):
        if self.lines is not None:
            return self.get_label_at_row(row)
        return "0000"

    def ResetViewProcessArgs(self, grid, editor, *args):
        if editor is not None:
            self.set_editor(editor)


class AssemblerTextCtrl(HexTextCtrl):
    def setMode(self, mode):
        self.mode='6502'
        self.SetMaxLength(0)
        self.autoadvance=0
        self.userpressed=False

class AssemblerEditor(HexCellEditor):
    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        self._tc = AssemblerTextCtrl(parent, id, self.parentgrid)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)


class DisassemblyPanel(ByteGrid):
    """
    View for editing in hexidecimal notation.
    """
    short_name = "disasm"
    
    # Segment saver interface for menu item display
    export_data_name = "Disassembly"
    export_extensions = [".s"]

    def __init__(self, parent, task, **kwargs):
        """Create the HexEdit viewer
        """
        table = DisassemblyTable()
        ByteGrid.__init__(self, parent, task, table, **kwargs)
        
        # During idle-time disassembly, an index may not yet be visible.  The
        # value is saved here so the view can be scrolled there once it does
        # get disassembled.
        self.pending_index = -1
    
    def get_default_cell_editor(self):
        return AssemblerEditor(self)

    def restart_disassembly(self, index):
        self.table.restart_disassembly(index)
    
    def get_disassembled_text(self, start, end):
        """Returns list of lines representing the disassembly
        
        Raises IndexError if the disassembly hasn't reached the index yet
        """
        t = self.table
        start_row = t.index_to_row[start]
        try:
            end_row = t.index_to_row[end]
        except IndexError:
            # check if entire segment selected; if so, end will be one past last
            # allowable entry in index_to_row
            end -= 1
            end_row = t.index_to_row[end]
        start_pc = t.get_pc(start_row)
        end_pc = t.get_pc(end_row)

        # pass 1: find any new labels
        extra_labels = {}
        offset_operand_labels = {}
        for row in range(start_row, end_row + 1):
            index, _ = t.get_index_range(row, 0)
            operand = t.lines[row]["instruction"]
            operand, target_pc, label = t.get_operand_label(operand, start_pc, end_pc, {})
            if target_pc >= 0:
                extra_labels[target_pc] = label

                good_opcode_target_pc = t.get_prior_valid_opcode_start(target_pc)
                diff = target_pc - good_opcode_target_pc
                if diff > 0:
                    offset_operand_labels[target_pc] = "L%04X+%d" % (good_opcode_target_pc, diff)
                    print "mapping %04X to %s" % (target_pc, offset_operand_labels[target_pc])
        print extra_labels
        print offset_operand_labels
        lines = []
        org = t.GetRowLabelValue(start_row)
        lines.append("        %s $%s" % (t.disassembler.asm_origin, org))
        for row in range(start_row, end_row + 1):
            index, _ = t.get_index_range(row, 0)
            pc = t.get_pc(row)
            code, _ = t.get_value_style(row, 1, start_pc, end_pc, extra_labels, offset_operand_labels)
            # expand to 8 spaces
            code = code[0:5] + "  " + code[5:]
            comment, _ = t.get_value_style(row, 2)
            if comment:
                if not comment.startswith(";"):
                    comment = ";" + comment
                lines.append("%s %s" % (code, comment))
            else:
                lines.append(code)
        return lines
    
    def encode_data(self, segment):
        """Segment saver interface: take a segment and produce a byte
        representation to save to disk.
        """
        index = len(self.table.index_to_row) - 1
        lines = self.get_disassembled_text(0, index)
        text = os.linesep.join(lines) + os.linesep
        data = text.encode("utf-8")
        return data

    def get_status_message_at_index(self, index, row, col):
        msg = ByteGrid.get_status_message_at_index(self, index, row, col)
        comments = self.table.get_comments(index)
        return "%s  %s" % (msg, comments)

    def goto_index(self, index):
        try:
            row = self.table.index_to_row[index]
            self.pending_index = -1
        except IndexError:
            self.pending_index = index
        else:
            row, col = self.table.get_row_col(index)
            self.SetGridCursor(row, col)
            self.MakeCellVisible(row,col)
        
    def change_value(self, row, col, text):
        """Called after editor has provided a new value for a cell.
        
        Can use this to override the default handler.  Return True if the grid
        should be updated, or False if the value is invalid or the grid will
        be updated some other way.
        """
        try:
            pc = self.table.get_pc(row)
            cmd = text.upper()
            bytes = self.table.disassembler.assemble_text(pc, cmd)
            start, _ = self.table.get_index_range(row, col)
            end = start + len(bytes)
            cmd = MiniAssemblerCommand(self.table.segment, start, end, bytes, cmd)
            self.task.active_editor.process_command(cmd)
            return True
        except RuntimeError, e:
            self.task.window.error(unicode(e))
            self.SetFocus()  # OS X quirk: return focus to the grid so the user can keep typing
        return False
    
    def search(self, search_text, match_case=False):
        # FIXME! search broken with udis_fast
        lines = self.table.lines
        s = self.table.start_addr
        if not match_case:
            search_text = search_text.lower()
            matches = [(t[0] - s, t[0] - s + len(t[1])) for t in lines if search_text in t[3].lower()]
        else:
            matches = [(t[0] - s, t[0] - s + len(t[1])) for t in lines if search_text in t[3]]
        return matches
    
    def get_goto_action(self, r, c):
        addr_dest = self.table.get_addr_dest(r)
        if addr_dest is not None:
            segment_start = self.table.segment.start_addr
            segment_num = -1
            addr_index = addr_dest - segment_start
            if addr_dest < segment_start or addr_dest > segment_start + len(self.table.segment):
                segment_num, segment_dest, addr_index = self.editor.document.find_segment_in_range(addr_dest)
                if segment_dest is not None:
                    msg = "Go to address $%04x in segment %s" % (addr_dest, str(segment_dest))
                else:
                    msg = "Address $%04x not in any segment" % addr_dest
                    addr_dest = None
            else:
                msg = "Go to address $%04x" % addr_dest
        else:
            msg = "No address to jump to"
        if addr_dest is not None:
            goto_action = GotoIndexAction(name=msg, enabled=True, segment_num=segment_num, addr_index=addr_index, task=self.task, active_editor=self.task.active_editor)
        else:
            goto_action = GotoIndexAction(name=msg, enabled=False, task=self.task)
        return goto_action
    
    def get_popup_actions(self, r, c):
        goto_action = self.get_goto_action(r, c)
        actions = [goto_action, None]
        actions.extend(self.editor.common_popup_actions())
        return actions
