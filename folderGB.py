import sys, os
#PyQt5/PySide2
from PySide2.QtCore    import Qt, Signal#pyqtSignal as Signal
from PySide2.QtGui     import QFontMetrics, QFont
from PySide2.QtWidgets import (QApplication, QCheckBox, QFileDialog,
     QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QStyle)
# to use PyQt5 instead of PySide2:
#    change 'PySide2' to 'PyQt5' and 'Signal' to 'pyqtSignal as Signal'

class folderGroupBox(QGroupBox):
    "folder locate/display widget from Orthallelous"
    pathChanged = Signal(str)

    def __init__(self, parent=None, base='', sub=''):
        super(folderGroupBox, self).__init__(parent)
        self.path = self.base = self.sub = ''
        self._pht = True  # use placeholdertext as subfolder or not
        self.setup(); self.setPath(base, sub)

    def findFolder(self):
        "locate folder via QFileDialog"
        fld = QFileDialog().getExistingDirectory(directory=self.base)
        if not fld: return

        if type(fld) != str: self.base = str(fld, sys.getfilesystemencoding())
        else: self.base = fld
        self.makePath()

    def setPath(self, base, sub=None):
        "set basefolder path to base, optional subfolder to sub"
        self.setFolder(base, sub)

    def getPath(self):
        "get full folder path"
        return self.path

    def setFolder(self, base, sub=None):
        "set basefolder path to base, optional subfolder to sub"
        if sub: self.base, self.sub = base, sub
        else: self.path = self.base = base
        self.makePath()

    def getFolder(self):
        "get full folder path"
        return self.path

    def setBaseFolder(self, base):
        "set basefolder to base"
        self.base = base

    def getBaseFolder(self):
        "get basefolder"
        return self.base

    def setSubFolder(self, sub=''):
        "set subfolder to sub; uses subfolderInput text if sub is empty"
        if not sub: self.sub = str(self.subfolderInput.text())
        else: self.subfolderInput.setText(sub); self.sub = str(sub)
        self.makePath()

    def getSubFolder(self):
        "get subfolder"
        return self.sub

    def setPlaceHolderText(self, text):
        "set subfolder's place holder text"
        self.subfolderInput.setPlaceholderText(text)
        self.makePath()

    def placeholderText(self):
        "return subfolder's place holder text"
        return self.subfolderInput.placeholderText()

    def usePlaceHolderText(self, state=True):
        "enable/disable use of subfolder placeholdertext as subfolder"
        self._pht = bool(state); self.makePath()

    def _toggleSubfolderInput(self, state):
        "enable/disable subfolder input via self.subfolderCB"
        if state: self.subfolderInput.setEnabled(True)
        else: self.subfolderInput.setEnabled(False)
        self.makePath()

    def allowSubfolderInput(self, state=True):
        "hides/shows subfolder input all together"
        if state:
            self.subfolderInput.setMinimumSize(70, 22)
            self.folderLabel.setMinimumSize(70, 22)
            self.subfolderInput.setEnabled(True)
            self.subfolderCB.setEnabled(True)
            self.subfolderInput.show()
            self._layout.setSpacing(6)
            self._layout.setMargin(11)
            self.subfolderCB.show()
        else:
            self.subfolderInput.setMinimumSize(3, 22)
            self.folderLabel.setMinimumSize(3, 22)
            self.subfolderInput.setEnabled(False)
            self.subfolderCB.setEnabled(False)
            self.sub, self._pht = '', False
            self.subfolderInput.hide()
            self._layout.setSpacing(4)
            self._layout.setMargin(6)
            self.subfolderCB.hide()
        self.update()

    def makePath(self, base='', sub=''):
        """makes, emits full path name
        if base is empty, uses self.base
        if sub is empty, uses self.sub
           uses subfolder placeholder text if use_pht is True
           (and no subfolder has been set)"""
        # set/get base folder
        if not base: base = self.base
        else: self.base = base
        if not base: return  # no base folder set anywhere!

        # set/get sub folder if being used
        if self.subfolderCB.isChecked():
            if not sub: sub = self.sub
            else: self.sub = sub
            if self._pht and not sub:  # no sub set anywhere, and using pht
                sub = str(self.subfolderInput.placeholderText())

        # make full folder path
        if sub: self.path = os.path.join(base, sub)
        else: self.path = self.base

        # emit new path name, update folder display
        self.pathChanged.emit(self.path); self.elidePath()

    def resizeEvent(self, event): self.elidePath()

    def elidePath(self):
        "displays current path, truncating as needed"
        lfg, rfg = Qt.ElideLeft, Qt.ElideRight
        label = self.folderLabel; wdh = label.width()
        el, sl = u'\u2026', os.sep  # ellipsis, slash chrs
        base, sub = self.base, self.sub

        if self._pht and not sub:  # using placeholder text as sub folder
            sub = str(self.subfolderInput.placeholderText())
        use_sub = self.subfolderCB.isChecked()
        if not base: return

        # assemble path, determine bottom (last) folder
        if not sub or not use_sub: path, lst = base, os.path.basename(base)
        else: path, lst = os.path.join(base, sub), sub
        path = path.replace(os.altsep or '\\', sl)

        # truncate folder location
        fnt = QFontMetrics(self.folderLabel.font())
        txt = str(fnt.elidedText(path, lfg, wdh))

        if len(txt) <= 1:  # label is way too short
            label.setToolTip(path)#; label.setText(u'\u22ee')
            label.setText(u'\u22ee' if txt != sl else txt)
            return  # nothing more can be done about this, so...

        # truncate some more (don't show part of a folder name)
        if len(txt) < len(path) and txt[1] != sl:
            txt = el + sl + txt.split(sl, 1)[-1]

            # don't truncate remaining folder name from the left
            if txt[2:] != lst and len(txt) - 4 < len(lst):
                txt = str(fnt.elidedText(el + sl + lst, rfg, wdh))
                if sub: sub = txt.split(sl, 1)[-1]

        if use_sub and sub:  # highlight sub folder (if there's one)
            col = u'<span style="color:#ff5500;">{}</span>'#cd4400
            txt = col.format(sub).join(txt.rsplit(sub, 1))
            path = col.format(lst).join(path.rsplit(lst, 1))

        self.subfolderInput.setToolTip(sub)
        label.setText(txt); label.setToolTip(path)

    def setup(self):
        "widget construction"
        self.setTitle('Save Location')

        self.folderButton = QPushButton('Folder')
        self.folderButton.setToolTip('Open folder')
        self.folderButton.setFixedSize(70, 22)
        self.folderButton.clicked.connect(self.findFolder)
        ico = self.style().standardIcon(QStyle.SP_DirIcon)
        self.folderButton.setIcon(ico)

        self.folderLabel = QLabel()
        self.folderLabel.setMinimumSize(70, 22)
        #self.folderLabel.setFrameStyle(QFrame.Box)

        self.subfolderCB = QCheckBox('subfolder')
        self.subfolderCB.setMinimumSize(70, 22)
        self.subfolderCB.setToolTip('save to subfolder')
        self.subfolderCB.stateChanged.connect(self._toggleSubfolderInput)

        self.subfolderInput = QLineEdit()
        self.subfolderInput.setEnabled(False)
        self.subfolderInput.setMinimumSize(70, 22)
        self.subfolderInput.textEdited.connect(self.setSubFolder)

        gl = QGridLayout()
        gl.addWidget(self.folderButton,   0, 0, 1, 1)
        gl.addWidget(self.folderLabel,    0, 1, 1, 1)
        gl.addWidget(self.subfolderCB,    1, 0, 1, 1)
        gl.addWidget(self.subfolderInput, 1, 1, 1, 1)
        self.setLayout(gl); self._layout = gl




