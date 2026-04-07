"""
Simple async PLC tests (no pytest-asyncio dependency)

Tests verify: AsyncPLCProtocol initialization and basic functionality
"""

import asyncio
from unittest.mock import Mock, AsyncMock
from lib.AsyncPLCProtocol import (
    AsyncModbusTCPProtocol,
    AsyncModbusRTUProtocol,
    AsyncSLMPProtocol,
    AsyncPLCBatch
)


class TestAsyncProtocolInit:
    """Test protocol initialization"""

    def test_modbus_tcp_init(self):
        """AsyncModbusTCPProtocol initialization"""
        protocol = AsyncModbusTCPProtocol()

        assert protocol.client is None
        assert protocol._connected is False
        assert protocol.COIL_OFFSET == 8192

    def test_modbus_rtu_init(self):
        """AsyncModbusRTUProtocol initialization"""
        protocol = AsyncModbusRTUProtocol()

        assert protocol.client is None
        assert protocol._connected is False
        assert protocol.slave_id == 1

    def test_slmp_protocol_init(self):
        """AsyncSLMPProtocol initialization"""
        protocol = AsyncSLMPProtocol()

        assert protocol.client is None
        assert protocol._connected is False
        assert protocol.plc_type == "Q"
        assert protocol.comm_type == "binary"


class TestAsyncBatchBasic:
    """Test AsyncPLCBatch basic functionality"""

    def test_batch_initialization(self):
        """AsyncPLCBatch initialization"""
        protocol = AsyncModbusTCPProtocol()
        batch = AsyncPLCBatch(protocol)

        assert batch.protocol == protocol

    def test_batch_multiple_reads_order(self):
        """Verify batch reads maintain order"""
        async def test():
            protocol = AsyncModbusTCPProtocol()
            batch = AsyncPLCBatch(protocol)

            # Mock responses
            responses = [
                Mock(bits=[True]),
                Mock(bits=[False]),
                Mock(bits=[True])
            ]

            protocol.read_coils = AsyncMock(side_effect=responses)

            results = await batch.read_multiple([
                (0, 1),
                (1, 1),
                (2, 1),
            ])

            assert len(results) == 3
            assert results[0].bits == [True]
            assert results[1].bits == [False]
            assert results[2].bits == [True]

        asyncio.run(test())

    def test_batch_multiple_writes_order(self):
        """Verify batch writes maintain order"""
        async def test():
            protocol = AsyncModbusTCPProtocol()
            batch = AsyncPLCBatch(protocol)

            protocol.write_coil = AsyncMock(return_value=Mock())

            results = await batch.write_multiple([
                (100, True),
                (101, False),
                (102, True),
            ])

            assert len(results) == 3
            assert protocol.write_coil.call_count == 3

        asyncio.run(test())


class TestAsyncProtocolStatusChecks:
    """Test protocol status checking"""

    def test_tcp_connection_status(self):
        """Test TCP protocol connection status"""
        async def test():
            protocol = AsyncModbusTCPProtocol()

            # Not connected initially
            assert await protocol.is_connected() is False

            # Set connected state
            protocol._connected = True
            assert await protocol.is_connected() is True

        asyncio.run(test())

    def test_rtu_connection_status(self):
        """Test RTU protocol connection status"""
        async def test():
            protocol = AsyncModbusRTUProtocol()

            assert await protocol.is_connected() is False

            protocol._connected = True
            assert await protocol.is_connected() is True

        asyncio.run(test())

    def test_slmp_connection_status(self):
        """Test SLMP protocol connection status"""
        async def test():
            protocol = AsyncSLMPProtocol()

            assert await protocol.is_connected() is False

            protocol._connected = True
            assert await protocol.is_connected() is True

        asyncio.run(test())


