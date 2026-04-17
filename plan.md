# ポモドーロタイマー 実装計画（詳細版）

このドキュメントは、[architecture.md](architecture.md) と [1.pomodoro/features.md](1.pomodoro/features.md) を基にした段階的な実装計画です。

## 目的と進め方

- 各フェーズで「動く成果物」を作る
- テスト可能性を優先して、ドメインロジックから先に実装する
- 1フェーズは 2〜4 日、1タスクは 1〜3 時間を目安に分割する

---

## Phase 0: プロジェクト土台整備（0.5〜1日）

### 目的
- 開発開始に必要な最小構成を整える
- 設定・依存・テスト基盤を先に確立する

### 実装内容
- ディレクトリ構成の作成
  - `models/`, `services/`, `templates/`, `static/css/`, `static/js/`, `tests/` など
- 設定ファイルの追加
  - `config.py`, `requirements.txt`, `pytest.ini`
- Flask アプリケーションの骨格実装
  - `create_app()` ベースの構成
- テスト共通設定の追加
  - `tests/conftest.py`

### タスク分解（1〜3時間単位）
1. 依存パッケージ定義（Flask, pytest, pytest-cov）
2. `config.py` の環境別設定作成（Development/Test/Production）
3. `app.py` のアプリファクトリー化
4. `tests/` と `conftest.py` の初期化

### テスト
- アプリ起動確認
- ルートアクセス確認（GET `/`）
- pytest 実行確認

### 完了条件（DoD）
- Flask が起動しトップページを返す
- pytest が失敗なく実行できる
- TestConfig で起動できる

---

## Phase 1: ドメインモデル実装（1〜2日）

### 目的
- UI/API から独立したコアロジックを固定する
- 副作用の少ない層からテストで品質を担保する

### 実装内容
- `models/timer.py`
  - `Timer` クラス（初期化、start、pause、reset、tick）
- `models/session.py`
  - `SessionState`、`SessionStateMachine`
- `models/repository.py`
  - `Repository` 抽象クラス
  - `InMemoryRepository` 実装
  - `FileRepository` 最小実装

### タスク分解（1〜3時間単位）
1. Timer の基本動作実装
2. Timer の境界値制御（0未満防止）
3. StateMachine の状態定義と遷移ルール実装
4. Repository 抽象化と2種実装の作成

### テスト
- `tests/unit/test_timer.py`
  - 初期化、作業中 tick、一時停止時 tick、0到達、reset
- `tests/unit/test_session.py`
  - 有効遷移、無効遷移、完了セッション数更新
- `tests/unit/test_repository.py`
  - save/load/delete の検証

### 完了条件（DoD）
- モデル層ユニットテストが全通過
- コアロジックが Flask 依存なしで実行可能

---

## Phase 2: サービス層 + API 最小機能（1〜2日）

### 目的
- API だけでポモドーロ基本フローが動く状態にする
- ビジネスロジックのオーケストレーションを確立する

### 実装内容
- `services/timer_service.py`
  - 作業開始、休憩開始、tick、reset、状態取得
  - セッション完了時の統計更新
- `services/stats_service.py`（最小版）
  - 本日の統計取得
- `app.py` API 実装
  - `POST /api/timer/start-work`
  - `POST /api/timer/start-break`
  - `GET /api/timer/state`
  - `POST /api/timer/tick`
  - `POST /api/timer/reset`
  - `GET /api/stats/today`

### タスク分解（1〜3時間単位）
1. TimerService の DI 対応（Repository, Config）
2. 開始/進行/完了ロジック実装
3. 統計保存処理の接続
4. API エンドポイント定義と JSON 返却統一
5. 異常系（無効遷移）のエラーレスポンス整理

### テスト
- `tests/unit/test_services.py`
  - TimerService 正常系・異常系
- `tests/integration/test_api.py`
  - 各 API のレスポンス検証
  - 開始→tick→完了の時系列シナリオ

### 完了条件（DoD）
- API 単体で基本サイクルを再現可能
- サービス・統合テストが通る

---

## Phase 3: UI 静的実装（1〜2日）

