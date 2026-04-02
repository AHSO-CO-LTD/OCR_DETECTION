# 🚀 OPTIMIZATION IMPLEMENTATION PLAN
**OCR Detection System - Performance Enhancement Roadmap**

---

## 📅 TỔNG QUAN KỀ HOẠCH

| Phase | Tên | Thời Gian | Benefit | Khó Độ |
|-------|-----|-----------|---------|--------|
| **Phase 1** | Frame Skipping | 2-3 ngày | 50% latency ↓ | 🟢 Easy |
| **Phase 2** | Buffer Pool | 2-3 ngày | 30% memory ↓ | 🟢 Easy |
| **Phase 3** | Query Caching | 2-3 ngày | 97% query ↓ | 🟢 Easy |
| **Phase 4** | Async I/O PLC | 3-5 ngày | 100% UI freeze ↓ | 🟡 Medium |
| **Phase 5** | Replace Sleep | 1-2 ngày | 10% CPU ↓ | 🟢 Easy |
| **Phase 6** | Code Refactor | 1-2 tuần | Better structure | 🔴 Hard |
| | **TỔNG CỘNG** | **3-4 TUẦN** | **30-80% ↑** | |

---

## ⏱️ TIMELINE CHI TIẾT

```
TUẦN 1: Foundation (Phase 1 + 2)
├─ Thứ 2-3: Frame Skipping
├─ Thứ 4-5: Buffer Pool
└─ Thứ 6-7: Testing & Integration

TUẦN 2: Database & Async (Phase 3 + 4)
├─ Thứ 2-3: Query Caching
├─ Thứ 4-5: Async PLC I/O
└─ Thứ 6-7: Testing & Integration

TUẦN 3: Cleanup (Phase 5)
├─ Thứ 2-3: Replace Sleep → QTimer
├─ Thứ 4-5: Testing
└─ Thứ 6: Buffer day

TUẦN 4: Major Refactor (Phase 6) - Optional
├─ Split Main_Screen.py
├─ Code cleanup
└─ Performance testing
```

---

# 🎯 PHASE 1: FRAME SKIPPING FOR AI INFERENCE

## 📋 Chi Tiết Task

### Task 1.1: Tạo ImageProcessor Class
**Thời gian:** 1 ngày
**Files:**
- `lib/Display.py` (modify)
- `lib/ImageProcessor.py` (new)

**Mô tả:**
```python
# lib/ImageProcessor.py
import threading
import queue
import time
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

class ImageProcessor(QObject):
    """Xử lý image với frame skipping"""

    # Signals
    result_ready = pyqtSignal(np.ndarray)
    processing_status = pyqtSignal(str)

    def __init__(self, model, min_interval_ms=500, queue_size=2):
        super().__init__()
        self.model = model
        self.min_interval = min_interval_ms / 1000  # Chuyển sang seconds
        self.queue_size = queue_size

        # Queue & timing
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.last_processed_time = 0
        self.is_running = False

        # Metrics
        self.frames_received = 0
        self.frames_skipped = 0
        self.frames_processed = 0

    def on_new_frame(self, frame):
        """Gọi mỗi khi camera có frame mới (30fps)"""
        self.frames_received += 1
        current_time = time.time()

        # Frame skipping logic
        if current_time - self.last_processed_time >= self.min_interval:
            # Đủ thời gian → xử lý frame này
            try:
                self.frame_queue.get_nowait()  # Bỏ frame cũ
            except queue.Empty:
                pass

            self.frame_queue.put(frame)
            self.last_processed_time = current_time
        else:
            # Chưa đủ thời gian → skip
            self.frames_skipped += 1

    def start_processing(self):
        """Bắt đầu thread xử lý"""
        self.is_running = True
        self.process_thread = threading.Thread(
            target=self._process_loop,
            daemon=True
        )
        self.process_thread.start()
        self.processing_status.emit("Started")

    def stop_processing(self):
        """Dừng xử lý"""
        self.is_running = False
        self.process_thread.join(timeout=2)
        self.processing_status.emit("Stopped")

    def _process_loop(self):
        """Loop xử lý AI (chạy trong thread riêng)"""
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)

                # Xử lý AI
                result = self.model.predict(frame)  # 300-500ms
                self.frames_processed += 1

                # Gửi signal kết quả
                self.result_ready.emit(result)

            except queue.Empty:
                continue
            except Exception as e:
                self.processing_status.emit(f"Error: {e}")

    def get_stats(self):
        """Lấy thống kê xử lý"""
        return {
            'received': self.frames_received,
            'skipped': self.frames_skipped,
            'processed': self.frames_processed,
            'skip_rate': f"{100 * self.frames_skipped / max(1, self.frames_received):.1f}%"
        }
```

**Checklist:**
- [ ] Tạo file `lib/ImageProcessor.py`
- [ ] Implement `on_new_frame()` với frame skipping logic
- [ ] Implement `_process_loop()` với AI inference
- [ ] Thêm metrics (frames_received, frames_skipped, frames_processed)
- [ ] Unit test ImageProcessor

---

### Task 1.2: Integrate vào Display.py
**Thời gian:** 1 ngày
**Files:** `lib/Display.py`

