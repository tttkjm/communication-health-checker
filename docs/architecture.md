# デスクトップ配布アプリ アーキテクチャ設計書

**スタック**: Python 3.14 + uv + FastAPI + DDD + Clean Architecture + Hexagonal + Pydantic v2 + PyInstaller
**配布形態**: PyInstaller シングルバイナリ／ローカル起動 FastAPI + StaticFiles で SPA を配信し、ブラウザでアクセス

> 本設計は `python-architecture-guide` スキルの原則（依存方向・レイヤ責務分離・Port/Adapter・DI 集約・src layout・コアパッケージ汚染防止）に厳密に従う。`<package_name>` は実際の名称（例 `myapp`）に置換すること。

---

## ⚠️ スキル方針との整合（重要な読み替え）

「domain は dataclass 等の純粋モデル」という分離について、本スキルは **domain も Pydantic v2 を使う**（ただし `BaseModel` 直継承禁止、`Entity[TId]`/`Aggregator[TId]`/`ValueObject` 基底を継承）と明確に規定している。そのためスキルに従い、分離方針を次のように実現する:

- **DTO** = プリミティブ型のみ・ドメイン非依存の腐敗防止層(ACL)
- **Domain** = ドメイン基底クラスを継承し不変条件を内包するリッチな Pydantic モデル

両者とも Pydantic v2 だが、依存方向と責務が完全に分離される。

---

## 1. レイヤ構成と依存方向

Clean Architecture（同心円）＋ Hexagonal（Port/Adapter）＋ DDD（集約）。依存は常に**内向き（Domain 方向）**のみ。

```
Presentation (apps/desktop)  ── FastAPIルーター / StaticFiles+SPA catch-all / 起動シーケンス
        │ Use Case 経由でのみ呼ぶ
        ▼
Application (src/<pkg>/application) ── UseCase(execute) / DTO(ACL) / AppService
        │ IFのみに依存
        ▼
Domain (src/<pkg>/domain) ★最内核 ── Entity/Aggregator/VO / Repository IF / Port IF
        ▲ implements
        │
Infrastructure (src/<pkg>/infrastructure) ── Repository実装(SQLite) / Adapter実装
        ▲ wires
DI: modules/ (injector.Module) ── IF→実装の束ね
```

**鉄則（`tests/architecture/` で機械検証）**:

| ルール | 内容 |
|---|---|
| Domain は何も import しない | `infrastructure`/`application`/`apps` import 禁止 |
| Application は IF にのみ依存 | infra 具象 import 禁止 |
| `apps/` は Use Case 経由 | AppService を直接呼ばない |
| **コアパッケージ汚染禁止** | `src/<pkg>/` に `fastapi`/`uvicorn` を import しない（`apps/` のみ） |
| DTO はドメイン非依存 | `application/dto/` から domain import 禁止 |

> 本アプリは単一プラットフォーム（デスクトップ）なので、スキルの `onpremise/aws/ros2` 3環境分割は不要。`modules/desktop_module.py` 1つで足りる。

---

## 2. 推奨ディレクトリ構造

