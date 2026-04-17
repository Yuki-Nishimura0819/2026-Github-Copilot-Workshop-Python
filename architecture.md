# ポモドーロタイマー Webアプリケーション - アーキテクチャ設計書

## 1. 概要

このドキュメントは、ポモドーロタイマー Webアプリケーションの包括的なアーキテクチャ設計を定義します。以下の要件を満たす設計となっています：

- **ユーザーインターフェース**: UIモック（25分作業/5分休憩のタイマー、進捗表示）に基づいた実装
- **テスト性**: 単体テストが容易な設計パターンの採用
- **保守性**: 関心の分離、依存性注入による疎結合な構成
- **拡張性**: 新機能追加が容易なモジュール構造

---

## 2. プロジェクト構造

```
1.pomodoro/
├── app.py                      # Flaskアプリケーションのエントリーポイント
├── config.py                   # 環境別設定管理
├── models/
│   ├── __init__.py
│   ├── timer.py               # タイマーコアロジック（Pure Functions）
│   ├── session.py             # セッション状態管理・状態遷移
│   └── repository.py          # データアクセス層（抽象化）
├── services/
│   ├── __init__.py
│   ├── timer_service.py       # ビジネスロジック層（DI対応）
│   └── stats_service.py       # 統計処理
├── static/
│   ├── css/
│   │   └── style.css          # UIスタイル定義
│   └── js/
│       └── timer.js           # フロントエンドロジック・API連携
├── templates/
│   └── index.html             # HTMLテンプレート
├── tests/                      # テストディレクトリ
│   ├── __init__.py
│   ├── conftest.py            # pytest共通設定・fixtures
│   ├── unit/
│   │   ├── test_timer.py      # タイマーロジックのテスト
│   │   ├── test_session.py    # セッション管理のテスト
│   │   └── test_services.py   # ビジネスロジックのテスト
│   ├── integration/
│   │   └── test_api.py        # APIエンドポイント統合テスト
│   └── fixtures/
│       └── sample_data.json   # テスト用サンプルデータ
├── requirements.txt           # Python依存パッケージ
├── pytest.ini                 # pytest設定ファイル
└── architecture.md            # このファイル
```

---

## 3. アーキテクチャレイヤー

### 3.1 全体データフロー

```
┌─────────────────────────────────────────────────────────────┐
│                    ユーザー操作（UI）                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          timer.js（フロントエンドロジック層）                  │
│  ・イベントハンドラ（開始/停止/リセット）                     │
│  ・定期的なAPI呼び出し（1秒ごと）                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask API（app.py）                          │
│  ・HTTPエンドポイント定義                                    │
│  ・リクエスト検証・レスポンス生成                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Services層（ビジネスロジック層）                      │
│  ・TimerService: タイマー状態管理                            │
│  ・StatsService: 統計データ計算                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      Models層（ドメインモデル・ビジネスロジック）              │
│  ・Timer: 純粋な時間計算                                     │
│  ・SessionStateMachine: 状態遷移管理                         │
│  ・Repository: データアクセス（抽象化）                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      Repository実装（FileRepository / InMemoryRepository）    │
│  ・ファイルI/O（sessions.json）                              │
│  ・テスト用メモリストレージ                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               永続データ層                                    │
│  ・sessions.json（本番環境）                                 │
│  ・インメモリストレージ（テスト環境）                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 レイヤーの責任

| レイヤー | 責任 | テスト性 |
|---------|------|---------|
| **UI層** (timer.js) | ユーザー入力の受け取り、画面更新 | JavaScript テスト（別途） |
| **API層** (app.py) | HTTPリクエスト処理、ルーティング | integration テスト |
| **Services層** | ビジネスロジック、オーケストレーション | unit テスト（DI活用） |
| **Models層** | ドメインロジック、状態管理、Pure Functions | unit テスト（最も高速） |
| **Repository層** | データ永続化の抽象化 | モック化可能 |

---

## 4. コアコンポーネント設計

### 4.1 Timer（models/timer.py）

```python
class Timer:
    """タイマーコアロジック - Pure Function指向
    
    特性：
    - 副作用なし（ファイルI/O、DBアクセスなし）
    - 単一責任：時間計算のみ
    - テスト容易性：最高
    """
    
    def __init__(self, initial_seconds: int):
        self.remaining = initial_seconds
        self.status = "idle"
    
    def tick(self) -> int:
        """1秒進める - 純粋な計算ロジック"""
        if self.status == "working":
            return max(0, self.remaining - 1)
        return self.remaining
    
    def start(self) -> None:
        """タイマー開始"""
        self.status = "working"
    
    def pause(self) -> None:
        """タイマー一時停止"""
        self.status = "paused"
    
    def reset(self) -> None:
        """タイマーリセット"""
        self.remaining = self.initial_seconds
        self.status = "idle"