**Mô tả:**
```python
# lib/Display.py - Thay đổi

from lib.ImageProcessor import ImageProcessor

class DisplayManager(QWidget):
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor(
            model=self.ai_model,
            min_interval_ms=500,
            queue_size=2
        )

        # Kết nối signals
        self.image_processor.result_ready.connect(self.display_result)
        self.image_processor.processing_status.connect(self.on_processor_status)

        # Bắt đầu xử lý
        self.image_processor.start_processing()

    def on_camera_frame(self, frame):
        """Callback từ camera"""
        # Gửi frame đến image processor (frame skipping xảy ra ở đây)
        self.image_processor.on_new_frame(frame)

    def display_result(self, result):
        """Callback khi AI xử lý xong"""
        # Cập nhật UI với result
        self.update_display(result)

    def on_processor_status(self, status):
        """Log processor status"""
        print(f"[ImageProcessor] {status}")
```

**Checklist:**
- [ ] Import ImageProcessor
- [ ] Khởi tạo ImageProcessor instance
- [ ] Kết nối camera_frame signal tới `on_new_frame()`
- [ ] Kết nối result_ready signal tới display UI
- [ ] Test integration với camera real

---

## ✅ Testing Plan (Phase 1)

```python
# tests/test_image_processor.py

import pytest
from unittest.mock import Mock, patch
from lib.ImageProcessor import ImageProcessor

class TestImageProcessor:

    def test_frame_skipping(self):
        """Test frame skipping logic"""
        processor = ImageProcessor(
            model=Mock(),
            min_interval_ms=100,  # 100ms interval
            queue_size=2
        )
        processor.start_processing()

        # Gửi frames nhanh (30fps = 33ms interval)
        for i in range(10):
            processor.on_new_frame(f"frame_{i}")

        # Kiểm tra: phải skip 7-8 frames
        stats = processor.get_stats()
        skip_rate = float(stats['skip_rate'].rstrip('%'))
        assert skip_rate > 50, f"Expected skip rate >50%, got {skip_rate}%"

        processor.stop_processing()

    def test_queue_max_size(self):
        """Test queue không tràn"""
        processor = ImageProcessor(
            model=Mock(),
            min_interval_ms=500,
            queue_size=2
        )
        processor.start_processing()

        # Gửi 100 frames nhanh liên tiếp
        for i in range(100):
            processor.on_new_frame(f"frame_{i}")

        # Queue size không vượt quá maxsize
        assert processor.frame_queue.qsize() <= 2

        processor.stop_processing()

    def test_processing_performance(self):
        """Test processing không block UI"""
        processor = ImageProcessor(
            model=Mock(),
            min_interval_ms=500,
            queue_size=2
        )
        processor.start_processing()

        import time

        # Đo thời gian gửi frame (phải <10ms, không block)
        start = time.time()
        for i in range(100):
            processor.on_new_frame(f"frame_{i}")
        elapsed = time.time() - start

        # 100 frames phải xong trong <50ms (không block)
        assert elapsed < 0.05, f"on_new_frame() blocking! {elapsed}s"

        processor.stop_processing()
```

**Checklist:**
- [ ] Run `pytest tests/test_image_processor.py`
- [ ] Verify frame skipping rate >50%
- [ ] Verify queue không tràn
- [ ] Verify không blocking UI
- [ ] Manual test với camera real
- [ ] Check CPU usage < 40% (before: 60-80%)
- [ ] Check latency < 300ms (before: 500ms)

---

## 📊 Success Metrics (Phase 1)

| Metric | Target | Current | Target Time |
|--------|--------|---------|------------|
| Frame skip rate | >50% | 0% | - |
| Latency | <300ms | 500ms | ↓ 40% |
| CPU usage | <40% | 60-80% | ↓ 33% |
| Memory stable | Yes | Unstable | ✓ |
| UI responsiveness | Smooth | Lag | ↑ 10x |

---

# 🎯 PHASE 2: BUFFER POOL MANAGEMENT

## 📋 Chi Tiết Task

### Task 2.1: Tạo BufferPool Class
**Thời gian:** 1 ngày
**Files:**
- `lib/BufferPool.py` (new)

**Mô tả:**
```python
# lib/BufferPool.py

import numpy as np
import threading
from typing import Tuple

class BufferPool:
    """
    Quản lý pool các numpy array buffers
    Tái sử dụng memory thay vì cấp phát mới mỗi frame
    """

    def __init__(self, num_buffers=5, buffer_shape=(2048, 1536, 3),
                 dtype=np.uint8):
        """
        Args:
            num_buffers: Số buffer trong pool
            buffer_shape: Shape của mỗi buffer
            dtype: Data type (uint8 cho ảnh)
        """
        self.buffer_shape = buffer_shape
        self.dtype = dtype
        self.num_buffers = num_buffers

        # Pre-allocate tất cả buffer ngay từ đầu
        self.buffers = [
            np.zeros(buffer_shape, dtype=dtype)
            for _ in range(num_buffers)
        ]

        # Track buffer nào available
        self.available_indices = list(range(num_buffers))
        self.in_use = [False] * num_buffers

        # Thread safety
        self.lock = threading.Lock()

        # Metrics
        self.total_requests = 0
        self.reuse_count = 0

    def get_buffer(self) -> Tuple[np.ndarray, int]:
        """
        Lấy buffer khả dụng từ pool

        Returns:
            (buffer_array, buffer_index)
        """
        with self.lock:
            self.total_requests += 1

            if self.available_indices:
                # Có buffer available
                idx = self.available_indices.pop()
                self.in_use[idx] = True
                self.reuse_count += 1
                return self.buffers[idx], idx
            else:
                # Không có buffer available → dùng lại oldest
                # (Trong production, nên log warning)
                idx = 0
                while self.in_use[idx]:
                    idx = (idx + 1) % self.num_buffers

                self.in_use[idx] = True
                return self.buffers[idx], idx

    def release_buffer(self, index: int):
        """
        Trả buffer về pool

        Args:
            index: Index của buffer được lấy từ get_buffer()
        """
        with self.lock:
            if 0 <= index < self.num_buffers:
                self.in_use[index] = False
                self.available_indices.append(index)

    def get_stats(self) -> dict:
        """Lấy thống kê sử dụng pool"""
        with self.lock:
            return {
                'total_requests': self.total_requests,
                'reuse_count': self.reuse_count,
                'reuse_rate': f"{100 * self.reuse_count / max(1, self.total_requests):.1f}%",
                'available': len(self.available_indices),
                'in_use': sum(self.in_use)
            }

    def clear(self):
        """Xóa tất cả buffers"""
        with self.lock:
            self.buffers = [
                np.zeros(self.buffer_shape, dtype=self.dtype)
                for _ in range(self.num_buffers)
            ]
            self.available_indices = list(range(self.num_buffers))
            self.in_use = [False] * self.num_buffers
```

