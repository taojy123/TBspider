# -*- mode: python -*-
a = Analysis(['run.py'],
             pathex=['E:\\workspace\\GitHub\\TBspider'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='run.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )