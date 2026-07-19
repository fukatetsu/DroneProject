# MediaController

## 概要

MediaController は Show が利用する演出制御コンポーネントである。

MediaController は以下のメディアを統一的に管理する。

- ドローンカメラ
- 静止画
- 動画
- BGM
- 効果音(SE)

Show は MediaController を利用して演出を行い、映像ライブラリや音声ライブラリを直接利用しない。

---

# 設計目的

Show は演出内容のみを記述できることを目的とする。

例

```python
await self.media.enable_camera()

self.media.show_image("title.png")

self.media.play_video("opening.mp4")

self.media.play_bgm("opening.mp3", loop=True)

self.media.play_se("flap.wav")

self.media.show_camera()
```

MediaController が

- CameraViewer
- OpenCV
- pygame
- VLC
- ffmpeg

などの実装を隠蔽する。

---

# 責務

MediaController は以下を担当する。

- ドローンカメラ管理
- ドローン映像表示
- 静止画表示
- 動画再生
- BGM再生
- SE再生
- 表示モード切替
- ウィンドウ管理
- 音量管理
- メディア終了通知

---

# 非責務

以下は担当しない。

- ドローン制御
- Scenario制御
- Show制御
- 画像認識
- 映像解析
- 録画
- 動画編集

---

# 利用者

MediaController を利用するのは

```text
Show
```

のみとする。

ScenarioRunner は MediaController を直接利用しない。

DroneController も MediaController を利用しない。

---

# システム構成

```text
ScenarioRunner
        │
        ▼
      Show
      │
      ├──────── DroneController
      │
      └──────── MediaController
                     │
                     ├── CameraViewer
                     ├── Image Renderer
                     ├── Video Player
                     ├── Audio Player
                     └── Window Manager
```

---

# CameraViewerとの関係

CameraViewer は既存実装を利用する。

CameraViewer の責務は

- streamon
- streamoff
- フレーム取得
- 最新フレーム保持

のみとする。

MediaController は

- CameraViewer の生成
- CameraViewer の破棄
- CameraViewer の起動停止
- 表示切替

を担当する。

---

# カメラ管理

MediaController はカメラの有効・無効を管理する。

状態は

```text
Disabled

Enabled
```

の2状態とする。

---

## enable_camera()

```python
await self.media.enable_camera()
```

以下を実行する。

- streamon
- CameraViewer生成（未生成の場合）
- CameraViewer開始

既に Enabled の場合は何もしない。

---

## disable_camera()

```python
await self.media.disable_camera()
```

以下を実行する。

- streamoff
- CameraViewer停止

現在 Camera 表示中であれば Black 表示へ切り替える。

---

# Showとカメラの関係

カメラを利用するかどうかは Show が決定する。

ScenarioRunner はカメラ制御を行わない。

---

## start()

カメラを利用する Show は start() 内で enable_camera() を呼ぶ。

```python
async def start(self):

    await self.media.enable_camera()
```

カメラを使用しない Show は呼ばなくてよい。

---

## stop()

カメラを有効化した Show は stop() 内で disable_camera() を呼ぶ。

```python
async def stop(self):

    await self.media.disable_camera()
```

これにより

- 通信量削減
- CPU負荷削減
- バッテリー節約

を実現する。

---

# 表示モード

MediaController は以下の表示モードを持つ。

```text
Camera

Image

Video

Black
```

ウィンドウは共通とし、描画内容のみ切り替える。

---

# アセット管理

プロジェクトルートに以下のディレクトリを配置する。

```text
assets/

    images/

    videos/

    audio/
        bgm/
        se/
```

Show は assets ディレクトリを意識しない。

---

# パス指定

画像

```python
self.media.show_image("title.png")

self.media.show_image("tutorial/page1.png")
```

↓

```text
assets/images/title.png

assets/images/tutorial/page1.png
```

動画

```python
self.media.play_video("opening.mp4")
```

↓

```text
assets/videos/opening.mp4
```

BGM

```python
self.media.play_bgm("opening.mp3")
```

↓

```text
assets/audio/bgm/opening.mp3
```

SE

```python
self.media.play_se("flap.wav")
```

↓

```text
assets/audio/se/flap.wav
```

---

# インターフェース

