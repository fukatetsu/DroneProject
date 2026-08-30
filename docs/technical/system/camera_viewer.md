# CameraViewer

## 概要

DroneController が提供する映像を取得し、
オペレータ向けウィンドウへ表示する。

CameraViewer は映像表示のみを担当する。

画像解析やフープ認識は担当しない。

---

# 設計方針

本プロジェクトでは映像取得元を抽象化する。

```text
CameraViewer
 ↓
DroneController
```

CameraViewer は具体的な実装を知らない。

```text
TelloController
MockDroneController
```

のどちらが渡されても動作するものとする。

---

# 対応環境

## 実機

```text
CameraViewer
 ↓
TelloController
 ↓
DJITelloPy
 ↓
Tello Camera
```

---

## Mock

```text
CameraViewer
 ↓
MockDroneController
 ↓
PC Camera
```

---

# 起動オプション

## カメラ無効

```bash
python src/main.py
```

CameraViewer は生成しない。

---

## カメラ有効

```bash
python src/main.py --camera
```

CameraViewer を生成する。

---

## Mockモード

```bash
python src/main.py --mock --camera
```

MockDroneController が生成される。

映像取得元は PC カメラとなる。

---

# 責務

## 映像表示

DroneController から取得した映像を表示する。

---

## ウィンドウ管理

表示ウィンドウの生成と破棄を行う。

---

## フレーム更新

一定周期で最新フレームを描画する。

---

# 非責務

以下は担当しない。

```text
ドローン制御

映像取得

映像ストリーム管理

画像認識

フープ認識

録画

画像保存

Scenario制御

Show制御
```

---

# データフロー

## 実機

```text
Tello Camera
 ↓
DJITelloPy
 ↓
TelloController
 ↓
CameraViewer
 ↓
Window
```

---

## Mock

```text
PC Camera
 ↓
OpenCV
 ↓
MockDroneController
 ↓
CameraViewer
 ↓
Window
```

---

# 利用者

```text
Application
```

のみ。

---

# DroneController追加インターフェース

映像取得用インターフェースを定義する。

```python
class DroneController(ABC):

    def start_video_stream(self) -> None:
        ...

    def stop_video_stream(self) -> None:
        ...

    def get_video_frame(self):
        ...
```

---

# TelloController実装

## start_video_stream()

DJITelloPy の

```python
tello.streamon()
```

を呼び出す。

---

## stop_video_stream()

DJITelloPy の

```python
tello.streamoff()
```

を呼び出す。

---

## get_video_frame()

```python
frame_read.frame
```

を返す。

戻り値

```python
numpy.ndarray
```

---

# MockDroneController実装

## start_video_stream()

PCカメラを開始する。

例

```python
cv2.VideoCapture(0)
```

---

## stop_video_stream()

PCカメラを解放する。

例

```python
capture.release()
```

---

## get_video_frame()

PCカメラから取得した最新フレームを返す。

戻り値

```python
numpy.ndarray
```

---

# CameraViewerインターフェース

```python
class CameraViewer:

    def __init__(
        self,
        drone: DroneController,
    ) -> None:
        ...

    def start(self) -> None:
        ...

    def update(self) -> None:
        ...

    def stop(self) -> None:
        ...
```

---

# start()

表示開始。

ウィンドウ生成を行う。

---

# update()

最新フレーム取得。

```python
frame = self.drone.get_video_frame()
```

取得したフレームを描画する。

---

# stop()

表示終了。

ウィンドウ破棄を行う。

---

# ライフサイクル

## 実機

```text
Application
 ↓
DroneController.connect()
 ↓
DroneController.start_video_stream()
 ↓
CameraViewer.start()
```

---

## Mock

```text
Application
 ↓
MockDroneController.connect()
 ↓
MockDroneController.start_video_stream()
 ↓
CameraViewer.start()
```

---

## 更新

```text
MainLoop
 ↓
CameraViewer.update()
```

---

## 終了

```text
CameraViewer.stop()
 ↓
DroneController.stop_video_stream()
 ↓
DroneController.disconnect()
```

---

# OpenCV表示

ウィンドウタイトル

```text
Drone Camera
```

---

# フレーム形式

```python
numpy.ndarray
```

OpenCV互換形式。

```text
Height
Width
BGR
```

---

# エラー時の動作

## フレーム取得失敗

描画をスキップする。

アプリケーションは停止しない。

---

## カメラ未接続

黒画面またはエラーメッセージを表示する。

アプリケーションは停止しない。

---

# 将来拡張

以下を追加可能。

```text
FPS表示

Battery表示

Height表示

Yaw表示

Scenario名表示

Show名表示

フープ検出結果表示

録画機能
```

---

# 責務整理

## DroneController

```text
映像取得

映像ストリーム管理
```

---

## CameraViewer

```text
映像表示

ウィンドウ管理
```

---

## Show

```text
演出制御
```

---

## ScenarioRunner

```text
シナリオ進行管理
```

CameraViewer は DroneController の抽象インターフェースのみを参照し、
実機と Mock の差異を意識しない設計とする。