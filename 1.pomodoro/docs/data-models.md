# データモデル仕様

ポモドーロタイマーアプリケーションで使用するデータモデルを説明します。

---

## Timer（`models/timer.py`）

タイマーのコアロジックを担うクラスです。ファイルI/Oや外部依存を持たない純粋なドメインオブジェクトです。

### フィールド

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `initial_seconds` | `int` | タイマーの初期秒数（0以上必須） |
| `remaining` | `int` | 残り秒数 |
| `status` | `str` | タイマーの動作状態（`"idle"` / `"working"` / `"paused"`） |

### メソッド

| メソッド | 説明 |
|---------|------|
| `__init__(initial_seconds: int)` | 初期化。`initial_seconds < 0` の場合 `ValueError` を送出 |
| `tick() -> int` | `status == "working"` かつ `remaining > 0` のとき `remaining` を1減算して返す |
| `start() -> None` | `status` を `"working"` に設定 |
| `pause() -> None` | `status` を `"paused"` に設定 |
| `reset() -> None` | `remaining` を `initial_seconds` に戻し、`status` を `"idle"` に設定 |

### 状態遷移

```
idle ──start()──▶ working ──pause()──▶ paused
  ▲                  │
  └──────reset()─────┘
```

---

## SessionState（`models/session.py`）

セッションの状態を定義する Enum です。

| 値 | 文字列表現 | 説明 |
|---|-----------|------|
| `SessionState.IDLE` | `"idle"` | 待機中（作業・休憩なし） |
| `SessionState.WORKING` | `"working"` | 作業中 |
| `SessionState.BREAK` | `"break"` | 休憩中 |

---

## SessionStateMachine（`models/session.py`）

セッションの状態遷移を管理するクラスです。不正な遷移を `bool` の返り値で通知します。

### フィールド

| フィールド | 型 | 初期値 | 説明 |
|-----------|-----|-------|------|
| `state` | `SessionState` | `SessionState.IDLE` | 現在のセッション状態 |
| `completed_sessions` | `int` | `0` | 完了した作業セッション数 |

### メソッド

| メソッド | 遷移条件 | 成功時の変化 | 失敗時 |
|---------|---------|------------|--------|
| `start_work() -> bool` | `state` が `IDLE` または `BREAK` | `state → WORKING` | `False` を返す |
| `start_break() -> bool` | `state` が `WORKING` | `state → BREAK`、`completed_sessions += 1` | `False` を返す |
| `reset() -> None` | 常に成功 | `state → IDLE` | — |

### 状態遷移図

```
        start_work()
IDLE ───────────────▶ WORKING
 ▲                       │
 │  reset()              │ start_break()
 │                       ▼
 └──────────────── BREAK ──── start_work() ───▶ WORKING
```

---

## Repository（`models/repository.py`）

データ永続化の抽象インタフェースです。

### 抽象クラス `Repository`

| メソッド | シグネチャ | 説明 |
|---------|-----------|------|
| `save` | `(key: str, data: dict) -> None` | キーに対してデータを保存 |
| `load` | `(key: str) -> dict` | キーに対するデータを取得（存在しない場合は `{}` を返す） |
| `delete` | `(key: str) -> None` | キーに対するデータを削除 |

### FileRepository

JSONファイル（デフォルト: `sessions.json`）を使ったローカル永続化実装です。

- ファイルが存在しない場合は空辞書として扱います
- 読み書きは UTF-8 エンコーディングで行います
- `filepath` は `Path` オブジェクトとして保持します

```python
repo = FileRepository(filepath="sessions.json")
```

### InMemoryRepository

テスト用のインメモリ実装です。

- `storage: dict[str, dict]` に全データを保持します
- ファイルI/Oが発生しないため高速です

```python
repo = InMemoryRepository()
```

---

## 統計データ形式

統計はリポジトリに `"stats:YYYY-MM-DD"` をキーとして保存されます。

### 保存形式（リポジトリ内部）

```json
{
  "sessions": 3,
  "total_focus_time": 4500
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `sessions` | integer | その日に完了した作業セッション数 |
| `total_focus_time` | integer | その日の合計集中時間（秒） |

統計は `TimerService._handle_session_complete()` によって作業セッション完了時にのみ更新されます。休憩セッションの完了では更新されません。