```
project-root/
├── pyproject.toml                      # uv/依存/ツール設定を集約
├── uv.lock
├── <package_name>.spec                 # PyInstaller spec
├── src/
│   └── <package_name>/                 # コアパッケージ（FastAPI 非import）
│       ├── domain/
│       │   ├── models/
│       │   │   ├── core/               # 基底クラス（唯一の集約場所）
│       │   │   │   ├── __init__.py     # re-export 許可（唯一の例外）
│       │   │   │   ├── entity.py        # Entity[TId]
│       │   │   │   ├── aggregator.py    # Aggregator[TId]
│       │   │   │   ├── value_object.py  # ValueObject (frozen)
│       │   │   │   └── exceptions.py    # DomainException 系（全例外集約）
│       │   │   └── note/               # 集約例
│       │   │       ├── note.py
│       │   │       ├── note_id.py
│       │   │       └── note_status.py
│       │   ├── repositories/i_note_repository.py
│       │   ├── ports/clock_port.py
│       │   └── services/
│       ├── application/
│       │   ├── dto/note_dto.py
│       │   ├── use_cases/{create,list,get}_note_use_case.py
│       │   └── services/
│       ├── infrastructure/
│       │   ├── repositories/sqlite/{note_repository,dao,models,mappers}
│       │   ├── adapters/system_clock.py
│       │   └── services/
│       └── modules/
│           ├── __init__.py             # get_di_container()
│           └── desktop_module.py       # DesktopModule(injector.Module)
├── apps/
│   └── desktop/                        # ★ Presentation層（FastAPI importはここだけ）
│       ├── main.py                     # PyInstaller エントリーポイント（起動シーケンス）
│       ├── app.py                      # create_app(): FastAPI + ルーター + StaticFiles
│       ├── resources.py                # sys._MEIPASS 解決ヘルパ
│       ├── routers/note_manager.py
│       ├── static/                     # ★ ビルド済みSPA（JS/CSS/index.html）を同梱
│       │   ├── index.html
│       │   └── assets/...
│       └── config/
├── frontend/                           # （任意）SPAソース → apps/desktop/static へ出力
├── db/
├── tests/{architecture,unit,integration}/
├── scripts/{build_frontend.sh,build_app.sh}
└── docs/
```

**SPA配置方針**: ビルド済みSPAは `apps/desktop/static/`（Presentation層内）に置く。SPAはプレゼンテーションの一部であり `src/` には置かない。

---

## 3. FastAPI Presentation 層

### 3-1. ルーター（`apps/desktop/routers/note_manager.py`）

ルーターは `async def`、Use Caseは同期 `def`（FastAPIが自動でスレッドプール実行）。ドメイン例外→HTTPステータス変換。

```python
from fastapi import APIRouter, Depends, HTTPException
from <package_name>.application.dto.note_dto import CreateNoteRequest, NoteResponse
from <package_name>.application.use_cases.create_note_use_case import CreateNoteUseCase
from <package_name>.domain.models.core.exceptions import DomainException, InvalidOperationException
from <package_name>.modules import get_di_container

router = APIRouter(prefix="/api/v1/notes", tags=["Note Management"])

def _create_uc() -> CreateNoteUseCase:
    return get_di_container().get(CreateNoteUseCase)

@router.post("/", status_code=201)
async def create_note(
    request: CreateNoteRequest,
    use_case: CreateNoteUseCase = Depends(_create_uc),
) -> NoteResponse:
    try:
        return use_case.execute(request)        # Use Case は同期
    except InvalidOperationException as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DomainException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
```

例外→HTTP: `EntityNotFoundException`→404、`InvalidOperationException`→400、`InvariantViolationException`→409、その他→500。

### 3-2. アプリ組み立て + SPA catch-all（`apps/desktop/app.py`）

**APIルーターを先に登録**し、最後に**catch-allで `index.html` を返す**ことで、SPAのクライアントサイドルーティング（ディープリンク/リロード）を成立させる。

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apps.desktop.resources import resource_path
from apps.desktop.routers import note_manager

def create_app() -> FastAPI:
    app = FastAPI(title="<package_name>")

    # 1) API ルーター（最優先で登録）
    app.include_router(note_manager.router)

    # 2) ビルド済み SPA の静的アセット配信
    static_dir = resource_path("apps/desktop/static")
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    # 3) SPA catch-all（最後に登録）— /api/ 以外の未マッチGETは index.html
    index_file = static_dir / "index.html"

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        return FileResponse(index_file)

    return app
```

**ポイント**: ルーター登録順が重要（API → `/assets` mount → catch-all）。`directory` は `resource_path()` でPyInstaller展開先と開発時ソースの両対応で解決。

---

## 4. Pydantic v2 の層別指針

| 層 | 使い方 | 依存 |
|---|---|---|
| **Domain** | `Entity[TId]`/`Aggregator[TId]`/`ValueObject` 基底を継承。`model_validator`で不変条件を内包。`BaseModel`直継承は禁止 | 何も import しない |
| **DTO** | `BaseModel`直継承可。**プリミティブ型のみ**。`Field(description=, examples=)`必須 | **ドメイン import禁止(ACL)** |
| **変換** | DTO→Domainは**Use Case内**で `model_validate()`、Domain→DTOも**Use Case内**でプリミティブ値を渡す | DTOは変換メソッドを持たない |

---

## 5. 構成要素の最小コード例

### 5-1. core 基底クラス

```python
# entity.py
from datetime import UTC, datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
TId = TypeVar("TId")

