from __future__ import annotations

import asyncio
from asyncio import DatagramProtocol
from typing import Optional

from ...models.imu_state import ImuState
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

    @property
    def state(self) -> ImuState:
        return self._state

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
        # Support one or more semicolon-delimited IMU packets in a single UDP payload.
        fragments = message.split(";")
        for fragment in fragments:
            cleaned = fragment.strip()
            if not cleaned:
                continue

            try:
                self._state = ImuState.from_udp_message(cleaned)
            except ValueError:
                pass