### 目的
- 添付モックに近い見た目を先に完成させる
- レイアウトと主要コンポーネントを確定する

### 実装内容
- `templates/index.html`
  - 状態ラベル、円形プログレス、残り時間、開始/リセット、今日の進捗
- `static/css/style.css`
  - 配色、余白、ボタン、カード
  - 円形リング（conic-gradient など）
  - レスポンシブ対応

### タスク分解（1〜3時間単位）
1. HTML 骨格の作成
2. メインカードとヘッダーのスタイル
3. 円形リングと中央時刻表示
4. ボタン群と進捗カードのスタイル
5. モバイル幅の崩れ修正

### テスト
- 手動確認（PC/モバイル）
- 主要ブラウザで表示崩れ確認
- モックとの差分確認（色、配置、余白）

### 完了条件（DoD）
- モックに沿った UI になっている
- 主要幅で致命的な崩れがない

---

## Phase 4: フロント連携 + リアルタイム動作（1〜2日）

### 目的
- UI と API を接続し、実際に利用できるタイマーにする

### 実装内容
- `static/js/timer.js`
  - 開始/リセット操作
  - 1秒ごとの更新（state/tick 連携）
  - 表示更新（状態、残り時間、進捗リング）
  - セッション完了時の切り替え（作業→休憩）

### タスク分解（1〜3時間単位）
1. API 呼び出しユーティリティの実装
2. 時刻フォーマット関数（MM:SS）
3. UI 更新関数の作成
4. setInterval 開始/停止制御
5. エラー時表示と二重起動防止

### テスト
- 手動 E2E
  - 開始→カウントダウン→完了→休憩
  - リセット
  - リロード時の状態復元
- 異常系
  - API 一時失敗時の表示
  - 連打時の多重タイマー防止

### 完了条件（DoD）
- 一連の操作が破綻せず動作する
- UI表示と内部状態にズレがない

---

## Phase 5: 統計機能と品質強化（1〜2日）

### 目的
- 今日の進捗表示を正確にし、回帰に強くする

### 実装内容
- `services/stats_service.py` 本実装
  - 今日の完了セッション数
  - 総集中時間（秒→分/時間表示）
- `app.py` の統計API整理
- `timer.js` で進捗表示の定期更新
- Repository の例外時処理と初期値整備

### タスク分解（1〜3時間単位）
1. StatsService 集計ロジック実装
2. 表示単位変換ルール統一
3. 進捗UI更新処理追加
4. 欠損データ時のデフォルト値調整
5. 回帰テスト追加

### テスト
- `tests/unit/test_services.py` に stats ケース追加
- `tests/integration/test_api.py` に stats API 追加
- 日付・データ無し・複数セッションの境界検証

### 完了条件（DoD）
- 進捗表示が仕様通り
- 欠損データでも UI が壊れない
- 既存含め全テスト通過

---

## Phase 6: 拡張機能（任意・優先度低）

### 目的
- 継続利用に向けた体験改善

### 実装候補
1. 音声通知
2. 設定画面（作業/休憩時間の変更）
3. 長休憩（一定セッションごと）
4. ダークモード

### 推奨実装順
1. 設定画面
2. 長休憩
3. 音声通知
4. ダークモード

### テスト
- 設定反映後のタイマー動作
- 長休憩挿入ロジック
- 既存フロー回帰

### 完了条件（DoD）
- 新機能追加後も既存テストが通る
- 設定と統計の整合性が保たれる

---

## フェーズ横断の運用ルール

1. 1フェーズ開始時に、4〜8 チケットへ分解する
2. 1チケットは半日以内に完了する粒度にする
3. 先にユニットテストを書く対象を明示する
4. フェーズ完了時に最低3つの手動確認シナリオを残す
5. 次フェーズに必要な前提条件を短く記録する

---

## 直近の着手順（おすすめ）

1. Phase 0 を完了して開発基盤を固定
2. Phase 1 でコアロジックをテスト先行で実装
3. Phase 2 で API とサービスを接続
4. Phase 3, 4 で UI とリアルタイム連携を完成
5. Phase 5 で統計品質を上げて安定化
