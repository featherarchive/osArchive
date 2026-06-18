class TkUnavailableError(RuntimeError):
    pass


try:
    import tkinter as tk
    from tkinter import simpledialog, ttk
except ImportError as exc:
    _IMPORT_ERROR = exc

    class _MissingWidget:
        def __init__(self, *args, **kwargs):
            raise TkUnavailableError(
                "Tkinter native libraries are not available. Install the OS Tk package "
                "(for example, `tk` on Arch/CachyOS) and rerun the app."
            ) from _IMPORT_ERROR

    class _MissingTkModule:
        Canvas = _MissingWidget
        Text = _MissingWidget
        StringVar = _MissingWidget

        @staticmethod
        def Tk():
            raise TkUnavailableError(
                "Tkinter native libraries are not available. Install the OS Tk package "
                "(for example, `tk` on Arch/CachyOS) and rerun the app."
            ) from _IMPORT_ERROR

    class _MissingTtkModule:
        Frame = _MissingWidget
        Label = _MissingWidget
        Button = _MissingWidget
        Entry = _MissingWidget
        Style = _MissingWidget

    class _MissingSimpleDialog:
        @staticmethod
        def askstring(*args, **kwargs):
            raise TkUnavailableError(
                "Tkinter native libraries are not available. Install the OS Tk package "
                "(for example, `tk` on Arch/CachyOS) and rerun the app."
            ) from _IMPORT_ERROR

    tk = _MissingTkModule()
    ttk = _MissingTtkModule()
    simpledialog = _MissingSimpleDialog()
