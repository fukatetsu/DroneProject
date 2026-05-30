# Drone Controller

## 概要

DroneController はシステム内で唯一のドローン制御インターフェースである。

すべての Show は DroneController を通してドローンを操作する。

Show は DJITelloPy を直接利用してはならない。

---

# 設計方針

## 1. ドローン制御を一元管理する

以下は必ず DroneController を経由する。

- 離陸
- 着陸
- 移動
- 回転
- RC制御
- 状態取得

---

## 2. DJITelloPy を隠蔽しない

本システムは DJI Tello 専用である。

そのため DJITelloPy の API に近いインターフェースを採用する。

利用者が DJITelloPy のドキュメントをそのまま参照できることを重視する。

---

## 3. 状態監視を内包する

DroneController は内部で DroneState を管理する。

Show は DroneState を直接取得できる。

```python
yaw = drone.state.yaw
```

---

## 4. コマンド競合を防止する

Move系コマンド実行中は RC制御を送信しない。

DroneController がコマンド状態を管理する。

---

# DroneController インターフェース

```python
from abc import ABC, abstractmethod


class DroneController(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def takeoff(self):
        pass

    @abstractmethod
    async def land(self):
        pass

    @abstractmethod
    async def emergency(self):
        pass

    @abstractmethod
    async def move_up(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def move_down(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def move_left(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def move_right(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def move_forward(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def move_back(
        self,
        distance: int
    ):
        pass

    @abstractmethod
    async def rotate_clockwise(
        self,
        angle: int
    ):
        pass

    @abstractmethod
    async def rotate_counter_clockwise(
        self,
        angle: int
    ):
        pass

    @abstractmethod
    async def go_xyz_speed(
        self,
        x: int,
        y: int,
        z: int,
        speed: int
    ):
        pass

    @abstractmethod
    def send_rc_control(
        self,
        left_right: int,
        forward_back: int,
        up_down: int,
        yaw: int
    ):
        pass

    @property
    @abstractmethod
    def state(self) -> DroneState:
        pass
```

---

# TelloController

## 概要

DroneController の標準実装。

内部で DJITelloPy を利用する。

---

## 実装

```python
class TelloController(
    DroneController
):
    ...
```

---

# DJITelloPy 対応表

| DroneController | DJITelloPy |
|---------------|------------|
| connect | tello.connect |
| takeoff | tello.takeoff |
| land | tello.land |
| emergency | tello.emergency |
| move_up | tello.move_up |
| move_down | tello.move_down |
| move_left | tello.move_left |
| move_right | tello.move_right |
| move_forward | tello.move_forward |
| move_back | tello.move_back |
| rotate_clockwise | tello.rotate_clockwise |
| rotate_counter_clockwise | tello.rotate_counter_clockwise |
| go_xyz_speed | tello.go_xyz_speed |
| send_rc_control | tello.send_rc_control |

---

# DroneState管理

## 概要

DroneController は内部で DroneState を保持する。

---

## 更新方法

内部監視タスクで定期更新する。

```text
Tello
 ↓
State Monitor
 ↓
DroneState更新
```

---

## 利用例

```python
battery = drone.state.battery
```

---

```python
yaw = drone.state.yaw
```

---

```python
height = drone.state.height
```

---

# 状態監視タスク

## 概要

接続時に開始する。

---

## 処理内容

定期的に以下を取得する。

- Battery
- Height
- Roll
- Pitch
- Yaw
- Velocity

---

## 更新周期

実装時に決定する。

推奨値

```python
0.05
```

秒程度。

---

# コマンド実行制御

## 概要

Move系コマンド実行中は RC制御を送信しない。

---

## 理由

Tello は Move系コマンドと RC制御の混在に弱い。

意図しない挙動を防止する。

---

# Command Lock

DroneController は内部に Command Lock を持つ。

---

## Move系コマンド

```python
async with command_lock:

    tello.move_up(...)
```

---

```python
async with command_lock:

    tello.move_forward(...)
```

---

## RC制御

```python
if command_lock.locked():
    return
```

---

RC制御は無視する。

---

# Showからの利用例

## 離陸

```python
await drone.takeoff()
```

---

## 上昇

```python
await drone.move_up(50)
```

---

## 回転

```python
await drone.rotate_clockwise(90)
```

---

## RC制御

```python
drone.send_rc_control(
    0,
    30,
    0,
    0
)
```

---

# 例外処理

DJITelloPy が例外を送出した場合、

DroneController は例外をそのまま上位へ伝播する。

最終的な処理は ScenarioRunner が担当する。

---

# DroneControllerが扱わないもの

以下は責務外とする。

---

Show切替

```python
runner.next_show()
```

---

Scenario管理

```python
scenario.current
```

---

IMU入力

```python
imu.state
```

---

キーボード入力

```python
keyboard.read()
```

---

# 将来的な拡張

以下の実装追加を想定する。

```python
MockDroneController
```

テスト用。

---

```python
MultiDroneController
```

複数機制御用。

---

```python
LoggingDroneController
```

ログ取得用。

---

既存 Show を変更せずに差し替えられる構造を維持する。