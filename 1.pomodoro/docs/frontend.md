# フロントエンド モジュールドキュメント

ポモドーロタイマーアプリケーションのフロントエンド実装を説明します。

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `templates/index.html` | アプリケーションの唯一のHTMLテンプレート |
| `static/css/style.css` | UIスタイル定義 |
| `static/js/timer.js` | タイマーロジック・API連携・UI更新 |

> **注意:** `index.html` は以前 `static/js/settings.js` を参照していましたが、設定モーダルのロジックは現在 `timer.js` に統合済みです。`settings.js` は不要です。

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
| `levelValue` | 現在レベルの表示（例: `Lv.3`） |
| `streakValue` | 連続記録日数の表示（例: `5日`） |
| `xpValue` | 累計XPの表示（例: `300 XP`） |
| `badgeList` | バッジ一覧コンテナ |
| `weekSummary` | 週間サマリーテキスト（完了率・平均集中時間） |
| `monthSummary` | 月間サマリーテキスト（完了率・平均集中時間） |
| `weekChart` | 週間ミニチャートコンテナ |
| `monthChart` | 月間ミニチャートコンテナ |
| `errorMessage` | エラーメッセージ表示エリア（`role="alert"` / `aria-live="polite"`） |
| `darkModeBtn` | テーマ切り替えボタン（`light` → `dark` → `focus` の順にサイクル） |
| `themeIcon` | テーマアイコン（☀️ / 🌙 / 🎯） |
| `settingsBtn` | 設定モーダル開閉ボタン |
| `settingsModal` | タイマー設定モーダル |
| `closeSettingsBtn` | 設定モーダルを閉じるボタン（×） |
| `cancelSettingsBtn` | 設定変更をキャンセルするボタン |
| `applySettingsBtn` | 設定変更を適用するボタン |
| `workDurationInput` | 作業時間入力フィールド |
| `breakDurationInput` | 休憩時間入力フィールド |
| `longBreakDurationInput` | 長休憩時間入力フィールド |
| `sessionsUntilLongBreakInput` | 長休憩までのセッション数入力フィールド |
| `themeSelect` | テーマ選択セレクトボックス |
| `startSoundCheckbox` | 開始音 有効/無効チェックボックス |
| `endSoundCheckbox` | 終了音 有効/無効チェックボックス |
| `tickSoundCheckbox` | チック音 有効/無効チェックボックス |

### テーマ

`<html data-theme="light|dark|focus">` 属性でテーマを切り替えます。初期値はローカルストレージの `theme` キーで決まります（デフォルト: `"light"`）。

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
| `soundSettings` | object | `localStorage` 参照 | 音声通知設定。`start`・`end`・`tick` の3つの boolean を持つ |
| `theme` | string | `localStorage` 参照 (`"light"`) | 現在のテーマ（`"light"` / `"dark"` / `"focus"`） |
| `uiVariant` | string | A/B割当 | UIバリアント（`"control"` / `"enhanced"`） |

---

### 主要関数

#### 初期化

| 関数 | 説明 |
|-----|------|
| `init()` | ページ読み込み時のエントリポイント。UIバリアント初期化 → テーマ適用 → 設定ロード → 状態取得 → ループ開始判定 → 統計更新 |
| `initUiVariant()` | `resolveUiVariant()` を呼び出し `state.uiVariant` を設定、`document.body.dataset.uiVariant` に反映 |
| `resolveUiVariant()` | クエリパラメータ→ `localStorage` の順で UIバリアントを解決。未設定時は 50% でランダム割当 |
| `applyTheme(theme)` | テーマ文字列を `state.theme` に設定し、`localStorage` と `data-theme` 属性に反映 |
| `cycleTheme()` | `light` → `dark` → `focus` の順でテーマをサイクル |
| `loadConfig()` | `GET /api/config` から設定を取得して `state` に反映 |

#### UI描画