**Checklist:**
- [ ] Tạo file `lib/BufferPool.py`
- [ ] Implement `get_buffer()` với thread-safe access
- [ ] Implement `release_buffer()` để trả buffer
- [ ] Implement `get_stats()` để monitor reuse
- [ ] Unit test BufferPool

---

### Task 2.2: Integrate vào Camera & Display
**Thời gian:** 1 ngày
**Files:**
- `lib/Camera_Program.py` (modify)
- `lib/Display.py` (modify)

**Mô tả:**
```python
# lib/Camera_Program.py - Thay đổi

from lib.BufferPool import BufferPool

class CameraController:
    def __init__(self):
        super().__init__()
        # ... existing code ...

        # Khởi tạo buffer pool
        self.buffer_pool = BufferPool(
            num_buffers=5,
            buffer_shape=(2048, 1536, 3),
            dtype=np.uint8
        )

        self.current_frame_idx = None

    def grab_image(self):
        """Capture frame từ camera với buffer reuse"""

        # Trả buffer cũ
        if self.current_frame_idx is not None:
            self.buffer_pool.release_buffer(self.current_frame_idx)

        # Lấy buffer mới từ pool
        buffer, buffer_idx = self.buffer_pool.get_buffer()
        self.current_frame_idx = buffer_idx

        try:
            # Grab image từ camera
            grab_result = self.cam.RetrieveResult(
                4000, pylon.TimeoutHandling_ThrowException
            )

            if grab_result.GrabSucceeded():
                # Copy data vào buffer có sẵn
                np.copyto(buffer, grab_result.GetArray())

                # Signal frame ready
                self.signal_frame_ready.emit(buffer, buffer_idx)

            grab_result.Release()

        except Exception as e:
            self.buffer_pool.release_buffer(buffer_idx)
            self.current_frame_idx = None
            raise


# lib/Display.py - Thay đổi

class DisplayManager:
    def __init__(self):
        super().__init__()
        # ... existing code ...

        # Display frame buffers (circular queue)
        self.display_buffers = [None, None, None]  # Keep 3 frame
        self.display_idx = 0

    def on_frame_received(self, frame, buffer_idx):
        """Callback khi camera có frame"""

        # Cập nhật display buffer
        old_buffer_idx = self.display_buffers[self.display_idx]
        self.display_buffers[self.display_idx] = buffer_idx
        self.display_idx = (self.display_idx + 1) % 3

        # Gửi đến image processor
        self.image_processor.on_new_frame(frame)
```

**Checklist:**
- [ ] Import BufferPool vào Camera_Program.py
- [ ] Khởi tạo buffer pool trong __init__()
- [ ] Modify grab_image() sử dụng buffer pool
- [ ] Implement circular queue cho display
- [ ] Test release_buffer() gọi đúng lúc
- [ ] Test memory không tăng sau 10 phút camera chạy

---

## ✅ Testing Plan (Phase 2)

```python
# tests/test_buffer_pool.py

import pytest
import numpy as np
from lib.BufferPool import BufferPool

class TestBufferPool:

    def test_buffer_reuse(self):
        """Test buffer được tái sử dụng"""
        pool = BufferPool(num_buffers=3)

        # Lấy & trả buffer 10 lần
        for _ in range(10):
            buf, idx = pool.get_buffer()
            assert buf is not None
            pool.release_buffer(idx)

        stats = pool.get_stats()
        # Reuse rate phải >80% (mỗi buffer dùng ~3 lần)
        reuse_rate = float(stats['reuse_rate'].rstrip('%'))
        assert reuse_rate > 80

    def test_no_memory_growth(self):
        """Test bộ nhớ không tăng sau nhiều lần sử dụng"""
        import psutil
        import time

        pool = BufferPool(num_buffers=5)

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Sử dụng pool 1000 lần
        for _ in range(1000):
            buf, idx = pool.get_buffer()
            # Simulate data copy
            buf[:] = np.random.randint(0, 256, buf.shape, dtype=np.uint8)
            pool.release_buffer(idx)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth phải <50MB (không leak)
        assert memory_growth < 50, f"Memory leak detected: {memory_growth}MB"

    def test_thread_safety(self):
        """Test thread safety"""
        pool = BufferPool(num_buffers=3)

        import threading

        results = []

        def worker():
            for _ in range(100):
                buf, idx = pool.get_buffer()
                results.append(idx)
                pool.release_buffer(idx)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Không được duplicate index
        assert len(results) == 500
        # Không được index out of range
        assert all(0 <= idx < 3 for idx in results)
```

