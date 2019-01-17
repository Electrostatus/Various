from Crypto.Random import random
from Crypto.Cipher import AES
import os, sys, struct
import hashlib, string
import time

# this program can run with either pyqt or pyside
from PyQt4 import QtCore, QtGui  
#from PySide import QtCore, QtGui (copy to clipboard doesn't work)

global app
app = QtGui.QApplication(sys.argv)  # app is used within the program

class main(QtGui.QWidget):
    def __init__(self, parent=None):
        super(main, self).__init__(parent)
        self.setup()  # connections, widgets, layouts, etc.

        self.blksize = 2 ** 20  # 1 MB; must be divisible by 16
        self.ext = '.enc'  # extension is appended to encrypted files
        self.path = ''
        self.encrypted = []  # to highlight done files in list
        self.decrypted = []
        
        self.clipboard = QtGui.QApplication.clipboard()
        self.timeout = None  # to clear message label, see setMessage

        # this program was just an excuse to play with QprogressBar
        if not hash(os.urandom(11)) % 11:
            QtCore.QTimer().singleShot(50, self.windDown)

    def genKey(self):
        "generate a random 32-character key"
        char = string.printable.rstrip()#map(chr, range(256))
        key = ''.join(random.sample(char, 32))
        self.keyInput.setText(key)

    def showKey(self, state=None):
        "hide/show key characters"
        if state is None: state = bool(self.showKeyCB.checkState())
        else: state = bool(state)
        if state: self.keyInput.setEchoMode(QtGui.QLineEdit.Normal)
        else: self.keyInput.setEchoMode(QtGui.QLineEdit.PasswordEchoOnEdit)

    def getFolder(self):
        "open file dialog and fill file table"
        path = QtGui.QFileDialog(directory=self.path).getExistingDirectory()
        if not path: return
        self.path = unicode(path)
        self.populateTable(self.path)
        self.encrypted, self.decrypted = [], []
        return

    def resizeEvent(self, event):
        self.showFolder(self.path)  # update how the folder is shown

    def splitterChanged(self, pos):
        self.showFolder(self.path)  # likewise

    def showFolder(self, path):
        "displays current path, truncating as needed"
        if not path: return

        # show truncated folder location
        sl = '/' if '/' in path else '\\'
        flg = QtCore.Qt.ElideLeft  # find longest size the text can be
        fnt = QtGui.QFontMetrics(self.folderLabel.font())
        txt = unicode(fnt.elidedText(path, flg, self.folderLabel.width()))

        # truncate some more (don't show part of a folder name)
        if len(txt) < len(path) and txt[1] != sl:
            txt = u'\u2026' + sl + txt.split(sl, 1)[-1]  # ellipsis character

        self.folderLabel.setText(txt)
        self.folderLabel.setToolTip(path)

    def populateTable(self, path):
        "fill file table with file names"
        self.showFolder(path)

        names = []
        for n in os.listdir(path):
            if os.path.isdir(os.path.join(path, n)): continue  # folder
            if os.path.splitext(n)[1]:  # add only files with extensions
                names.append(n)

        self.folderTable.clearContents()
        self.folderTable.setRowCount(len(names))
        self.folderTable.setColumnCount(1)

        if not names:  # no files in this folder, inform user
            self.setMessage('This folder has no files')
            return

        for i, n in enumerate(names):
            item = QtGui.QTableWidgetItem()
            item.setText(n); item.setToolTip(n)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            # color code encrypted/decrypted files
            if n in self.encrypted:  # PySide doesn't have setTextColor
                #item.setTextColor(QtGui.QColor(211, 70, 0))
                item.setForeground(QtGui.QBrush(QtGui.QColor(211, 70, 0)))
            if n in self.decrypted:
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 170, 255)))
            self.folderTable.setItem(i, 0, item)
        if len(names) > 5:
            self.setMessage('{:,} files'.format(len(names)), 7)
        
        return

    def setMessage(self, message, secs=4):
        "show a message for a few seconds"
        if self.timeout:  # https://stackoverflow.com/a/21081371
            self.timeout.stop(); self.timeout.deleteLater()
            
        self.messageLabel.setStyleSheet('background-color: rgb(255, 170, 127);')
        self.messageLabel.setText(message)
        #self.messageLabel.showMessage(message, secs * 1000)
        self.messageLabel.setToolTip(message)

        self.timeout = QtCore.QTimer()
        self.timeout.timeout.connect(self.clearMessage)
        self.timeout.setSingleShot(True)
        self.timeout.start(secs * 1000)

    def clearMessage(self):
        self.messageLabel.setStyleSheet('')
        self.messageLabel.setToolTip('')
        self.messageLabel.setText('')

    def getName(self):
        "return file name of selected"
        items = self.folderTable.selectedItems()
        names = [unicode(i.text()) for i in items]
        if names: return names[0]  # only the first selected file
        else: return ''

    def showKeyLen(self, string):
        "displays a tooltip showing length of key"
        s = len(string)
        note = '{:,} character{}'.format(s, '' if s == 1 else 's')
        tip = QtGui.QToolTip
        pos = self.genKeyButton.mapToGlobal(QtCore.QPoint(0,0))
        
        if s < self.minKeyLen:
            note = '<span style="color:#c80000;">{}</span>'.format(note)
        else:
            note = '<span style="color:#258f22;">{}</span>'.format(note)
        tip.showText(pos, note)

    def lock(self, flag=True):
        "locks buttons if True"
        stuff = [self.openButton, self.encryptButton, self.decryptButton,
                 self.genKeyButton, self.hashButton, self.showKeyCB,
                 self.copyButton, self.keyInput, ]
        for i in stuff:
            i.blockSignals(flag)
            i.setEnabled(not flag)
        return

    def _lerp(self, v1, v2, numPts=10):
        "linearly interpolate from v1 to v2\nFrom Orthallelous"
        if len(v1) != len(v2): raise ValueError("different dimensions")
        D, V, n = [], [], abs(numPts)
        for i, u in enumerate(v1): D.append(v2[i] - u)
        for i in range(n + 1):
            vn = []
            for j, u in enumerate(v1): vn.append(u + D[j] / float(n + 2) * i)
            V.append(tuple(vn))
        return V

    def weeeeeee(self):
        "party time"
        self.lock()
        self.setMessage('Party time!', 2.5)
        a, b, c = self.encryptPbar, self.decryptPbar, self.hashPbar
        process, sleep = app.processEvents, time.sleep

        am, bm, cm = a.minimum(), b.minimum(), c.minimum()
        ax, bx, cx = a.maximum(), b.maximum(), c.maximum()
        a.reset(); b.reset(); c.reset()

        loops = self._lerp((am, bm, cm), (ax, bx, cx), 100)
        ivops = loops[::-1]

        # up and up!
        for i in range(3):
            for j, k, l in loops:
                a.setValue(int(j)); b.setValue(int(k)); c.setValue(int(l))
                process(); sleep(0.01)

        a.setValue(ax); b.setValue(bx); c.setValue(cx)
        sleep(0.25)
        a.setValue(am); b.setValue(bm); c.setValue(cm)

        # snake!
        self.setMessage('Snake time!')
        self.messageLabel.setStyleSheet('background-color: rgb(127, 170, 255);')
        for i in range(2):
            for j, k, l in loops: a.setValue(int(j)); process(); sleep(0.002)
            process(); a.setInvertedAppearance(True); process()
            for j, k, l in ivops: a.setValue(int(j)); process(); sleep(0.002)

            for j, k, l in loops: b.setValue(int(k)); process(); sleep(0.002)
            process(); b.setInvertedAppearance(False); process()
            for j, k, l in ivops: b.setValue(int(k)); process(); sleep(0.002)

            for j, k, l in loops: c.setValue(int(l)); process(); sleep(0.002)
            process(); c.setInvertedAppearance(True); process()
            for j, k, l in ivops: c.setValue(int(l)); process(); sleep(0.002)

            process(); b.setInvertedAppearance(True); process()
            for j, k, l in loops: b.setValue(int(k)); process(); sleep(0.002)
            process(); b.setInvertedAppearance(False); process()
            for j, k, l in ivops: b.setValue(int(k)); process(); sleep(0.002)
            process()

            a.setInvertedAppearance(False)
            b.setInvertedAppearance(True)
            c.setInvertedAppearance(False)

        # bars
        sleep(0.5); self.setMessage('Bars!'); process()
        self.messageLabel.setStyleSheet('background-color: rgb(127, 255, 170);')
        for i in range(2):
            a.setValue(ax); time.sleep(0.65); a.setValue(am); sleep(0.25)
            process()
            b.setValue(bx); time.sleep(0.65); b.setValue(bm); sleep(0.25)
            process()
            c.setValue(cx); time.sleep(0.65); c.setValue(cm); sleep(0.25)
            process()
            b.setValue(bx); time.sleep(0.65); b.setValue(bm); sleep(0.25)
            process()

        # okay, enough
        process()
        a.setValue(ax); b.setValue(bx); c.setValue(cx)
        #a.setValue(am); b.setValue(bm); c.setValue(cm)
        a.setInvertedAppearance(False)
        b.setInvertedAppearance(True)
        c.setInvertedAppearance(False)
        self.lock(False)
        return

    def windDown(self, note=None):
        "silly deload on load"
        if note is None: note = 'Loading...'
        self.lock(); self.setMessage(note)
        self.messageLabel.setStyleSheet('background-color: rgb(9, 190, 130);')
        a, b, c = self.encryptPbar, self.decryptPbar, self.hashPbar
        am, bm, cm = a.minimum(), b.minimum(), c.minimum()
        ax, bx, cx = a.maximum(), b.maximum(), c.maximum()
        a.reset(); b.reset(); c.reset()
        loops = self._lerp((ax, bx, cx), (am, bm, cm), 100)
        for j, k, l in loops:
            a.setValue(int(j)); b.setValue(int(k)); c.setValue(int(l))
            app.processEvents()
            time.sleep(0.02)
        a.reset(); b.reset(); c.reset()
        self.lock(False); self.clearMessage()

    def genHash(self, action):
        "generate hash of selected file and display it"
        name, t0 = self.getName(), time.clock()

        if str(action.text()) == 'Party':
            self.weeeeeee()
            self.windDown('Winding down...')
            return
        
        if not name:
            self.setMessage('No file selected')
            return

        self.lock()
        hsh = self.hashFile(os.path.join(self.path, name),
                            getattr(hashlib, str(action.text())))
        self.lock(False)
        self.hashLabel.setText(hsh)
        self.hashLabel.setToolTip(hsh)
        self.extraLabel.setText(str(action.text()) + ' hash took ' +
                                self.secs_fmt(time.clock() - t0))

    def hashFile(self, fn, hasher):
        "returns the hash value of a file"
        hsh, blksize = hasher(), self.blksize
        fsz, csz = os.path.getsize(fn), 0.0
        self.hashPbar.reset()
        with open(fn, 'rb') as f:
            while 1:
                blk = f.read(blksize)
                if not blk: break
                hsh.update(blk)

                csz += blksize
                self.hashPbar.setValue(int(round(csz * 100.0 / fsz)))
                app.processEvents()
        self.hashPbar.setValue(self.hashPbar.maximum())
        return hsh.hexdigest()

    def hashKey(self, key):
        "hashes a key for encrypting/decrypting file"
        key = hashlib.sha512(key.encode('utf-8')).digest()
        for i in range(23): key = key + hashlib.sha512(key).digest()
        return hashlib.sha256(key).digest()  # AES requires a 32 character key

    def encrypt(self):
        "encrypt selected file with key"
        name, t0 = self.getName(), time.clock()
        if not name:
            self.setMessage('No file selected')
            return

        key = unicode(self.keyInput.text())
        if len(key) < self.minKeyLen:
            self.setMessage(('Key must be at least '
                            '{} characters long').format(self.minKeyLen))
            return

        self.lock()
        gn = self.encryptFile(key, os.path.join(self.path, name))
        if not gn: self.lock(False); return
        self.setMessage('saved "{}"'.format(os.path.basename(gn)), 7)
        self.encrypted.append(os.path.basename(gn))
        self.lock(False)
        self.populateTable(self.path)  # repopulate folder list
        self.extraLabel.setText('Encrypting took ' +
                                self.secs_fmt(time.clock() - t0))


    def encryptFile(self, key, fn):
        "encrypts a file using AES (MODE_CBC)"
        chars = map(chr, range(255))
        chk = AES.block_size
        iv = ''.join(random.sample(chars, chk))

        vault = AES.new(self.hashKey(key), AES.MODE_CBC, iv)
        fsz = os.path.getsize(fn)
        blksize = self.blksize; gn = fn + self.ext

        csz = 0.0  # current processed value
        self.encryptPbar.reset()

        with open(fn, 'rb') as src, open(gn, 'wb') as dst:
            # store actual file size and iv
            dst.write(struct.pack('<Q', fsz)); dst.write(iv)

            while 1:
                dat = src.read(blksize)
                if not dat: break
                elif len(dat) % chk:  # add padding
                    fil = chk - len(dat) % chk
                    dat += ''.join(random.sample(chars, fil))
                dst.write(vault.encrypt(dat))

                csz += blksize
                self.encryptPbar.setValue(int(round(csz * 100.0 / fsz)))
                app.processEvents()

        self.encryptPbar.setValue(self.encryptPbar.maximum())
        return gn

    def decrypt(self):
        "encrypt selected file with key"
        name, t0 = self.getName(), time.clock()
        if not name:
            self.setMessage('No file selected')
            return
        
        key = unicode(self.keyInput.text())
        if len(key) < self.minKeyLen:
            self.setMessage(('Key must be at least '
                            '{} characters long').format(self.minKeyLen))
            return

        self.lock()
        gn = self.decryptFile(key, os.path.join(self.path, name))
        if not gn: self.lock(False); return
        self.setMessage('saved "{}"'.format(os.path.basename(gn)), 7)
        self.decrypted.append(os.path.basename(gn))
        self.lock(False)
        self.populateTable(self.path)  # repopulate folder list
        self.extraLabel.setText('Decrypting took ' +
                                self.secs_fmt(time.clock() - t0))

    def decryptFile(self, key, fn):
        "decrypts a file using AES (MODE_CBC)"
        blksize = self.blksize
        gn = os.path.splitext(fn)[0]
        if os.path.exists(gn):
            self.setMessage('file already exists')
            return

        csz = 0.0  # current processed value
        fnsz = os.path.getsize(fn)
        self.decryptPbar.reset()
        
        with open(fn, 'rb') as src, open(gn, 'wb') as dst:
            # extract actual file size and iv
            fsz = struct.unpack('<Q', src.read(struct.calcsize('Q')))[0]
            iv = src.read(AES.block_size)
            vault = AES.new(self.hashKey(key), AES.MODE_CBC, iv)

            while 1:
                dat = src.read(blksize)
                if not dat: break
                dst.write(vault.decrypt(dat))

                csz += blksize
                self.decryptPbar.setValue(int(round(csz * 100.0 / fnsz)))
                app.processEvents()

            dst.truncate(fsz)  # remove padding
        self.decryptPbar.setValue(self.decryptPbar.maximum())
        return gn

    def copyKeyHash(self, action):
        "copies either the key or the hash to clipboard"
        act = str(action.text()).lower()

        if 'key' in act: txt = unicode(self.keyInput.text())
        elif 'hash' in act: txt = str(self.hashLabel.text())
        else: self.setMessage('Invalid copy selection'); return

        if not txt: self.setMessage('Empty text; Nothing to copy'); return

        if 'key' in act: self.setMessage('Key copied to clipboard')
        elif 'hash' in act: self.setMessage('Hash copied to clipboard')
        else: self.setMessage('Invalid copy selection'); return

        self.clipboard.clear()
        self.clipboard.setText(txt)

    def secs_fmt(self, secs):
        "6357 -> '1h 45m 57s'"
        Y, D, H, M = 31556952, 86400, 3600, 60
        y = int(secs // Y); secs -= y * Y
        d = int(secs // D); secs -= d * D
        h = int(secs // H); secs -= h * H
        m = int(secs // M); secs -= m * M
        res = ''
        if secs:
            if int(secs) == secs: res = str(int(secs)) + 's'
            else: res = str(round(secs, 3)) + 's'
        if m: res = str(m) + 'm ' + res
        if h: res = str(h) + 'h ' + res
        if d: res = str(d) + 'd ' + res
        if y: res = str(y) + 'y ' + res
        return res.strip()

    def closeEvent(self, event):
        self.clipboard.clear()

    def setup(self):
        "constructs the gui"
        Fixed = QtGui.QSizePolicy()
        ##MinimumExpanding = QtGui.QSizePolicy(1, 2)  # works only in PyQt4
        MinimumExpanding = QtGui.QSizePolicy(  # works in PySide and PyQt4
        QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        self.minKeyLen = 8
        self.maxKeyLen = 4096

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.splitterMoved.connect(self.splitterChanged)

        # left column
        self.leftColumn = QtGui.QWidget()
        self.vl01 = QtGui.QVBoxLayout()

        # left column - first item (0; horizonal layout 0)
        self.hl00 = QtGui.QHBoxLayout()
        self.hl00.setSpacing(5)

        self.openButton = QtGui.QPushButton('Open')
        self.openButton.setToolTip('Open folder')
        self.openButton.setMinimumSize(60, 20)
        self.openButton.setMaximumSize(60, 20)
        self.openButton.setSizePolicy(Fixed)
        self.openButton.clicked.connect(self.getFolder)

        self.folderLabel = QtGui.QLabel()
        self.folderLabel.setMinimumSize(135, 20)
        self.folderLabel.setMaximumSize(16777215, 20)
        self.folderLabel.setSizePolicy(MinimumExpanding)
        self.hl00.insertWidget(0, self.openButton)
        self.hl00.insertWidget(1, self.folderLabel)

        # left column - second item (1)
        self.folderTable = QtGui.QTableWidget()
        self.folderTable.setMinimumSize(200, 32)
        self.folderTable.horizontalHeader().setVisible(False)
        self.folderTable.horizontalHeader().setStretchLastSection(True)
        self.folderTable.verticalHeader().setVisible(False)
        self.folderTable.verticalHeader().setDefaultSectionSize(15)

        # left column - third item (2)
        self.extraLabel = QtGui.QLabel()
        self.extraLabel.setMinimumSize(200, 20)
        self.extraLabel.setMaximumSize(16777215, 20)
        self.extraLabel.setSizePolicy(MinimumExpanding)

        # finalize left column
        self.vl01.insertLayout(0, self.hl00)
        self.vl01.insertWidget(1, self.folderTable)
        self.vl01.insertWidget(2, self.extraLabel)
        self.leftColumn.setLayout(self.vl01)


        # right column
        self.rightColumn = QtGui.QWidget()
        self.vl02 = QtGui.QVBoxLayout()

        # right column - first item (0)
        self.messageLabel = QtGui.QLabel()#QtGui.QStatusBar()
        self.messageLabel.setMinimumSize(290, 20)
        self.messageLabel.setMaximumSize(16777215, 20)
        self.messageLabel.setSizePolicy(MinimumExpanding)
        #self.messageLabel.setSizeGripEnabled(False)
        self.messageLabel.setAlignment(QtCore.Qt.AlignCenter)

        # right column - second item (2; horizontal layout 1)
        self.hl01 = QtGui.QHBoxLayout()
        self.hl01.setSpacing(5)

        self.encryptButton = QtGui.QPushButton('Encrypt')
        self.encryptButton.setToolTip('Encrypt selected file')
        self.encryptButton.setMinimumSize(60, 20)
        self.encryptButton.setMaximumSize(60, 20)
        self.encryptButton.setSizePolicy(Fixed)
        self.encryptButton.clicked.connect(self.encrypt)

        self.encryptPbar = QtGui.QProgressBar()
        self.encryptPbar.setMinimumSize(225, 20)
        self.encryptPbar.setMaximumSize(16777215, 20)
        self.encryptPbar.setSizePolicy(MinimumExpanding)
        self.encryptPbar.setTextVisible(False)

        palette = self.encryptPbar.palette()  # color of progress bar
        color = QtGui.QColor(211, 70, 0)
        palette.setColor(QtGui.QPalette.Highlight, color)
        #palette.setColor(QtGui.QPalette.Base, color)
        #palette.setColor(QtGui.QPalette.WindowText, color)
        #palette.setColor(QtGui.QPalette.Button, color)
        self.encryptPbar.setPalette(palette)

        self.hl01.insertWidget(0, self.encryptButton)
        self.hl01.insertWidget(1, self.encryptPbar)

        # right column - third item (3; horizontal layout 2)
        self.hl02 = QtGui.QHBoxLayout()
        self.hl02.setSpacing(5)

        self.keyInput = QtGui.QLineEdit()
        self.keyInput.setMinimumSize(225, 20)
        self.keyInput.setMaximumSize(16777215, 20)
        self.keyInput.setSizePolicy(MinimumExpanding)
        self.keyInput.setPlaceholderText('key')
        self.keyInput.setMaxLength(self.maxKeyLen)
        self.keyInput.setAlignment(QtCore.Qt.AlignCenter)
        self.keyInput.textEdited.connect(self.showKeyLen)

        self.genKeyButton = QtGui.QPushButton('Gen Key')
        self.genKeyButton.setToolTip('Generate a random key')
        self.genKeyButton.setMinimumSize(60, 20)
        self.genKeyButton.setMaximumSize(60, 20)
        self.genKeyButton.setSizePolicy(Fixed)
        self.genKeyButton.clicked.connect(self.genKey)

        self.hl02.insertWidget(0, self.keyInput)
        self.hl02.insertWidget(1, self.genKeyButton)

        # right column - fourth item (4; horizontal layout 3)
        self.hl03 = QtGui.QHBoxLayout()
        self.hl03.setSpacing(5)

        self.decryptButton = QtGui.QPushButton('Decrypt')
        self.decryptButton.setToolTip('Decrypt selected file')
        self.decryptButton.setMinimumSize(60, 20)
        self.decryptButton.setMaximumSize(60, 20)
        self.decryptButton.setSizePolicy(Fixed)
        self.decryptButton.clicked.connect(self.decrypt)

        self.decryptPbar = QtGui.QProgressBar()
        self.decryptPbar.setMinimumSize(225, 20)
        self.decryptPbar.setMaximumSize(16777215, 20)
        self.decryptPbar.setSizePolicy(MinimumExpanding)
        self.decryptPbar.setTextVisible(False)
        self.decryptPbar.setInvertedAppearance(True)

        palette = self.decryptPbar.palette()  # color of progress bar
        color = QtGui.QColor(0, 170, 255)
        palette.setColor(QtGui.QPalette.Highlight, color)
        #palette.setColor(QtGui.QPalette.Base, color)
        #palette.setColor(QtGui.QPalette.WindowText, color)
        #palette.setColor(QtGui.QPalette.Button, color)
        self.decryptPbar.setPalette(palette)

        self.hl03.insertWidget(0, self.decryptButton)
        self.hl03.insertWidget(1, self.decryptPbar)

        # right column - fifth item (7; horizontal layout 4)
        self.hl04 = QtGui.QHBoxLayout()
        self.hl04.setSpacing(5)

        self.showKeyCB = QtGui.QCheckBox('Show Key')
        self.showKeyCB.setToolTip('Show/Hide key value')
        self.showKeyCB.setMinimumSize(75, 20)
        self.showKeyCB.setMaximumSize(75, 20)
        self.showKeyCB.setSizePolicy(Fixed)
        self.showKeyCB.clicked.connect(self.showKey)
        self.showKeyCB.setChecked(True)

        self.hashPbar = QtGui.QProgressBar()
        self.hashPbar.setMinimumSize(150, 20)
        self.hashPbar.setMaximumSize(16777215, 20)
        self.hashPbar.setSizePolicy(MinimumExpanding)
        self.hashPbar.setTextVisible(False)

        palette = self.hashPbar.palette()  # color of progress bar
        color = QtGui.QColor(31, 120, 73)
        palette.setColor(QtGui.QPalette.Highlight, color)
        #palette.setColor(QtGui.QPalette.Base, color)
        #palette.setColor(QtGui.QPalette.WindowText, color)
        #palette.setColor(QtGui.QPalette.Button, color)
        #palette.setColor(QtGui.QPalette.ButtonText, color)
        self.hashPbar.setPalette(palette)

        self.hashButton = QtGui.QPushButton('Hash')
        self.hashButton.setToolTip('Determine file hash')
        self.hashButton.setMinimumSize(60, 20)
        self.hashButton.setMaximumSize(60, 20)
        self.hashButton.setSizePolicy(Fixed)

        menu = QtGui.QMenu(self.hashButton)
        for alg in hashlib.algorithms_guaranteed: menu.addAction(alg)
        menu.addAction('Party')
        self.hashButton.setMenu(menu)
        menu.triggered.connect(self.genHash)

        self.hl04.insertWidget(0, self.showKeyCB)
        self.hl04.insertWidget(1, self.hashPbar)
        self.hl04.insertWidget(2, self.hashButton)

        # right column - sixth item (8; horizontal layout 5)
        self.hl05 = QtGui.QHBoxLayout()
        self.hl05.setSpacing(5)

        self.copyButton = QtGui.QPushButton('Copy')
        self.copyButton.setToolTip('Copy key or hash to clipboard')
        self.copyButton.setMinimumSize(60, 20)
        self.copyButton.setMaximumSize(60, 20)
        self.copyButton.setSizePolicy(Fixed)

        menu2 = QtGui.QMenu(self.copyButton)
        menu2.addAction('Copy Key'); menu2.addAction('Copy Hash')
        self.copyButton.setMenu(menu2)
        menu2.triggered.connect(self.copyKeyHash)
        #self.copyButton.clicked.connect(self.copyKeyHash)

        self.hashLabel = QtGui.QLabel()
        self.hashLabel.setMinimumSize(225, 20)
        self.hashLabel.setMaximumSize(16777215, 20)
        self.hashLabel.setSizePolicy(MinimumExpanding)
        self.hashLabel.setTextFormat(QtCore.Qt.PlainText)
        self.hashLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.hl05.insertWidget(0, self.copyButton)
        self.hl05.insertWidget(1, self.hashLabel)

        # finalize right column
        self.vl02.insertWidget(0, self.messageLabel)
        self.vl02.insertSpacerItem(1, QtGui.QSpacerItem(0, 0))
        self.vl02.insertLayout(2, self.hl01)
        self.vl02.insertLayout(3, self.hl02)
        self.vl02.insertLayout(4, self.hl03)
        self.vl02.insertSpacerItem(5, QtGui.QSpacerItem(0, 0))
        self.vl02.insertWidget(6, QtGui.QFrame())
        self.vl02.insertLayout(7, self.hl04)
        self.vl02.insertLayout(8, self.hl05)
        self.rightColumn.setLayout(self.vl02)

        # finalize main window
        self.splitter.insertWidget(0, self.leftColumn)
        self.splitter.insertWidget(1, self.rightColumn)

        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.setWindowTitle('Simple File Encryptor/Decryptor')
        self.resize(self.sizeHint())


if __name__ == '__main__':
    app.setStyle(QtGui.QStyleFactory.create('Plastique'))
    #print QtGui.QStyleFactory.keys()

    w = main(); w.show()
    ico = w.style().standardIcon(QtGui.QStyle.SP_FileDialogDetailedView)
    w.setWindowIcon(ico)
    sys.exit(app.exec_())
