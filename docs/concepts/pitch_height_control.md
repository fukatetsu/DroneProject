**Pitch→高度制御モジュール (`shows.interaction.pitch_height_control`)**

概要:
- `PitchHeightController` はフープのピッチ角を目標高度に変換し、ドローンに上下速度コマンドを送るための再利用可能なコントローラです。
- 既存のショー（例: `src/shows/ISCA/halo.py`）の内部ロジックを変更せずに、同等の機能を外出しして使えるよう設計されています。

設置場所:
- モジュール: `src/shows/interaction/pitch_height_control.py`

使い方（基本）:
1. `PitchHeightController` をインポートします。

   from shows.interaction.pitch_height_control import PitchHeightController

2. インスタンスを作成します（`DroneController` と必要なら `HoopAnalyzer` を渡す）。

   controller = PitchHeightController(drone=my_drone, analyzer=my_analyzer)

3. 既存のフィルタ状態を保持しつつ呼び出します。戻り値は更新済みの `(filtered_pitch, filtered_vz)` です。

   filtered_pitch, filtered_vz = await controller.follow_pitch_for_height(
       duration_sec=10,
       filtered_pitch=filtered_pitch,
       filtered_vz=filtered_vz,
       pitch_min=-90,
       pitch_max=90,
       height_min=30,
       height_max=200,
       height_gain=1.0,
       x=0, y=0, yaw=0,
   )

遅延（ラグ）機能:
- 引数 `apply_lag_seconds` に秒数を指定すると、検出された目標高度がその秒数だけ遅延してドローンへ適用されます。内部的にはシンプルな FIFO キューを用いて、指定時刻を過ぎたエントリだけを取り出して `calc_height_vz` を計算、RC コマンドを送信します。
- 例: 0.5秒の遅延を付与する

   filtered_pitch, filtered_vz = await controller.follow_pitch_for_height(..., apply_lag_seconds=0.5)

注意事項:
- 既存のファイル（`halo.py` など）は現状のまま変更していません。必要に応じて手動で既存の `_follow_pitch_for_height` 呼び出しを、このコントローラへ置き換えてください。
- `PitchHeightController` は `calc_height_vz` と `send_rc_control` を利用します。ドローンの状態取得 (`height_tof`) やコマンドの安全性は呼び出し元の責任です。

今後の移行案:
- 自動ラッパーを用意して順次既存ショーから移行することを推奨します（このリポジトリの他ショーはほぼ同様のロジックを持つため、まとめて移行可能です）。
