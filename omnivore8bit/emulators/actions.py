""" Action definitions for emulators

"""
import os
import sys

import wx
import wx.lib.dialogs

# Enthought library imports.
from traits.api import on_trait_change, Any, Int, Bool
from pyface.api import YES, NO

from atrcopy import user_bit_mask, data_style, add_xexboot_header, add_atr_header, BootDiskImage, SegmentData, interleave_segments, get_xex

from omnivore.framework.enthought_api import Action, ActionItem, EditorAction, NameChangeAction, TaskDynamicSubmenuGroup
from omnivore.utils.command import StatusFlags

from subprocess import *
from omnivore.utils.wx.dialogs import prompt_for_hex, prompt_for_dec, prompt_for_string, get_file_dialog_wildcard, ListReorderDialog
from ..ui.dialogs import SegmentOrderDialog
from .. import emulators as emu
from .document import EmulationDocument

if sys.platform == "darwin":
    RADIO_STYLE = "toggle"
else:
    RADIO_STYLE = "radio"

import logging
log = logging.getLogger(__name__)


class UseEmulatorAction(EditorAction):
    """Change the default emulator
    """
    # Traits
    name = "<emu>"
    emulator = Any
    style = RADIO_STYLE

    def perform(self, event):
        self.active_editor.document.emulator_class_override = self.emulator


class BootDiskImageAction(EditorAction):
    """Run the current disk image in an emulator
    """
    name = "Boot Current Disk Image"
    tooltip = "Start emulator using the current file as the boot disk"

    def perform(self, event=None):
        source = self.active_editor.document
        doc = EmulationDocument(source_document=source, emulator_type=source.emulator_class_override)
        doc.boot()
        self.task.new(doc)

    def _update_enabled(self, ui_state):
        self.enabled = not self.active_editor.has_emulator


class BootSegmentAction(EditorAction):
    """Start an emulator by pre-populating memory using the contents of some
    selected segments.
    """
    name = "Boot Current Segment"
    tooltip = "Start emulator using current segment to pre-fill the memory of the emulator"

    def perform(self, event=None):
        source = self.active_editor.document
        doc = EmulationDocument(source_document=source, emulator_type=source.emulator_class_override)
        doc.boot(self.active_editor.segment)
        self.task.new(doc)

    def _update_enabled(self, ui_state):
        self.enabled = not self.active_editor.has_emulator


class LoadSegmentAction(EditorAction):
    """Initialize memory of an emulator using the contents of some
    selected segments.
    """
    name = "Load Current Segment"
    tooltip = "Create (but not boot) an emulator using current segment to pre-fill the memory"

    def perform(self, event=None):
        source = self.active_editor.document
        doc = EmulationDocument(source_document=source, emulator_type=source.emulator_class_override)
        doc.load(self.active_editor.segment)
        self.task.new(doc)

    def _update_enabled(self, ui_state):
        self.enabled = not self.active_editor.has_emulator


class EmulatorAction(EditorAction):
    """Base class for emulator actions
    """
    name = "<emulator action>"
    tooltip = "control the emulator"

    def perform(self, event=None):
        print("emulate!")

    def _update_enabled(self, ui_state):
        self.enabled = self.active_editor.has_emulator


class PauseResumeAction(EmulatorAction):
    """Stop/Restart the emulation
    """
    name = "Resume"
    tooltip = "Pause or restart the emulation"
    accelerator = 'F8'

    def perform(self, event=None):
        if self.active_editor.document.emulator_running:
            self.active_editor.document.pause_emulator()
        else:
            self.active_editor.document.restart_emulator()

    def _update_enabled(self, ui_state):
        self.enabled = self.active_editor.has_emulator
        if self.enabled and not self.active_editor.document.emulator_running:
            self.name = "Resume"
        else:
            self.name = "Pause"


class StepAction(EmulatorAction):
    """Restart the emulation
    """
    name = "Step"
    tooltip = "Restart the emulation"
    accelerator = 'F9'

    def perform(self, event=None):
        self.active_editor.document.debugger_step()

    def _update_enabled(self, ui_state):
        self.enabled = self.active_editor.has_emulator and self.active_editor.document.emulator_paused


class StepIntoAction(StepAction):
    """Restart the emulation
    """
    name = "Step Into"
    tooltip = "Restart the emulation"
    accelerator = 'F10'

    def perform(self, event=None):
        print("resume!")


class StepOverAction(StepAction):
    """Restart the emulation
    """
    name = "Step Over"
    tooltip = "Restart the emulation"
    accelerator = 'F11'

    def perform(self, event=None):
        print("resume!")


class StartAction(EmulatorAction):
    name = "Start"
    tooltip = "Press the Start button"
    accelerator = 'F4'

    def perform(self, event=None):
        print("START!")
        self.active_editor.document.emulator.forced_modifier = "start"


class SelectAction(EmulatorAction):
    name = "Select"
    tooltip = "Press the Select button"
    accelerator = 'F3'

    def perform(self, event=None):
        self.active_editor.document.emulator.forced_modifier = "select"


class OptionAction(EmulatorAction):
    name = "Option"
    tooltip = "Press the Option button"
    accelerator = 'F2'

    def perform(self, event=None):
        self.active_editor.document.emulator.forced_modifier = "option"


class ColdstartAction(EmulatorAction):
    name = "Reboot"
    tooltip = "Simulate turning off the power and turning it back on again"
    accelerator = 'Shift F5'

    def perform(self, event=None):
        self.active_editor.document.emulator.coldstart()


class WarmstartAction(EmulatorAction):
    name = "System Reset"
    tooltip = "Simulate pressing the system reset key"
    accelerator = 'F5'

    def perform(self, event=None):
        self.active_editor.document.emulator.warmstart()


class PreviousSaveStateAction(EmulatorAction):
    """Load the previous saved frame into the current state of the emulator
    """
    name = "Previous Save Point"
    tooltip = "Show previous frame in saved state of the history"
    accelerator = 'F6'

    def perform(self, event=None):
        d = self.active_editor.document
        if d.emulator_running:
            d.pause_emulator()
        else:
            d.history_previous()


class NextSaveStateAction(EmulatorAction):
    """Load the next saved frame into the current state of the emulator
    """
    name = "Next Save Point"
    tooltip = "Show next frame in saved state of the history"
    accelerator = 'F7'

    def perform(self, event=None):
        d = self.active_editor.document 
        print("OEUOEU", d.emulator_running)
        if d.emulator_running:
            d.pause_emulator()
        else:
            print("BBVJKBVJKBQJBKQB")
            d.history_next()
