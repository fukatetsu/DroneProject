import socket
from datetime import datetime

# UDP設定
HOST = "0.0.0.0"
PORT = 50001

# ソケット作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"Listening UDP {HOST}:{PORT}")

while True:
    # 受信
    data, addr = sock.recvfrom(4096)

    # bytes → string
    raw_message = data.decode("utf-8", errors="ignore")

    # Processing由来の ;\n を除去
    message = raw_message.replace(";\n", "").strip()

    # 空データ対策
    if not message:
        continue

    # 分割
    parts = message.split()

    parsed = []

    for i, value in enumerate(parts):
        try:
            parsed.append(float(value))
        except ValueError:
            parsed.append(value)

    # 時刻
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    # 出力整形
    print("=" * 60)
    print(f"time   : {now}")
    print(f"from   : {addr[0]}:{addr[1]}")
    print(f"length : {len(parsed)}")

    for i, value in enumerate(parsed):
        print(f"dt[{i:02d}] = {value}")

    print()