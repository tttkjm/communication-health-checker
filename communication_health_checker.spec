# PyInstaller spec — communication_health_checker シングルバイナリ（SPA 同梱・ローカルブラウザ起動）
# ビルド: uv run pyinstaller communication_health_checker.spec --clean --noconfirm
from PyInstaller.utils.hooks import collect_submodules

# ビルド済み SPA を同梱（src, dest）。dest を "statics" にすることで
# 実行時に sys._MEIPASS/statics へ展開され、resource_path("statics") が解決する。
datas = [("statics", "statics")]

hiddenimports = (
    collect_submodules("uvicorn")  # uvicorn は動的 import が多い
    + collect_submodules("communication_health_checker")
    + [
        "communication_health_checker.modules.desktop_module",  # DI で動的解決されるため明示
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
    ]
)

a = Analysis(
    ["apps/desktop/main.py"],
    pathex=["src"],  # src layout を import パスに追加
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="communication_health_checker",
    console=False,  # GUI 配布（デバッグ時は True にするとログが見える）
    onefile=True,
    upx=False,
)