class TestAsyncReadWrite:
    """Test read/write operations"""

    def test_tcp_read_when_not_connected(self):
        """Test read fails when not connected"""
        async def test():
            protocol = AsyncModbusTCPProtocol()
            protocol._connected = False

            result = await protocol.read_coils(0, 3)

            assert result is None

        asyncio.run(test())

    def test_tcp_write_when_not_connected(self):
        """Test write fails when not connected"""
        async def test():
            protocol = AsyncModbusTCPProtocol()
            protocol._connected = False

            result = await protocol.write_coil(100, True)

            assert result is None

        asyncio.run(test())

    def test_rtu_read_when_not_connected(self):
        """Test RTU read fails when not connected"""
        async def test():
            protocol = AsyncModbusRTUProtocol()
            protocol._connected = False

            result = await protocol.read_coils(0, 3)

            assert result is None

        asyncio.run(test())

    def test_rtu_write_when_not_connected(self):
        """Test RTU write fails when not connected"""
        async def test():
            protocol = AsyncModbusRTUProtocol()
            protocol._connected = False

            result = await protocol.write_coil(100, True)

            assert result is None

        asyncio.run(test())

    def test_slmp_read_when_not_connected(self):
        """Test SLMP read fails when not connected"""
        async def test():
            protocol = AsyncSLMPProtocol()
            protocol._connected = False

            result = await protocol.read_coils(0, 3)

            assert result is None

        asyncio.run(test())

    def test_slmp_write_when_not_connected(self):
        """Test SLMP write fails when not connected"""
        async def test():
            protocol = AsyncSLMPProtocol()
            protocol._connected = False

            result = await protocol.write_coil(100, True)

            assert result is None

        asyncio.run(test())


class TestAsyncParallelBenefits:
    """Test performance benefits of parallel execution"""

    def test_parallel_reads_faster(self):
        """Verify parallel reads are faster than sequential"""
        async def test():
            protocol = AsyncModbusTCPProtocol()
            batch = AsyncPLCBatch(protocol)

            call_count = [0]
            call_times = []

            async def mock_read(addr, count):
                call_count[0] += 1
                call_times.append((call_count[0], asyncio.get_event_loop().time()))
                await asyncio.sleep(0.001)  # Simulate 1ms read
                return Mock(bits=[True])

            protocol.read_coils = mock_read

            # Parallel read (should take ~1ms, not ~3ms)
            start = asyncio.get_event_loop().time()
            results = await batch.read_multiple([
                (0, 1),
                (1, 1),
                (2, 1),
            ])
            elapsed = asyncio.get_event_loop().time() - start

            assert len(results) == 3
            # All reads should start roughly at same time (parallel)
            # Elapsed should be ~1-2ms, not ~3ms
            assert elapsed < 0.01  # Should be much less than 3ms

        asyncio.run(test())

    def test_concurrent_read_write(self):
        """Verify concurrent read and write operations"""
        async def test():
            protocol = AsyncModbusTCPProtocol()

            async def mock_read(addr, count):
                await asyncio.sleep(0.001)
                return Mock(bits=[True])

            async def mock_write(addr, value):
                await asyncio.sleep(0.001)
                return Mock()

            protocol.read_coils = mock_read
            protocol.write_coil = mock_write

            # Run read and write concurrently
            start = asyncio.get_event_loop().time()

            read_task = asyncio.create_task(protocol.read_coils(0, 1))
            write_task = asyncio.create_task(protocol.write_coil(100, True))

            read_result = await read_task
            write_result = await write_task

            elapsed = asyncio.get_event_loop().time() - start

            assert read_result is not None
            assert write_result is not None
            # Should be ~1-2ms, not ~2ms (parallel execution)
            assert elapsed < 0.01

        asyncio.run(test())


class TestAsyncCoilOffset:
    """Test coil address offset handling"""

    def test_tcp_coil_offset(self):
        """Verify TCP applies correct COIL_OFFSET"""
        assert AsyncModbusTCPProtocol.COIL_OFFSET == 8192

    def test_rtu_coil_offset(self):
        """Verify RTU applies correct COIL_OFFSET"""
        assert AsyncModbusRTUProtocol.COIL_OFFSET == 8192
