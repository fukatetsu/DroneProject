# KeyboardController 拡張設計書

## 1. 概要

既存の KeyboardController を拡張し、Show 実行中にオペレータがキーボードから個別の操作を行えるようにする。

従来の Scenario 制御用コマンドに加え、各 Show が独自のキーイベントを定義・処理できる仕組みを追加する。

例えば、ある Show では矢印キーによってドローンを移動させ、別の Show では同じ矢印キーによって異なる演出を実行できるようにする。

キー入力後に Enter キーを押す必要はなく、キー入力を即座に検出すること。

## 2. 基本方針

- 既存の KeyboardController の実装を拡張する。
- 既存の KeyboardCommand による Scenario 制御は維持する。
- キー入力に対する個別のイベントを各 Show が定義できるようにする。
- 同じキーでも、実行中の Show によって異なる処理を割り当てられるようにする。
- Show はキーボード入力そのものを直接取得しない。
- キー入力後に Enter キーを要求しない。
- KeyboardController は入力取得とイベント通知を担当する。
- ScenarioRunner は Scenario 制御と、入力イベントの振り分けを担当する。
- Show は自身に割り当てられたイベントの処理を担当する。

## 3. 既存実装からの変更点

### 3.1 既存の KeyboardCommand

既存の KeyboardCommand は Scenario 全体の制御に使用する。

以下のコマンドは引き続き利用可能とする。

```python
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

これらは従来どおり ScenarioRunner が処理する。

### 3.2 Show 個別のキーイベント

新たに、Show 個別のキーイベントを追加する。

Show は使用するキーと、それに対応する処理を個別に定義できるものとする。

例えば、以下のような定義を可能にする。

```python
class ExampleShow(Show):

    def __init__(self):
        self.key_events = {
            "UP": self.move_forward,
            "DOWN": self.move_backward,
            "LEFT": self.rotate_left,
            "RIGHT": self.rotate_right,
        }

    async def move_forward(self):
        ...

    async def move_backward(self):
        ...

    async def rotate_left(self):
        ...

    async def rotate_right(self):
        ...
```

上記は設計例であり、実際の実装方法は既存の Show 基底クラスやイベント管理方式に合わせること。

別の Show では、同じキーに異なるイベントを割り当てられるようにする。

## 4. キー入力の取得

KeyboardController は、Enter キーを必要とせず、キー入力を即座に検出する。

従来の Scenario 制御用コマンドと Show 個別のキー入力を区別できるようにする。

入力の流れ：

```text
Keyboard
    ↓
KeyboardController
    ↓
キー入力の判定
    ├── Scenario制御コマンド
    │       ↓
    │   KeyboardCommand
    │       ↓
    │   ScenarioRunner
    │
    └── Show個別のキー入力
            ↓
        キーイベント
            ↓
        ScenarioRunner
```

キー入力の取得には、Enter キーによる確定を必要としない方式を採用する。

また、キーを押し続けた場合の連続入力や、キーリピートの扱いについても実装時に考慮すること。

## 5. ScenarioRunner の拡張

ScenarioRunner は、従来の KeyboardCommand の処理に加え、Show 個別のキーイベントを振り分ける。

Show 個別のキー入力を受け取った場合、現在実行中の Show に対して入力されたキーを通知する。

```text
KeyboardController
        ↓
ScenarioRunner
        ↓
現在の Show
        ↓
対応するイベントを実行
```

イベントの振り分け先は、現在実行中の Show のみとする。

Show の切り替え時には、イベントの振り分け先も新しい Show に切り替えること。

Show が登録していないキー入力については、何も実行しない。

## 6. Show 基底クラスの拡張

Show 基底クラスに、個別のキーイベントを定義・処理する仕組みを追加する。

各 Show は必要に応じてキーイベントを登録できるようにする。

例えば、以下のようなインターフェースを想定する。

```python
class Show:

    def __init__(self):
        self.key_events = {}

    async def handle_key(self, key: str) -> None:
        event = self.key_events.get(key)

        if event is not None:
            await event()
```

上記は概念例であり、既存の Show 基底クラスの構造に合わせて実装すること。

### Show 側の利用例

```python
class ExampleShow(Show):

    def __init__(self):
        super().__init__()

        self.key_events = {
            "UP": self.move_forward,
            "DOWN": self.move_backward,
        }

    async def move_forward(self):
        # このShow独自の処理
        ...

    async def move_backward(self):
        # このShow独自の処理
        ...
```

別の Show では、同じ UP キーに別の処理を登録できる。

Show はキーボードや KeyboardController を直接参照せず、ScenarioRunner から通知されたキーイベントを処理する。

## 7. 既存の安全制御との関係

既存の安全制御は変更しない。

以下のコマンドは従来どおり ScenarioRunner が受け取り、現在の Show に対して処理を要求する。

- LAND
- EMERGENCY

Show の個別イベントと安全制御用コマンドは区別すること。

Show 個別のイベントによって、安全制御用コマンドの処理が妨げられないようにする。

## 8. 責務の整理

| クラス | 責務 |
|---|---|
| KeyboardController | キー入力の取得、入力内容の判定、イベント通知 |
| ScenarioRunner | Scenario制御、現在のShowへのキーイベント振り分け、安全制御 |
| Show | 演出、Show固有のキーイベント定義・処理 |

## 9. 既存実装との互換性

今回の変更は、既存の KeyboardController を拡張する形で実装する。

以下の既存機能は維持すること。

- Pause / Resume
- Next Show / Previous Show
- Restart Show
- Jump To Show
- Land
- Emergency

既存の ScenarioRunner と Show の構造を可能な限り維持し、必要な部分のみを変更する。

## 10. 実装時の注意事項

- キー入力は Enter キーなしで検出すること。
- キー入力の取得処理と Show 固有の処理を分離すること。
- 同じキーに対して Show ごとに異なるイベントを登録できること。
- Show の切り替え後に、前の Show のイベントが実行されないこと。
- キーイベントが非同期処理に対応できること。
- 登録されていないキーが入力されてもエラーにならないこと。
- 既存の Scenario 制御用 KeyboardCommand と Show 個別のキーイベントが競合しないこと。
- 既存コードの構造を確認してから拡張し、不必要な大規模リファクタリングは行わないこと。