# Project Structure

## 概要

本ドキュメントはプロジェクトのディレクトリ構成と各モジュールの責務を定義する。

責務の分離を重視し、

- 入力
- 解析
- 演出
- ドローン制御
- シナリオ管理

を独立したモジュールとして実装する。

---

# ディレクトリ構成

```text
src/

├─ analyzers/
│
├─ controllers/
│   ├─ drone/
│   └─ keyboard/
│
├─ inputs/
│   └─ imu/
│
├─ models/
│
├─ runtime/
│
├─ scenarios/
│
├─ shows/
│   ├─ base/
│   ├─ flight/
│   └─ interaction/
│
├─ registry/
│
└─ main.py
```

---

# analyzers

## 概要

IMUデータを演出向けデータへ変換する。

---

例

```text
analyzers/

├─ analyzer.py
└─ hoop_analyzer.py
```

---

責務

```text
ImuState
 ↓
HoopState
```

変換

---

利用先

```text
Show
```

---

# controllers

## 概要

外部システム制御を担当する。

---

# controllers/drone

ドローン制御。

---

例

```text
controllers/drone/

├─ drone_controller.py
└─ tello_controller.py
```

---

責務

```text
DroneController
TelloController
```

---

# controllers/keyboard

キーボード入力処理。

---

例

```text
controllers/keyboard/

└─ keyboard_controller.py
```

---

責務

```text
Pause
Resume

NextShow
PreviousShow

Land
Emergency
```

イベント生成。

---

# inputs

## 概要

センサ入力取得を担当する。

---

# inputs/imu

BLE IMU入力。

---

例

```text
inputs/imu/

├─ input_device.py
└─ ble_imu_input.py
```

---

責務

```text
BLE通信
ImuState生成
```

---

# models

## 概要

共通データモデル。

---

例

```text
models/

├─ imu_state.py
├─ hoop_state.py
├─ drone_state.py
└─ rotation_direction.py
```

---

責務

```text
データ保持のみ
```

---

処理は持たない。

---

# runtime

## 概要

システム実行管理。

---

例

```text
runtime/

├─ scenario_runner.py
└─ application.py
```

---

責務

```text
Scenario実行

Show管理

イベント処理
```

---

# scenarios

## 概要

Scenario JSON配置場所。

---

例

```text
scenarios/

├─ demo.json
├─ duet_show.json
└─ test.json
```

---

責務

```text
Show順序定義
Transition定義
```

---

Pythonコードは置かない。

---

# shows

## 概要

演出本体を実装する。

---

# shows/base

基底クラス。

---

例

```text
shows/base/

└─ show.py
```

---

責務

```python
Show
```

定義。

---

# shows/flight

飛行演出。

---

例

```text
shows/flight/

├─ takeoff_show.py
├─ landing_show.py
├─ hover_show.py
├─ move_show.py
└─ circle_show.py
```

---

特徴

```text
センサ入力不要
```

---

# shows/interaction

外部入力と連動する演出。

---

例

```text
shows/interaction/

├─ follow_hoop_show.py
├─ mirror_yaw_show.py
└─ hoop_control_show.py
```

---

特徴

```text
Analyzer利用
```

---

# registry

## 概要

Show名とShowクラスの対応付けを管理する。

---

例

```text
registry/

└─ show_registry.py
```

---

責務

```python
registry.register(
    "follow_hoop",
    FollowHoopShow
)
```

---

```python
registry.create(
    "follow_hoop"
)
```

---

# main.py

## 概要

アプリケーション起動点。

---

責務

```text
設定読み込み

Controller生成

Analyzer生成

ScenarioRunner生成

Scenario開始
```

---

# 実行時構成

```text
main.py

 ↓

ScenarioRunner

 ↓

Show

 ↓

DroneController

 ↓

Tello
```

---

センサ系

```text
BLE IMU

 ↓

BleImuInput

 ↓

Analyzer

 ↓

HoopState

 ↓

Show
```

---

# importルール

## 許可

```text
Show
 ↓
DroneController

Show
 ↓
Analyzer

Analyzer
 ↓
Model
```

---

## 禁止

```text
DroneController
 ↓
Show
```

---

```text
Model
 ↓
Controller
```

---

```text
Show
 ↓
ScenarioRunner
```

---

```text
Show
 ↓
KeyboardController
```

---

# テスト構成

将来的に以下を追加する。

```text
tests/

├─ analyzers/
├─ controllers/
├─ runtime/
└─ shows/
```

---

# 設計目標

以下を追加する際に既存コードの修正を最小化する。

- 新しいShow
- 新しいIMU
- カメラ入力
- モーションキャプチャ
- 複数ドローン

各機能を独立したモジュールとして実装できる構造を維持する。