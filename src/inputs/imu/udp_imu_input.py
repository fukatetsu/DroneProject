from __future__ import annotations

import asyncio
from asyncio import DatagramProtocol
from typing import Optional

from ...models.imu_state import ImuState
from .dt_estimator import DtEstimator
from .input_device import InputDevice


class _UdpImuProtocol(DatagramProtocol):
    def __init__(self, owner: "UdpImuInput") -> None:
        self.owner = owner

    def datagram_received(self, data: bytes, addr) -> None:
        message = data.decode("utf-8", errors="ignore")
        try:
            self.owner._process_message(message)
        except Exception:
            pass

    def error_received(self, exc: Exception) -> None:
        pass


class UdpImuInput(InputDevice):
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 50001,
    ) -> None:
        self.host = host
        self.port = port

        self._state = ImuState()

        self._transport: Optional[asyncio.BaseTransport] = None
        self._protocol: Optional[_UdpImuProtocol] = None
        self._started = False

        self._dt_estimator = DtEstimator(window_size=20)

    @property
    def state(self) -> ImuState:
        return self._state
    
    @property
    def dt(self) -> float:
        return self._dt_estimator.dt

    @property
    def sample_rate(self) -> float:
        return self._dt_estimator.sample_rate

    @property
    def dt_ready(self) -> bool:
        return self._dt_estimator.ready

    async def start(self) -> None:
        if self._started:
            return

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _UdpImuProtocol(self),
            local_addr=(self.host, self.port),
        )
        self._transport = transport
        self._protocol = protocol
        self._started = True

    async def stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
        self._started = False

    def _process_message(self, message: str) -> None:
        self._dt_estimator.update()

        fragments = message.split(";")

        for fragment in fragments:
            cleaned = fragment.strip()

            if not cleaned:
                continue

            try:
                self._state = ImuState.from_udp_message(
                    cleaned,
                    previous_state=self._state,
                    dt=self._dt_estimator.dt,
                )
            except ValueError:
                pass