```

### 4.2 SessionStateMachine（models/session.py）

```python
from enum import Enum

class SessionState(Enum):
    """セッションの状態定義"""
    IDLE = "idle"
    WORKING = "working"
    BREAK = "break"
    PAUSED = "paused"

class SessionStateMachine:
    """状態遷移の明確化 - テスト可能な設計
    
    特性：
    - 状態遷移ルールを名示的に定義
    - 無効な遷移を防止
    - テスト：各遷移パターンを検証
    """
    
    def __init__(self):
        self.state = SessionState.IDLE
        self.completed_sessions = 0
    
    def start_work(self) -> bool:
        """作業開始（IDLE -> WORKING）"""
        if self.state == SessionState.IDLE:
            self.state = SessionState.WORKING
            return True
        return False
    
    def start_break(self) -> bool:
        """休憩開始（WORKING -> BREAK）"""
        if self.state == SessionState.WORKING:
            self.state = SessionState.BREAK
            self.completed_sessions += 1
            return True
        return False
    
    def resume_work(self) -> bool:
        """作業再開（BREAK -> WORKING）"""
        if self.state == SessionState.BREAK:
            self.state = SessionState.WORKING
            return True
        return False
    
    def reset(self) -> None:
        """リセット（任意 -> IDLE）"""
        self.state = SessionState.IDLE
```

### 4.3 Repository パターン（models/repository.py）

```python
from abc import ABC, abstractmethod
import json

class Repository(ABC):
    """データアクセス層の抽象化
    
    メリット：
    - 本番環境とテスト環境でストレージを切り替え可能
    - ビジネスロジック層がストレージ実装に依存しない
    """
    
    @abstractmethod
    def save(self, key: str, data: dict) -> None:
        pass
    
    @abstractmethod
    def load(self, key: str) -> dict:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        pass