**Checklist:**
- [ ] Run `pytest tests/test_buffer_pool.py`
- [ ] Verify reuse rate >80%
- [ ] Verify no memory leak (<50MB growth)
- [ ] Verify thread-safe operation
- [ ] Manual memory profiling với psutil
- [ ] Check memory stable ~450MB (before: 600MB)

---

## 📊 Success Metrics (Phase 2)

| Metric | Target | Current | Target Time |
|--------|--------|---------|------------|
| Memory idle | 450MB | 600MB | ↓ 25% |
| Memory after 1h | 470MB | 900MB | ↓ 48% |
| Buffer reuse rate | >80% | 0% | - |
| GC pause time | <10ms | 200-500ms | ↓ 95% |
| Memory leak | None | Yes 🔴 | Fixed ✅ |

---

# 🎯 PHASE 3: QUERY CACHING

## 📋 Chi Tiết Task

### Task 3.1: Tạo CacheLayer Class
**Thời gian:** 1 ngày
**Files:**
- `lib/CacheLayer.py` (new)

**Mô tả:**
```python
# lib/CacheLayer.py

import time
import threading
from typing import Any, Optional
from functools import wraps

class CacheEntry:
    """Một entry trong cache"""
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # seconds

    def is_expired(self) -> bool:
        """Check xem entry có expired không"""
        age = time.time() - self.created_at
        return age > self.ttl

    def get_value(self) -> Optional[Any]:
        """Lấy value nếu còn hạn"""
        if self.is_expired():
            return None
        return self.value


class CacheLayer:
    """Simple cache layer với TTL"""

    def __init__(self, default_ttl=60):
        """
        Args:
            default_ttl: Thời gian sống mặc định (giây)
        """
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Lấy value từ cache

        Returns:
            Value nếu cache hit và không expire, None nếu cache miss
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]
            value = entry.get_value()

            if value is None:
                # Expired → delete entry
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Lưu value vào cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (giây), dùng default_ttl nếu None
        """
        with self.lock:
            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl)

    def invalidate(self, key: str):
        """Xóa entry khỏi cache"""
        with self.lock:
            self.cache.pop(key, None)

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate tất cả entries match pattern

        Args:
            pattern: Pattern như "user_*" để xóa tất cả "user_*"
        """
        import fnmatch
        with self.lock:
            keys_to_delete = [
                k for k in self.cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_delete:
                del self.cache[key]

    def clear(self):
        """Xóa tất cả cache"""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> dict:
        """Lấy cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (100 * self.hits / total) if total > 0 else 0

            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}%",
                'entries': len(self.cache)
            }

    def cached(self, ttl: Optional[int] = None):
        """
        Decorator để cache function results

        Usage:
            @cache_layer.cached(ttl=60)
            def expensive_operation():
                return result
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Tạo cache key từ function name + args
                cache_key = f"{func.__name__}_{args}_{kwargs}"

                # Kiểm tra cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Cache miss → execute function
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result

            return wrapper
        return decorator


# Global cache instance
global_cache = CacheLayer(default_ttl=60)
```

**Checklist:**
- [ ] Tạo file `lib/CacheLayer.py`
- [ ] Implement CacheEntry với TTL logic
- [ ] Implement CacheLayer.get() / .set() / .invalidate()
- [ ] Implement @cached decorator
- [ ] Unit test CacheLayer

---

### Task 3.2: Integrate vào Authentication
**Thời gian:** 1 ngày
**Files:**
- `lib/Authentication.py` (modify)
- `lib/Database.py` (modify)

**Mô tả:**
```python
# lib/Authentication.py - Thay đổi

from lib.CacheLayer import global_cache

class AuthenticationManager:
    def __init__(self):
        self.cache = global_cache

    def login_user(self, username: str, password: str) -> Optional[dict]:
        """
        Login user với cache support

        Nếu user_list cache available → dùng cache (5ms)
        Nếu cache miss → query database (50-200ms)
        """

        # Kiểm tra cache trước
        user_list = self.cache.get("all_users")

        if user_list is None:
            # Cache miss → query database
            user_list = User.get_all()
            # Lưu vào cache 60 giây
            self.cache.set("all_users", user_list, ttl=60)

        # Tìm user (dùng cached data)
        for user in user_list:
            if user['username'] == username:
                if check_password(password, user['password_hash']):
                    return user

        return None

    def create_user(self, username: str, password: str, role: str = "operator"):
        """
        Tạo user + invalidate cache
        """

        # Tạo user trong DB
        User.insert({
            'username': username,
            'password_hash': hash_password(password),
            'role': role
        })

        # ⚠️ IMPORTANT: Invalidate cache vì dữ liệu thay đổi
        self.cache.invalidate("all_users")

        return True

    def update_user(self, user_id: int, **kwargs):
        """
        Update user + invalidate cache
        """

        User.update(user_id, kwargs)

        # Invalidate cache
        self.cache.invalidate("all_users")

        return True

    def delete_user(self, user_id: int):
        """
        Delete user + invalidate cache
        """

        User.delete(user_id)

        # Invalidate cache
        self.cache.invalidate("all_users")

        return True

    def get_cache_stats(self) -> dict:
        """Lấy cache statistics"""
        return self.cache.get_stats()


# lib/Database.py - Thay đổi (add cache logic)

class User(BaseModel):
    table_name = "users"
    allowed_columns = ["UserID", "UserName", "PasswordHash", "Role"]

    @classmethod
    def get_all_cached(cls, cache_layer=None):
        """
        Get all users từ cache nếu available
        """
        if cache_layer is None:
            from lib.CacheLayer import global_cache
            cache_layer = global_cache

        # Kiểm tra cache
        users = cache_layer.get("all_users")
        if users is not None:
            return users

        # Cache miss → query DB
        users = cls.get_all()
        cache_layer.set("all_users", users, ttl=60)
        return users
```

