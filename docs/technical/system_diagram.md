# システム図（実機：DJI Tello を使用）

以下は本プロジェクトを実機ドローン（DJI Tello）で運用する場合のシステム図です。
Mock 系のコンポーネントは含めていません。

## 概要

- 入力: BLE IMU、キーボード（オペレータ）、外部カメラ（任意）
- センシング→解析→演出→ドローン制御 の流れで構成
- DroneController は `TelloController` を想定し、内部で `DJITelloPy` を利用する

---

## 図（Mermaid）

```mermaid
flowchart LR
  subgraph Inputs
    IMU["BLE IMU"]
    Keyboard["Keyboard (Operator)"]
    Cam["External Camera (optional)"]
  end

  IMU --> InputDevice["InputDevice\n(UdpImuInput / BleImuInput)"]
  InputDevice --> ImuState["ImuState"]
  ImuState --> Analyzer["Analyzer\n(HoopAnalyzer)"]
  Analyzer --> HoopState["HoopState"]

  Keyboard --> KeyboardController["KeyboardController"]
  Cam --> CameraProcessing["Camera Processing (optional)"]
  CameraProcessing --> Show

  subgraph Runtime
    ScenarioRunner["ScenarioRunner"]
    Registry["Show Registry"]
    Show["Show\n(Takeoff/FollowHoop/Circle/...)"]
    Output["Media Output\n(CameraViewer)"]
  end

  HoopState --> Show
  Show --> DroneController["DroneController\n(TelloController)"]
  DroneController --> DJITelloPy["DJITelloPy\n(Tello API)"]
  DJITelloPy --> Tello["Tello (Physical Drone)"]

  Show --> Output

  %% State and control relationships
  DroneController -->|provides| DroneState["DroneState\n(battery, height, yaw, etc.)"]
  DroneController -->|command| DJITelloPy
  DroneState --> Show

  %% Operator controls
  KeyboardController -->|operator events| ScenarioRunner
  ScenarioRunner -->|creates| Show
  Registry -->|factory| Show

  %% Notes
  classDef note fill:#fff7c2,stroke:#e6c200;
  class DroneController note
  
```

---

## コンポーネント説明（簡易）

- InputDevice: BLE経由のIMUを受け取り `ImuState` を生成する。例: `src/inputs/imu/udp_imu_input.py`。
- Analyzer: `ImuState` を解析して `HoopState` を生成する。例: `src/analyzers/hoop_analyzer.py`。
- Show: 演出ロジック。`DroneController` を通じてドローンを制御する（直接 DJITelloPy を呼ばない）。例: `src/shows/*`。
- DroneController (TelloController): `DJITelloPy` を内包し、接続・状態監視・コマンド排他（Command Lock）を扱う。例: `src/controllers/drone/tello_controller.py`。
- DJITelloPy: 実機Telloとの橋渡しを行うライブラリ（外部依存）。
- ScenarioRunner: シナリオ管理・Show 切替・オペレータコマンド処理を担当。例: `src/runtime/scenario_runner.py`。
- Registry: Show 名からインスタンスを生成するファクトリ（`src/registry/show_registry.py`）。
- CameraViewer / Media Output: Show の可視化出力（オプション）。

---

## 備考

- 本図は実機運用を前提とし、Mock 系 (`MockDroneController`) は含めていません。
- 実運用時は `TelloController` の接続や例外（接続障害、タイムアウト等）を ScenarioRunner 側で適切に扱ってください。
- ファイル: [docs/system_diagram.md](docs/system_diagram.md)
