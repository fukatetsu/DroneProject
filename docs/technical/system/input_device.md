# Input Device

## 概要

InputDevice は外部入力デバイスを扱うためのコンポーネントである。

本システムでは以下の入力を扱う。

- BLE IMU
- Keyboard

将来的には以下の入力追加を想定する。

- Drone Camera
- External Camera
- Motion Capture
- OSC
- MIDI

InputDevice は入力取得のみを担当する。

取得したデータの解釈は行わない。

---

# 設計方針

## 1. 入力取得と解析を分離する

InputDevice

```text
データ取得
```

のみ担当する。

Analyzer

```text
データ解釈
```

を担当する。

---

## 2. Showは入力デバイスを直接参照しない

Show は InputDevice を直接利用しない。

必ず

```text
InputDevice
 ↓
Analyzer
 ↓
HoopState
 ↓
Show
```

の流れを通す。

---

## 3. キーボードはScenarioRunner専用

キーボード入力は演出制御用である。

Show はキーボードを監視しない。

---

# InputDevice インターフェース

```python
from abc import ABC, abstractmethod


class InputDevice(ABC):

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
```

---

# BLE IMU

## 概要

フープに取り付けられた IMU からデータを取得する。

通信方式は BLE を利用する。

---

# BleImuInput

```python
class BleImuInput(
    InputDevice
):
    ...
```

---

# 責務

- BLE接続
- BLE切断
- IMUデータ受信
- ImuState生成

---

# 出力

```python
ImuState
```

---

# データフロー

```text
BLE IMU
 ↓
BleImuInput
 ↓
ImuState
 ↓
Analyzer
```

---

# 利用例

```python
imu_state = imu_input.state
```

---

# BleImuInputが行わないこと

以下は責務外。

---

姿勢推定

```python
roll
pitch
yaw
```

---

回転方向判定

```python
CLOCKWISE
```

---

演出制御

```python
drone.move_up(...)
```

---

# KeyboardController

## 概要

オペレータ操作を管理する。

---

# 責務

- キー入力監視
- ScenarioRunnerへのイベント通知

---

# 利用者

```text
ScenarioRunner
```

のみ。

---

# KeyboardCommand

```python
from enum import Enum


class KeyboardCommand(Enum):

    PAUSE = "pause"

    RESUME = "resume"

    NEXT_SHOW = "next_show"

    PREVIOUS_SHOW = "previous_show"

    RESTART_SHOW = "restart_show"

    LAND = "land"

    EMERGENCY = "emergency"
```

---

# データフロー

```text
Keyboard
 ↓
KeyboardController
 ↓
KeyboardCommand
 ↓
ScenarioRunner
```

---

# キーボードが制御できる内容

## Scenario制御

```text
Pause
Resume

Next Show
Previous Show

Restart Show
Jump To Show
```

---

## 安全制御

```text
Land

Emergency
```

---

# Showとの関係

Show はキーボードを参照しない。

以下は禁止する。

```python
if keyboard.is_pressed(...):
```

Show の進行は ScenarioRunner が管理する。

---

# Camera Input

## 概要

将来的な拡張。

現時点では実装しない。

---

候補

```python
DroneCameraInput

ExternalCameraInput
```

---

用途

```text
物体追跡

人物追跡

画像認識

ビジョンベース制御
```

---

# Motion Capture Input

## 概要

将来的な拡張。

現時点では実装しない。

---

候補

```python
MotionCaptureInput
```

---

用途

```text
位置取得

姿勢取得

演者追跡
```

---

# OSC Input

## 概要

将来的な拡張。

現時点では実装しない。

---

用途

```text
TouchDesigner

Unity

Max/MSP

Ableton Live
```

との連携。

---

# 設計目標

新しい入力デバイス追加時に、

- Show
- Scenario
- DroneController

を変更せずに拡張できる構造を維持する。