```python
class MediaController:

    # Camera

    async def enable_camera()

    async def disable_camera()

    def is_camera_enabled()

    def show_camera()

    # Image

    def show_image(path)

    def show_black()

    # Video

    def play_video(
        path,
        on_finished=None,
    )

    def stop_video()

    def is_playing_video()

    # Audio

    def play_bgm(
        path,
        loop=False,
        on_finished=None,
    )

    def stop_bgm()

    def play_se(
        path,
        on_finished=None,
    )

    def stop_all_audio()

    # Volume

    def set_master_volume(volume)

    def set_bgm_volume(volume)

    def set_se_volume(volume)

    # Window

    def set_window(
        monitor,
        x,
        y,
        width,
        height,
    )

    def set_fullscreen(enabled)
```

---

# Camera

## show_camera()

```python
self.media.show_camera()
```

表示モードを Camera に変更する。

Camera が Disabled の場合は

- Black表示
- Warningログ出力

を行う。

例外は送出しない。

---

# Image

## show_image()

```python
self.media.show_image("title.png")
```

画像表示へ切り替える。

呼び出し後すぐ復帰する。

---

## show_black()

```python
self.media.show_black()
```

黒画面表示へ切り替える。

---

# Video

## play_video()

```python
self.media.play_video(
    "intro.mp4",
    on_finished=self.video_finished,
)
```

動画再生を開始する。

- 非同期再生
- 即座に復帰
- バックグラウンド再生

動画に音声が含まれている場合は音声も同時再生する。

---

## stop_video()

動画再生を停止する。

---

## is_playing_video()

動画再生状態を返す。

---

# Audio

MediaController は

- BGM
- SE
- 動画音声

を管理する。

---

## BGM

長時間再生する音源。

```python
self.media.play_bgm(
    "opening.mp3",
    loop=True,
)
```

停止

```python
self.media.stop_bgm()
```

---

## SE

短時間の効果音。

```python
self.media.play_se("flap.wav")
```

SE は複数同時再生可能とする。

---

# 音量

MediaController は

```python
set_master_volume(volume)

set_bgm_volume(volume)

set_se_volume(volume)
```

を提供する。

volume は

```text
0〜100
```

とする。

Master Volume は

- BGM
- SE
- 動画音声

すべてに適用される。

---

# メディア終了通知

動画

```python
self.media.play_video(
    "intro.mp4",
    on_finished=self.video_finished,
)
```

BGM

```python
self.media.play_bgm(
    "ending.mp3",
    loop=False,
    on_finished=self.finish_show,
)
```

SE

```python
self.media.play_se(
    "success.wav",
    on_finished=self.next_scene,
)
```

同期関数・非同期関数の双方に対応する。

---

# Window

MediaController が管理するウィンドウは1つとする。

表示内容のみ切り替える。

---

## set_window()

```python
self.media.set_window(
    monitor=1,
    x=0,
    y=0,
    width=1280,
    height=720,
)
```

変更可能項目

- モニタ番号
- x座標
- y座標
- 幅
- 高さ

モニタ変更時は指定モニタへウィンドウを移動する。

---

## set_fullscreen()

全画面表示を切り替える。

---

# Showでの利用例

```python
async def start(self):

    await self.media.enable_camera()

    self.media.set_window(
        monitor=1,
        x=0,
        y=0,
        width=1280,
        height=720,
    )

    self.media.play_bgm(
        "opening.mp3",
        loop=True,
    )


async def run(self):

    self.media.show_image("title.png")

    await asyncio.sleep(2)

    self.media.play_video(
        "intro.mp4",
        on_finished=self.video_finished,
    )

    await self.drone.takeoff()

    self.media.show_camera()

    self.media.play_se("flap.wav")


async def stop(self):

    await self.media.disable_camera()

    self.media.stop_bgm()
```

---

# 実装方針

- CameraViewer は既存実装を利用する。
- MediaController は CameraViewer のラッパーとして実装する。
- 描画処理はバックグラウンドタスクで実行する。
- 動画再生もバックグラウンドタスクで行う。
- 音声再生は表示モードとは独立して動作する。
- CameraViewer は `enable_camera()` が呼ばれている間のみ動作する。
- カメラの有効・無効は各 Show が `start()` と `stop()` の中で管理する。
- MediaController はメディアの状態管理のみを担当し、Scenario の進行制御は行わない。

---

# 将来的な拡張

以下の機能を追加できる設計とする。

- 映像フェードイン・フェードアウト
- BGMフェードイン・フェードアウト
- BGMクロスフェード
- オーバーレイ画像表示
- テキスト表示
- GIFアニメーション表示
- スライドショー
- プレイリスト再生
- 複数画面出力
- プロジェクタ出力
- 録画機能
```