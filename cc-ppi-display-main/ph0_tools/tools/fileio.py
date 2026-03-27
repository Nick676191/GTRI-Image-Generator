from PyQt5 import QtWidgets

def show_message_box(title, message, details=""):
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setDetailedText(str(details))
    msg.exec_()

def file_is_valid(file):
    """
    Returns True if the file exists and can be
    opened. Returns False otherwise.
    """
    try:
        file = open(file, "r")
        file.close()
        return True
    except FileNotFoundError:
        return False