**Checklist:**
- [ ] Import CacheLayer vào Authentication.py
- [ ] Add cache logic vào login_user()
- [ ] Add cache invalidation vào create_user(), update_user(), delete_user()
- [ ] Add get_cache_stats() cho monitoring
- [ ] Unit test caching behavior
- [ ] Manual test login performance

---

## ✅ Testing Plan (Phase 3)

```python
# tests/test_cache_layer.py

import pytest
import time
from lib.CacheLayer import CacheLayer

class TestCacheLayer:

    def test_cache_hit(self):
        """Test cache hit"""
        cache = CacheLayer(default_ttl=60)

        # Set value
        cache.set("user_list", ["user1", "user2"])

        # Get value (cache hit)
        value = cache.get("user_list")
        assert value == ["user1", "user2"]

        # Check stats
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 0

    def test_cache_miss(self):
        """Test cache miss"""
        cache = CacheLayer()

        # Get non-existent key
        value = cache.get("non_existent")
        assert value is None

        # Check stats
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 1

    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        cache = CacheLayer()

        # Set value với 1 giây TTL
        cache.set("temp", "value", ttl=1)

        # Ngay lập tức: cache hit
        assert cache.get("temp") == "value"

        # Chờ 1.1 giây → expires
        time.sleep(1.1)
        assert cache.get("temp") is None

    def test_cache_invalidation(self):
        """Test manual cache invalidation"""
        cache = CacheLayer()

        cache.set("user_1", {"id": 1, "name": "Alice"})
        cache.set("user_2", {"id": 2, "name": "Bob"})

        # Invalidate user_1
        cache.invalidate("user_1")

        assert cache.get("user_1") is None
        assert cache.get("user_2") is not None

    def test_cached_decorator(self):
        """Test @cached decorator"""
        cache = CacheLayer()

        call_count = [0]

        @cache.cached(ttl=10)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        # First call → execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call → use cache (function not called)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not incremented

        # Different argument → execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count[0] == 2


# tests/test_authentication_cache.py

def test_login_performance_with_cache():
    """Test login latency improvement"""
    import time

    auth = AuthenticationManager()

    # First login → cache miss, query DB (~100-150ms)
    start = time.time()
    user = auth.login_user("operator1", "Oper@DRB2024!")
    first_login_time = time.time() - start

    # Second login → cache hit (~5ms)
    start = time.time()
    user = auth.login_user("operator1", "Oper@DRB2024!")
    second_login_time = time.time() - start

    # Second login phải nhanh hơn >20x
    assert second_login_time < first_login_time / 20

    # Check cache stats
    stats = auth.get_cache_stats()
    assert float(stats['hit_rate'].rstrip('%')) > 50
```

**Checklist:**
- [ ] Run `pytest tests/test_cache_layer.py`
- [ ] Verify cache hit/miss logic
- [ ] Verify TTL expiration
- [ ] Verify @cached decorator
- [ ] Test authentication performance
- [ ] Manual test: first login ~150ms, second login ~5ms
- [ ] Verify cache invalidation on create/update/delete

---

## 📊 Success Metrics (Phase 3)

| Metric | Target | Current | Target Time |
|--------|--------|---------|------------|
| Cache hit rate | >80% | 0% | - |
| Login latency | <50ms | 150ms | ↓ 67% |
| DB query/min | <2 | 30 | ↓ 93% |
| Query cache benefit | >100x | - | First query: 150ms → 5ms |

---

# 🎯 PHASE 4: ASYNC PLC I/O

## 📋 Chi Tiết Task

### Task 4.1: Refactor PLC.py với QTimer
**Thời gian:** 2 ngày
**Files:**
- `lib/PLC.py` (major refactor)