| 関数 | 説明 |
|-----|------|
| `renderTimer()` | `timeDisplay`、`statusText`、円形プログレスバーを `state` に基づいて更新。`uiVariant === "enhanced"` かつ作業中は残り時間割合に応じた色グラデーションを適用 |
| `applyApiState(payload)` | APIレスポンスの `state`・`remaining` を `state` オブジェクトに反映し `renderTimer()` を呼び出す |
| `formatTime(seconds)` | 秒数を `"MM:SS"` 形式の文字列に変換 |
| `modeText(mode)` | `mode` に対応する日本語テキストを返す（`"作業中"` / `"休憩中"` / `"待機中"`） |
| `modeColor(mode)` | `mode` に対応するカラーコードを返す（`#e4572e` / `#0f766e` / `#8b6d5c`） |
| `blendHexColor(startHex, endHex, ratio)` | 2色をブレンドし `rgb(r, g, b)` 形式で返す |
| `focusColorByRemainingRatio(remainingRatio)` | 残り時間割合(0〜1)に応じて青→黄→赤のグラデーション色を返す |
| `setError(message)` | `errorMessage` 要素にエラーテキストを設定（空文字でクリア） |
| `renderBadges(badges)` | バッジ配列から `badge-chip` 要素を生成し `badgeList` を更新 |
| `renderPeriodSummary(target, periodStats)` | 完了率と平均集中時間のテキストを指定要素に設定 |
| `renderMiniChart(target, chartData, limit)` | 棒グラフのバー要素を生成しチャートコンテナを更新 |

#### タイマーループ

| 関数 | 説明 |
|-----|------|
| `startLoop()` | 1秒ごとに `POST /api/timer/tick` を呼び出す `setInterval` を開始 |
| `stopLoop()` | タイマーループを停止 |
| `startStatsRefresh()` | 5秒ごとに `GET /api/stats/today` を取得する `setInterval` を開始 |
| `stopStatsRefresh()` | 統計更新ループを停止 |

`startLoop()` 内の処理フロー:

1. `POST /api/timer/tick` を呼び出す
2. `remaining > 0` の場合: `playNotificationSound("tick")` を実行
3. `remaining === 0` になった場合:
   - `playNotificationSound("end")` を実行
   - `state === "working"` なら `POST /api/timer/start-break` を呼び出して自動休憩開始し統計を更新
   - `state !== "working"`（休憩終了）なら `stopLoop()` と `stopStatsRefresh()` を呼び出す

#### ユーザー操作

| 関数 | 説明 |
|-----|------|
| `startWork()` | `POST /api/timer/start-work` を呼び出し、開始音を再生してタイマーループを開始 |
| `resetTimer()` | `POST /api/timer/reset` を呼び出してループを停止し状態を初期化、統計を更新 |
| `refreshStats()` | `GET /api/stats/today`、`/api/stats/week`、`/api/stats/month` を並行取得してUI全体を更新 |
| `refreshState()` | `GET /api/timer/state` を取得して表示を同期 |

#### 設定モーダル

| 関数 | 説明 |
|-----|------|
| `openSettingsModal()` | 設定フォームに現在の `state` 値を反映してモーダルを表示 |
| `closeSettingsModal()` | モーダルを非表示にする |
| `applySettings()` | フォーム値を `POST /api/config` で送信し、テーマ・サウンド設定を適用してモーダルを閉じる |
| `syncSoundSettingsUI()` | `state.soundSettings` の値をチェックボックスに反映 |
| `applySoundSettingsFromUI()` | チェックボックスの値を `state.soundSettings` と `localStorage` に保存 |

#### サウンド・テーマ

| 関数 | 説明 |
|-----|------|
| `playNotificationSound(type)` | Web Audio API でビープ音を生成。`"start"` は 660Hz/0.2秒、`"end"` は 800Hz/0.5秒、`"tick"` は 420Hz/0.08秒。対応するサウンド設定が無効の場合は再生しない |
| `applyTheme(theme)` | テーマ（`"light"` / `"dark"` / `"focus"`）を適用 |
| `cycleTheme()` | テーマを `light` → `dark` → `focus` の順にサイクル |

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
| `#darkModeBtn` | `click` | `cycleTheme()` |
| `#settingsBtn` | `click` | `openSettingsModal()` |
| `#closeSettingsBtn` | `click` | `closeSettingsModal()` |
| `#cancelSettingsBtn` | `click` | `closeSettingsModal()` |
| `#applySettingsBtn` | `click` | `applySettings()` |
| `#settingsModal` | `click` (モーダル背景) | `closeSettingsModal()` |

---

## style.css

CSS変数（カスタムプロパティ）によるテーマ切り替えに対応しています。

### 円形プログレスバー

`#ringWrap` の CSS変数 `--progress`（0〜100）と `--ring-color` で動的に描画されます。`timer.js` の `renderTimer()` が毎秒更新します。

### ダークモード

`[data-theme="dark"]` セレクタによる上書きで対応します。