class Entity(BaseModel, Generic[TId]):
    model_config = ConfigDict(validate_assignment=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    @property
    def id(self) -> TId: raise NotImplementedError
    def __eq__(self, other): return isinstance(other, self.__class__) and self.id == other.id
    def __hash__(self): return hash(self.id)

# aggregator.py
class Aggregator(Entity[TId], Generic[TId]):
    def validate_invariants(self) -> None: ...

# value_object.py
class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True)

# exceptions.py
class DomainException(Exception): ...
class EntityNotFoundException(DomainException): ...
class InvalidOperationException(DomainException): ...
class InvariantViolationException(DomainException): ...
```

### 5-2〜5-3. ValueObject(ID) と Aggregator

```python
# domain/models/note/note_id.py
import uuid
from pydantic import Field
from <package_name>.domain.models.core import ValueObject

class NoteId(ValueObject):
    value: str = Field(..., pattern=r"^note_[0-9a-f]{32}$", description="ノートID")
    @classmethod
    def generate(cls) -> "NoteId":
        return cls(value=f"note_{uuid.uuid4().hex}")
    def __str__(self) -> str: return self.value

# domain/models/note/note.py
from enum import StrEnum
from pydantic import Field
from <package_name>.domain.models.core import Aggregator
from <package_name>.domain.models.core.exceptions import InvalidOperationException
from <package_name>.domain.models.note.note_id import NoteId

class NoteStatus(StrEnum):
    DRAFT = "DRAFT"; PUBLISHED = "PUBLISHED"; ARCHIVED = "ARCHIVED"

class Note(Aggregator[NoteId]):
    note_id: NoteId = Field(..., description="ノートID")
    title: str = Field(..., min_length=1, max_length=200, description="タイトル")
    body: str = Field(default="", max_length=10000, description="本文")
    status: NoteStatus = Field(default=NoteStatus.DRAFT, description="状態")
    @property
    def id(self) -> NoteId: return self.note_id
    def publish(self) -> None:
        if self.status != NoteStatus.DRAFT:
            raise InvalidOperationException(f"Cannot publish in status: {self.status}")
        self.status = NoteStatus.PUBLISHED
    def validate_invariants(self) -> None:
        if self.status == NoteStatus.PUBLISHED and not self.title.strip():
            raise InvalidOperationException("Published note must have a title")
```

### 5-4〜5-5. Repository (Port/Adapter) と Port/Adapter

```python
# domain/repositories/i_note_repository.py
from abc import ABC, abstractmethod
class INoteRepository(ABC):
    @abstractmethod
    def save(self, entity: Note) -> None: ...
    @abstractmethod
    def find_by_id(self, entity_id: NoteId) -> Note | None: ...
    @abstractmethod
    def find_all(self) -> list[Note]: ...

# infrastructure/repositories/sqlite/note_repository.py（Repository→DAO→Mapper の3層）
class NoteRepository(INoteRepository):
    def __init__(self, db_path: str) -> None: self._db_path = db_path
    def save(self, entity: Note) -> None: ...
    # ...

# domain/ports/clock_port.py
class ClockPort(ABC):
    @abstractmethod
    def now(self) -> datetime: ...

# infrastructure/adapters/system_clock.py
class SystemClock(ClockPort):
    def now(self) -> datetime: return datetime.now(UTC)
```

### 5-6〜5-8. DTO / Use Case / DI

```python
# application/dto/note_dto.py
from pydantic import BaseModel, Field
class CreateNoteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="タイトル", examples=["買い物メモ"])
    body: str = Field(default="", max_length=10000, description="本文")
