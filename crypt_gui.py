# Simple file encrypter
# Copyright (C) 2019 - 2025, Electrostatus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pip install pycryptodome
from Crypto.Random import random
from Crypto.Cipher import AES
import os, sys, struct
import hashlib, string
import time

# pip install pyside6
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QActionGroup, QKeySequence, QFontMetrics, QColor
from PySide6.QtWidgets import (QApplication, QStyle, QFileDialog, QMessageBox,
     QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QProgressBar, QPushButton,
     QSizePolicy, QSpacerItem, QSplitter, QStatusBar, QCheckBox, QStyleFactory,
     QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout, QWidget, QSpinBox,
      QToolButton, QWidgetAction, QGridLayout)


# Version (1.2.0) - Second Update (2025-09-16)
# https://orthallelous.wordpress.com/2025/09/16/simple-file-encrypter-version-1-2/
#   PROGRAM CHANGES:
#    moved to PySide6 (2025-06-07)
#    added more options to the generate key button (2025-05-24)
#    added short 'how to' description (2025-05-17)
#    fiddled the the layout a bit, switched to icons for some buttons (2025-05-10)
#    changed copy and hash buttons to tool buttons for better selecting (2025-05-07)
#    fixed showFolder/showFolder now accurate to elide path: https://orthallelous.wordpress.com/2019/07/15/elide-path/ (2019-11-09)
#    fixed cancel button not disappearing on failed decryption (2019-11-07)
#
# Version (1.1.0) - First Update (2019-05-02):
# https://orthallelous.wordpress.com/2019/05/02/simple-file-encrypter-version-1-1/
#   CRYPTION CHANGES:
#    encryption mode changed from CBC to GCM
#    encrypts original file name, now encrypts original file size
#    better handling on wrong key or file during decryption
#    original file name restored on decryption
#    can (only) rename freshly encrypted files
#    added adjustable key size
#    key hashing improved
#   PROGRAM CHANGES:
#    now works in python 3, with pyqt5 or pyside 2
#    now can view files without extensions
#    hash can now be copied right from its text with the mouse
#    random "tips" occasionally appear on program start
#    what hash was previously used is now marked
#    displays % progress in window title
#    improved fancy folder display
#    added version number
#    added cancel button
#    placed this file/program under GNU General Public License v3.0
#
# Version (1.0.0) - First Release (2019-01-17):
# https://orthallelous.wordpress.com/2019/01/17/simple-file-encrypter/

VERSION = '1.2.0'

global app
app = QApplication(sys.argv)  # app is used within the program

