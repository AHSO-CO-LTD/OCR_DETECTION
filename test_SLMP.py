"""
Test SLMP (MC Protocol) với PLC Mitsubishi FX5UC
Chạy file này để kiểm tra kết nối trước khi tích hợp vào chương trình chính.

Lưu ý:
- Cần cấu hình mở port SLMP trên PLC bằng GxWorks3
- Port mặc định thường là 5000 hoặc 5001
- FX5UC (iQ-F series) thử với plc_type="iQ-R" hoặc "Q"
"""

import pymcprotocol
import time

# =============================================================================
# CẤU HÌNH - THAY ĐỔI THEO PLC CỦA BẠN
# =============================================================================
PLC_IP = "192.168.0.250"  # Địa chỉ IP của PLC
PLC_PORT = 5000           # Port MC Protocol (thường là 5000 hoặc 5001)
PLC_TYPE = "iQ-R"         # Thử "iQ-R", "Q", "L", "iQ-L" nếu không được
COMM_TYPE = "binary"      # "binary" hoặc "ascii"


def test_connection():
    """Test kết nối cơ bản"""
    print("=" * 50)
    print("TEST KẾT NỐI SLMP")
    print("=" * 50)
    print(f"IP: {PLC_IP}")
    print(f"Port: {PLC_PORT}")
    print(f"PLC Type: {PLC_TYPE}")
    print(f"Comm Type: {COMM_TYPE}")
    print("-" * 50)

    try:
        # Tạo client
        client = pymcprotocol.Type3E(plctype=PLC_TYPE)

        if COMM_TYPE == "ascii":
            client.setaccessopt(commtype="ascii")

        # Kết nối
        print("Đang kết nối...")
        client.connect(PLC_IP, PLC_PORT)
        print("✓ Kết nối thành công!")

        return client

    except Exception as e:
        print(f"✗ Lỗi kết nối: {e}")
        return None


def test_read_M(client, address=0, count=3):
    """Test đọc bit M"""
    print("-" * 50)
    print(f"TEST ĐỌC M{address} - M{address + count - 1}")
    print("-" * 50)

    try:
        values = client.batchread_bitunits(headdevice=f"M{address}", readsize=count)
        print(f"✓ Đọc thành công!")
        for i, v in enumerate(values):
            print(f"  M{address + i} = {v} ({bool(v)})")
        return values

    except Exception as e:
        print(f"✗ Lỗi đọc: {e}")
        return None


def test_write_M(client, address=100, value=True):
    """Test ghi bit M"""
    print("-" * 50)
    print(f"TEST GHI M{address} = {value}")
    print("-" * 50)

    try:
        client.batchwrite_bitunits(headdevice=f"M{address}", values=[1 if value else 0])
        print(f"✓ Ghi thành công!")

        # Đọc lại để xác nhận
        result = client.batchread_bitunits(headdevice=f"M{address}", readsize=1)
        print(f"  Đọc lại: M{address} = {result[0]} ({bool(result[0])})")
        return True

    except Exception as e:
        print(f"✗ Lỗi ghi: {e}")
        return False


def test_read_D(client, address=0, count=5):
    """Test đọc word D"""
    print("-" * 50)
    print(f"TEST ĐỌC D{address} - D{address + count - 1}")
    print("-" * 50)

    try:
        values = client.batchread_wordunits(headdevice=f"D{address}", readsize=count)
        print(f"✓ Đọc thành công!")
        for i, v in enumerate(values):
            print(f"  D{address + i} = {v}")
        return values

    except Exception as e:
        print(f"✗ Lỗi đọc: {e}")
        return None


def test_write_D(client, address=100, value=12345):
    """Test ghi word D"""
    print("-" * 50)
    print(f"TEST GHI D{address} = {value}")
    print("-" * 50)

    try:
        client.batchwrite_wordunits(headdevice=f"D{address}", values=[value])
        print(f"✓ Ghi thành công!")

        # Đọc lại để xác nhận
        result = client.batchread_wordunits(headdevice=f"D{address}", readsize=1)
        print(f"  Đọc lại: D{address} = {result[0]}")
        return True

    except Exception as e:
        print(f"✗ Lỗi ghi: {e}")
        return False


def test_continuous_read(client, address=0, count=3, interval=0.1, duration=5):
    """Test đọc liên tục (giống như trong chương trình chính)"""
    print("-" * 50)
    print(f"TEST ĐỌC LIÊN TỤC M{address}-M{address + count - 1}")
    print(f"Interval: {interval}s, Duration: {duration}s")
    print("Nhấn Ctrl+C để dừng sớm")
    print("-" * 50)

    start_time = time.time()
    read_count = 0
    error_count = 0

    try:
        while time.time() - start_time < duration:
            try:
                values = client.batchread_bitunits(headdevice=f"M{address}", readsize=count)
                read_count += 1
                status = " | ".join([f"M{address + i}={v}" for i, v in enumerate(values)])
                print(f"\r[{read_count}] {status}    ", end="", flush=True)
            except Exception:
                error_count += 1

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n(Dừng bởi người dùng)")

    print(f"\n✓ Hoàn thành: {read_count} lần đọc, {error_count} lỗi")
    if read_count > 0:
        print(f"  Tỷ lệ thành công: {(read_count - error_count) / read_count * 100:.1f}%")


def disconnect(client):
    """Ngắt kết nối"""
    print("-" * 50)
    print("NGẮT KẾT NỐI")
    print("-" * 50)

    try:
        client.close()
        print("✓ Đã ngắt kết nối")
    except Exception as e:
        print(f"✗ Lỗi ngắt kết nối: {e}")


def main():
    print("\n" + "=" * 50)
    print("  CHƯƠNG TRÌNH TEST SLMP - PLC MITSUBISHI")
    print("=" * 50 + "\n")

    # Test kết nối
    client = test_connection()
    if client is None:
        print("\nKhông thể kết nối. Kiểm tra:")
        print("  1. IP và Port có đúng không")
        print("  2. PLC đã bật chưa")
        print("  3. Port SLMP đã được cấu hình trong GxWorks3 chưa")
        print("  4. Thử đổi PLC_TYPE (iQ-R, Q, L, iQ-L)")
        return

    try:
        # Test đọc M
        test_read_M(client, address=0, count=3)

        # Test ghi M (bật M100)
        test_write_M(client, address=100, value=True)
        time.sleep(0.5)
        test_write_M(client, address=100, value=False)

        # Test đọc D
        test_read_D(client, address=0, count=5)

        # Test ghi D
        # test_write_D(client, address=100, value=12345)

        # Test đọc liên tục (5 giây)
        # test_continuous_read(client, address=0, count=3, interval=0.002, duration=5)

    finally:
        # Ngắt kết nối
        disconnect(client)

    print("\n" + "=" * 50)
    print("  TEST HOÀN TẤT")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
