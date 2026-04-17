# API リファレンス

ポモドーロタイマーアプリケーションの REST API リファレンスです。

---

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | メインUI（HTML）の表示 |
| POST | `/api/timer/start-work` | 作業セッション開始 |
| POST | `/api/timer/start-break` | 休憩セッション開始 |
| GET | `/api/timer/state` | タイマーの現在状態取得 |
| POST | `/api/timer/tick` | タイマーを1秒進める |
| POST | `/api/timer/reset` | タイマーのリセット |
| GET | `/api/stats/today` | 本日の統計取得 |
| GET | `/api/stats/week` | 直近7日間の統計取得 |
| GET | `/api/stats/date/<date_str>` | 指定日の統計取得 |
| GET | `/api/config` | 現在の設定取得 |
| POST | `/api/config` | 設定の更新 |

---

## タイマー API

### タイマー状態レスポンス共通フォーマット

タイマー関連エンドポイントはすべて以下の JSON を返します。

```json
{
  "remaining": 1500,
  "status": "working",
  "state": "working",
  "completed_sessions": 0
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `remaining` | integer | 残り秒数 |
| `status` | string | タイマーの動作状態 (`idle` / `working` / `paused`) |
| `state` | string | セッションの状態 (`idle` / `working` / `break`) |
| `completed_sessions` | integer | 完了した作業セッション数 |

---

### POST /api/timer/start-work

作業セッションを開始します。

**前提条件:** セッション状態が `idle` または `break` であること。

**レスポンス:**

- **200 OK** — セッション開始成功

```json
{
  "remaining": 1500,
  "status": "working",
  "state": "working",
  "completed_sessions": 0
}
```

- **400 Bad Request** — 無効な状態遷移（すでに `working` 状態の場合）

```json
{
  "error": "無効な状態遷移"
}
```

---

### POST /api/timer/start-break

休憩セッションを開始します。完了セッション数に応じて通常休憩または長休憩が自動選択されます。

**前提条件:** セッション状態が `working` であること。

**長休憩の条件:** `completed_sessions` が `sessions_until_long_break` の倍数のとき（0を除く）。

**レスポンス:**

- **200 OK** — セッション開始成功

```json
{
  "remaining": 300,
  "status": "working",
  "state": "break",
  "completed_sessions": 1
}
```

- **400 Bad Request** — 無効な状態遷移

```json
{
  "error": "無効な状態遷移"
}
```

---

### GET /api/timer/state

タイマーの現在状態を取得します。

**レスポンス:**

- **200 OK**

```json
{
  "remaining": 1485,
  "status": "working",
  "state": "working",
  "completed_sessions": 2
}
```

---

### POST /api/timer/tick

タイマーを1秒進めます。タイマーが `working` 状態のときのみカウントダウンされます。

作業セッションが0秒になった場合、統計がリポジトリに保存されます。

**レスポンス:**

- **200 OK**

```json
{
  "remaining": 1499,
  "status": "working",
  "state": "working",
  "completed_sessions": 0
}
```

---

### POST /api/timer/reset

タイマーとセッション状態を初期化します。

**レスポンス:**

- **200 OK**

```json
{
  "remaining": 1500,
  "status": "idle",
  "state": "idle",
  "completed_sessions": 0
}
```

---

## 統計 API

### GET /api/stats/today

本日の集中統計を取得します。

**レスポンス:**

- **200 OK**

```json
{
  "sessions": 3,
  "total_focus_time": 4500,
  "total_minutes": 75,
  "total_hours": 1,
  "remaining_minutes": 15,
  "formatted_time": "1時間15分"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `sessions` | integer | 完了した作業セッション数 |
| `total_focus_time` | integer | 集中時間合計（秒） |
| `total_minutes` | integer | 集中時間合計（分） |
| `total_hours` | integer | 集中時間合計（時間単位の整数部） |
| `remaining_minutes` | integer | 時間を超えた余り分数 |
| `formatted_time` | string | 表示用文字列（例: `"1時間15分"` / `"45分"`） |

---

### GET /api/stats/week

直近7日間（本日を含む）の統計を取得します。

**レスポンス:**

- **200 OK**

```json
{
  "daily": {
    "2025-04-17": { "sessions": 3, "total_focus_time": 4500 },
    "2025-04-16": { "sessions": 2, "total_focus_time": 3000 },
    "...": {}
  },
  "total_sessions": 5,
  "total_focus_time": 7500,
  "formatted_time": "2時間5分"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `daily` | object | 日付 (`YYYY-MM-DD`) をキーとした各日の統計 |
| `total_sessions` | integer | 7日間の合計セッション数 |
| `total_focus_time` | integer | 7日間の合計集中時間（秒） |
| `formatted_time` | string | 表示用文字列 |

---

### GET /api/stats/date/<date_str>

指定日付の統計を取得します。

**パスパラメータ:**

| パラメータ | 形式 | 例 |
|-----------|------|-----|
| `date_str` | `YYYY-MM-DD` | `2025-04-17` |

**レスポンス:**

- **200 OK** — 統計取得成功（`/api/stats/today` と同じフォーマット）
- **400 Bad Request** — 日付フォーマットが不正

```json
{
  "error": "Invalid date format: invalid-date. Use YYYY-MM-DD",
  "sessions": 0,
  "total_focus_time": 0
}
```

---

## 設定 API

### GET /api/config

現在のタイマー設定を取得します。

**レスポンス:**

- **200 OK**

```json
{
  "work_duration": 1500,
  "break_duration": 300,
  "long_break_duration": 900,
  "sessions_until_long_break": 4
}
```

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `work_duration` | integer | 1500 | 作業時間（秒） |
| `break_duration` | integer | 300 | 通常休憩時間（秒） |
| `long_break_duration` | integer | 900 | 長休憩時間（秒） |
| `sessions_until_long_break` | integer | 4 | 長休憩までのセッション数 |

---

### POST /api/config

タイマー設定を更新します。バリデーションに失敗した値は無視されます（エラーにはなりません）。

**リクエストボディ（JSON）:**

```json
{
  "work_duration": 1200,
  "break_duration": 600,
  "long_break_duration": 1200,
  "sessions_until_long_break": 3
}
```

**バリデーション範囲:**

| フィールド | 最小値 | 最大値 |
|-----------|--------|--------|
| `work_duration` | 60 | 3600 |
| `break_duration` | 60 | 1800 |
| `long_break_duration` | 300 | 3600 |
| `sessions_until_long_break` | 1 | 10 |

**レスポンス:**

- **200 OK**

```json
{
  "status": "updated"
}
```
