from .class_designer import ClassDesigner
from . import cxn_editor


def run_connection_editor(filepaths=None):
    cxn_editor.run_editor(filepaths)


def run_class_designer(filepath=None):
    clsDes = ClassDesigner(filepath)
