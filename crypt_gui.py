from Crypto.Random import random
from Crypto.Cipher import AES
import os, sys, struct
import hashlib, string
import time

# this program can run with either pyqt5 or pyside2 - change PySide2 to PyQt5
from PySide2.QtCore import QPoint, QTimer, Qt
from PySide2.QtGui import QFontMetrics, QPalette, QColor
from PySide2.QtWidgets import (QApplication, QStyle, QFileDialog, QMessageBox,
     QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QProgressBar, QPushButton,
     QSizePolicy, QSpacerItem, QSplitter, QStatusBar, QCheckBox, QStyleFactory,
     QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout, QWidget, QSpinBox)

# new in this version (1.1.0):
#   now works in python 3, with pyqt5 or pyside 2
#   encrypts original file name, now encrypts original file size
#   original file name restored on decryption
#   can (only) rename freshly encrypted files
#   now can view files without extensions
#   better handling on wrong key or file during decryption
#   hash can now be copied right from its text with the mouse
#   random tips occasionally appear on program start
#   added version number
#   key hashing improved
#   encryption mode changed from CBC to GCM
#   what hash was previously used is now marked
#   added adjustable key size
#   improved fancy folder display
#   displays % progress in window title
#
# version (1.0.0) - no documentation of whatever (this line added for 1.1.0!)

VERSION = '1.1.0'# still in progress

global app
app = QApplication(sys.argv)  # app is used within the program

