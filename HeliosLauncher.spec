# Build from repository root: python -m PyInstaller HeliosLauncher.spec
a = Analysis(['main.py'], pathex=[], binaries=[],
             datas=[('assets', 'assets')], hiddenimports=[],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='HeliosLauncher', debug=False, bootloader_ignore_signals=False,
          strip=False, upx=False, console=False, icon='assets/helios.ico')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='HeliosLauncher')
