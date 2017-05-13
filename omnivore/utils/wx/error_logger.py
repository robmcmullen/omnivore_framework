# Standard library imports.
import os
import logging
debug_log = logging.getLogger(__name__)


# singleton; only one logging frame available at one time
logging_frame = None

LEVEL_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
    }

known_loggers = {}

def enable_loggers(text):
    """Turn loggers on or off based on simple string matching
    """
    global known_loggers

    if len(known_loggers) == 0:
        # first time through, make sure there are default levels for everything
        get_default_levels()

    match_strings = [t.strip() for t in text.split(",") if t] if "," in text else [text.strip()] if text else []
    count = 0
    for logger_name, level in known_loggers.iteritems():
        if level < 0:
            level = logging.INFO
        for match in match_strings:
            if match and match in logger_name:
                level = logging.DEBUG
                count += 1
                break
        log = logging.getLogger(logger_name)
        log.setLevel(level)
    return count

def get_default_levels():
    global known_loggers

    current_loggers = logging.Logger.manager.loggerDict
    for logger_name in current_loggers.keys():
        if logger_name not in known_loggers:
            known_log = logging.getLogger(logger_name)
            level = known_log.getEffectiveLevel()
            known_loggers[logger_name] = level
            debug_log.debug("default log level for %s: %s" % (logger_name, LEVEL_MAP.get(level, str(level))))