class NoteResponse(BaseModel):
    id: str = Field(..., description="ノートID")
    title: str = Field(..., description="タイトル")
    status: str = Field(..., description="状態")
    created_at: str = Field(..., description="作成日時(ISO8601)")

# application/use_cases/create_note_use_case.py
class CreateNoteUseCase:
    def __init__(self, repository: INoteRepository) -> None:
        self._repository = repository
    def execute(self, request: CreateNoteRequest) -> NoteResponse:
        note = Note.model_validate({
            "note_id": NoteId.generate(),
            "title": request.title, "body": request.body,
        })
        note.validate_invariants()
        self._repository.save(note)
        return NoteResponse(
            id=note.id.value, title=note.title,
            status=note.status.value, created_at=note.created_at.isoformat(),
        )

# modules/desktop_module.py
import os
from injector import Injector, Module, provider, singleton
class DesktopModule(Module):
    _instance: Injector | None = None
    @classmethod
    def get_instance(cls) -> Injector:
        if cls._instance is None:
            cls._instance = Injector([cls()])
        return cls._instance
    @singleton
    @provider
    def note_repository(self) -> INoteRepository:
        return NoteRepository(db_path=os.getenv("SQLITE_DB_PATH", "notes.db"))
    @singleton
    @provider
    def create_note_use_case(self, note_repository: INoteRepository) -> CreateNoteUseCase:
        return CreateNoteUseCase(repository=note_repository)

# modules/__init__.py
def get_di_container():
    from <package_name>.modules.desktop_module import DesktopModule
    return DesktopModule.get_instance()
```

---

## 6. PyInstaller パッケージング設計（最重要・固有要件）

### 6-1. リソースパス解決（`sys._MEIPASS` 両対応）

```python
# apps/desktop/resources.py
import sys
from pathlib import Path

def resource_path(relative: str) -> Path:
    """PyInstaller実行時は sys._MEIPASS、開発時はプロジェクトルートから解決."""
    base = getattr(sys, "_MEIPASS", None)
    if base is not None:                      # 凍結バイナリ実行中
        return Path(base) / relative
    return Path(__file__).resolve().parents[2] / relative  # apps/desktop → root
```

### 6-2. エントリーポイント + ブラウザ自動起動（`apps/desktop/main.py`）

空きポート確保 → uvicornを別スレッドで起動 → 待受確認後にブラウザを自動で開く → メインスレッド常駐。

```python
import socket, threading, time, webbrowser
import uvicorn
from apps.desktop.app import create_app

def _find_free_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred)); return preferred
        except OSError:
            s.bind(("127.0.0.1", 0)); return s.getsockname()[1]

def _open_browser_when_ready(host: str, port: int) -> None:
    url = f"http://{host}:{port}/"
    for _ in range(50):                       # 最大 ~5秒待機
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) == 0:
                webbrowser.open(url); return
        time.sleep(0.1)
    webbrowser.open(url)

def main() -> None:
    # 書き込みDBはユーザー領域へ（_MEIPASS は読取専用・一時展開のため）
    import os
    from pathlib import Path
    default_db = Path.home() / ".<package_name>" / "notes.db"
    default_db.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SQLITE_DB_PATH", str(default_db))

    host, port = "127.0.0.1", _find_free_port()
    app = create_app()
    threading.Thread(target=_open_browser_when_ready, args=(host, port), daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
```

> **注意**: PyInstallerでは `reload=True` やワーカープロセスは使わない（再起動でバイナリ再importが破綻）。`uvicorn.run(app, ...)` にアプリオブジェクトを直接渡す（import文字列を渡さない）。

### 6-3. spec ファイル（SPA同梱・隠れimport収集）

```python
# <package_name>.spec
from PyInstaller.utils.hooks import collect_submodules

datas = [("apps/desktop/static", "apps/desktop/static")]   # SPA同梱 (src, dest)
hiddenimports = (
    collect_submodules("uvicorn")        # uvicornは動的importが多い
    + collect_submodules("<package_name>")
    + ["<package_name>.modules.desktop_module"]
)
a = Analysis(["apps/desktop/main.py"], pathex=["src"], datas=datas, hiddenimports=hiddenimports)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
    name="<package_name>", console=False, onefile=True)
