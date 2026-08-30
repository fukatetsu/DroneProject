# Architecture

## 概要

本システムは DJI Tello を利用したドローン演出制作・研究のためのフレームワークである。

主な目的は以下である。

- ドローン演目の制作
- フープなどの外部道具とドローンの連動
- 自律飛行演出の実装
- 演目の再利用
- 演目進行の管理
- 研究用ログ取得

本システムは DJI Tello を対象とし、DJITelloPy ライブラリを利用して実装する。

---

# 設計方針

本システムは以下の原則に従う。

## 1. 演出ロジックとシステム制御を分離する

演出内容は Show が担当する。

シナリオ進行は ScenarioRunner が担当する。

ドローン制御は DroneController が担当する。

各責務を明確に分離し、独立して開発可能な構造とする。

---

## 2. 演目は再利用可能にする

演目は Show クラスとして実装する。

例：

- TakeoffShow
- FollowHoopShow
- CircleShow
- LandingShow

同一 Show を複数の Scenario で再利用できるようにする。

---

## 3. 演目順序は JSON で管理する

Show の実装は Python に記述する。

演目の順序や切り替え条件は JSON に記述する。

これによりプログラムを変更せずに演目構成を変更できる。

---

## 4. 外部入力を拡張可能にする

現在利用する入力デバイス

- BLE IMU

将来的に追加する可能性のある入力デバイス

- ドローンカメラ
- 外部カメラ
- モーションキャプチャ
- OSC
- MIDI
- その他センサ

追加時に既存 Show を大きく変更しなくてよい構造とする。

---

## 5. オペレータによる介入を常に可能にする

演目実行中であってもオペレータはキーボードから介入できる。

例：

- Pause
- Resume
- Next Show
- Previous Show
- Restart Show
- Jump To Show
- Land
- Emergency

安全確保を優先する。

---

# システム構成

## 全体構成

```text
BLE IMU
    ↓
InputDevice
    ↓
ImuState
    ↓
Analyzer
    ↓
HoopState
    ↓
Show
    ↓
DroneController
    ↓
DJITelloPy
    ↓
Tello


KeyboardController
    ↓
ScenarioRunner
    ↓
Show管理
```

---

# コンポーネント構成

## InputDevice

責務

- BLE通信
- IMUデータ取得
- ImuState生成

出力

```text
ImuState
```

---

## Analyzer

責務

- ImuState解析
- 演出向け状態生成

入力

```text
ImuState
```

出力

```text
HoopState
```

---

## Show

責務

- 演出ロジック実装
- ドローン動作決定

入力

```text
HoopState
DroneState
```

出力

```text
DroneController API 呼び出し
```

例

```text
FollowHoopShow
CircleShow
TakeoffShow
LandingShow
```

---

## DroneController

責務

- Tello制御
- DroneState取得
- コマンド管理

出力

```text
Tello Command
```

実装

```text
TelloController
```

---

## ScenarioRunner

責務

- Scenario実行
- Show切り替え
- 演目進行管理
- オペレータコマンド処理

---

## KeyboardController

責務

- キーボード監視
- オペレータコマンド生成

対象コマンド

```text
Pause
Resume

NextShow
PreviousShow

RestartShow
JumpToShow

Land
Emergency
```

---

# データフロー

```text
IMU
 ↓
ImuState
 ↓
Analyzer
 ↓
HoopState
 ↓
Show
 ↓
DroneController
 ↓
Tello
```

---

# Scenario実行フロー

```text
ScenarioRunner

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

# Showライフサイクル

すべての Show は以下のライフサイクルを持つ。

```text
start()

↓
run()

↓
stop()
```

---

## start()

演目開始時に一度だけ呼ばれる。

用途例

- 初期化
- 変数リセット
- ドローン準備

---

## run()

演目本体。

Show ごとの演出を実装する。

---

## stop()

演目終了時に一度だけ呼ばれる。

用途例

- RC停止
- 状態初期化
- リソース解放

---

# DroneController設計方針

DroneController はシステム内唯一のドローン制御窓口とする。

Show は DJITelloPy を直接呼び出してはならない。

必ず DroneController を経由する。

---

# DroneState管理

DroneController は内部で状態監視タスクを保持する。

定期的に Tello 状態を取得し DroneState を更新する。

利用側は以下のように参照する。

```python
drone_state = drone.state
```

---

# コマンド実行制御

Move系コマンド実行中は RC制御を送信しない。

DroneController は内部に Command Lock を持つ。

```text
Move Command
    ↓
Command Lock取得
    ↓
実行

RC Command
    ↓
Lock中なら送信しない
```

これにより Tello への競合コマンド送信を防止する。

---

# 今後の拡張

将来的に以下を追加できる設計とする。

- カメラ画像利用
- コンピュータビジョン
- モーションキャプチャ
- OSC入力
- MIDI入力
- 複数ドローン制御
- 外部演出システム連携

既存 Show の修正を最小限に抑えることを目標とする。