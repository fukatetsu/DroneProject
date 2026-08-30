# Show

## 概要

Show は本システムにおける演出の最小実行単位である。

すべての演出は Show として実装する。

例：

- TakeoffShow
- LandingShow
- CircleShow
- FollowHoopShow

Scenario は Show の並びによって構成される。

---

# 設計方針

## 1. Showは演出のみを担当する

Show は演出ロジックのみを担当する。

以下は Show の責務ではない。

- Scenario管理
- Show切り替え
- キーボード操作
- BLE通信
- Tello通信実装

これらはそれぞれ専用コンポーネントが担当する。

---

## 2. Showは再利用可能であること

Show は単独で実行できること。

複数の Scenario から再利用できること。

---

## 3. Show同士は依存しない

以下のような構造は禁止する。

```python
class ShowA:
    ...

class ShowB:

    async def run(self):
        await ShowA().run()
```

Show の組み合わせは Scenario が管理する。

---

## 4. ShowはDroneController経由でドローンを操作する

Show は DJITelloPy を直接利用してはならない。

必ず DroneController を利用する。

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

# Show インターフェース

```python
from abc import ABC, abstractmethod


class Show(ABC):

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def run(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
```

---

# start()

## 概要

Show開始時に1回だけ呼ばれる。

---

## 用途

- 初期化
- 状態リセット
- ログ出力
- 開始演出

---

## 例

```python
async def start(self):

    self.start_time = time.time()
```

---

# run()

## 概要

Show本体。

演出内容を実装する。

---

## 用途

- ドローン制御
- HoopState監視
- DroneState監視
- 演出実行

---

## 例

```python
async def run(self):

    while True:

        hoop = self.analyzer.state

        self.drone.send_rc_control(
            ...
        )

        await asyncio.sleep(0.02)
```

---

## 終了条件

Showごとに自由に定義する。

例：

```python
return
```

---

```python
while self.running:
    ...
```

---

```python
await asyncio.sleep(10)
```

---

# stop()

## 概要

Show終了時に1回だけ呼ばれる。

---

## 用途

- RC停止
- 状態初期化
- ログ出力
- リソース解放

---

## 例

```python
async def stop(self):

    self.drone.send_rc_control(
        0,
        0,
        0,
        0
    )
```

---

# Showが利用できる情報

## HoopState

Analyzer経由で取得する。

```python
hoop = analyzer.state
```

---

利用例

```python
yaw = hoop.yaw
```

---

```python
rotation = hoop.rotation_direction
```

---

## DroneState

DroneController経由で取得する。

```python
drone_state = drone.state
```

---

利用例

```python
battery = drone_state.battery
```

---

```python
yaw = drone_state.yaw
```

---

# Showが利用できる機能

## Move系

```python
await drone.takeoff()

await drone.land()

await drone.move_up(x)

await drone.move_down(x)

await drone.move_left(x)

await drone.move_right(x)

await drone.move_forward(x)

await drone.move_back(x)

await drone.rotate_clockwise(x)

await drone.rotate_counter_clockwise(x)

await drone.go_xyz_speed(...)
```

---

## RC制御

```python
drone.send_rc_control(
    lr,
    fb,
    ud,
    yaw
)
```

---

# Showの種類

## Flight Show

移動演出。

例：

- TakeoffShow
- LandingShow
- CircleShow
- HoverShow

---

## Interaction Show

外部入力と連動する演出。

例：

- FollowHoopShow
- MirrorYawShow
- HoopControlShow

---

# Show生成

Show は実行時に毎回新規生成する。

---

例

```python
show = FollowHoopShow(...)
```

---

以下は禁止する。

```python
show = registry["follow_hoop"]
```

インスタンス使い回しは禁止。

---

# Show Registry

Scenario は Show 名のみを保持する。

実際の生成は Registry が行う。

---

例

```python
registry.register(
    "follow_hoop",
    FollowHoopShow
)
```

---

```python
show = registry.create(
    "follow_hoop"
)
```

---

# Showの実装ルール

## 許可

```python
hoop = analyzer.state

yaw = drone.state.yaw

await drone.move_up(50)

drone.send_rc_control(...)
```

---

## 禁止

DJITelloPy直接利用

```python
tello.move_up(50)
```

---

Scenario操作

```python
runner.next_show()
```

---

Keyboard監視

```python
keyboard.is_pressed(...)
```

---

BLE通信

```python
ble.read(...)
```

---

# エラーハンドリング

Show内部で例外が発生した場合、

例外は ScenarioRunner へ伝播する。

ScenarioRunner が最終処理を担当する。

---

# 将来的な拡張

以下のShow追加を想定する。

- MoveToPositionShow
- SpiralShow
- FigureEightShow
- FollowHoopShow
- MirrorYawShow
- CameraTrackingShow
- VisionFollowShow

既存Showを変更せず追加できる構造を維持する。