"""
This file is part of Hmark.

    Hmark is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Hmark is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Hmark.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import platform
import version

pf = platform.platform()
bits, _ = platform.architecture()

if 'Windows' in pf:
    osName = "win"
    if "64" in bits:
        bits = "_x64"
    else:
        bits = "_x86"
elif 'Linux' in pf:
    osName = 'linux'
    if "64" in bits:
        bits = "_x64"
    else:
        bits = "_x86"
else:
    osName = "osx"
    bits = ""

version = version.version

fp = open("hmark_" + version + '_' + osName + bits + ".spec", "w")
cwd = os.getcwd()
print(os.path.join(cwd, 'icon.gif'))
if osName == "linux":
    fp.write("\
# -*- mode: python -*-\n\n\
block_cipher = None\n\n\n\
a = Analysis(['hmark.py'],\n\
             pathex=[r'" + cwd + "'],\n\
             binaries=None,\n\
             datas=None,\n\
             hiddenimports=[],\n\
             hookspath=[],\n\
             runtime_hooks=[],\n\
             excludes=[],\n\
             win_no_prefer_redirects=False,\n\
             win_private_assemblies=False,\n\
             cipher=block_cipher)\n\
a.datas += [('icon.gif', r'" + os.path.join(cwd, 'icon.gif') + "', 'DATA')]\n\
pyz = PYZ(a.pure, a.zipped_data,\n\
             cipher=block_cipher)\n\
exe = EXE(pyz,\n\
          a.scripts,\n\
          a.binaries,\n\
          a.zipfiles,\n\
          a.datas,\n\
          name='hmark_" + version + "_" + osName + bits + "',\n\
          debug=False,\n\
          strip=False,\n\
          upx=True,\n\
          console=True )\n\
""")

elif osName == "osx":
    fp.write("\
# -*- mode: python -*-\n\n\
block_cipher = None\n\n\n\
a = Analysis(['hmark.py'],\n\
             pathex=[r'" + cwd + "'],\n\
             binaries=None,\n\
             datas=None,\n\
             hiddenimports=[],\n\
             hookspath=[],\n\
             runtime_hooks=[],\n\
             excludes=[],\n\
             win_no_prefer_redirects=False,\n\
             win_private_assemblies=False,\n\
             cipher=block_cipher)\n\
a.datas += [('icon.gif', r'" + os.path.join(cwd, 'icon.gif') + "', 'DATA')]\n\
pyz = PYZ(a.pure, a.zipped_data,\n\
             cipher=block_cipher)\n\
exe = EXE(pyz,\n\
          a.scripts,\n\
          a.binaries,\n\
          a.zipfiles,\n\
          a.datas,\n\
          name='hmark_" + version + "_" + osName + bits + "',\n\
          debug=False,\n\
          strip=False,\n\
          upx=True,\n\
          console=True,\n\
          icon='icon.ico')\n\
""")

elif osName == "win":
    fp.write("\
# -*- mode: python -*-\n\n\
block_cipher = None\n\n\n\
a = Analysis(['hmark.py'],\n\
             pathex=[r'" + cwd + "'],\n\
             binaries=None,\n\
             datas=None,\n\
             hiddenimports=[],\n\
             hookspath=[],\n\
             runtime_hooks=[],\n\
             excludes=[],\n\
             win_no_prefer_redirects=False,\n\
             win_private_assemblies=False,\n\
             cipher=block_cipher)\n\
a.datas += [('icon.gif', r'" + os.path.join(cwd, 'icon.gif') + "', 'DATA')]\n\
pyz = PYZ(a.pure, a.zipped_data,\n\
             cipher=block_cipher)\n\
exe = EXE(pyz,\n\
          a.scripts,\n\
          a.binaries,\n\
          a.zipfiles,\n\
          a.datas,\n\
          name='hmark_" + version + "_" + osName + bits + "',\n\
          debug=False,\n\
          strip=False,\n\
          upx=True,\n\
          console=True,\n\
          icon='icon.ico')\
""")

fp.close()
print("Pyinstaller spec file generated: " + "hmark_" + version + '_' + osName + bits + ".spec")
