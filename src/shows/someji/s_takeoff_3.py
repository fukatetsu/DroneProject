from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class TakeoffShow_s3(Show):
    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.takeoff()
        self.drone.send_rc_control(0,0,0,0)
        print(f"Battery: {self.drone.state.battery}%")
        await asyncio.sleep(2)

        target_height = 60  # cm
        tolerance = 3       # ±3 cm

        while True:
            current_height = self.drone.state.height_tof

            error = target_height - current_height

            print(
                f"Height: {current_height} cm "
                f"Error: {error}"
            )

            if abs(error) <= tolerance:
                self.drone.send_rc_control(0, 0, 0, 0)
                break

            # 上下速度を決定
            vz = int(error * 3)

            # TelloのRC値範囲
            vz = max(-40, min(40, vz))

            self.drone.send_rc_control(
                0,  # left_right
                0,  # forward_back
                vz, # up_down
                0,  # yaw
            )

            await asyncio.sleep(0.1)

        self.drone.send_rc_control(0,0,0,0)
        print(f"Target reached: {self.drone.state.height_tof} cm")
        await asyncio.sleep(1)
        

    async def stop(self) -> None:
        return None