**Mô tả:**
```python
# lib/PLC.py - Refactor

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from concurrent.futures import ThreadPoolExecutor
import threading

class PLCController(QObject):
    """Quản lý PLC communication với async I/O"""

    # Signals (để communicate với UI thread)
    coils_updated = pyqtSignal(dict)  # Khi có dữ liệu mới
    registers_updated = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool)
    plc_error = pyqtSignal(str)

    def __init__(self, host='192.168.3.250', port=502, poll_interval=500):
        super().__init__()
        self.host = host
        self.port = port
        self.poll_interval = poll_interval

        self.plc_client = None
        self.is_connected = False

        # Thread pool để chạy I/O operations
        self.executor = ThreadPoolExecutor(max_workers=2)

        # QTimer để poll PLC (thay vì while loop + sleep)
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_plc_async)

        # Write timer (separate, vì write không cần frequent)
        self.write_queue = []
        self.write_lock = threading.Lock()
        self.write_timer = QTimer()
        self.write_timer.timeout.connect(self._process_write_queue)
        self.write_timer.setInterval(100)  # Process writes mỗi 100ms

        # Connection check timer
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_connection_health)
        self.health_check_timer.setInterval(5000)  # Check mỗi 5 giây

    def connect(self):
        """Kết nối tới PLC (async)"""
        self.executor.submit(self._connect_in_background)

    def _connect_in_background(self):
        """Kết nối PLC trong background thread"""
        try:
            from pymodbus.client import ModbusTcpClient

            self.plc_client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=10
            )

            result = self.plc_client.connect()

            if result:
                self.is_connected = True
                self.connection_status_changed.emit(True)

                # Bắt đầu polling
                self.poll_timer.start(self.poll_interval)
                self.write_timer.start()
                self.health_check_timer.start()

                print("✓ PLC connected")
            else:
                self.is_connected = False
                self.connection_status_changed.emit(False)
                self.plc_error.emit("Connection failed")

        except Exception as e:
            self.is_connected = False
            self.connection_status_changed.emit(False)
            self.plc_error.emit(f"Connection error: {e}")

    def disconnect(self):
        """Ngắt kết nối PLC"""
        self.poll_timer.stop()
        self.write_timer.stop()
        self.health_check_timer.stop()

        self.executor.submit(self._disconnect_in_background)

    def _disconnect_in_background(self):
        """Ngắt kết nối trong background"""
        try:
            if self.plc_client:
                self.plc_client.close()
            self.is_connected = False
            self.connection_status_changed.emit(False)
        except Exception as e:
            print(f"Disconnect error: {e}")

    def _poll_plc_async(self):
        """
        Poll PLC trong background (called by QTimer)
        Không block UI vì chạy trong thread pool
        """
        if not self.is_connected or not self.plc_client:
            return

        # Submit polling tasks
        self.executor.submit(self._read_coils_in_background)
        self.executor.submit(self._read_registers_in_background)

    def _read_coils_in_background(self):
        """Đọc coils trong background"""
        try:
            # Blocking I/O, nhưng không ảnh hưởng UI
            response = self.plc_client.read_coils(address=0, count=8)

            if not response.isError():
                # Gửi kết quả về main thread thông qua signal
                self.coils_updated.emit({
                    'coils': response.bits,
                    'timestamp': time.time(),
                    'status': 'ok'
                })
            else:
                self.plc_error.emit(f"Read coils failed: {response}")

        except Exception as e:
            self.plc_error.emit(f"Read error: {e}")

    def _read_registers_in_background(self):
        """Đọc registers trong background"""
        try:
            response = self.plc_client.read_holding_registers(address=0, count=10)

            if not response.isError():
                self.registers_updated.emit({
                    'registers': response.registers,
                    'timestamp': time.time(),
                    'status': 'ok'
                })
            else:
                self.plc_error.emit(f"Read registers failed: {response}")

        except Exception as e:
            self.plc_error.emit(f"Register read error: {e}")

    def write_coil_async(self, address: int, value: bool):
        """Ghi coil (async, queue-based)"""
        with self.write_lock:
            self.write_queue.append(('coil', address, value))

    def write_register_async(self, address: int, value: int):
        """Ghi register (async, queue-based)"""
        with self.write_lock:
            self.write_queue.append(('register', address, value))

    def _process_write_queue(self):
        """Process pending writes"""
        with self.write_lock:
            queue = self.write_queue.copy()
            self.write_queue.clear()

        for item in queue:
            if item[0] == 'coil':
                _, address, value = item
                self.executor.submit(
                    self._write_coil_in_background,
                    address, value
                )
            elif item[0] == 'register':
                _, address, value = item
                self.executor.submit(
                    self._write_register_in_background,
                    address, value
                )

    def _write_coil_in_background(self, address: int, value: bool):
        """Ghi coil trong background"""
        try:
            result = self.plc_client.write_coil(address=address, value=value)

            if result.isError():
                self.plc_error.emit(f"Write coil failed: {result}")
            else:
                self.coils_updated.emit({
                    'status': 'write_success',
                    'address': address,
                    'value': value
                })

        except Exception as e:
            self.plc_error.emit(f"Write error: {e}")

    def _write_register_in_background(self, address: int, value: int):
        """Ghi register trong background"""
        try:
            result = self.plc_client.write_register(address=address, value=value)

            if result.isError():
                self.plc_error.emit(f"Write register failed: {result}")
            else:
                self.registers_updated.emit({
                    'status': 'write_success',
                    'address': address,
                    'value': value
                })

        except Exception as e:
            self.plc_error.emit(f"Write error: {e}")

    def _check_connection_health(self):
        """Kiểm tra sức khỏe kết nối (health check)"""
        if not self.is_connected:
            return

        self.executor.submit(self._health_check_in_background)

    def _health_check_in_background(self):
        """Health check dalam background"""
        try:
            # Try read 1 coil để kiểm tra connection
            response = self.plc_client.read_coils(address=0, count=1)

            if response.isError():
                self.is_connected = False
                self.connection_status_changed.emit(False)
                self.plc_error.emit("Connection lost (health check failed)")

        except Exception as e:
            self.is_connected = False
            self.connection_status_changed.emit(False)
            self.plc_error.emit(f"Health check error: {e}")
```

**Checklist:**
- [ ] Refactor PLC.py remove while loop
- [ ] Add QTimer untuk polling
- [ ] Implement async read/write
- [ ] Add write queue system
- [ ] Add health check mechanism
- [ ] Connect signals tới Main_Screen
- [ ] Test no UI freeze during PLC operations

---

### Task 4.2: Integrate vào Main_Screen
**Thời gian:** 1 ngày
**Files:**
- `lib/Main_Screen.py` (modify)

