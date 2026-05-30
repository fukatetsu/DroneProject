from djitellopy import Tello
import time

tello = Tello()
tello.connect()

print(f"Battery: {tello.get_battery()}%")

tello.takeoff()

# 安定化
time.sleep(3)

start_time = time.time()

while time.time() - start_time < 30:
    # 左へ
    tello.send_rc_control(-10, 0, 0, 0)
    time.sleep(1)

    # 右へ
    tello.send_rc_control(10, 0, 0, 0)
    time.sleep(1)

# 停止
tello.send_rc_control(0, 0, 0, 0)

# 安定化
time.sleep(3)

tello.land()