def show_logging_frame():
    global logging_frame

    # Wait until this function is called to import other packages so we don't
    # cause any module-loading-order-dependent problems by importing these
    # before needed in the application
    import wx

    # Logging handler & frame based on code from:
    # http://stackoverflow.com/questions/2819791/

    class WindowLogHandler(logging.Handler):
        """
        A handler class which sends log strings to a wx object
        """

        def __init__(self, printer):
            """
            Initialize the handler
            @param wxDest: the destination object to post the event to 
            @type wxDest: wx.Window
            """
            logging.Handler.__init__(self)
            self.level = logging.DEBUG
            self.printer = printer

        def flush(self):
            """
            does nothing for this handler
            """

        def emit(self, record):
            """
            Emit a record.

            """
            msg = self.format(record)
            wx.CallAfter(self.printer, msg + "\n")


    class LoggerList(wx.CheckListBox):
        count = 0

        def update(self):
            items = []
            checked = []
            count = 0
            for i, logger_name in enumerate(sorted(known_loggers)):
                items.append(logger_name)
                log = logging.getLogger(logger_name)
                level = log.getEffectiveLevel()
                if level <= logging.DEBUG:
                    checked.append(i)
                    count += 1
            self.Set(items)
            self.SetChecked(checked)
            self.count = count


    class LoggingFrame(wx.Frame):
        LEVELS = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        ]

        logger_state_button = False

        def __init__(self, parent, *args, **kwargs):
            wx.Frame.__init__(self, parent, *args, title="Debug Log Viewer", size=(800,600), **kwargs)
            panel = wx.Panel(self, wx.ID_ANY)

            log_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.loggers = LoggerList(panel, wx.ID_ANY, size=(200,600))
            self.loggers.Bind(wx.EVT_CHECKLISTBOX, self.on_logger_checked)
            self.text = wx.TextCtrl(panel, wx.ID_ANY, size=(800,600),
                              style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
            log_sizer.Add(self.loggers, 1, wx.RIGHT|wx.EXPAND, 5)
            log_sizer.Add(self.text, 4, wx.ALL|wx.EXPAND, 0)

            top_hsizer = wx.BoxSizer(wx.HORIZONTAL)
            top_hsizer.Add(wx.StaticText(panel, -1, "Filter:"), 0, wx.ALL|wx.CENTER, 0)
            self.filter = wx.TextCtrl(panel, wx.ID_ANY)
            self.filter.Bind(wx.EVT_CHAR, self.on_char)
            top_hsizer.Add(self.filter, 1, wx.ALL|wx.CENTER, 0)

            bot_hsizer = wx.BoxSizer(wx.HORIZONTAL)
            self.stats = wx.StaticText(panel, -1, "")
            bot_hsizer.Add(self.stats, 1, wx.ALL|wx.CENTER, 0)
            self.freeze = wx.Button(panel, wx.ID_ANY, 'Freeze')
            self.freeze.Bind(wx.EVT_BUTTON, self.on_freeze)
            bot_hsizer.Add(self.freeze, 0, wx.LEFT|wx.CENTER, 10)
            if self.logger_state_button:
                btn = wx.Button(panel, wx.ID_ANY, 'Show Logger State')
                btn.Bind(wx.EVT_BUTTON, self.on_known_button)
                bot_hsizer.Add(btn, 0, wx.LEFT|wx.CENTER, 10)

            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(log_sizer, 1, wx.ALL|wx.EXPAND, 5)
            sizer.Add(top_hsizer, 0, wx.ALL|wx.EXPAND, 5)
            sizer.Add(bot_hsizer, 0, wx.ALL|wx.EXPAND, 5)
            panel.SetSizer(sizer)

            self.add_handler()
            get_default_levels()
            self.loggers.update()
            self.show_logger_stats()
            self.Bind(wx.EVT_CLOSE, self.on_close)
            self.is_frozen = False

        def on_close(self, evt):
            #self.remove_handler()
            self.Show(False)

        def Show(self, state=True):
            wx.Frame.Show(self, state)
            if state:
                self.filter.SetFocus()
                self.filter.SetInsertionPointEnd()
                self.text.SetInsertionPointEnd()

        def add_handler(self):
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            self.handler = WindowLogHandler(self.log)
            logger.addHandler(self.handler)
            self.handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(msg)s"))
            logger.setLevel(logging.INFO)

        def remove_handler(self):
            logger = logging.getLogger()
            logger.removeHandler(self.handler)

        def log(self, msg, override=False):
            if not self.is_frozen or override:
                if not msg.endswith("\n"):
                    msg += "\n"
                self.text.AppendText(msg)
                # self.text.SetInsertionPointEnd()

        def show_known(self):
            get_default_levels()

            ruler = "----------------------------------------------------------"
            self.log("\n%s\nKNOWN LOGGER NAMES:\n" % ruler)
            for logger_name in sorted(known_loggers):
                log = logging.getLogger(logger_name)
                level = log.getEffectiveLevel()
                self.log("%s %s\n" % (LEVEL_MAP.get(level, str(level)), logger_name), override=True)
            self.log("%s\n\n" % ruler)

        def on_test_button(self, evt):
            import random
            debug_log.debug(random.choice(self.LEVELS), "More? click again!")

        def on_known_button(self, evt):
            self.show_known()

        def on_freeze(self, evt):
            if self.is_frozen:
                self.freeze.SetLabel(" Freeze ")
                self.is_frozen = False
            else:
                self.freeze.SetLabel("Resume")
                self.is_frozen = True

        def on_char(self, evt):
            evt.Skip()
            wx.CallAfter(self.process_value)

        def on_logger_checked(self, evt):
            index = evt.GetSelection()
            logger_name = self.loggers.GetString(index)
            state = self.loggers.IsChecked(index)
            debug_log.debug("logger: %s; state=%s" % (logger_name, state))
            if state:
                level = logging.DEBUG
            else:
                level = known_loggers[logger_name]
            log = logging.getLogger(logger_name)
            log.setLevel(level)
            self.show_logger_stats()
            self.filter.ChangeValue("")

        def process_value(self):
            text = self.filter.GetValue()
            count = enable_loggers(text)
            self.show_logger_stats()

        def show_logger_stats(self):
            self.loggers.update()
            label = "1 debug logger enabled" if self.loggers.count == 1 else "%d debug loggers enabled" % self.loggers.count
            self.stats.SetLabel(label)


    if logging_frame is None:
        logging_frame = LoggingFrame(None)
        # logging_frame.show_known()
    logging_frame.Show()


if __name__ == '__main__':
    import wx
    
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("omnivore")
    log = logging.getLogger("omnivore.framework")
    log = logging.getLogger("omnivore.framework.editor")
    log = logging.getLogger("omnivore8bit.hex_edit")
    log = logging.getLogger("omnivore.utils.wx.error_logger")
    app = wx.App(redirect = False)
    show_logging_frame()
    app.MainLoop()