**Mô tả:**
```python
# lib/Main_Screen.py - Thay đổi

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing code ...

        # Khởi tạo PLC controller
        self.plc = PLCController(
            host='192.168.3.250',
            port=502,
            poll_interval=500  # Poll mỗi 500ms
        )

        # Kết nối signals
        self.plc.coils_updated.connect(self.on_plc_coils_updated)
        self.plc.registers_updated.connect(self.on_plc_registers_updated)
        self.plc.connection_status_changed.connect(self.on_plc_connection_changed)
        self.plc.plc_error.connect(self.on_plc_error)

        # Kết nối PLC
        self.plc.connect()

    def on_plc_coils_updated(self, data):
        """Callback khi PLC coils được cập nhật"""
        print(f"✓ Coils updated: {data}")
        # Update UI
        self.update_plc_status_display(data)

    def on_plc_registers_updated(self, data):
        """Callback khi PLC registers được cập nhật"""
        print(f"✓ Registers updated: {data}")
        # Update UI
        self.update_plc_values_display(data)

    def on_plc_connection_changed(self, connected):
        """Callback khi PLC connection status thay đổi"""
        status = "Connected ✓" if connected else "Disconnected ✗"
        self.status_label.setText(f"PLC: {status}")

    def on_plc_error(self, error_msg):
        """Callback khi PLC lỗi"""
        print(f"✗ PLC Error: {error_msg}")
        QMessageBox.warning(self, "PLC Error", error_msg)

    def on_button_write_coil_clicked(self):
        """Khi user bấm button Write Coil"""
        address = self.input_address.value()
        value = self.input_value.isChecked()

        # Async write (không block UI)
        self.plc.write_coil_async(address, value)

        # UI vẫn responsive ngay lập tức
        self.status_label.setText(f"Writing to coil {address}...")

    def on_button_write_register_clicked(self):
        """Khi user bấm button Write Register"""
        address = self.input_address.value()
        value = self.input_value.value()

        # Async write
        self.plc.write_register_async(address, value)

        self.status_label.setText(f"Writing to register {address}...")

    def closeEvent(self, event):
        """Cleanup khi close app"""
        self.plc.disconnect()
        super().closeEvent(event)
```

**Checklist:**
- [ ] Import PLCController
- [ ] Khởi tạo PLC instance
- [ ] Kết nối PLC signals tới Main_Screen slots
- [ ] Implement on_plc_* callbacks
- [ ] Update write button handlers (async)
- [ ] Test: no UI freeze during PLC operations
- [ ] Test: multiple concurrent PLC reads
- [ ] Test: write operations complete async

---

## ✅ Testing Plan (Phase 4)

```python
# tests/test_plc_async.py

import pytest
from unittest.mock import Mock, patch
from PyQt5.QtCore import QTimer
from lib.PLC import PLCController

class TestPLCAsync:

    def test_no_ui_blocking(self):
        """Test PLC operations không block UI"""
        plc = PLCController()

        import time

        # Gọi polling operation
        start = time.time()
        plc._poll_plc_async()
        elapsed = time.time() - start

        # Poll operation phải return ngay (<10ms)
        assert elapsed < 0.01, "PLC polling blocking UI!"

    def test_async_write_queue(self):
        """Test write operations queued"""
        plc = PLCController()

        # Queue multiple writes
        for i in range(10):
            plc.write_coil_async(i, True)

        # Queue size should be 10
        assert len(plc.write_queue) == 10

    def test_signal_emission(self):
        """Test signals emitted correctly"""
        plc = PLCController()

        signal_received = []
        plc.coils_updated.connect(lambda data: signal_received.append(data))

        # Emit signal
        plc.coils_updated.emit({'coils': [1, 0, 1]})

        assert len(signal_received) == 1
        assert signal_received[0]['coils'] == [1, 0, 1]

    def test_connection_health_check(self):
        """Test health check mechanism"""
        plc = PLCController()

        # Health check should be async
        import time
        start = time.time()
        plc._check_connection_health()
        elapsed = time.time() - start

        # Should return immediately
        assert elapsed < 0.01
```

**Checklist:**
- [ ] Run `pytest tests/test_plc_async.py`
- [ ] Verify no UI blocking (<10ms)
- [ ] Verify write queue system
- [ ] Verify signals emission
- [ ] Manual test: click button while reading PLC
- [ ] Button should respond immediately (not wait 500ms)
- [ ] Verify multiple concurrent operations

---

## 📊 Success Metrics (Phase 4)

| Metric | Target | Current | Target Time |
|--------|--------|---------|------------|
| PLC read latency | 500ms async | 500ms blocking | ✓ UI free |
| UI freeze on PLC op | 0ms | 500ms | ↓ 100% |
| Click response | <10ms | 500ms | ↓ 98% |
| Concurrent ops | Multiple | Single | ✓ Full |
| User experience | Smooth | Lag 🔴 | Instant ✅ |

---

# 🎯 PHASE 5: REPLACE SLEEP → QTIMER

## 📋 Chi Tiết Task

**Thời gian:** 1-2 ngày
**Files:**
- `lib/Main_Screen.py` (modify)
- `lib/Display.py` (modify)
- `lib/PLC.py` (already done in Phase 4)

**Mô tả:**