class FileRepository(Repository):
    """ファイルベースのリポジトリ（本番環境）"""
    
    def __init__(self, filepath: str = "sessions.json"):
        self.filepath = filepath
    
    def save(self, key: str, data: dict) -> None:
        try:
            with open(self.filepath, 'r') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            all_data = {}
        
        all_data[key] = data
        with open(self.filepath, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    def load(self, key: str) -> dict:
        try:
            with open(self.filepath, 'r') as f:
                all_data = json.load(f)
                return all_data.get(key, {})
        except FileNotFoundError:
            return {}
    
    def delete(self, key: str) -> None:
        try:
            with open(self.filepath, 'r') as f:
                all_data = json.load(f)
            all_data.pop(key, None)
            with open(self.filepath, 'w') as f:
                json.dump(all_data, f, indent=2)
        except FileNotFoundError:
            pass

class InMemoryRepository(Repository):
    """メモリベースのリポジトリ（テスト環境）
    
    特性：
    - ファイルI/Oなし - 高速
    - テスト間で独立したストレージ
    """
    
    def __init__(self):
        self.storage = {}
    
    def save(self, key: str, data: dict) -> None:
        self.storage[key] = data
    
    def load(self, key: str) -> dict:
        return self.storage.get(key, {})
    
    def delete(self, key: str) -> None:
        self.storage.pop(key, None)
```

### 4.4 Services層（services/timer_service.py）

```python
from models.timer import Timer
from models.session import SessionStateMachine
from models.repository import Repository
from datetime import datetime

class TimerService:
    """ビジネスロジックのオーケストレーション
    
    特性：
    - 依存性注入により、モック化可能
    - Models と Repository の協調
    """
    
    def __init__(self, repository: Repository, config):
        self.repository = repository
        self.config = config
        self.timer = Timer(config.WORK_DURATION)
        self.state_machine = SessionStateMachine()
    
    def start_work_session(self) -> dict:
        """作業セッション開始"""
        if not self.state_machine.start_work():
            return {"error": "無効な状態遷移"}
        
        self.timer = Timer(self.config.WORK_DURATION)
        self.timer.start()
        return self._get_current_state()
    
    def start_break_session(self) -> dict:
        """休憩セッション開始"""
        if not self.state_machine.start_break():
            return {"error": "無効な状態遷移"}
        
        self.timer = Timer(self.config.BREAK_DURATION)
        self.timer.start()
        return self._get_current_state()
    
    def tick(self) -> dict:
        """1秒進める"""
        new_remaining = self.timer.tick()
        
        # ここでセッション完了時の処理を追加可能
        if new_remaining == 0:
            self._handle_session_complete()
        
        return self._get_current_state()
    
    def _handle_session_complete(self) -> None:
        """セッション完了時の処理"""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self.repository.load(f"stats:{today}")
        if not stats:
            stats = {"sessions": 0, "total_focus_time": 0}
        
        stats["sessions"] += 1
        stats["total_focus_time"] += self.config.WORK_DURATION
        self.repository.save(f"stats:{today}", stats)
    
    def _get_current_state(self) -> dict:
        """現在の状態を辞書で返す"""
        return {
            "remaining": self.timer.remaining,
            "status": self.timer.status,
            "state": self.state_machine.state.value,
            "completed_sessions": self.state_machine.completed_sessions
        }
```

---

## 5. 構成管理（config.py）

```python
import os

class Config:
    """基本設定"""
    WORK_DURATION = int(os.getenv('WORK_DURATION', 1500))  # 25分
    BREAK_DURATION = int(os.getenv('BREAK_DURATION', 300))  # 5分
    REPOSITORY_TYPE = os.getenv('REPOSITORY_TYPE', 'file')

class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    REPOSITORY_TYPE = 'file'

class TestConfig(Config):
    """テスト環境設定"""
    DEBUG = False
    REPOSITORY_TYPE = 'memory'  # テストではメモリストレージを使用
    WORK_DURATION = 10  # テスト高速化のため短く設定
    BREAK_DURATION = 5

class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    REPOSITORY_TYPE = 'file'
```

---

## 6. API設計

### 6.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | リクエスト | レスポンス |
|---------|---------------|------|----------|----------|
| GET | `/` | UIの表示 | - | HTML |
| POST | `/api/timer/start-work` | 作業開始 | - | JSON |
| POST | `/api/timer/start-break` | 休憩開始 | - | JSON |
| GET | `/api/timer/state` | 現在の状態取得 | - | JSON |
| POST | `/api/timer/reset` | リセット | - | JSON |
| GET | `/api/stats/today` | 本日の統計 | - | JSON |

### 6.2 レスポンス例

```json
# GET /api/timer/state
{
  "remaining": 1485,
  "status": "working",
  "state": "working",
  "completed_sessions": 3
}

# GET /api/stats/today
{
  "sessions": 4,
  "total_focus_time": 6000
}
```

---

## 7. Flask アプリケーション構成（app.py）

```python
from flask import Flask, render_template, jsonify, request
from config import DevelopmentConfig
from models.repository import FileRepository, InMemoryRepository
from services.timer_service import TimerService

def create_app(config=None):
    """アプリケーションファクトリー"""
    app = Flask(__name__)
    
    if config is None:
        config = DevelopmentConfig()
    
    app.config.from_object(config)
    
    # リポジトリ選択
    if config.REPOSITORY_TYPE == 'memory':
        repository = InMemoryRepository()
    else:
        repository = FileRepository()
    
    # サービス初期化
    timer_service = TimerService(repository, config)
    
    # UI
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # API
    @app.route('/api/timer/start-work', methods=['POST'])
    def start_work():
        state = timer_service.start_work_session()
        return jsonify(state)
    
    @app.route('/api/timer/state', methods=['GET'])
    def get_state():
        state = timer_service._get_current_state()
        return jsonify(state)
    
    @app.route('/api/timer/tick', methods=['POST'])
    def tick():
        state = timer_service.tick()
        return jsonify(state)
    
    @app.route('/api/stats/today', methods=['GET'])
    def get_stats():
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        stats = repository.load(f"stats:{today}")
        return jsonify(stats or {"sessions": 0, "total_focus_time": 0})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

---

## 8. テスト戦略

### 8.1 pytest 共通設定（tests/conftest.py）

```python
import pytest
from config import TestConfig
from models.repository import InMemoryRepository
from services.timer_service import TimerService

@pytest.fixture
def test_config():
    """テスト用設定"""
    return TestConfig()

@pytest.fixture
def mock_repository():
    """モックリポジトリ"""
    return InMemoryRepository()

@pytest.fixture
def timer_service(mock_repository):
    """DIでモックリポジトリを注入"""
    config = TestConfig()
    return TimerService(mock_repository, config)
```

### 8.2 ユニットテスト例（tests/unit/test_timer.py）

```python
import pytest
from models.timer import Timer

def test_timer_initialization():
    """初期化テスト"""
    timer = Timer(1500)
    assert timer.remaining == 1500
    assert timer.status == "idle"

def test_timer_tick_when_working():
    """作業中の経過テスト"""
    timer = Timer(100)
    timer.start()
    new_remaining = timer.tick()
    assert new_remaining == 99

def test_timer_tick_when_paused():
    """一時停止中は進まない"""
    timer = Timer(100)
    timer.pause()
    new_remaining = timer.tick()
    assert new_remaining == 100

def test_timer_reaches_zero():
    """0に達する"""
    timer = Timer(2)
    timer.start()
    timer.tick()
    remaining = timer.tick()
    assert remaining == 0
```

### 8.3 テスト実行コマンド

```bash
# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit/ -v

# 統合テスト
pytest tests/integration/ -v

# カバレッジ出力
pytest --cov=models --cov=services tests/

# 特定ファイルのテスト
pytest tests/unit/test_timer.py -v
```

---

## 9. 実装フェーズ

### **Phase 1: コア機能**（1週間）
- [ ] Timer クラス実装・ユニットテスト
- [ ] SessionStateMachine 実装・ユニットテスト
- [ ] Repository 抽象化・実装選択テスト
- [ ] TimerService 実装・ユニットテスト
- [ ] Flask アプリベース実装
- [ ] 基本 API エンドポイント実装

### **Phase 2: UI実装**（1週間）
- [ ] HTMLテンプレート（index.html）
- [ ] CSS スタイル（style.css） - モック画面の再現
- [ ] JavaScript フロントエンドロジック（timer.js）
- [ ] API連携・リアルタイム表示
- [ ] 手動テスト・UI調整

### **Phase 3: 進捗機能**（1週間）
- [ ] セッション記録機能
- [ ] 本日の統計表示
- [ ] プログレスバー表示
- [ ] 統計テストの追加

### **Phase 4: 拡張機能**（2週間）
- [ ] 音声通知機能
- [ ] 設定画面（時間カスタマイズ）
- [ ] 長休憩（15分）の自動挿入
- [ ] ダークモード
- [ ] ローカルストレージの履歴保存

---

## 10. テスト可能性チェックリスト

| 項目 | 実装状况 | 効果 |
|------|----------|------|
| **ビジネスロジック分離** | ✅ Pure Functions 中心 | 副作用なし - 高速テスト |
| **ファイルI/O隔離** | ✅ Repository Pattern | モック化可能 |
| **依存性注入** | ✅ DI Pattern 採用 | ビジネスロジック層の独立性 |
| **状態管理明確性** | ✅ State Machine 導入 | 状態遷移の検証 |
| **設定管理** | ✅ Config Classes | 環境ごとの設定切り替え |
| **テストフィクスチャ** | ✅ conftest.py整備 | セットアップ簡潔化・再利用性 |

---

## 11. 主要設計パターン・原則

### 11.1 採用パターン

- **Repository Pattern**: データアクセス層の抽象化
- **Service Layer**: ビジネスロジックのオーケストレーション
- **Dependency Injection**: 疎結合・テスト可能性向上
- **State Machine**: 状態遷移の明確化
- **Factory Pattern**: アプリケーション初期化

### 11.2 適用原則

- **SOLID原則**: 単一責任・Open/Closed・Liskov置換・インターフェース分離・依存性逆転
- **DRY（Don't Repeat Yourself）**: コードの重複排除
- **KISS（Keep It Simple, Stupid）**: シンプルでわかりやすい設計

---

## 12. ディレクトリ別の責任

| ディレクトリ | 責任 | テスト対象 | テスト速度 |
|-------------|------|----------|----------|
| `models/` | ドメインロジック | unit test | 最速（副作用なし） |
| `services/` | ビジネスロジック | unit test + integration | 速い（DI活用） |
| `app.py` | HTTP処理 | integration test | 中程度 |
| `static/` | UI表示・ユーザー操作 | E2E/manual | 遅い |

---

## 13. 今後の保守・拡張ガイドライン

1. **新機能追加時**:
   - 先にビジネスロジックをModelsに実装
   - 次に Services でテスト
   - 最後に Flask API・UI で公開

2. **テスト追加時**:
   - Pure Functions のテストから始める
   - 複雑な状態遷移はテストカバレッジを高める
   - 統合テストで全体動作を確認

3. **設定変更時**:
   - `config.py` で環境ごとに管理
   - 環境変数でオーバーライド可能に

4. **ストレージ変更時**:
   - Repository 実装を追加（SQLAlchemy など）
   - 既存コードは変更不要

---

## まとめ

このアーキテクチャは以下の特性を兼ね備えています：

✅ **テスト可能性**: Pure Functions・DI・モック化しやすい設計  
✅ **保守性**: 関心の明確な分離・責任の分散  
✅ **拡張性**: 新機能追加が容易・既存コード変更は最小限  
✅ **理解しやすさ**: わかりやすいレイヤー分割・責任定義  

このアーキテクチャに従うことで、高品質で長期的に保守しやすいポモドーロタイマーアプリケーションが実現できます。