```

要点: `dest` を `apps/desktop/static` にすることで `resource_path()` が `sys._MEIPASS/apps/desktop/static` を正しく指す。uvicornは `collect_submodules` で隠れimportを補い、DIで動的解決する `desktop_module` も明示。

**CLI簡易形（Windowsは `--add-data` 区切りが `;`）**:

```bash
uv run pyinstaller apps/desktop/main.py --name <package_name> --onefile --noconsole \
  --paths src --add-data "apps/desktop/static;apps/desktop/static" \
  --collect-submodules uvicorn
```

### 6-4. SQLiteデータの扱い

`sys._MEIPASS` は読取専用・一時展開なので**書き込みDBを置かない**。`main.py` 冒頭でユーザー領域（`~/.<package_name>/notes.db`）を設定する（上記 6-2 参照）。

---

## 7. uv 開発ワークフロー

```toml
# pyproject.toml（要点）
[project]
name = "<package-name>"
requires-python = ">=3.14"
dependencies = ["injector>=0.22.0", "pydantic>=2.11"]

[project.optional-dependencies]
desktop = ["fastapi>=0.115", "uvicorn>=0.30"]   # FastAPIはdesktop extra（srcへ入れない）
build   = ["pyinstaller>=6.0"]
dev     = ["ruff>=0.9", "ty>0.0.1a29"]
test    = ["pytest>=8", "httpx>=0.27", "pytest-env>=1.1.5"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
env = ["SQLITE_DB_PATH=:memory:"]
markers = ["smoke", "critical", "regression", "slow"]

[tool.ruff]
target-version = "py314"
line-length = 120
```

```bash
uv add fastapi --optional desktop          # 依存追加
uv sync --extra desktop --extra dev --extra test
uv run python -m apps.desktop.main         # 開発起動（ブラウザ自動オープン）
uv run ruff check --fix src/ apps/ tests/  # 品質チェック
bash scripts/build_app.sh                  # バイナリビルド → dist/<package_name>(.exe)
```

---

## 8. テスト戦略（Testing Trophy — 統合テスト最重点）

- **architecture**: 依存方向・コアパッケージ汚染（`src/`に`fastapi`/`uvicorn`混入禁止）・`__init__.py`空を機械検証。CI最初に実行。
- **unit**: domain（状態遷移・不変条件・境界値）、application（Use Case正常/異常系、Repositoryモック）、infrastructure（Mapper変換、インメモリSQLite）。
- **integration**: `TestClient` で `create_app()` を起動しAPIシナリオ検証。**SPAフォールバック確認**（`GET /unknown/path` が `index.html`＝200）も含む。
- **packaging スモーク（任意）**: ビルド済みバイナリをsubprocess起動 → HTTP到達 → `/`がindex.html、`/api/v1/...`がJSONを返すことを確認。

```bash
uv run pytest tests/architecture/ tests/unit/ -v      # CI 常時
uv run pytest -m "smoke or critical" -v               # 開発サイクル
uv run pytest -v --cov=src --cov-report=term-missing  # リリース前
```

---

## このスタック固有の最重要ポイント（5点）

1. **コアパッケージ汚染の死守**: `src/<pkg>/` に `fastapi`/`uvicorn` を絶対importしない。SPA配信・ルーター・起動・`_MEIPASS`解決はすべて `apps/desktop/` に閉じ込める。
2. **catch-allは最後**: API → `/assets` mount → SPA catch-all の順。誤るとAPIがindex.htmlに飲まれる。
3. **PyInstallerでのuvicorn起動**: アプリオブジェクト直接渡し、`reload`/workers不使用、`collect_submodules("uvicorn")` 必須。
4. **書き込みデータは`_MEIPASS`に置かない**: SQLiteはユーザーディレクトリへ。
5. **DTO/Domainの二重Pydantic**: DTO=プリミティブACL、Domain=core基底継承のリッチモデル。変換はUse Case内の `model_validate()` のみ。
