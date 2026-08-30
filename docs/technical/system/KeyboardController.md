# KeyboardController

## 概要

オペレータによるキーボード入力を監視し、
ScenarioRunner へ操作イベントを通知する。

KeyboardController は入力の取得のみを担当し、
Scenario の進行制御は ScenarioRunner が担当する。

Show はキーボード入力を直接参照しない。

---

# 責務

## キー入力監視

オペレータのキーボード入力を取得する。

例:

- Pause
- Resume
- Next Show
- Previous Show
- Restart Show
- Land
- Emergency

---

## イベント通知

入力内容を KeyboardCommand に変換し、
ScenarioRunner へ通知する。

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

# 利用者

```text
ScenarioRunner
```

のみ。

Show から参照してはならない。

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

    JUMP_TO_SHOW = "jump_to_show"

    LAND = "land"

    EMERGENCY = "emergency"
```

---

# 制御可能な内容

## Scenario制御

ScenarioRunner が担当する。

### Pause

現在の Show を一時停止する。

```text
Show.run()
 ↓
Pause
 ↓
停止状態
```

---

### Resume

Pause 状態から再開する。

---

### Next Show

現在の Show を終了し、
次の Show へ遷移する。

---

### Previous Show

現在の Show を終了し、
前の Show へ遷移する。

---

### Restart Show

現在の Show を終了し、
同じ Show を最初から実行する。

---

### Jump To Show

指定された Show へ遷移する。

主にデバッグ用途で利用する。

---

## 安全制御

安全制御は Show に委譲する。

ScenarioRunner は現在実行中の Show に対して
安全操作を要求する。

---

### Land

現在実行中の Show の

```python
await show.land()
```

を呼び出す。

目的:

- 安全着陸
- 演出を中断して着陸

---

### Emergency

現在実行中の Show の

```python
await show.emergency()
```

を呼び出す。

目的:

- 緊急停止
- モーター停止

---

# Showとの関係

Show はキーボードを参照しない。

以下は禁止する。

```python
if keyboard.is_pressed(...):
```

```python
keyboard_controller.get_command()
```

```python
keyboard_controller.is_paused()
```

Show は演出のみを担当する。

進行管理は ScenarioRunner が担当する。

---

# Show基底クラス要件

全ての Show は共通の安全操作を持つ。

```python
class Show:

    async def start(self) -> None:
        pass

    async def run(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def land(self) -> None:
        pass

    async def emergency(self) -> None:
        pass
```

---

# land()

安全着陸を行う。

デフォルト実装:

```python
async def land(self) -> None:
    await self.drone.land()
```

必要に応じて Show 側でオーバーライド可能。

例:

```python
async def land(self) -> None:

    self.drone.send_rc_control(
        0,
        0,
        0,
        0,
    )

    await self.drone.land()
```

---

# emergency()

緊急停止を行う。

デフォルト実装:

```python
async def emergency(self) -> None:
    await self.drone.emergency()
```

必要に応じて Show 側でオーバーライド可能。

---

# 設計方針

KeyboardController は

```text
入力取得
```

のみ担当する。

ScenarioRunner は

```text
Scenario進行管理
安全制御
```

を担当する。

Show は

```text
演出
```

のみ担当する。

責務を明確に分離し、
Show がキーボード入力に依存しない設計とする。