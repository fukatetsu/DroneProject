import asyncio


async def adjust_height(
    drone,
    target_height: int = 90,
    tolerance: int = 3,
    gain: float = 3.0,
    max_speed: int = 40,
    interval: float = 0.1,
    x:int = 0,
    y:int = 0,
    yaw:int = 0,
) -> None:
    """
    TOFセンサを用いて指定高度まで移動する。

    Args:
        drone: Telloインスタンス
        target_height: 目標高度(cm)
        tolerance: 許容誤差(cm)
        gain: P制御ゲイン
        max_speed: RC制御の最大上下速度
        interval: 制御周期(sec)
    """

    while True:
        current_height = drone.state.height_tof
        error = target_height - current_height

        print(
            f"Height: {current_height} cm "
            f"Error: {error}"
        )

        if abs(error) <= tolerance:
            break

        vz = int(error * gain)
        vz = max(-max_speed, min(max_speed, vz))

        drone.send_rc_control(
            x,
            y,
            vz,
            yaw,
        )

        await asyncio.sleep(interval)

    drone.send_rc_control(0, 0, 0, 0)

    print(
        f"Target reached: "
        f"{drone.state.height_tof} cm"
    )

def calc_height_vz(
    drone,
    target_height: float,
    tolerance: float = 3,
    gain: float = 3.0,
    max_speed: int = 40,
) -> int:
    """
    ドローンの現在高度と目標高度から上下速度(vz)を計算する。
    """

    current_height = drone.state.height_tof
    error = target_height - current_height

    if abs(error) <= tolerance:
        return 0

    vz = int(error * gain)
    return max(-max_speed, min(max_speed, vz))