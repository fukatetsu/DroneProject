# Analyzer

## 概要

Analyzer は IMU から取得した生データを演出向け情報へ変換するコンポーネントである。

Show は IMU の生データを直接扱わない。

Show は Analyzer が生成した HoopState のみを参照する。

---

# 設計方針

## 1. センサ解釈をShowから分離する

Show は以下を意識しない。

- Quaternion
- Accelerometer
- Gyroscope
- Magnetometer

Show が利用するのは HoopState のみとする。

---

## 2. IMU変更の影響を局所化する

将来的に IMU を変更した場合でも、

Show の修正を最小限にする。

---

## 3. 演出向け情報を生成する

Analyzer はセンサ値の保持を行わない。

意味付けのみを担当する。

---

# データフロー

```text
BLE IMU
 ↓
ImuState
 ↓
Analyzer
 ↓
HoopState
 ↓
Show
```

---

# Analyzer インターフェース

```python
from abc import ABC, abstractmethod


class Analyzer(ABC):

    @property
    @abstractmethod
    def state(self) -> HoopState:
        pass

    @abstractmethod
    def update(
        self,
        imu_state: ImuState
    ):
        pass
```

---

# state

## 概要

最新の解析結果を返す。

---

## 利用例

```python
hoop = analyzer.state
```

---

```python
yaw = analyzer.state.yaw
```

---

# update()

## 概要

新しい ImuState を受け取り、

HoopState を更新する。

---

## 入力

```python
ImuState
```

---

## 出力

内部状態として

```python
HoopState
```

を更新する。

---

# HoopState生成

Analyzer は ImuState を解析して HoopState を生成する。

---

例

```python
HoopState(
    roll=...,
    pitch=...,
    yaw=...,
    rotation_speed=...,
    rotation_direction=...
)
```

---

# Quaternion利用

IMU が出力する Quaternion を利用する。

Analyzer は Quaternion から姿勢角を計算する。

---

例

```python
roll
pitch
yaw
```

---

# 回転方向判定

Analyzer は回転方向を判定する。

---

出力

```python
RotationDirection.NONE

RotationDirection.CLOCKWISE

RotationDirection.COUNTER_CLOCKWISE
```

---

# 回転速度計算

Analyzer は回転速度を計算する。

---

出力

```python
rotation_speed
```

---

単位は実装時に定義する。

---

# Showから見た利用例

```python
hoop = analyzer.state

yaw = hoop.yaw

speed = hoop.rotation_speed
```

---

```python
if (
    hoop.rotation_direction
    == RotationDirection.CLOCKWISE
):
    ...
```

---

# Analyzer実装

## HoopAnalyzer

標準実装。

---

責務

- Quaternion解析
- 姿勢角計算
- 回転方向判定
- 回転速度計算

---

例

```python
class HoopAnalyzer(Analyzer):
    ...
```

---

# Analyzerが扱わないもの

以下は責務外とする。

---

ドローン制御

```python
drone.move_up(...)
```

---

Show切替

```python
runner.next_show()
```

---

Scenario管理

```python
scenario.current_show
```

---

キーボード入力

```python
keyboard.read(...)
```

---

BLE通信

```python
ble.read(...)
```

---

# 将来的な拡張

Analyzer は複数実装を許可する。

---

例

```python
HoopAnalyzer

VisionAnalyzer

MotionCaptureAnalyzer

HybridAnalyzer
```

---

Analyzer の差し替えによって

Show を変更せずに入力手法を変更できる。

---

# 設計目標

Show が以下だけを意識すれば良い状態を目指す。

```python
hoop = analyzer.state

yaw = hoop.yaw

rotation = hoop.rotation_direction
```

Quaternion や IMU の詳細は Analyzer に隠蔽する。