###############################################################################
###############################################################################



import sys, os
# to use PyQt5 instead of PySide2:
#    change 'PySide2' to 'PyQt5' and 'Signal' to 'pyqtSignal as Signal'
from PySide2.QtCore    import Qt, Signal  # to get elide flags, custom signal
from PySide2.QtGui     import QFontMetrics  # to get label font, elide text
from PySide2.QtWidgets import (QApplication, QFileDialog,
     QHBoxLayout, QFrame, QLabel, QPushButton, QStyle)


class pathBox(QFrame):
    "folder locate/display widget from Orthallelous"
    pathChanged = Signal(str)
    def __init__(self, parent=None, path=''):
        super(pathBox, self).__init__(parent)
        self.path = path; self.setup()

    def _findPath(self):
        "locate folder via QFileDialog"
        path = QFileDialog().getExistingDirectory(directory=self.path)
        if not path: return
        if type(path) != str: path = str(path, sys.getfilesystemencoding())
        self.setFolder(path)

    def setPath(self, path):
        "set folder path to path, same as setFolder"
        self.setFolder(path)

    def getPath(self):
        "get folder path, same as getFolder"
        return self.path

    def setFolder(self, path):
        "set folder path to path"
        self.path = path.replace(os.altsep or '\\', os.sep)
        self.pathLabel.setToolTip(self.path)
        self.pathChanged.emit(path); self.elidePath()

    def getFolder(self):
        "get folder path"
        return self.path

    def resizeEvent(self, event): self.elidePath()

    def elidePath(self):
        "displays current path, truncating as needed"
        Lflg, Rflg = Qt.ElideLeft, Qt.ElideRight
        
        labl = self.pathLabel
        vl, el, sl = u'\u22ee', u'\u2026', os.sep
        path, wdth = self.path, labl.width()
        base = os.path.basename(path)

        # truncate folder location
        font = QFontMetrics(labl.font())
        text = str(font.elidedText(path, Lflg, wdth))
        if len(text) <= 1: labl.setText(vl if text != sl else text); return

        # truncate some more (don't show part of a folder name)
        if len(text) < len(path) and text[1] != sl:
            text = el + sl + text.split(sl, 1)[-1]

            # don't truncate remaining folder name from the left
            if text[2:] != base and len(text) - 4 < len(base):
                text = str(font.elidedText(el + sl + base, Rflg, wdth))
        labl.setText(text)

    def useShortForm(self, state=False):
        "enable/disable shorter icon form, default False"
        if state:
            self.pathButton.setFixedSize(24, 24)
            ico = self.style().standardIcon(QStyle.SP_DirIcon)
            self.pathButton.setIcon(ico)
            self.pathButton.setText('')
        else:
            self.pathButton.setFixedSize(75, 24)
            self.pathButton.setIcon(QIcon())
            self.pathButton.setText('Folder')
        self.update()

    def setup(self):
        "widget construction"
        self.pathButton = QPushButton('Folder')#'Open')
        self.pathButton.setToolTip('Open folder')
        self.pathButton.setFixedSize(75, 24)
        self.pathButton.clicked.connect(self._findPath)
        ico = self.style().standardIcon(QStyle.SP_DirIcon)
        self.pathButton.setIcon(ico)

        self.pathLabel = QLabel(); self.pathLabel.setMinimumSize(3, 24)

        ly = QHBoxLayout(); ly.setMargin(0)
        ly.addWidget(self.pathButton); ly.addWidget(self.pathLabel)
        self.setLayout(ly); self._layout = ly




if __name__ == '__main__':
    app = QApplication(sys.argv)

    #w.setPath('B:/floppy/my/on/somewhere/stored/folder/nested/deeply/and/long/very/a/on/data/important/Version 3 final edited')
    
    w.show()     
    sys.exit(app.exec_())
