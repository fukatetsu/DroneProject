# ImuState 姿勢推定機能追加

## 背景

現在、UDP経由でIMUデータを受信している。

### 実装済み

* `UdpImuInput`

  * UDPパケットの受信
  * `ImuState` の生成
* `DtEstimator`

  * UDP受信周期の推定
  * 中央値ベースの移動窓による `dt` 更新
  * `dt` は常時更新される

### 未実装

* IMUデータからの姿勢推定
* `roll`
* `pitch`
* `yaw`

現在の `ImuState` には上記フィールドが存在するが、実際には意味のある値が設定されていない。

---

## 前提条件

UDPパケットには以下の情報が含まれる。

```text
不明な値
accel_x
accel_y
accel_z
gyro_x
gyro_y
gyro_z
mag_x
mag_y
mag_z
不明な値1
不明な値2
不明な値3
不明な値4
```

ただし、

```text
不明な値
```

は姿勢推定には使用しない。

使用するのは以下のみ。

```text
accel_x
accel_y
accel_z

gyro_x
gyro_y
gyro_z

mag_x
mag_y
mag_z
```

---

## 要件

### 1. roll / pitch / yaw を推定する

姿勢推定結果を

```python
roll
pitch
yaw
```

へ格納する。

---

### 2. dt を利用する

現在 `DtEstimator` によって推定される

```python
dt
```

を利用する。

ジャイロ積分を行うこと。

---

### 3. Complementary Filter を採用する

以下を融合する。

#### 加速度

重力方向から

```python
roll
pitch
```

を推定する。

#### 地磁気

傾き補正後の地磁気から

```python
yaw
```

を推定する。

#### ジャイロ

```python
gyro * dt
```

で角度を更新する。

#### 融合

Complementary Filter により

```python
gyro推定値
```

と

```python
accel + mag推定値
```

を融合する。

---

## 初期化

初回サンプルでは前回姿勢が存在しない。

そのため初回のみ

```python
accel
+
mag
```

から姿勢を直接求める。

以降のサンプルでジャイロ積分を使用する。

---

## 実装方針

### ImuState の責務

`ImuState` は現在のセンサ状態を表すオブジェクトとする。

姿勢推定結果

```python
roll
pitch
yaw
```

は `ImuState` に保持する。

---

### 状態保持

Complementary Filter のため、

前回姿勢

```python
previous_roll
previous_pitch
previous_yaw
```

を保持する必要がある。

保持方法は実装しやすい方法を選択してよい。

ただし、

* 毎サンプルで姿勢更新可能
* dtを利用可能

であること。

---

## 実装対象

### 修正

```text
src\models\imu_state.py
```

### 必要に応じて修正

```text
src\inputs\imu\dt_estimator.py
src\inputs\imu\udp_imu_input.py
```

---

## 期待する成果物

* 実装コード
* クラス構成
* 変更後の処理フロー
* 姿勢推定アルゴリズムの説明
* 主要パラメータ（Complementary Filter係数等）の説明