class main(QWidget):
    def __init__(self, parent=None):
        super(main, self).__init__(parent)
        self.setup()  # connections, widgets, layouts, etc.

        self.blksize = 2 ** 20  # 1 MB; must be divisible by 16
        self.ext = '.enc'  # extension is appended to encrypted files
        self.path = ''
        self.encrypted = []  # to highlight done files in list
        self.decrypted = []

        self.clipboard = QApplication.clipboard()
        self.timeout = None  # to clear message label, see setMessage

        # this program was just an excuse to play with QprogressBar
        if not hash(os.urandom(11)) % 11:
            QTimer().singleShot(50, self.windDown)

        # various random hints
        hints = ['Freshly encrypted files can be renamed in the table!',
         'Clipboard is always cleared on program close!',
         'Keys can contain emoji if you <em>really</em> want: \U0001f4e6',
         'Keys can contain emoji if you <em>really</em> want: \U0001F511',
         'This isn\'t a tip, I just wanted to say hello!',
         'Keys can be anywhere from 8 to 4096 characters long!',
         'This program was just an excuse to play with the progress bars!',
         'Select \'Party\' in the hash button for progress bar fun!',
         ('Did you know you can donate one or all of your vital organs to '
          'the Aperture Science Self-Esteem Fund for Girls? It\'s true!'),
         ('It\'s been {:,} days since Half-Life 2: Episode '
          'Two'.format(int((time.time()-1191988800)/86400))),
         'I\'m version {}!'.format(VERSION),
         'I\'m version {}.whatever!'.format(VERSION.split('.')[0]),
         ('Brought to you by me, I\'m <a href="https://orthallelous.word'
          'press.com/">Orthallelous!</a>'),
         #'Brought to you by me, I\'m Htom Sirveaux!',
         'I wonder if there\'s beer on the sun',
         'Raspberry World: For all your raspberry needs. Off the beltline',
         #'I\'ve plummented to my death and I can\'t get up',
         '<em>NOT</em> compatible with the older version!',
         ('Hello there, fellow space travellers! Until somebody gives me '
          'some new lines in KAS, that is all I can say. - Bentusi Exchange')
          ]
        if not hash(os.urandom(9)) % 4:
            self.extraLabel.setText(random.choice(hints))

    def genKey(self):
        "generate a random key"
        n = self.keySizeSB.value()
        char = string.printable.rstrip()#map(chr, range(256))
        while len(char) < n: char += char
        key = ''.join(random.sample(char, n))
        self.keyInput.setText(key)

    def showKey(self, state=None):
        "hide/show key characters"
        if state is None: state = bool(self.showKeyCB.checkState())
        else: state = bool(state)
        if state: self.keyInput.setEchoMode(QLineEdit.Normal)
        else: self.keyInput.setEchoMode(QLineEdit.PasswordEchoOnEdit)

    def getFolder(self):
        "open file dialog and fill file table"
        path = QFileDialog(directory=self.path).getExistingDirectory()
        if not path: return
        self.path = str(path)
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

        vll, ell, sl = '\u22ee', '\u2026', os.path.sep # ellipsis, slash chars
        lfg, rfg = Qt.ElideLeft, Qt.ElideRight
        lst, wdh = os.path.basename(path), self.folderLabel.width()

        path = path.replace(os.path.altsep, sl)
        self.folderLabel.setToolTip(path)

        # truncate folder location
        fnt = QFontMetrics(self.folderLabel.font())
        txt = str(fnt.elidedText(path, lfg, wdh))

        if len(txt) <= 1:  # label is way too short
            self.folderLabel.setText(vll)
            return  # but when would this happen?

        # truncate some more (don't show part of a folder name)
        if len(txt) < len(path) and txt[1] != sl:
            txt = ell + sl + txt.split(sl, 1)[-1]

        # don't truncate remaining folder name from the left
        if txt[2:] != lst and len(txt[2:]) < len(lst) + 2:
            txt = str(fnt.elidedText(ell + sl + lst, rfg, wdh))

        self.folderLabel.setText(txt)

    def populateTable(self, path):
        "fill file table with file names"
        self.showFolder(path)

        names = []
        for n in os.listdir(path):
            if os.path.isdir(os.path.join(path, n)): continue  # folder
            names.append(n)

        self.folderTable.clearContents()
        self.folderTable.setRowCount(len(names))
        self.folderTable.setColumnCount(1)

        if not names:  # no files in this folder, inform user
            self.setMessage('This folder has no files')
            return

        self.folderTable.blockSignals(True)
        selEnab = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        for i, n in enumerate(names):
            item = QTableWidgetItem()
            item.setText(n); item.setToolTip(n)
            item.setFlags(selEnab)

            # color code encrypted/decrypted files
            if n in self.encrypted:
                item.setTextColor(QColor(211, 70, 0))
                # allowed encrypted filenames to be changed
                item.setFlags(selEnab | Qt.ItemIsEditable)
            if n in self.decrypted:
                item.setForeground(QColor(0, 170, 255))
            self.folderTable.setItem(i, 0, item)
        if len(names) > 5:
            self.setMessage('{:,} files'.format(len(names)), 7)
        self.folderTable.blockSignals(False)
        return

    def editFileName(self, item):
        "change file name"
        new, old = str(item.text()), str(item.toolTip())

        result = QMessageBox.question(self, 'Renaming?',
                 ("<p align='center'>Do you wish to rename<br>" +
                  '<span style="color:#d34600;">{}</span>'.format(old) +
                  "<br>to<br>" +
                  '<span style="color:#ef4b00;">{}</span>'.format(new) +
                  '<br>?</p>'))

        self.folderTable.blockSignals(True)
        if any(i in new for i in '/?<>:*|"^'):
            self.setMessage('Invalid character in name', 7)
            item.setText(old)
        elif result == QMessageBox.Yes:
            oold = os.path.join(self.path, old)
            try:
                os.rename(oold, os.path.join(self.path, new))
                self.encrypted.remove(old); self.encrypted.append(new)
                item.setToolTip(new)
            except Exception as err:
                self.setMessage(str(err), 9)
                item.setText(old); item.setToolTip(old)
                self.encrypted.remove(new); self.encrypted.append(old)
        else: item.setText(old)
        self.folderTable.blockSignals(False)

    def setMessage(self, message, secs=4, col=None):
        "show a message for a few seconds - col must be rgb triplet tuple"
        if self.timeout:  # https://stackoverflow.com/a/21081371
            self.timeout.stop(); self.timeout.deleteLater()

        if col is None: color = 'rgb(255, 170, 127)'
        else:
            try: color = 'rgb({}, {}, {})'.format(*col)
            except: color = 'rgb(255, 170, 127)'

        self.messageLabel.setStyleSheet('background-color: {};'.format(color))
        self.messageLabel.setText(message)
        self.messageLabel.setToolTip(message)

        self.timeout = QTimer()
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
        names = [str(i.text()) for i in items]
        if names: return names[0]  # only the first selected file
        else: return ''

    def showKeyLen(self, string):
        "displays a tooltip showing length of key"
        s = len(string)
        note = '{:,} character{}'.format(s, '' if s == 1 else 's')
        tip = QToolTip
        pos = self.genKeyButton.mapToGlobal(QPoint(0,0))

        if s < self.minKeyLen:
            note = '<span style="color:#c80000;">{}</span>'.format(note)
        else:
            note = '<span style="color:#258f22;">{}</span>'.format(note)
        tip.showText(pos, note)

    def lock(self, flag=True):
        "locks buttons if True"
        stuff = [self.openButton, self.encryptButton, self.decryptButton,
                 self.genKeyButton, self.hashButton, self.showKeyCB,
                 self.copyButton, self.keyInput, self.keySizeSB, ]
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
        self.messageLabel.setStyleSheet('background-color: rgb(127,170,255);')
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
        for j, k, l in loops: a.setValue(int(j)); process(); sleep(0.002)
        process(); a.setInvertedAppearance(True); process()
        for j, k, l in ivops: a.setValue(int(j)); process(); sleep(0.002)

        # bars
        sleep(0.5); self.setMessage('Bars!'); process()
        self.messageLabel.setStyleSheet('background-color: rgb(127,255,170);')
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
        name, t0 = self.getName(), time.perf_counter()

        # mark what hash was used in the drop-down menu
        for i in self.hashButton.menu().actions():
            if i == action: i.setIconVisibleInMenu(True)
            else: i.setIconVisibleInMenu(False)

        if str(action.text()) == 'Party':
            self.weeeeeee(); self.windDown('Winding down...')
            return
        if not name:
            self.setMessage('No file selected')
            return
        if not os.path.exists(os.path.join(self.path, name)):
            self.setMessage('File does not exist')
            return

        self.lock()
        hsh = self.hashFile(os.path.join(self.path, name),
                            getattr(hashlib, str(action.text())))
        self.lock(False)
        #hsh = str(action.text()) + ': ' + hsh
        self.hashLabel.setText(hsh); self.hashLabel.setToolTip(hsh)
        self.extraLabel.setText(str(action.text()) + ' hash took ' +
                                self.secs_fmt(time.perf_counter() - t0))

    def hashFile(self, fn, hasher):
        "returns the hash value of a file"
        hsh, blksize = hasher(), self.blksize
        fsz, csz = os.path.getsize(fn), 0.0

        self.hashPbar.reset()
        prog, title = '(# {:.02%}) {}', self.windowTitle()
        with open(fn, 'rb') as f:
            while 1:
                blk = f.read(blksize)
                if not blk: break
                hsh.update(blk)

                csz += blksize
                self.hashPbar.setValue(int(round(csz * 100.0 / fsz)))
                app.processEvents()
                self.setWindowTitle(prog.format(csz / fsz, title))

        self.hashPbar.setValue(self.hashPbar.maximum())
        self.setWindowTitle(title)
        return hsh.hexdigest()

    def hashKey(self, key, salt=b''):
        "hashes a key for encrypting/decrypting file"
        salt = salt.encode() if type(salt) != bytes else salt
        key = key.encode() if type(key) != bytes else key
        p = app.processEvents
        self.setMessage('Key Hashing...', col=(226, 182, 249)); p()
        key = hashlib.pbkdf2_hmac('sha512', key, salt, 333101); p()
        self.clearMessage(); p()
        return hashlib.sha3_256(key).digest() # AES requires a 32 char key

    def encrypt(self):
        "encrypt selected file with key"
        name, t0 = self.getName(), time.perf_counter()
        if not name:
            self.setMessage('No file selected')
            return
        if not os.path.exists(os.path.join(self.path, name)):
            self.setMessage('File does not exist')
            return
        key = str(self.keyInput.text())
        if len(key) < self.minKeyLen:
            self.setMessage(('Key must be at least '
            '{} characters long').format(self.minKeyLen))
            return

        self.lock()
        gn = self.encryptFile(key, os.path.join(self.path, name))
        if not gn: self.lock(False); return
        self.encrypted.append(os.path.basename(gn))
        self.lock(False)

        self.populateTable(self.path)  # repopulate folder list
        bn, tt = os.path.basename(gn), time.perf_counter() - t0
        self.setMessage('Encrypted, saved "{}"'.format(bn, 13))
        self.extraLabel.setText('Encrypting took ' + self.secs_fmt(tt))

    def encryptFile(self, key, fn):
        "encrypts a file using AES (MODE_GCM)"
        chars = ''.join(map(chr, range(256))).encode()
        chk = AES.block_size; sample = random.sample
        iv = bytes(sample(chars, chk * 2)); salt = bytes(sample(chars*2, 256))

        vault = AES.new(self.hashKey(key, salt), AES.MODE_GCM, iv)
        fsz = os.path.getsize(fn); del key
        blksize = self.blksize; gn = fn + self.ext

        fne = os.path.basename(fn).encode(); fnz = len(fne)
        if len(fne) % chk: fne += bytes(sample(chars, chk - len(fne) % chk))

        csz = 0.0  # current processed value
        self.encryptPbar.reset()
        prog, title = '(E {:.02%}) {}', self.windowTitle()

        with open(fn, 'rb') as src, open(gn, 'wb') as dst:
            dst.write(bytes([0] * 16))  # spacer for MAC written at end
            dst.write(iv); dst.write(salt)  # store iv, salt
            # is it safe to store MAC, iv, salt plain right in file?
            # can't really store them encrypted,
            # or elsewhere in this model of single file encryption?
            # can't have another file for the file to lug around

            # store file size, file name length
            dst.write(vault.encrypt(struct.pack('<2Q', fsz, fnz)))
            dst.write(vault.encrypt(fne))  # store filename

            while 1:
                dat = src.read(blksize)
                if not dat: break
                elif len(dat) % chk:  # add padding
                    fil = chk - len(dat) % chk
                    dat += bytes(sample(chars, fil))
                dst.write(vault.encrypt(dat))

                csz += blksize  # show progress
                self.encryptPbar.setValue(int(round(csz * 100.0 / fsz)))
                self.setWindowTitle(prog.format(csz / fsz, title))
                app.processEvents()

            stuf = random.randrange(23)  # pack in more stuffing just 'cause
            fing = b''.join(bytes(sample(chars, 16)) for i in range(stuf))
            dst.write(vault.encrypt(fing))  # and for annoyance

            dst.seek(0); dst.write(vault.digest())  # write MAC
            self.hashLabel.setText('MAC: ' + vault.hexdigest())

        self.encryptPbar.setValue(self.encryptPbar.maximum())
        self.setWindowTitle(title)
        return gn

    def decrypt(self):
        "encrypt selected file with key"
        name, t0 = self.getName(), time.perf_counter()
        if not name:
            self.setMessage('No file selected')
            return
        if not os.path.exists(os.path.join(self.path, name)):
            self.setMessage('File does not exist')
            return
        key = str(self.keyInput.text())
        if len(key) < self.minKeyLen:
            self.setMessage(('Key must be at least '
            '{} characters long').format(self.minKeyLen))
            return

        self.lock()
        gn = self.decryptFile(key, os.path.join(self.path, name))
        if not gn: self.lock(False); return
        self.decrypted.append(os.path.basename(gn))
        self.lock(False)

        self.populateTable(self.path)  # repopulate folder list
        bn, tt = os.path.basename(gn), time.perf_counter() - t0
        self.setMessage('Decrypted, saved "{}"'.format(bn, 13))
        self.extraLabel.setText('Decrypting took ' + self.secs_fmt(tt))


    def decryptFile(self, key, fn):
        "decrypts a file using AES (MODE_GCM)"
        blksize = self.blksize
        gn = hashlib.md5(os.path.basename(fn).encode()).hexdigest()
        gn = os.path.join(self.path, gn)  # temporary name
        if os.path.exists(gn): self.setMessage('file already exists'); return

        self.decryptPbar.reset(); csz = 0.0  # current processed value
        chk, fnsz = AES.block_size, os.path.getsize(fn)
        prog, title = '(D {:.02%}) {}', self.windowTitle()
        try:
            with open(fn, 'rb') as src, open(gn, 'wb') as dst:
                # extract iv, salt
                MAC = src.read(16)
                iv = src.read(AES.block_size * 2); salt = src.read(256)
                vault = AES.new(self.hashKey(key, salt), AES.MODE_GCM, iv)

                # extract file size, file name length
                sizes = src.read(struct.calcsize('<2Q'))
                fsz, fnz = struct.unpack('<2Q', vault.decrypt(sizes))

                # extract filename; round up fnz to nearest chk
                rnz = fnz if not fnz % chk else fnz + chk - fnz % chk
                rfn = vault.decrypt(src.read(rnz))[:fnz].decode()
                self.setMessage('Found "{}"'.format(rfn), 13, (255, 211, 127))

                while 1:
                    dat = src.read(blksize)
                    if not dat: break
                    dst.write(vault.decrypt(dat))

                    csz += blksize  # show progress
                    self.decryptPbar.setValue(int(round(csz * 100.0 / fnsz)))
                    self.setWindowTitle(prog.format(csz / fnsz, title))
                    app.processEvents()

                dst.truncate(fsz)  # remove padding
            vault.verify(MAC); self.hashLabel.setText('')

        except (ValueError, KeyError) as err:
            os.remove(gn); self.setMessage('Invalid decryption!')
            self.setWindowTitle(title)
            return
        except Exception as err:
            os.remove(gn); self.setMessage('Invalid key or file!')
            self.setWindowTitle(title)
            return
        self.decryptPbar.setValue(self.decryptPbar.maximum())
        self.setWindowTitle(title)

        # restore original file name
        name, ext = os.path.splitext(rfn); count = 1
        fn = os.path.join(self.path, name + ext)
        while os.path.exists(fn):
            fn = os.path.join(self.path, name + '_{}'.format(count) + ext)
            count += 1
        os.rename(gn, fn)  # restore original name
        return fn  # saved name

    def copyKeyHash(self, action):
        "copies either the key or the hash to clipboard"
        act = str(action.text()).lower()

        if 'key' in act: txt = str(self.keyInput.text())
        elif 'hash' in act: txt = str(self.hashLabel.text())
        else: self.setMessage('Invalid copy selection'); return

        if not txt: self.setMessage('Empty text; Nothing to copy'); return

        if 'key' in act: self.setMessage('Key copied to clipboard')
        elif 'hash' in act: self.setMessage('Hash copied to clipboard')
        else: self.setMessage('Invalid copy selection'); return

        self.clipboard.clear()
        self.clipboard.setText(txt)

    def secs_fmt(self, s):
        "6357 -> '1h 45m 57s'"
        Y, D, H, M = 31556952, 86400, 3600, 60
        y = int(s // Y); s -= y * Y
        d = int(s // D); s -= d * D
        h = int(s // H); s -= h * H
        m = int(s // M); s -= m * M

        r = (str(int(s)) if int(s) == s else str(round(s, 3))) + 's'

        if m: r = str(m) + 'm ' + r
        if h: r = str(h) + 'h ' + r
        if d: r = str(d) + 'd ' + r
        if y: r = str(y) + 'y ' + r
        return r.strip()

    def closeEvent(self, event):
        self.clipboard.clear()

    def setup(self):
        "constructs the gui"
        Fixed = QSizePolicy()
        MinimumExpanding = QSizePolicy(
        QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.minKeyLen = 8
        self.maxKeyLen = 4096

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.splitterMoved.connect(self.splitterChanged)

        # left column
        self.leftColumn = QWidget()
        self.vl01 = QVBoxLayout()

        # left column - first item (0; horizonal layout 0)
        self.hl00 = QHBoxLayout()
        self.hl00.setSpacing(5)

        self.openButton = QPushButton('Open')
        self.openButton.setToolTip('Open folder')
        self.openButton.setMinimumSize(60, 20)
        self.openButton.setMaximumSize(60, 20)
        self.openButton.setSizePolicy(Fixed)
        self.openButton.clicked.connect(self.getFolder)
        #ico = self.style().standardIcon(QStyle.SP_DirIcon)
        #self.openButton.setIcon(ico)

        self.folderLabel = QLabel()
        self.folderLabel.setMinimumSize(135, 20)
        self.folderLabel.setMaximumSize(16777215, 20)
        self.folderLabel.setSizePolicy(MinimumExpanding)
        self.hl00.insertWidget(0, self.openButton)
        self.hl00.insertWidget(1, self.folderLabel)

        # left column - second item (1)
        self.folderTable = QTableWidget()
        self.folderTable.setMinimumSize(200, 32)
        self.folderTable.horizontalHeader().setVisible(False)
        self.folderTable.horizontalHeader().setStretchLastSection(True)
        self.folderTable.verticalHeader().setVisible(False)
        self.folderTable.verticalHeader().setDefaultSectionSize(15)
        self.folderTable.itemChanged.connect(self.editFileName)

        # left column - third item (2)
        self.extraLabel = QLabel()
        self.extraLabel.setMinimumSize(200, 20)
        self.extraLabel.setMaximumSize(16777215, 20)
        self.extraLabel.setSizePolicy(MinimumExpanding)
        self.extraLabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

        # finalize left column
        self.vl01.insertLayout(0, self.hl00)
        self.vl01.insertWidget(1, self.folderTable)
        self.vl01.insertWidget(2, self.extraLabel)
        self.leftColumn.setLayout(self.vl01)

        # right column
        self.rightColumn = QWidget()
        self.vl02 = QVBoxLayout()

        # right column - first item (0)
        self.messageLabel = QLabel()
        self.messageLabel.setMinimumSize(290, 20)
        self.messageLabel.setMaximumSize(16777215, 20)
        self.messageLabel.setSizePolicy(MinimumExpanding)
        self.messageLabel.setAlignment(Qt.AlignCenter)

        # right column - second item (2; horizontal layout 1)
        self.hl01 = QHBoxLayout()
        self.hl01.setSpacing(5)

        self.encryptButton = QPushButton('Encrypt')#\U0001F512
        self.encryptButton.setToolTip('Encrypt selected file')
        self.encryptButton.setMinimumSize(60, 20)
        self.encryptButton.setMaximumSize(60, 20)
        self.encryptButton.setSizePolicy(Fixed)
        self.encryptButton.clicked.connect(self.encrypt)

        self.encryptPbar = QProgressBar()
        self.encryptPbar.setMinimumSize(225, 20)
        self.encryptPbar.setMaximumSize(16777215, 20)
        self.encryptPbar.setSizePolicy(MinimumExpanding)
        self.encryptPbar.setTextVisible(False)

        palette = self.encryptPbar.palette()  # color of progress bar
        color = QColor(211, 70, 0)
        palette.setColor(QPalette.Highlight, color)
        self.encryptPbar.setPalette(palette)

        self.hl01.insertWidget(0, self.encryptButton)
        self.hl01.insertWidget(1, self.encryptPbar)

        # right column - third item (3; horizontal layout 2)
        self.hl02 = QHBoxLayout()
        self.hl02.setSpacing(5)

        self.keyInput = QLineEdit()
        self.keyInput.setMinimumSize(225, 20)
        self.keyInput.setMaximumSize(16777215, 20)
        self.keyInput.setSizePolicy(MinimumExpanding)
        self.keyInput.setPlaceholderText('key')
        self.keyInput.setMaxLength(self.maxKeyLen)
        self.keyInput.setAlignment(Qt.AlignCenter)
        self.keyInput.textEdited.connect(self.showKeyLen)

        self.genKeyButton = QPushButton('Gen Key')#\U0001F511
        self.genKeyButton.setToolTip('Generate a random key')
        self.genKeyButton.setMinimumSize(60, 20)
        self.genKeyButton.setMaximumSize(60, 20)
        self.genKeyButton.setSizePolicy(Fixed)
        self.genKeyButton.clicked.connect(self.genKey)

        self.keySizeSB = QSpinBox()
        self.keySizeSB.setToolTip('Length of key to generate')
        self.keySizeSB.setRange(32, 1024)
        self.keySizeSB.setMinimumSize(40, 20)
        self.keySizeSB.setMaximumSize(40, 20)
        self.keySizeSB.setSizePolicy(Fixed)
        self.keySizeSB.setAlignment(Qt.AlignCenter)
        self.keySizeSB.setButtonSymbols(QSpinBox.NoButtons)
        self.keySizeSB.setWrapping(True)

        self.hl02.insertWidget(0, self.keyInput)
        self.hl02.insertWidget(1, self.genKeyButton)
        self.hl02.insertWidget(2, self.keySizeSB)

        # right column - fourth item (4; horizontal layout 3)
        self.hl03 = QHBoxLayout()
        self.hl03.setSpacing(5)

        self.decryptButton = QPushButton('Decrypt')#\U0001F513
        self.decryptButton.setToolTip('Decrypt selected file')
        self.decryptButton.setMinimumSize(60, 20)
        self.decryptButton.setMaximumSize(60, 20)
        self.decryptButton.setSizePolicy(Fixed)
        self.decryptButton.clicked.connect(self.decrypt)

        self.decryptPbar = QProgressBar()
        self.decryptPbar.setMinimumSize(225, 20)
        self.decryptPbar.setMaximumSize(16777215, 20)
        self.decryptPbar.setSizePolicy(MinimumExpanding)
        self.decryptPbar.setTextVisible(False)
        self.decryptPbar.setInvertedAppearance(True)

        palette = self.decryptPbar.palette()  # color of progress bar
        color = QColor(0, 170, 255)
        palette.setColor(QPalette.Highlight, color)
        self.decryptPbar.setPalette(palette)

        self.hl03.insertWidget(0, self.decryptButton)
        self.hl03.insertWidget(1, self.decryptPbar)

        # right column - fifth item (7; horizontal layout 4)
        self.hl04 = QHBoxLayout()
        self.hl04.setSpacing(5)

        self.showKeyCB = QCheckBox('Show Key')
        self.showKeyCB.setToolTip('Show/Hide key value')
        self.showKeyCB.setMinimumSize(75, 20)
        self.showKeyCB.setMaximumSize(75, 20)
        self.showKeyCB.setSizePolicy(Fixed)
        self.showKeyCB.clicked.connect(self.showKey)
        self.showKeyCB.setChecked(True)

        self.hashPbar = QProgressBar()
        self.hashPbar.setMinimumSize(150, 20)
        self.hashPbar.setMaximumSize(16777215, 20)
        self.hashPbar.setSizePolicy(MinimumExpanding)
        self.hashPbar.setTextVisible(False)

        palette = self.hashPbar.palette()  # color of progress bar
        color = QColor(31, 120, 73)
        palette.setColor(QPalette.Highlight, color)
        self.hashPbar.setPalette(palette)

        self.hashButton = QPushButton('Hash')
        self.hashButton.setToolTip('Determine file hash')
        self.hashButton.setMinimumSize(60, 20)
        self.hashButton.setMaximumSize(60, 20)
        self.hashButton.setSizePolicy(Fixed)

        menu = QMenu(self.hashButton)
        ico = self.style().standardIcon(QStyle.SP_DialogYesButton)
        for alg in sorted(filter(lambda x: 'shake' not in x, hashlib.algorithms_guaranteed), key=lambda n:(len(n), sorted(hashlib.algorithms_guaranteed).index(n))):
            menu.addAction(ico, alg)  # drop shake algs as their .hexdigest requires an argument - the rest don't
        menu.addAction(ico, 'Party')
        for i in menu.actions(): i.setIconVisibleInMenu(False)
        self.hashButton.setMenu(menu)
        menu.triggered.connect(self.genHash)

        self.hl04.insertWidget(0, self.showKeyCB)
        self.hl04.insertWidget(1, self.hashPbar)
        self.hl04.insertWidget(2, self.hashButton)

        # right column - sixth item (8; horizontal layout 5)
        self.hl05 = QHBoxLayout()
        self.hl05.setSpacing(5)

        self.copyButton = QPushButton('Copy')#\U0001F4CB
        self.copyButton.setToolTip('Copy key or hash to clipboard')
        self.copyButton.setMinimumSize(60, 20)
        self.copyButton.setMaximumSize(60, 20)
        self.copyButton.setSizePolicy(Fixed)

        menu2 = QMenu(self.copyButton)
        menu2.addAction('Copy Key'); menu2.addAction('Copy Hash')
        self.copyButton.setMenu(menu2)
        menu2.triggered.connect(self.copyKeyHash)

        self.hashLabel = QLabel()
        self.hashLabel.setMinimumSize(225, 20)
        self.hashLabel.setMaximumSize(16777215, 20)
        self.hashLabel.setSizePolicy(MinimumExpanding)
        self.hashLabel.setTextFormat(Qt.PlainText)
        self.hashLabel.setAlignment(Qt.AlignCenter)
        self.hashLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.hl05.insertWidget(0, self.copyButton)
        self.hl05.insertWidget(1, self.hashLabel)

        # finalize right column
        self.vl02.insertWidget(0, self.messageLabel)
        self.vl02.insertSpacerItem(1, QSpacerItem(0, 0))
        self.vl02.insertLayout(2, self.hl01)
        self.vl02.insertLayout(3, self.hl02)
        self.vl02.insertLayout(4, self.hl03)
        self.vl02.insertSpacerItem(5, QSpacerItem(0, 0))
        self.vl02.insertWidget(6, QFrame())
        self.vl02.insertLayout(7, self.hl04)
        self.vl02.insertLayout(8, self.hl05)
        self.rightColumn.setLayout(self.vl02)

        # finalize main window
        self.splitter.insertWidget(0, self.leftColumn)
        self.splitter.insertWidget(1, self.rightColumn)

        layout = QHBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.setWindowTitle('Simple File Encryptor/Decryptor')
        self.resize(self.sizeHint())


if __name__ == '__main__':
    w = main(); w.show()
    ico = w.style().standardIcon(QStyle.SP_FileDialogDetailedView)
    w.setWindowIcon(ico)
    sys.exit(app.exec_())
