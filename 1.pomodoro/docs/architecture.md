# アーキテクチャ概要

ポモドーロタイマーアプリケーションの現行アーキテクチャを説明します。

---

## プロジェクト構造

```
1.pomodoro/
├── app.py                      # Flaskアプリケーションファクトリ・エンドポイント定義
├── config.py                   # 環境別設定クラス
├── models/
│   ├── __init__.py
│   ├── timer.py               # タイマーコアロジック
│   ├── session.py             # セッション状態機械
│   └── repository.py          # データアクセス層（抽象化）
├── services/
│   ├── __init__.py
│   ├── timer_service.py       # タイマービジネスロジック
│   └── stats_service.py       # 統計ビジネスロジック
├── static/
│   ├── css/
│   │   └── style.css          # UIスタイル
│   └── js/
│       └── timer.js           # フロントエンドロジック
├── templates/
│   └── index.html             # HTMLテンプレート
├── tests/
│   ├── conftest.py            # pytest フィクスチャ
│   ├── unit/
│   │   ├── test_timer.py
│   │   ├── test_session.py
│   │   ├── test_repository.py
│   │   └── test_services.py
│   └── integration/
│       ├── test_app.py
│       └── test_api.py
├── requirements.txt
└── pytest.ini
```

---

## レイヤー構成

```
┌─────────────────────────────────────┐
│       ユーザー操作（ブラウザ UI）      │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│     フロントエンド層（static/js/timer.js）│
│  ・1秒ごとの /api/timer/tick ポーリング │
│  ・開始/リセットボタンのイベント処理    │
│  ・統計の5秒ごと自動更新              │
│  ・設定の初期ロード                   │
└────────────────┬────────────────────┘
                 │ HTTP（JSON）
                 ▼
┌─────────────────────────────────────┐
│        API層（app.py）              │
│  ・Flaskアプリケーションファクトリ     │
│  ・HTTPルーティングとレスポンス生成    │
│  ・サービスへの委譲                  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│       サービス層（services/）        │
│  ・TimerService: タイマー制御        │
│  ・StatsService: 統計集計            │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      モデル層（models/）             │
│  ・Timer: 残り時間・状態管理          │
│  ・SessionStateMachine: 状態遷移     │
│  ・Repository: ストレージ抽象化       │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      永続化層                        │
│  ・FileRepository: sessions.json     │
│  ・InMemoryRepository: テスト用       │
└─────────────────────────────────────┘
```

---

## レイヤーの責任

| レイヤー | 主な責任 | テスト種別 |
|---------|---------|-----------|
| フロントエンド（timer.js） | UI描画・API呼び出し・状態反映 | 手動テスト |
| API（app.py） | HTTPルーティング・リクエスト検証 | 統合テスト |
| サービス（services/） | ビジネスロジック・オーケストレーション | ユニットテスト |
| モデル（models/） | ドメインロジック・状態管理 | ユニットテスト |
| リポジトリ | データ永続化 | モック化可能 |

---

## アプリケーション初期化

`app.py` の `create_app(config_object)` ファクトリ関数がアプリケーションを生成します。

1. `config_object` から設定を読み込む（省略時は `DevelopmentConfig`）
2. `REPOSITORY_TYPE` が `"memory"` なら `InMemoryRepository`、それ以外なら `FileRepository` を生成
3. `TimerService` と `StatsService` をインスタンス化し、サービスに渡す
4. Flask のルートをクロージャで定義し、サービスを参照させる

---

## 設定管理

`config.py` で環境ごとのクラスを定義しています。

| クラス | 用途 | `REPOSITORY_TYPE` | `DEBUG` |
|-------|------|-------------------|---------|
| `Config` | 基底クラス（環境変数オーバーライド対応） | `"file"` | `False` |
| `DevelopmentConfig` | ローカル開発 | `"file"` | `True` |
| `TestConfig` | pytest 実行 | `"memory"` | `False` |
| `ProductionConfig` | 本番環境 | `"file"` | `False` |

環境変数 `WORK_DURATION`、`BREAK_DURATION`、`LONG_BREAK_DURATION`、`SESSIONS_UNTIL_LONG_BREAK`、`REPOSITORY_TYPE` でデフォルト値をオーバーライドできます。

---

## 採用パターン

| パターン | 適用箇所 | 目的 |
|---------|---------|------|
| **Factory Pattern** | `create_app()` | 環境ごとのアプリ初期化 |
| **Repository Pattern** | `models/repository.py` | ストレージ実装の抽象化 |
| **Service Layer** | `services/` | ビジネスロジックの集約 |
| **Dependency Injection** | `TimerService(repository, config)` | テスト時のモック注入 |
| **State Machine** | `SessionStateMachine` | 状態遷移の明確化と不正操作防止 |

---

## テスト戦略

- **ユニットテスト**: `models/` と `services/` を `InMemoryRepository` と `TestConfig` でテスト
- **統合テスト**: `app.test_client()` を使い Flask エンドポイントをエンドツーエンドで検証
- `conftest.py` で `app`、`client`、`mock_repository`、`timer_service` フィクスチャを共有定義
