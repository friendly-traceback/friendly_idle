"""This module takes care of patching a few methods from various
IDLE classes at import time."""

from friendly_idle.patching_hook import add_patch


# In normal usage, idlelib.run is imported multiple times
# during a normal session with IDLE.


def add_recreate_syntax_error(module):
    """Adds a method to idlelib.run.Executive to recreate
    a SyntaxError or other errors occurring at compile time
    and show the relevant information.
    """

    def recreate_syntax_error(self, source, filename):
        import friendly_traceback

        try:
            compile(source + "\n", filename, "single")
        except (OverflowError, SyntaxError, ValueError):
            old_included = friendly_traceback.get_include()
            if old_included == "friendly_tb":
                friendly_traceback.set_include("message_plus")
            friendly_traceback.explain_traceback()
            friendly_traceback.set_include(old_included)

    module.Executive.recreate_syntax_error = recreate_syntax_error

    return module


add_patch("idlelib.run", add_recreate_syntax_error)
# ========================================================================


def replace_transfer_path(module):
    """Modify the command run in idlelib.pyshell.ModifiedInterpreter.transfer_path
    to set up friendly/friendly-traceback as an exception hook.
    """

    def transfer_path(self, with_cwd=False):
        import sys

        if with_cwd:
            path = [""]
            path.extend(sys.path)
        else:
            path = sys.path

        # Add required info for friendly
        self.runcommand(
            """if 1:
        import sys as _sys
        _sys.path = %r
        from friendly.idle import *
        from friendly_traceback import exclude_file_from_traceback
        exclude_file_from_traceback(%r)
        del _sys
        \n"""
            % (path, __file__)
        )

    module.ModifiedInterpreter.transfer_path = transfer_path
    return module


add_patch("idlelib.pyshell", replace_transfer_path)
# ========================================================================


def replace_idle_title(module):
    """Replaces IDLE's title, prepending it by Friendly"""
    from platform import python_version
    from friendly_idle import __version__

    module.PyShell.shell_title = (
        f"Friendly IDLE (version {__version__}; Python version {python_version()})"
    )
    return module


add_patch("idlelib.pyshell", replace_idle_title)
# ========================================================================


def replace_runsource(module):
    """Replaces idlelib.pyshell.runsource so that we save the source code
    entered in the shell, together with the 'filename' which would be of
    the form '<pyshell#...>'.
    """

    def runsource(self, source):
        "Extend base class method: Stuff the source in the line cache first"
        from code import InteractiveInterpreter

        # There is no point in keeping highlighting of previous SyntaxError
        # location when new code is entered.
        self.tkconsole.text.tag_remove("ERROR", "1.0", "end")

        filename = self.stuffsource(source)

        self._source = source
        self._filename = filename

        return InteractiveInterpreter.runsource(self, source, filename)

    module.ModifiedInterpreter.runsource = runsource
    return module


add_patch("idlelib.pyshell", replace_runsource)
# ========================================================================


def replace_showsyntaxerror(module):
    """Replaces idlelib.pyshell.ModifiedInterpreter.showsyntaxerror
    adding a call to a function added to idlelib.run.Executive and
    used to recreate the SyntaxError and process it with friendly-traceback.
    """

    def showsyntaxerror(self, filename=None):
        """Override Interactive Interpreter method: Use Colorizing

        Color the offending position instead of printing it and pointing at it
        with a caret.

        """
        import sys

        tkconsole = self.tkconsole
        text = tkconsole.text
        type, value, tb = sys.exc_info()
        lineno = getattr(value, "lineno", "") or 1
        offset = getattr(value, "offset", "") or 0
        if offset == 0:
            lineno += 1  # mark end of offending line
        if lineno == 1:
            pos = "iomark + %d chars" % (offset - 1)
        else:
            pos = "iomark linestart + %d lines + %d chars" % (lineno - 1, offset - 1)

        tkconsole.colorize_syntax_error(text, pos)
        tkconsole.resetoutput()

        # We might be tempted to use something like:
        #    self.runcommand(self._source)
        # to recreate the error on the client side.
        # However, the code that would run on the client side
        # would not be saved anew in linecache which, in some instances,
        # would cause friendly to raise an exception.
        # Furthermore, the traceback would show the problematic line twice
        # once with the location of the error (on the original code at the prompt)
        # highlighted in red, and a second time (in the friendly-traceback) with
        # carets (^) indicating the location of the error.
        # The approach we use is to *compile* the code with the repeated filename
        # and explicitly catch the exception in the part of the code
        # where it will be executed..

        if self.rpcclt:
            self.rpcclt.remotequeue(
                "exec", "recreate_syntax_error", (self._source, self._filename), {}
            )
        else:
            print("This should not happen")
        tkconsole.showprompt()

    module.ModifiedInterpreter.showsyntaxerror = showsyntaxerror
    return module


