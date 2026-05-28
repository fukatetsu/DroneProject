from __future__ import annotations

import asyncio
from dataclasses import asdict

from ...controllers.drone import DroneController
from ..base.show import Show


class StateMonitorShow(Show):
    """ドローンを軽く飛行させながら状態を定期的に出力するテスト用ショー。

    動作:
    - takeoff -> 指定回数状態を表示してホバリング -> land

    パラメータはクラス内に固定してあり、シナリオJSONには依存しない。
    """

    def __init__(
        self,
        drone: DroneController,
        interval: float = 0.5,
        iterations: int = 20,
    ) -> None:
        super().__init__(drone)
        self.interval = interval
        self.iterations = iterations
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def run(self) -> None:
        # シンプルに離陸して数回状態を表示して着陸する

        for i in range(self.iterations):
            if not self._running:
                break
            # ドローンコントローラが同期プロパティで state を提供する前提
            try:
                state = self.drone.state
                # dataclassなら asdict で見やすく表示
                try:
                    print(asdict(state))
                except Exception:
                    print(repr(state))
            except Exception as e:
                print(f"StateMonitorShow: failed to read state: {e}")

            await asyncio.sleep(self.interval)

            self.drone.send_rc_control(0, 0, 0, 20)



    async def stop(self) -> None:
        self._running = False
        # 緊急停止は行わず、rc をゼロにしておく
        self.drone.send_rc_control(0, 0, 0, 0)