class main(QWidget):
    def __init__(self, parent=None):
        super(main, self).__init__(parent)
        self.setup()  # connections, widgets, layouts, etc.

        self.blksize = 2 ** 21  # 2 MB; must be divisible by 16
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
            hnt = random.choice(hints)
            self.extraLabel.setText(hnt)
            self.extraLabel.setToolTip(hnt)

    def genKey(self):
        "generate a random key"
        n = self.keySizeSB.value()

        #char = string.printable.strip()
        char = ''
        if self.useUprCB.isChecked(): char += string.ascii_uppercase
        if self.useLwrCB.isChecked(): char += string.ascii_lowercase
        if self.useNumCB.isChecked(): char += string.digits
        if self.usePunCB.isChecked(): char += string.punctuation

        if self.useAccCB.isChecked():
            m = max(16, min(2 * n, 191))
            acc = random.sample(range(192, 383), m)
            char += ''.join(map(chr, acc))

        # https://en.wikipedia.org/wiki/Miscellaneous_Symbols_and_Pictographs
        if self.useEmjCB.isChecked():
            # generate m random emojis
            m = max(16, min(2 * n, 768))
            emj = random.sample(range(0x1F300, 0x1F600), m)
            char += ''.join(map(chr, emj))

        if not char:
            self.showKeyPB.setChecked(False)
            self.showKey(True)
            hey = 'Turn one of those checkboxes back on'
            self.keyInput.setPlaceholderText(hey)
            self.keyInput.setText('')
            return
        else:
            while len(char) < n: char += char
            key = ''.join(random.sample(char, n))

        self.keyInput.setText(key)
        self.keyInput.setPlaceholderText('Key')
        self.showKeyLen(key, False)

    def showKey(self, state=None):
        "hide/show key characters"
        if state is None: state = bool(self.showKeyPB.checkState())
        else: state = bool(state)
        if state: self.keyInput.setEchoMode(QLineEdit.Normal)
        else: self.keyInput.setEchoMode(QLineEdit.PasswordEchoOnEdit)

    def showKeyLen(self, string, display=True):
        "displays a tooltip showing length of key"
        s = len(string)
        note = '{:,} character{}'.format(s, '' if s == 1 else 's')
        col = '#c80000' if s < self.minKeyLen else '#258f22'
        note = f'<span style="color:{col};">{note}</span>'

        if display:
            pos = self.genKeyButton.mapToGlobal(QPoint(0,0))
            QToolTip.showText(pos, note)
        self.keyInput.setToolTip(note)

    def getFolder(self):
        "open file dialog and fill file table"
        path = QFileDialog(directory=self.path).getExistingDirectory()
        if not path: return
        self.path = str(path)
        self.populateTable(self.path)
        self.encrypted, self.decrypted = list(), list()

    def showFolder(self, path):
        "displays current path, truncating as needed"
        if not path: return

        ell, sl = '\u2026', os.path.sep # ellipsis, slash chars
        lfg, rfg = Qt.ElideLeft, Qt.ElideRight
        lst, wdh = os.path.basename(path), self.folderLabel.width()

        path = path.replace(os.path.altsep or '\\', sl)
        self.folderLabel.setToolTip(path)

        # truncate folder location
        fnt = QFontMetrics(self.folderLabel.font())
        txt = str(fnt.elidedText(path, lfg, wdh))

        if len(txt) <= 1:  # label is way too short
            self.folderLabel.setText('\u22ee' if txt != sl else txt)
            return  # but when would this happen?

        # truncate some more (don't show part of a folder name)
        if len(txt) < len(path) and txt[1] != sl:
            txt = ell + sl + txt.split(sl, 1)[-1]

            # don't truncate remaining folder name from the left
            if txt[2:] != lst and len(txt[2:]) < len(lst) + 2:
                txt = str(fnt.elidedText(ell + sl + lst, rfg, wdh))
        # you'd think len(txt) < len(lst) would work, but no; you'd be wrong
        self.folderLabel.setText(txt)

    def resizeEvent(self, event):
        self.showFolder(self.path)  # update how the folder is shown

    def splitterChanged(self, pos):
        self.showFolder(self.path)  # likewise

    def populateTable(self, path):
        "fill file table with file names"
        self.showFolder(path)

        names = []  # in Windows, listdir is sorted; in Linux, not so.
        for n in sorted(os.listdir(path)):
            if os.path.isdir(os.path.join(path, n)): continue  # folder
            names.append(n)

        self.folderTable.clearContents()
        self.folderTable.verticalHeader().setStretchLastSection(False)
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
                item.setForeground(QColor(211, 70, 0))
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

        self.encryptPbar.setValue(self.encryptPbar.minimum())
        self.decryptPbar.setValue(self.decryptPbar.minimum())
        self.hashPbar.setValue(self.hashPbar.minimum())

    def getName(self):
        "return file name of selected"
        items = self.folderTable.selectedItems()
        names = [str(i.text()) for i in items]
        if names: return names[0]  # only the first selected file
        else: return ''

    def lock(self, flag=True):
        "locks buttons if True"
        stuff = [self.openButton, self.encryptButton, self.decryptButton,
                 self.genKeyButton, self.hashButton, self.showKeyPB,
                 self.copyButton, self.keyInput,
                 self.keySizeSB, self.folderTable, ]
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
        av, bv, cv = a.setValue, b.setValue, c.setValue
        p, s = app.processEvents, time.sleep

        am, bm, cm = a.minimum(), b.minimum(), c.minimum()
        ax, bx, cx = a.maximum(), b.maximum(), c.maximum()
        a.reset(); b.reset(); c.reset()

        loops = self._lerp((am, bm, cm), (ax, bx, cx), 100)
        ivops = loops[::-1]

        # up and up!
        for i in range(3):
            for j, k, l in loops:
                av(int(j)); bv(int(k)); cv(int(l))
                p(); s(0.01)

        av(ax); bv(bx); cv(cx)
        s(0.25)
        av(am); bv(bm); cv(cm)

        # snake!
        self.setMessage('Snake time!')
        self.messageLabel.setStyleSheet('background-color:rgb(127,170,255);')
        for i in range(2):
            for j, k, l in loops: av(int(j)); p(); s(0.002)
            p(); a.setInvertedAppearance(True); p()
            for j, k, l in ivops: av(int(j)); p(); s(0.002)

            for j, k, l in loops: bv(int(k)); p(); s(0.002)
            p(); b.setInvertedAppearance(False); p()
            for j, k, l in ivops: bv(int(k)); p(); s(0.002)

            for j, k, l in loops: cv(int(l)); p(); s(0.002)
            p(); c.setInvertedAppearance(True); p()
            for j, k, l in ivops: cv(int(l)); p(); s(0.002)

            p(); b.setInvertedAppearance(True); p()
            for j, k, l in loops: bv(int(k)); p(); s(0.002)
            p(); b.setInvertedAppearance(False); p()
            for j, k, l in ivops: bv(int(k)); p(); s(0.002)
            p()

            a.setInvertedAppearance(False)
            b.setInvertedAppearance(True)
            c.setInvertedAppearance(False)
        for j, k, l in loops: av(int(j)); p(); s(0.002)
        p(); a.setInvertedAppearance(True); p()
        for j, k, l in ivops: av(int(j)); p(); s(0.002)

        # bars
        s(0.5); self.setMessage('Bars!'); p()
        self.messageLabel.setStyleSheet('background-color:rgb(127,255,170);')
        for i in range(2):
            av(ax); s(0.65); av(am); s(0.25); p()
            bv(bx); s(0.65); bv(bm); s(0.25); p()
            cv(cx); s(0.65); cv(cm); s(0.25); p()
            bv(bx); s(0.65); bv(bm); s(0.25); p()

        # okay, enough
        p(); av(ax); bv(bx); cv(cx)
        #av(am); bv(bm); cv(cm)
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
        av, bv, cv = a.setValue, b.setValue, c.setValue
        a.reset(); b.reset(); c.reset()
        loops = self._lerp((ax, bx, cx), (am, bm, cm), 100)
        for j, k, l in loops:
            av(int(j)); bv(int(k)); cv(int(l))
            app.processEvents()
            time.sleep(0.02)
        a.reset(); b.reset(); c.reset()
        self.lock(False); self.clearMessage()

    def genHash(self, action=None):
        "generate hash of selected file and display it"
        name, t0 = self.getName(), time.perf_counter()
        if type(action) is bool: action = None

        # find what hash was used in the drop-down menu
        for act in self.hashButton.menu().actions():
            if act.isChecked():
                self.hashButton.setToolTip(act.text())
                if str(act.text()) != 'Party':
                    self._prior_hsh = act
                if action is None: action = act
                break

        if str(action.text()) == 'Party':
            self.weeeeeee(); self.windDown('Winding down...')
            self._prior_hsh.setChecked(True)
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
        info = (str(action.text()) + ' hash took ' +
                self.secs_fmt(time.perf_counter() - t0))
        self.extraLabel.setText(info); self.extraLabel.setToolTip(info)

    def setCancel(self):
        "cancel operation"
        self._requestStop = True

    def showCancelButton(self, state=False):
        "show/hide cancel button"
        self.cancelButton.blockSignals(not state)
        self.cancelButton.setEnabled(state)
        if state:
            self.cancelButton.show()
            self.showKeyPB.hide()
            self.keyInput.hide()
            self.genKeyButton.hide()
            self.keySizeSB.hide()
        else:
            self.cancelButton.hide()
            self.showKeyPB.show()
            self.keyInput.show()
            self.genKeyButton.show()
            self.keySizeSB.show()

    def hashFile(self, fn, hasher):
        "returns the hash value of a file"
        hsh, blksize = hasher(), self.blksize
        fsz, csz = os.path.getsize(fn), 0.0

        self.hashPbar.reset(); self.showCancelButton(True)
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
                if self._requestStop: break

        self.hashPbar.setValue(self.hashPbar.maximum())
        self.setWindowTitle(title); self.showCancelButton(False)

        if self._requestStop:
            self.setMessage('Hashing canceled!')
            self.hashPbar.setValue(self.hashPbar.minimum())
            self._requestStop = False; return
        return hsh.hexdigest()

    def hashKey(self, key, salt=b''):
        "hashes a key for encrypting/decrypting file"
        salt = salt.encode() if type(salt) != bytes else salt
        key = key.encode() if type(key) != bytes else key
        p = app.processEvents
        self.setMessage('Key Hashing...', col=(226, 182, 249)); p()
        key = hashlib.pbkdf2_hmac('sha512', key, salt, 444401); p()
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
        #self.encryptPbar.setValue(self.encryptPbar.minimum())
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
        prog, title = '({:.02%}) {}', self.windowTitle()
        self.showCancelButton(True)

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

            # read file in and encrypt
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

                if self._requestStop: break

            # finished file, finish up
            if not self._requestStop:
                stuf = random.randrange(263)  # pack in more stuffing
                fing = b''.join(bytes(sample(chars, 16)) for i in range(stuf))
                dst.write(vault.encrypt(fing))  # and for annoyance

                dst.seek(0); dst.write(vault.digest())  # write MAC
                self.hashLabel.setText('MAC: ' + vault.hexdigest())

        self.encryptPbar.setValue(self.encryptPbar.maximum())
        self.setWindowTitle(title); self.showCancelButton(False)

        if self._requestStop:
            self.setMessage('Encryption canceled!')
            self.encryptPbar.setValue(self.encryptPbar.minimum())
            self._requestStop = False; os.remove(gn); return
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
        prog, title = '({:.02%}) {}', self.windowTitle()
        try:
            with open(fn, 'rb') as src, open(gn, 'wb') as dst:
                # extract iv, salt
                MAC = src.read(16)
                iv = src.read(AES.block_size * 2); salt = src.read(256)
                vault = AES.new(self.hashKey(key, salt), AES.MODE_GCM, iv)
                self.showCancelButton(True)

                # extract file size, file name length
                sizes = src.read(struct.calcsize('<2Q'))
                fsz, fnz = struct.unpack('<2Q', vault.decrypt(sizes))

                # extract filename; round up fnz to nearest chk
                rnz = fnz if not fnz % chk else fnz + chk - fnz % chk
                rfn = vault.decrypt(src.read(rnz))[:fnz].decode()
                self.setMessage('Found "{}"'.format(rfn), 13, (255, 211, 127))

                # read in file and decrypt
                while 1:
                    dat = src.read(blksize)
                    if not dat: break
                    dst.write(vault.decrypt(dat))

                    csz += blksize  # show progress
                    self.decryptPbar.setValue(int(round(csz * 100.0 / fnsz)))
                    self.setWindowTitle(prog.format(1 - (csz / fnsz), title))
                    app.processEvents()
                    if self._requestStop: break

                if not self._requestStop: dst.truncate(fsz)  # remove padding
            if not self._requestStop:
                vault.verify(MAC); self.hashLabel.setText('')

        except (ValueError, KeyError) as err:
            os.remove(gn); self.setMessage('Invalid decryption!')
            self.setWindowTitle(title); self.showCancelButton(False)
            return
        except Exception as err:
            os.remove(gn); self.setMessage('Invalid key or file!')
            self.setWindowTitle(title); self.showCancelButton(False)
            return
        self.decryptPbar.setValue(self.decryptPbar.maximum())
        self.setWindowTitle(title); self.showCancelButton(False)

        if self._requestStop:
            self.setMessage('Decryption canceled!')
            self.decryptPbar.setValue(self.decryptPbar.minimum())
            self._requestStop = False; os.remove(gn); return

        # restore original file name
        name, ext = os.path.splitext(rfn); count = 1
        fn = os.path.join(self.path, name + ext)
        while os.path.exists(fn):
            fn = os.path.join(self.path, name + '_{}'.format(count) + ext)
            count += 1
        os.rename(gn, fn)  # restore original name
        return fn  # saved name

    def copyKeyHash(self, action=None):
        "copies either the key or the hash to clipboard"
        if type(action) is bool: action = None

        # mark what hash was used in the drop-down menu
        for act in self.copyButton.menu().actions():
            if act.isChecked():
                self.copyButton.setToolTip(act.text())
                if action is None: action = act
                break

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

    def checkExclusive(self):
        "checks if at least one checkbox remains checked in self._cb_lst"
        if self.sender() not in self._cb_lst: return
        if not any(i.isChecked() for i in self._cb_lst):
            self.sender().setChecked(True)
        return
        

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

        hgt = 25#20
        wdh = 75

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.splitterMoved.connect(self.splitterChanged)
        #self.splitter.setStyleSheet("QSplitter::handle{background-color:#333;}")


        # left column --------------------------------------------------------
        self.leftColumn = QWidget()
        self.vl01 = QVBoxLayout()

        # left column - first item (0; horizontal layout 0)
        self.hl00 = QHBoxLayout()
        self.hl00.setSpacing(5)

        self.openButton = QPushButton('&Open')
        self.openButton.setToolTip('Open folder')
        self.openButton.setMinimumSize(wdh, hgt)
        self.openButton.setMaximumSize(wdh, hgt)
        self.openButton.setSizePolicy(Fixed)
        self.openButton.clicked.connect(self.getFolder)
        #ico = self.style().standardIcon(QStyle.SP_DirIcon)
        #self.openButton.setIcon(ico)

        self.folderLabel = QLabel()
        self.folderLabel.setMinimumSize(135, hgt)
        self.folderLabel.setMaximumSize(16777215, hgt)
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
        self.folderTable.setAlternatingRowColors(True)
        self.folderTable.setSelectionMode(QTableWidget.SingleSelection)
        #self.folderTable.setStyleSheet('QTableWidget{background-color:white;}')

        # add one row, one column with an item explaining how to use program
        self.folderTable.verticalHeader().setStretchLastSection(True)
        self.folderTable.setRowCount(1)
        self.folderTable.setColumnCount(1)
        info = QTableWidgetItem()
        #info.setTextAlignment(Qt.AlignCenter)
        txt = ('How to:\n  1. Open a folder with the button above\n'
               '  (This spot will list the files in the selected folder)\n'
               '  2. Select a file in this list\n'
               '  3. Encrypt/Decrypt the selected file with the controls '
               'on the right\n'
               '  (Encrypted files store their file name; decrypted '
               'files are given the stored name on extraction)\n'
               '  4. (Optional) Double click on newly encrypted files '
               'within this list to rename them.\n'
               )
        info.setText(txt); info.setToolTip(txt)
        info.setForeground(QColor(130, 130, 130))
        info.setBackground(QColor(255, 255, 255))
        info.setFlags(Qt.ItemIsEnabled)
        self.folderTable.setItem(0, 0, info)
        self.folderTable.itemChanged.connect(self.editFileName)


        # left column - third item (2)
        self.extraLabel = QLabel()
        self.extraLabel.setWordWrap(True)
        self.extraLabel.setMinimumSize(200, hgt)
        self.extraLabel.setMaximumSize(16777215, 2 * hgt)
        self.extraLabel.setSizePolicy(MinimumExpanding)
        self.extraLabel.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)

        # finalize left column
        self.vl01.addLayout(self.hl00)
        self.vl01.addWidget(self.folderTable)
        self.vl01.addWidget(self.extraLabel)
        self.leftColumn.setLayout(self.vl01)

        # right column -------------------------------------------------------
        self.rightColumn = QWidget()
        self.vl02 = QVBoxLayout()

        # right column - first item (0)
        self.messageLabel = QLabel()
        self.messageLabel.setMinimumSize(290, hgt)
        self.messageLabel.setMaximumSize(16777215, hgt)
        self.messageLabel.setSizePolicy(MinimumExpanding)
        self.messageLabel.setAlignment(Qt.AlignCenter)

        # right column - second item (2; horizontal layout 1)
        self.hl01 = QHBoxLayout()
        self.hl01.setSpacing(5)
        self.hl01.setContentsMargins(0,0,0,0)

        self.encryptButton = QPushButton('&Encrypt')#\U0001F512
        self.encryptButton.setToolTip('Encrypt selected file')
        self.encryptButton.setMinimumSize(wdh, hgt)
        self.encryptButton.setMaximumSize(wdh, hgt)
        self.encryptButton.setSizePolicy(Fixed)
        self.encryptButton.clicked.connect(self.encrypt)

        self.encryptPbar = QProgressBar()
        self.encryptPbar.setMinimumSize(225, hgt)
        self.encryptPbar.setMaximumSize(16777215, hgt)
        self.encryptPbar.setSizePolicy(MinimumExpanding)
        self.encryptPbar.setTextVisible(False)

        palette = self.encryptPbar.palette()  # color of progress bar
        color = QColor(211, 70, 0)
        palette.setColor(palette.ColorRole.Highlight, color)
        self.encryptPbar.setPalette(palette)

        self.hl01.addWidget(self.encryptButton)
        self.hl01.addWidget(self.encryptPbar)

        # right column - third item (3; horizontal layout 2)
        self.hl02 = QHBoxLayout()
        self.hl02.setSpacing(5)
        self.hl02.setContentsMargins(0,0,0,0)

        self.cancelButton = QPushButton('C&ANCEL')
        self.cancelButton.setToolTip('Cancels current operation')
        self.cancelButton.setMinimumSize(70, 24)
        self.cancelButton.setMaximumSize(70, 24)
        self.cancelButton.setSizePolicy(Fixed)
        self.cancelButton.clicked.connect(self.setCancel)
        font = self.cancelButton.font(); font.setBold(True)
        self.cancelButton.setFont(font)
        self.cancelButton.blockSignals(True)
        self.cancelButton.setEnabled(False)
        self.cancelButton.hide()
        self._requestStop = False

        self.showKeyPB = QPushButton('\U0001F511')
        self.showKeyPB.setToolTip('Show/Hide key value; Alt + s')
        self.showKeyPB.setShortcut(QKeySequence(Qt.ALT | Qt.Key.Key_S))
        self.showKeyPB.setMinimumSize(hgt, hgt)
        self.showKeyPB.setMaximumSize(hgt, hgt)
        self.showKeyPB.setSizePolicy(Fixed)
        self.showKeyPB.setCheckable(True)
        self.showKeyPB.clicked.connect(self.showKey)
        self.showKeyPB.setChecked(True)

        self.keyInput = QLineEdit()
        self.keyInput.setMinimumSize(225, hgt)
        self.keyInput.setMaximumSize(16777215, hgt)
        self.keyInput.setSizePolicy(MinimumExpanding)
        self.keyInput.setPlaceholderText('Key')
        self.keyInput.setMaxLength(self.maxKeyLen)
        self.keyInput.setAlignment(Qt.AlignCenter)
        self.keyInput.textEdited.connect(self.showKeyLen)
        self.keyInput.setStyleSheet('QLineEdit{background-color:white;'
                        'selection-background-color:rgb(220,138,221);}')

        self.genKeyButton = QToolButton()
        self.genKeyButton.setText('&Gen Key')
        self.genKeyButton.setToolTip('Generate a random key')
        self.genKeyButton.setMinimumSize(wdh, hgt)
        self.genKeyButton.setMaximumSize(wdh, hgt)
        self.genKeyButton.setSizePolicy(Fixed)
        self.genKeyButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.genKeyButton.clicked.connect(self.genKey)

        # stuff to stuff into the genKeyButton
        self.keySizeSB = QSpinBox()
        self.keySizeSB.setToolTip('Length of key to generate')
        self.keySizeSB.setRange(16, 2048)
        #self.keySizeSB.setMinimumSize(50, hgt)
        #self.keySizeSB.setMaximumSize(50, hgt))
        #self.keySizeSB.setSizePolicy(Fixed)
        self.keySizeSB.setAlignment(Qt.AlignCenter)
        #self.keySizeSB.setButtonSymbols(QSpinBox.PlusMinus)
        self.keySizeSB.setWrapping(True)
        self.keySizeSB.setStyleSheet('QSpinBox{'#background-color:white;'
            'selection-background-color:rgb(220,138,221);}')

        kslbl = QLabel('Key &length:')
        kslbl.setBuddy(self.keySizeSB)
        kslbl.setToolTip(self.keySizeSB.toolTip())

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Raised)

        # letters, numbers, emoji, extended
        self.useUprCB = QCheckBox('&Upper Case\n(ABC...)')
        self.useLwrCB = QCheckBox('&Lower Case\n(abc...)')
        self.useNumCB = QCheckBox('&Numbers\n(0123...)')
        self.usePunCB = QCheckBox('&Punctuation\n(!:?&&...)')
        self.useAccCB = QCheckBox('&Accents\n(ÀçĕĨ...)')# ¢ÜćĨ
        self.useEmjCB = QCheckBox('Emo&ji\n(\U0001F3B2\U0001F4CB'
                                  '\U0001F4E6\U0001F511...)')

        self.useUprCB.setChecked(True)
        self.useLwrCB.setChecked(True)
        self.useNumCB.setChecked(True)

        lst = [self.useUprCB, self.useLwrCB, self.useNumCB,
               self.usePunCB, self.useAccCB, self.useEmjCB]
        for ckb in lst:
            knd = ckb.text().split('\n')[0].replace('&', '')
            ckb.setToolTip(f'Have {knd} in the generated key')
            ckb.clicked.connect(self.checkExclusive)
        self._cb_lst = lst

        gk_ly = QGridLayout()
        gk_ly.setContentsMargins(1,1,1,1)
        gk_ly.addWidget(kslbl,          0, 0)
        gk_ly.addWidget(self.keySizeSB, 0, 1)
        gk_ly.addWidget(hline,          1, 0, 1, -1)
        gk_ly.addWidget(self.useUprCB,  2, 0)
        gk_ly.addWidget(self.useLwrCB,  2, 1)
        gk_ly.addWidget(self.usePunCB,  3, 0)
        gk_ly.addWidget(self.useNumCB,  3, 1)
        gk_ly.addWidget(self.useAccCB,  4, 0)
        gk_ly.addWidget(self.useEmjCB,  4, 1)

        gk_wt = QFrame()
        gk_wt.setFrameShadow(QFrame.Sunken)
        gk_wt.setFrameShape(QFrame.Panel)
        gk_wt.setContentsMargins(2,2,2,2)
        gk_wt.setLayout(gk_ly)

        # menu item in gen key button holding action that holds all the above
        mnu = QMenu(self.genKeyButton)
        act = QWidgetAction(mnu)
        act.setDefaultWidget(gk_wt)
        mnu.addAction(act)
        self.genKeyButton.setMenu(mnu)

        self.hl02.addWidget(self.cancelButton)
        self.hl02.addWidget(self.showKeyPB)
        self.hl02.addWidget(self.keyInput)
        self.hl02.addWidget(self.genKeyButton)

        # right column - fourth item (4; horizontal layout 3)
        self.hl03 = QHBoxLayout()
        self.hl03.setSpacing(5)

        self.decryptButton = QPushButton('&Decrypt')#\U0001F513
        self.decryptButton.setToolTip('Decrypt selected file')
        self.decryptButton.setMinimumSize(wdh, hgt)
        self.decryptButton.setMaximumSize(wdh, hgt)
        self.decryptButton.setSizePolicy(Fixed)
        self.decryptButton.clicked.connect(self.decrypt)

        self.decryptPbar = QProgressBar()
        self.decryptPbar.setMinimumSize(225, hgt)
        self.decryptPbar.setMaximumSize(16777215, hgt)
        self.decryptPbar.setSizePolicy(MinimumExpanding)
        self.decryptPbar.setTextVisible(False)
        self.decryptPbar.setInvertedAppearance(True)
        #self.decryptPbar.setLayoutDirection(Qt.RightToLeft)

        palette = self.decryptPbar.palette()  # color of progress bar
        color = QColor(0, 170, 255)
        palette.setColor(palette.ColorRole.Highlight, color)
        self.decryptPbar.setPalette(palette)

        self.hl03.addWidget(self.decryptButton)
        self.hl03.addWidget(self.decryptPbar)

        # right column - fifth item (7; horizontal layout 4)
        self.hl04 = QHBoxLayout()
        self.hl04.setSpacing(5)

        self.copyButton = QToolButton()
        self.copyButton.setText('&Copy')#\U0001F4CB
        self.copyButton.setToolTip('Copy key or hash to clipboard')
        self.copyButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.copyButton.setMinimumSize(wdh, hgt)
        self.copyButton.setMaximumSize(wdh, hgt)
        self.copyButton.setSizePolicy(Fixed)
        self.copyButton.setLayoutDirection(Qt.RightToLeft)

        menu2 = QMenu(self.copyButton)
        agrp2 = QActionGroup(self)
        act = menu2.addAction('Copy Key'); act.setCheckable(True)
        act.setChecked(True); act.setActionGroup(agrp2)

        act = menu2.addAction('Copy Hash'); act.setCheckable(True)
        act.setChecked(False); act.setActionGroup(agrp2)

        self.copyButton.setMenu(menu2)
        self.copyButton.clicked.connect(self.copyKeyHash)
        menu2.triggered.connect(self.copyKeyHash)

        self.hashPbar = QProgressBar()
        self.hashPbar.setMinimumSize(150, hgt)
        self.hashPbar.setMaximumSize(16777215, hgt)
        self.hashPbar.setSizePolicy(MinimumExpanding)
        self.hashPbar.setTextVisible(False)

        palette = self.hashPbar.palette()  # color of progress bar
        color = QColor(31, 120, 73)
        palette.setColor(palette.ColorRole.Highlight, color)
        self.hashPbar.setPalette(palette)

        self.hashButton = QToolButton()
        self.hashButton.setText('&Hash')
        self.hashButton.setToolTip('Determine file hash')
        self.hashButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.hashButton.setMinimumSize(wdh, hgt)
        self.hashButton.setMaximumSize(wdh, hgt)
        self.hashButton.setSizePolicy(Fixed)

        menu = QMenu(self.hashButton)
        agrp = QActionGroup(self)

        key =lambda n:(len(n),sorted(hashlib.algorithms_guaranteed).index(n))
        # drop shake algs as their .hexdigest requires an argument
        flt =lambda x: 'shake' not in x  # the rest don't
        hsh_guar = hashlib.algorithms_guaranteed
        for i, alg in enumerate(sorted(filter(flt, hsh_guar), key=key)):
            act = menu.addAction(alg)
            act.setCheckable(True)
            act.setActionGroup(agrp)
            if not i:
                act.setChecked(True)
                self._prior_hsh = act
            else: act.setChecked(False)

        act = menu.addAction('Party'); act.setCheckable(True)
        act.setChecked(False); act.setActionGroup(agrp)

        self.hashButton.setMenu(menu)
        self.hashButton.clicked.connect(self.genHash)
        menu.triggered.connect(self.genHash)

        self.hl04.addWidget(self.copyButton)
        self.hl04.addWidget(self.hashPbar)
        self.hl04.addWidget(self.hashButton)

        # right column - sixth item (8; horizontal layout 5)
        self.hashLabel = QLabel()
        self.hashLabel.setMinimumSize(225, hgt)
        self.hashLabel.setMaximumSize(16777215, hgt)
        self.hashLabel.setSizePolicy(MinimumExpanding)
        self.hashLabel.setTextFormat(Qt.PlainText)
        self.hashLabel.setAlignment(Qt.AlignCenter)
        self.hashLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # finalize right column
        self.vl02.addWidget(self.messageLabel)
        self.vl02.addLayout(self.hl01)
        self.vl02.addLayout(self.hl02)
        self.vl02.addLayout(self.hl03)
        self.vl02.addStretch()
        self.vl02.addLayout(self.hl04)
        self.vl02.addWidget(self.hashLabel)
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
    sys.exit(app.exec())