add_patch("idlelib.pyshell", replace_showsyntaxerror)
# ========================================================================


def replace_build_subprocess_arglist(module):
    """Replaces idlelib.pyshell.ModifiedInterpreter.build_subprocess_arglist
    to ensure that idlelib.run is patched every time the shell is restarted.
    """

    def build_subprocess_arglist(self):
        import sys
        from idlelib.config import idleConf

        assert self.port != 0, "Socket should have been assigned a port number."
        w = ["-W" + s for s in sys.warnoptions]
        # Maybe IDLE is installed and is being accessed via sys.path,
        # or maybe it's not installed and the idle.py script is being
        # run from the IDLE source directory.
        del_exitf = idleConf.GetOption(
            "main", "General", "delete-exitfunc", default=False, type="bool"
        )
        # Patch idlelib.run, then call its main function
        command = (
            "__import__('friendly_idle.patch_idle');__import__('idlelib.run').run.main(%r);"
            % (del_exitf,)
        )
        return [sys.executable] + w + ["-c", command, str(self.port)]

    module.ModifiedInterpreter.build_subprocess_arglist = build_subprocess_arglist
    return module


add_patch("idlelib.pyshell", replace_build_subprocess_arglist)
# ========================================================================


def replace_checksyntax(module):
    """Replaces idlelib.runscript.ScriptBinding.checksyntax so that
    the information from friendly-traceback can be shown in the popup window.
    This method is called either when a menu item is used to check the syntax
    or to actually run a module.
    """

    def checksyntax(self, filename):
        import friendly_traceback
        from friendly import idle_writer
        from functools import partial

        # Most of the code below is recopied as is from IDLE.
        self.shell = shell = self.flist.open_shell()
        saved_stream = shell.get_warning_stream()
        shell.set_warning_stream(shell.stderr)
        with open(filename, "rb") as f:
            source = f.read()
        if b"\r" in source:
            source = source.replace(b"\r\n", b"\n")
            source = source.replace(b"\r", b"\n")
        if source and source[-1] != ord(b"\n"):
            source = source + b"\n"
        editwin = self.editwin
        text = editwin.text
        text.tag_remove("ERROR", "1.0", "end")
        try:
            # If successful, return the compiled code
            return compile(source, filename, "exec")
        except (SyntaxError, OverflowError, ValueError) as value:
            msg = getattr(value, "msg", "") or value or "<no detail available>"
            lineno = getattr(value, "lineno", "") or 1
            offset = getattr(value, "offset", "") or 0
            if offset == 0:
                lineno += 1  # mark end of offending line
            pos = "0.0 + %d lines + %d chars" % (lineno - 1, offset - 1)
            editwin.colorize_syntax_error(text, pos)
            # New code, to prepare the new try block.
            _writer = partial(idle_writer.writer, stream=shell)
            _formatter = idle_writer.formatter
            try:
                friendly_traceback.exclude_file_from_traceback(__file__)
                friendly_traceback.set_formatter(_formatter)
                friendly_traceback.explain_traceback(redirect=_writer)
                self.shell.showprompt()
            except Exception as exc:
                print("Attempting to process SyntaxError with friendly failed.")
                print(exc)
                # Normally, this would be the only line executed by IDLE.
                self.errorbox("SyntaxError", "%-20s" % msg)
            return False
        finally:
            shell.set_warning_stream(saved_stream)

    module.ScriptBinding.checksyntax = checksyntax
    return module


add_patch("idlelib.runscript", replace_checksyntax)
