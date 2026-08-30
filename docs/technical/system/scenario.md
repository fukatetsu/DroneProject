# Scenario

## 概要

Scenario は演目全体の進行を定義する。

Show の実装内容は Python に記述し、

Scenario は

- Show の順番
- Show の切り替え条件

のみを管理する。

演出ロジックは保持しない。

---

# 設計方針

## 1. 演出と進行を分離する

Show

```text
何をするか
```

を担当する。

---

Scenario

```text
いつ実行するか
どの順番で実行するか
```

を担当する。

---

## 2. ShowはPythonで実装する

Scenario は Show 名のみを保持する。

---

例

```json
{
  "show": "follow_hoop"
}
```

---

## 3. ScenarioはJSONで記述する

演目順序変更時に

Pythonコードの修正を不要にする。

---

# JSON仕様

## 基本構造

```json
{
  "shows": [
    {
      "id": "takeoff",

      "comment": "離陸",

      "show": "takeoff",

      "transition": {
        "type": "auto"
      }
    }
  ]
}
```

---

# Show定義

## id

Scenario 内で一意となる識別子。

---

例

```json
{
  "id": "intro_follow"
}
```

---

用途

- ログ出力
- デバッグ
- JumpToShow

---

## comment

人間向け説明。

実行には使用しない。

---

例

```json
{
  "comment": "フープ追従パート"
}
```

---

## show

実行する Show 名。

ShowRegistry に登録された名前を指定する。

---

例

```json
{
  "show": "follow_hoop"
}
```

---

# Transition

## 概要

現在の Show から次の Show へ移行する条件。

---

## auto

Show.run() 終了時に自動遷移する。

---

例

```json
{
  "transition": {
    "type": "auto"
  }
}
```

---

用途

- 離陸
- 着陸
- 単発移動

---

## manual

オペレータが切り替えるまで継続する。

---

例

```json
{
  "transition": {
    "type": "manual"
  }
}
```

---

用途

- フープ追従
- 即興演技
- インタラクティブ演出

---

## duration

指定秒数後に自動遷移する。

---

例

```json
{
  "transition": {
    "type": "duration",
    "seconds": 30
  }
}
```

---

用途

- オープニング
- 一定時間演出

---

# Scenario例

```json
{
  "shows": [
    {
      "id": "takeoff",

      "comment": "離陸",

      "show": "takeoff",

      "transition": {
        "type": "auto"
      }
    },

    {
      "id": "follow",

      "comment": "フープ追従",

      "show": "follow_hoop",

      "transition": {
        "type": "manual"
      }
    },

    {
      "id": "circle",

      "comment": "円運動",

      "show": "circle",

      "transition": {
        "type": "duration",
        "seconds": 20
      }
    },

    {
      "id": "landing",

      "comment": "着陸",

      "show": "landing",

      "transition": {
        "type": "auto"
      }
    }
  ]
}
```

---

# ScenarioRunner

## 概要

Scenario を実行するランタイムコンポーネント。

---

責務

- Show生成
- Show開始
- Show終了
- Transition判定
- オペレータ操作処理

---

# 実行フロー

```text
Scenario読み込み

↓
Show生成

↓
Show.start()

↓
Show.run()

↓
Transition判定

↓
Show.stop()

↓
次のShow
```

---

# Show生成

Show は毎回新規生成する。

---

例

```python
show = registry.create(
    "follow_hoop"
)
```

---

インスタンス使い回しは禁止する。

---

# ScenarioRunnerコマンド

## Start

Scenario開始。

---

## Stop

Scenario停止。

現在の Show を終了する。

ドローン着陸は行わない。

---

## Pause

Scenario一時停止。

---

## Resume

Pause解除。

---

## NextShow

次の Show へ移動する。

---

## PreviousShow

前の Show へ移動する。

---

## RestartShow

現在の Show を最初から実行する。

---

## JumpToShow

指定した Show へ移動する。

対象は id を利用する。

---

例

```python
runner.jump_to_show(
    "follow"
)
```

---

## Land

ドローンを着陸させる。

Scenario は停止しない。

---

## Emergency

緊急停止。

DJI Tello の emergency コマンドを実行する。

---

# Pause仕様

Pause 中は Show の更新を停止する。

---

Pause解除後に再開する。

---

Pause は

```text
演目停止
```

であり、

```text
着陸
```

ではない。

---

# Scenario終了

最後の Show が終了した場合、

ScenarioRunner は停止状態へ移行する。

---

自動ループは行わない。

---

# ShowRegistry

## 概要

Show 名と Show クラスを対応付ける。

---

例

```python
registry.register(
    "takeoff",
    TakeoffShow
)
```

---

```python
registry.register(
    "follow_hoop",
    FollowHoopShow
)
```

---

Scenario は Registry を介して Show を生成する。

---

# エラーハンドリング

Show 内で例外が発生した場合、

ScenarioRunner が例外を受け取る。

---

対応は実装時に決定する。

候補

- Scenario停止
- Land実行
- Emergency実行

---

# 将来的な拡張

必要になった場合のみ追加する。

- Scenario Loop
- Branch
- Condition
- Parallel Show
- External Trigger

現時点では実装しない。