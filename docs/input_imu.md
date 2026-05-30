# UDP IMUセンサデータ仕様書

## 概要

このシステムでは、IMUセンサデータをUDP通信によって受信する。

- 通信方式: UDP
- ポート番号: `50001`
- エンコード: UTF-8
- データ形式: スペース区切り文字列
- メッセージ終端: `;\n`

受信データ例:

```text
0 -0.014069033 0.0031434065 -1.0151372 0.39292583 0.8697775 -0.08011109 0.0033500493 3.1301043 3.9240534 1.0 5.1433868e-05 0.00011385361 -1.0486517e-05;
```

---

## データ受信方法

UDPで受信した文字列をスペース区切りで分割し、float配列 `dt` として扱う。

```python
dt = [float(x) for x in message.split()]
```

想定される配列長:

```text
14要素
```

---

## データ仕様

| index | 名前 | 内容 |
|---|---|---|
| dt[0] | id | センサIDまたはタイムスタンプ系の値 |
| dt[1] | accel_x | 加速度X |
| dt[2] | accel_y | 加速度Y |
| dt[3] | accel_z | 加速度Z |
| dt[4] | gyro_x | ジャイロX |
| dt[5] | gyro_y | ジャイロY |
| dt[6] | gyro_z | ジャイロZ |
| dt[7] | mag_x | 地磁気X |
| dt[8] | mag_y | 地磁気Y |
| dt[9] | mag_z | 地磁気Z |
| dt[10] | quat_w | クォータニオンW |
| dt[11] | quat_x | クォータニオンX |
| dt[12] | quat_y | クォータニオンY |
| dt[13] | quat_z | クォータニオンZ |

---

## クォータニオンの順番

クォータニオンは以下の順番で格納される。

```text
[w, x, y, z]
```

例:

```python
qw = dt[10]
qx = dt[11]
qy = dt[12]
qz = dt[13]
```


---

## UDP受信サンプルコード

```python
import socket

HOST = "0.0.0.0"
PORT = 50001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"Listening UDP {HOST}:{PORT}")

while True:
    data, addr = sock.recvfrom(4096)

    # bytes -> string
    message = data.decode("utf-8", errors="ignore")

    # Processing側の終端を除去
    message = message.replace(";\n", "").strip()

    if not message:
        continue

    # float配列へ変換
    dt = [float(x) for x in message.split()]

    print(dt)
```