import io, sys

#if sys.platform.startswith( 'linux' ) :
#    from OpenGL import GL

#import ctypes
#ctypes.cdll.LoadLibrary("libGL.so.1")

import folium
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                             QMessageBox, QShortcut)
from PyQt5.QtGui import (QKeySequence, QTextBlockFormat, QTextCursor,
                         QStandardItemModel, QStandardItem)
from PyQt5.QtWebEngineWidgets import QWebEngineView

from gui.output import Ui_MainWindow


def boolify(s):
    if s == 'True' or s == 'true':
            return True
    if s == 'False' or s == 'false':
            return False
    raise ValueError('Not Boolean Value!')

def estimateType(var):
    '''guesses the str representation of the variables type'''
    var = str(var) #important if the parameters aren't strings...
    for caster in (boolify, int, float):
            try:
                    return caster(var)
            except ValueError:
                    pass
    return var


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        # Initialise the Main window
        QMainWindow.__init__(self, parent=parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        coordinate = (37.8199286, -122.4782551)
        m = folium.Map(
        	tiles='Stamen Terrain',
        	zoom_start=13,
        	location=coordinate
        )

        # save map data to data object
        data = io.BytesIO()
        m.save(data, close_file=False)


        self.webView = QWebEngineView()
        self.webView.setHtml(data.getvalue().decode())
        self.ui.horizontalLayout_5.addWidget(self.webView)

        self.ui.actionload.triggered.connect(lambda: self.load_data())
        self.ui.actionsave.triggered.connect(lambda: self.save_data())

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.ui.plainTextEdit)
        self.save_shortcut.activated.connect(lambda: self.save_data())

        self.ui.pushButton.clicked.connect(lambda: self.validate())
        #self.ui.StopButton.clicked.connect(lambda: self.stop_exit())

        self.highlight_format = QTextBlockFormat()
        self.highlight_format.setBackground(QtCore.Qt.yellow)
        self.error_format = QTextBlockFormat()
        self.error_format.setBackground(QtCore.Qt.red)
        self.default_format = QTextBlockFormat()
        self.default_format.setBackground(QtCore.Qt.white)
        self.validate_info = {
            "version":{
                "mandatory":True, "present":False, "unique":True,
                "args":[int(), int(), int()]
                       },

            "command_timeout":{
                "mandatory":True, "present":False, "unique":True,
                "args":[int()]
                       },
            "init":{
                "mandatory":True, "present":False, "unique":True,
                "args":[str()]
                       },
            "ascending":{
                "mandatory":True, "present":False, "unique":True,
                "args":[str(), int()]
                       },
            "descending":{
                "mandatory":True, "present":False, "unique":True,
                "args":[str(), int()]
                       },
            "exit":{
                "mandatory":True, "present":False, "unique":True,
                "args":[str()]
                       },
            "region":{
                # args for region is special: nested lists of types per expected line
                "mandatory":False, "present":False, "unique":False,
                "args":[[str()],
                        [str()],
                        [float(), float()],
                        [float(), float()],
                        [float(), float()],
                        [float(), float()]]
                       },
        }

        self.tablemodel = QStandardItemModel(self)
        self.ui.tableView.setModel(self.tablemodel)


    def load_data(self):
        self.tablemodel.clear()
        try:
            data_path, _ =QFileDialog.getOpenFileName(None, 'Open File', "./DCP_files/", '*.txt')
            dcp_file = open(data_path, "r")
            self.ui.plainTextEdit.clear()
            for line in dcp_file.readlines():
                self.ui.plainTextEdit.appendPlainText(line.rstrip('\n')) #strip newlines from end
            self.ui.plainTextEdit.document().setModified(False)
            #print(self.ui.plainTextEdit.document().isModified())
        except FileNotFoundError:
            pass
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(str(type(e)))
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()


    def save_data(self):
        try:
            data_path, _ =QFileDialog.getSaveFileName(None, 'Save File', "./DCP_files/", '*.txt')
            with open(data_path, "w") as save_file:
                for line in range(self.ui.plainTextEdit.document().blockCount()):
                    save_file.write(self.ui.plainTextEdit.document().findBlockByLineNumber(line).text()+str("\n"))
                save_file.close()
        except FileNotFoundError:
            pass
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(str(type(e)))
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()


    def validate(self):
        self.tablemodel.clear()
        try:
            # this will go as high as 6 before rolling back to 0
            region_counter = 0
            for line in range(self.ui.plainTextEdit.document().blockCount()):
                line_obj = self.ui.plainTextEdit.document().findBlockByLineNumber(line)

                line_text = line_obj.text().split('#',1)[0]
                #print(line_text)
                recognised_command = False
                line_breakdown = line_text.strip().split()
                line_breakdown = [estimateType(x) for x in line_breakdown]
                # if "region block" validation is activated
                if region_counter:
                    # check to make sure lines are indented
                    if len(line_text.rstrip().split(" ")) == len(line_breakdown):
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.highlight_format)
                        self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ": Indent missing - part of \"region\" block"))

                    # check if number of arguments are correct
                    elif len(line_breakdown) != len(self.validate_info["region"]["args"][region_counter-1]):
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.highlight_format)
                        self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ': Incorrect number of arguments - expected ('+
                                                                str(len(self.validate_info["region"]["args"][region_counter-1])) +
                                                                ") but got ("+str(len(line_breakdown)) +")"))
                    # check if arguments types are correct
                    elif [type(x) for x in line_breakdown] != [type(y) for y in self.validate_info["region"]["args"][region_counter-1]]:
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.highlight_format)
                        self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ': Incorrect argument types - expected ('+
                                        ", ".join([type(y).__name__ for y in self.validate_info["region"]["args"][region_counter-1]])+
                                        ") but got ("+ ", ".join([type(x).__name__ for x in line_breakdown])+")"))
                    # line seems valid, remove any highlights
                    else:
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.default_format)
                    if region_counter > 5:
                        region_counter = 0
                    else:
                        region_counter += 1
                    continue

                for key, value in self.validate_info.items():
                    if key in line_breakdown:
                        # Command is approved
                        recognised_command = True
                        # if key already in DCP - raise multiple error
                        if self.validate_info[key]["present"] and self.validate_info[key]["unique"]:
                            cursor = QTextCursor(line_obj)
                            cursor.setBlockFormat(self.error_format)
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Critical)
                            msg.setText("Too many occurences of \""+str(key)+"\" in file")
                            msg.setInformativeText("The \""+str(key)+"\" command should only be specified once")
                            msg.setWindowTitle("Too many occurences of \""+str(key)+"\" in file")
                            msg.exec_()
                            self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ": \""+str(key)+"\" command is already present"))
                            break
                        # Flag the command as present in the editor: Do this after "already-present" check
                        self.validate_info[key]["present"] = True

                        # check if first arguments is the command in question
                        if line_breakdown[0] != key:
                            cursor = QTextCursor(line_obj)
                            cursor.setBlockFormat(self.highlight_format)
                            self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ": \""+str(key)+"\" command must occur at start of line"))

                            break
                        #this is special, activate region_counter and break
                        elif key == "region":
                            region_counter += 1
                            break
                        # check if number of arguments are correct
                        elif len(line_breakdown) != len(value["args"])+1:
                            cursor = QTextCursor(line_obj)
                            cursor.setBlockFormat(self.highlight_format)
                            self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ': Incorrect number of arguments - expected ('+
                                                                    str(len(self.validate_info["region"]["args"][region_counter-1])) +
                                                                    ") but got ("+str(len(line_breakdown)) +")"))
                            break
                        # check if arguments types are correct
                        elif [type(x) for x in line_breakdown[1:]] != [type(y) for y in value["args"]]:
                            cursor = QTextCursor(line_obj)
                            cursor.setBlockFormat(self.highlight_format)
                            self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ': Incorrect argument types - expected ('+
                                                      ", ".join([type(y).__name__ for y in value["args"]]) +
                                                      ") but got ("+ ", ".join([type(x).__name__ for x in line_breakdown[1:]])+")"))
                            break
                        # line seems valid, remove any highlights
                        else:
                            cursor = QTextCursor(line_obj)
                            cursor.setBlockFormat(self.default_format)
                            break

                # "command" on line is not recognised
                if not recognised_command:
                    # actual input on line, highlight as unknown command
                    if line_breakdown and line_breakdown[0]:
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.highlight_format)
                        self.tablemodel.appendRow(QStandardItem("Line "+str(line)+ ": Unrecognised command"))
                    # don't worry about "empty" lines
                    else:
                        cursor = QTextCursor(line_obj)
                        cursor.setBlockFormat(self.default_format)

            # make sure all mandatory fields are present, if not then raise error message
            mandatory_fields = [(key, value["present"]) for (key, value) in self.validate_info.items() if value["mandatory"] == True]
            if not all([tup[1] for tup in mandatory_fields]):
                missing_fields = [key for (key, value) in mandatory_fields if value == False]
                #print("False detected in following fields: " + ", ".join(missing_fields))
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Commands missing from the DCP file")
                msg.setInformativeText("The following commands are missing from the DCP file: " + ", ".join(missing_fields))
                msg.setWindowTitle("Commands missing from the DCP file")
                msg.exec_()
                for missing in missing_fields:
                    self.tablemodel.appendRow(QStandardItem("Command missing from file: \""+str(missing)+"\""))
        except FileNotFoundError:
            pass
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(str(type(e)))
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()

        for key, value in self.validate_info.items():
            self.validate_info[key]["present"] = False
        #self.tablemodel.appendRow(QStandardItem("BLAH BLAH"))
        if not self.tablemodel.rowCount():
            self.tablemodel.appendRow(QStandardItem("No errors found: DCP is valid!"))
        self.ui.tableView.model().layoutChanged.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