```python
# ❌ BEFORE (Polling + Sleep)
# lib/Main_Screen.py

def update_ui_loop(self):
    while self.app_running:
        # Update display
        self.update_display()

        # Lấy latest result từ AI
        result = self.get_latest_ai_result()
        if result:
            self.display_ai_result(result)

        # Check status
        self.check_status()

        # Sleep (blocking, waste CPU)
        time.sleep(0.01)  # ← 100ms per iteration


# ✅ AFTER (QTimer)
# lib/Main_Screen.py

def init_timers(self):
    """Khởi tạo timers thay vì while loop + sleep"""

    # Display update timer (100ms)
    self.update_timer = QTimer()
    self.update_timer.timeout.connect(self._on_update_tick)
    self.update_timer.setInterval(100)
    self.update_timer.start()

    # Status check timer (500ms)
    self.status_timer = QTimer()
    self.status_timer.timeout.connect(self._check_status)
    self.status_timer.setInterval(500)
    self.status_timer.start()

def _on_update_tick(self):
    """Called by QTimer mỗi 100ms"""
    # Update display
    self.update_display()

    # Get latest AI result
    result = self.get_latest_ai_result()
    if result:
        self.display_ai_result(result)

def _check_status(self):
    """Called by QTimer mỗi 500ms"""
    # Check status
    self.check_status()

def closeEvent(self, event):
    """Stop timers khi close"""
    self.update_timer.stop()
    self.status_timer.stop()
    super().closeEvent(event)
```

**Checklist:**
- [ ] Identify all `time.sleep()` calls
- [ ] Create QTimer for each
- [ ] Replace sleep loops with timer callbacks
- [ ] Test: application responsive
- [ ] Verify: CPU usage down 10%
- [ ] Benchmark: no performance regression

---

# 🎯 PHASE 6: CODE REFACTORING (Optional)

## 📋 Chi Tiết Task

**Thời gian:** 1-2 tuần
**Files:**
- Split `Main_Screen.py` (1195 lines → too large)
- `lib/Main_Screen_UI.py` (UI layout)
- `lib/Main_Screen_Logic.py` (Business logic)
- `lib/Main_Screen_Handlers.py` (Event handlers)

**Chi tiết:** Chia nhỏ Main_Screen thành các module logic hơn.

---

# 📊 COMPLETE TIMELINE

```
┌─────────────────────────────────────────────────────────────┐
│           OPTIMIZATION IMPLEMENTATION TIMELINE              │
└─────────────────────────────────────────────────────────────┘

TUẦN 1 (Foundation)
├─ Mon-Tue: Frame Skipping
│  └─ Create ImageProcessor + integrate to Display
│  └─ Testing & benchmarking
├─ Wed-Thu: Buffer Pool
│  └─ Create BufferPool + integrate to Camera
│  └─ Memory profiling & leak testing
└─ Fri-Sat: Integration testing

TUẦN 2 (Database & Async)
├─ Mon-Tue: Query Caching
│  └─ Create CacheLayer + integrate to Authentication
│  └─ Cache invalidation testing
├─ Wed-Thu: Async PLC I/O
│  └─ Refactor PLC.py with QTimer
│  └─ Integration with Main_Screen
└─ Fri-Sat: Full system testing

TUẦN 3 (Cleanup)
├─ Mon-Tue: Replace Sleep → QTimer
│  └─ Identify all sleep calls
│  └─ Create timers, remove while loops
├─ Wed-Fri: Performance testing & profiling
│  └─ CPU usage analysis
│  └─ Memory stability test
└─ Sat: Buffer & bug fixes

TUẦN 4 (Major Refactor - Optional)
├─ Split Main_Screen.py
├─ Code cleanup & documentation
└─ Final validation & release

═══════════════════════════════════════════════════════════════

TOTAL TIME: 3-4 weeks
ESTIMATED BENEFIT: 30-80% performance improvement
HIGH PRIORITY: Phase 1-4 (Quick Wins)
OPTIONAL: Phase 5-6 (Nice to Have)
```

---

# ✅ VALIDATION CHECKLIST

## Trước Bắt Đầu Mỗi Phase

- [ ] Code review plan với team
- [ ] Create feature branch: `git checkout -b optimize/phase-X`
- [ ] Backup current code
- [ ] Document baseline metrics (CPU, memory, latency)

## Trong Quá Trình Thực Hiện

- [ ] Write unit tests trước code (TDD)
- [ ] Run tests after mỗi commit
- [ ] Benchmark metrics (CPU, memory, latency)
- [ ] Code review trước merge
- [ ] Document changes

## Sau Khi Complete

- [ ] All tests passing (unit + integration)
- [ ] Performance metrics improved
- [ ] No memory leaks detected
- [ ] UI responsive
- [ ] Code documented
- [ ] Create pull request
- [ ] Merge to main

---

# 📈 SUCCESS CRITERIA

### Tổng Cộng Sau 4 Tuần

| Metric | Target | Expected | Status |
|--------|--------|----------|--------|
| **Latency** | <200ms | 500ms → 150ms | ↓ 70% |
| **CPU** | <40% | 80% → 35% | ↓ 56% |
| **Memory** | 470MB stable | 600-900MB → 470MB | ↓ 48% |
| **UI Responsiveness** | Smooth 30fps | Lag → Smooth | ↑ 10x |
| **Database Queries** | <5ms cache | 150ms → 5ms | ↓ 97% |
| **PLC Read** | Async, 0 freeze | 500ms blocking → Async | ✓ Fixed |
| **Memory Leak** | None | Yes → No | ✓ Fixed |

---

# 🚀 START PHASE 1 NGAY!

Bạn sẵn sàng bắt đầu? 👇

**Hành động ngay:**
1. `git checkout -b optimize/phase-1-frame-skipping`
2. Create `lib/ImageProcessor.py`
3. Run tests để verify
4. Commit & push
5. Create PR

---

**Questions?** Liên hệ để discuss plan chi tiết!
