# ポモドーロタイマー - 実装機能一覧

## 1. バックエンド（Python / Flask）

### コアモデル（`models/`）

#### Timer クラス（`models/timer.py`）
- [ ] タイマーの初期化（秒数指定）
- [ ] `tick()` で1秒カウントダウン
- [ ] `start()` でタイマー開始
- [ ] `pause()` で一時停止
- [ ] `reset()` でリセット

#### SessionStateMachine クラス（`models/session.py`）
- [ ] 状態定義：`IDLE` → `WORKING` → `BREAK` → `IDLE`
- [ ] 無効な状態遷移の防止
- [ ] 完了セッション数のカウント

#### Repository パターン（`models/repository.py`）
- [ ] 抽象基底クラス `Repository`
- [ ] `FileRepository`（本番：JSONファイル保存）
- [ ] `InMemoryRepository`（テスト用）

### サービス層（`services/`）

#### TimerService（`services/timer_service.py`）
- [ ] 作業セッション開始
- [ ] 休憩セッション開始
- [ ] `tick()` の呼び出し管理
- [ ] セッション完了時の統計保存

#### StatsService（`services/stats_service.py`）
- [ ] 本日の完了セッション数集計
- [ ] 集中時間（分）の計算・表示

### API エンドポイント（`app.py`）
- [ ] `POST /api/timer/start-work` — 作業開始
- [ ] `POST /api/timer/start-break` — 休憩開始
- [ ] `GET /api/timer/state` — 現在状態取得
- [ ] `POST /api/timer/reset` — リセット
- [ ] `GET /api/stats/today` — 本日の統計取得
- [ ] `GET /` — UI表示

### 設定管理（`config.py`）
- [ ] `DevelopmentConfig` / `TestConfig` / `ProductionConfig`
- [ ] 作業時間（25分）・休憩時間（5分）の環境変数対応

---

## 2. フロントエンド（HTML / CSS / JavaScript）

### UIレイアウト（`templates/index.html`）
- [ ] 「作業中 / 休憩中」の状態ラベル
- [ ] 円形プログレスバー（リング状）
- [ ] 残り時間の中央表示（`MM:SS` 形式）
- [ ] 「開始」「リセット」ボタン

### スタイル（`static/css/style.css`）
- [ ] 紫系カラーデザイン
- [ ] 円形プログレスバーのCSS実装
- [ ] ボタンスタイル（塗り / アウトライン）
- [ ] 「今日の進捗」エリアのレイアウト

### フロントエンドロジック（`static/js/timer.js`）
- [ ] 1秒ごとの画面カウントダウン処理
- [ ] 「開始」ボタンで `start-work` API を呼び出し
- [ ] 「リセット」ボタンで `reset` API を呼び出し
- [ ] 残り時間・状態のリアルタイム画面更新
- [ ] セッション完了時の自動休憩切り替え
- [ ] 「今日の進捗」（完了数・集中時間）の表示更新

---

## 3. テスト（`tests/`）

- [ ] `conftest.py` — `TestConfig`・`InMemoryRepository`・`TimerService` のフィクスチャ定義
- [ ] `unit/test_timer.py` — `Timer` クラスの単体テスト
- [ ] `unit/test_session.py` — `SessionStateMachine` の状態遷移テスト
- [ ] `unit/test_services.py` — `TimerService` / `StatsService` のビジネスロジックテスト
- [ ] `integration/test_api.py` — Flaskエンドポイントの統合テスト

---

## 4. プロジェクト設定ファイル

- [ ] `requirements.txt` — Flask、pytest、pytest-cov 等
- [ ] `pytest.ini` — テスト設定（カバレッジ対象パス等）

---

## 優先度

| フェーズ | 対象 | 優先度 |
|---------|------|-------|
| Phase 1 | モデル・サービス・API基盤・単体テスト | 高 |
| Phase 2 | HTML / CSS / JS・UI実装 | 高 |
| Phase 3 | 統計機能・進捗表示 | 中 |
| Phase 4 | 音声通知・設定画面・長休憩・ダークモード | 低 |
