# フロントエンド モジュールドキュメント

ポモドーロタイマーアプリケーションのフロントエンド実装を説明します。

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `templates/index.html` | アプリケーションの唯一のHTMLテンプレート |
| `static/css/style.css` | UIスタイル定義 |
| `static/js/timer.js` | タイマーロジック・API連携・UI更新 |

> **注意:** `index.html` は `static/js/settings.js` を参照していますが、このファイルは現時点では存在しません。設定モーダルの保存・適用ロジックは未実装です。

---

## index.html

Flask の Jinja2 テンプレートとして提供されます。言語は日本語 (`lang="ja"`)。

### 主要要素

| 要素ID | 説明 |
|-------|------|
| `statusText` | 現在の状態テキスト（`待機中` / `作業中` / `休憩中`） |
| `timeDisplay` | 残り時間の `MM:SS` 表示 |
| `ringWrap` | 円形プログレスバーのラッパー（CSS変数 `--progress`、`--ring-color` で制御） |
| `startButton` | 作業開始ボタン |
| `resetButton` | リセットボタン |
| `sessionsValue` | 完了セッション数の表示 |
| `focusMinutesValue` | 集中時間の表示 |
| `errorMessage` | エラーメッセージ表示エリア（`role="alert"` / `aria-live="polite"`） |
| `darkModeBtn` | ダークモード切り替えボタン |
| `settingsBtn` | 設定モーダル開閉ボタン |
| `settingsModal` | タイマー設定モーダル |

### テーマ

`<html data-theme="light|dark">` 属性でライト/ダークモードを切り替えます。初期値はローカルストレージの `darkMode` キーで決まります。

---

## timer.js

### 状態オブジェクト（`state`）

アプリ全体の状態を保持するシングルトンオブジェクトです。

| プロパティ | 型 | 初期値 | 説明 |
|-----------|-----|-------|------|
| `mode` | string | `"idle"` | 現在のセッション状態（`idle` / `working` / `break`） |
| `remaining` | number | `0` | 残り秒数 |
| `workDuration` | number | `1500` | 作業時間（秒）※サーバー設定で上書き |
| `breakDuration` | number | `300` | 通常休憩時間（秒）※サーバー設定で上書き |
| `longBreakDuration` | number | `900` | 長休憩時間（秒）※サーバー設定で上書き |
| `sessionsUntilLongBreak` | number | `4` | 長休憩までのセッション数 |
| `timerId` | number\|null | `null` | `setInterval` のID（タイマーループ） |
| `statsRefreshId` | number\|null | `null` | `setInterval` のID（統計更新ループ） |
| `soundEnabled` | boolean | `localStorage` 参照 | 音声通知の有効/無効 |
| `darkMode` | boolean | `localStorage` 参照 | ダークモードの有効/無効 |

---

### 主要関数

#### 初期化

| 関数 | 説明 |
|-----|------|
| `init()` | ページ読み込み時のエントリポイント。ダークモード初期化 → 設定ロード → 状態取得 → ループ開始判定 → 統計更新 |
| `initDarkMode()` | `localStorage.darkMode` を読み取り `data-theme` 属性を設定 |
| `loadConfig()` | `GET /api/config` から設定を取得して `state` に反映 |

#### UI描画

| 関数 | 説明 |
|-----|------|
| `renderTimer()` | `timeDisplay`、`statusText`、円形プログレスバーを `state` に基づいて更新 |
| `applyApiState(payload)` | APIレスポンスの `state`・`remaining` を `state` オブジェクトに反映し `renderTimer()` を呼び出す |
| `formatTime(seconds)` | 秒数を `"MM:SS"` 形式の文字列に変換 |
| `modeText(mode)` | `mode` に対応する日本語テキストを返す（`"作業中"` / `"休憩中"` / `"待機中"`） |
| `modeColor(mode)` | `mode` に対応するカラーコードを返す（`#e4572e` / `#0f766e` / `#8b6d5c`） |
| `setError(message)` | `errorMessage` 要素にエラーテキストを設定（空文字でクリア） |

#### タイマーループ

| 関数 | 説明 |
|-----|------|
| `startLoop()` | 1秒ごとに `POST /api/timer/tick` を呼び出す `setInterval` を開始 |
| `stopLoop()` | タイマーループを停止 |
| `startStatsRefresh()` | 5秒ごとに `GET /api/stats/today` を取得する `setInterval` を開始 |
| `stopStatsRefresh()` | 統計更新ループを停止 |

`startLoop()` 内の処理フロー:

1. `POST /api/timer/tick` を呼び出す
2. `remaining === 0` になった場合:
   - `playNotificationSound("complete")` を実行
   - `state === "working"` なら `POST /api/timer/start-break` を呼び出して自動休憩開始
   - `state !== "working"`（休憩終了）なら `stopLoop()` と `stopStatsRefresh()` を呼び出す

#### ユーザー操作

| 関数 | 説明 |
|-----|------|
| `startWork()` | `POST /api/timer/start-work` を呼び出してタイマーループを開始 |
| `resetTimer()` | `POST /api/timer/reset` を呼び出してループを停止し状態を初期化 |
| `refreshStats()` | `GET /api/stats/today` を取得して `sessionsValue`・`focusMinutesValue` を更新 |
| `refreshState()` | `GET /api/timer/state` を取得して表示を同期 |

#### サウンド・テーマ

| 関数 | 説明 |
|-----|------|
| `playNotificationSound(type)` | Web Audio API でビープ音を生成。`"complete"` は 800Hz/0.5秒、`"break"` は 600Hz/0.3秒 |
| `toggleDarkMode()` | ダークモードを切り替えて `localStorage` と `data-theme` 属性に反映 |

---

### APIユーティリティ

```javascript
async function api(path, options = {})
```

`fetch` のラッパー関数です。

- デフォルトメソッドは `GET`
- レスポンスが `ok` でない場合、`data.error` のメッセージで `Error` を送出します
- リクエストヘッダーに `Content-Type: application/json` を設定します

---

### イベントリスナー

| 要素 | イベント | ハンドラ |
|-----|---------|---------|
| `#startButton` | `click` | `startWork()` |
| `#resetButton` | `click` | `resetTimer()` |

---

## style.css

CSS変数（カスタムプロパティ）によるテーマ切り替えに対応しています。

### 円形プログレスバー

`#ringWrap` の CSS変数 `--progress`（0〜100）と `--ring-color` で動的に描画されます。`timer.js` の `renderTimer()` が毎秒更新します。

### ダークモード

`[data-theme="dark"]` セレクタによる上書きで対応します。
