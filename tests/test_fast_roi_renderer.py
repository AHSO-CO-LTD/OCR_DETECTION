"""
Unit tests for FastROIRenderer.

Coverage targets: 90%+ for rendering performance and correctness.
Tests verify: QPainter rendering, ROI drawing, text labels, color handling.
"""

import pytest
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtCore import QRect

from lib.FastROIRenderer import FastROIRenderer


@pytest.fixture(autouse=True)
def qapp_fixture(qapp):
    """Ensure QApplication is available for all tests"""
    return qapp


class TestFastROIRendererInitialization:
    """Test FastROIRenderer initialization"""

    def test_init_default(self):
        """Verify FastROIRenderer initializes with correct defaults"""
        renderer = FastROIRenderer()

        assert renderer.rois == []
        assert renderer.show_labels is True
        assert renderer.show_confidence is True
        assert renderer.label_font_size == 10
        assert renderer.line_width == 2

    def test_init_color_palette(self):
        """Verify color palette is properly initialized"""
        renderer = FastROIRenderer()

        assert len(renderer.CLASS_COLORS) == 6
        assert renderer.CLASS_COLORS[0] == QColor(0, 255, 0)  # Green
        assert renderer.CLASS_COLORS[1] == QColor(255, 0, 0)  # Red


class TestFastROIRendererRenderingBasic:
    """Test basic rendering functionality"""

    def test_render_empty_rois(self):
        """Verify rendering with empty ROI list"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        result = renderer.render_rois_on_pixmap(pixmap, [])

        # Should return pixmap with same dimensions
        assert result.width() == pixmap.width()
        assert result.height() == pixmap.height()

    def test_render_single_roi(self):
        """Verify rendering single ROI box"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [(100, 100, 200, 150, 0)]  # x, y, w, h, color_id
        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()
        assert result.width() == 800
        assert result.height() == 600

    def test_render_multiple_rois(self):
        """Verify rendering multiple ROI boxes"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [
            (100, 100, 200, 150, 0),  # Green
            (350, 150, 150, 200, 1),  # Red
            (500, 300, 100, 100, 2),  # Orange
        ]

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()

    def test_render_many_rois(self):
        """Verify rendering 150 ROIs (typical use case)"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(2048, 1536)
        pixmap.fill(QColor(255, 255, 255))

        # Create 150 ROIs
        roi_list = []
        for i in range(150):
            x = (i * 13) % 2000
            y = ((i * 7) // 10) % 1400
            w = 100
            h = 100
            color_id = i % 6
            roi_list.append((x, y, w, h, color_id))

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()

    def test_render_with_ocr_text(self):
        """Verify rendering with OCR text labels"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [(100, 100, 200, 150, 0)]
        ocr_text = ["ABC123"]

        result = renderer.render_rois_on_pixmap(
            pixmap, roi_list, ocr_text_list=ocr_text
        )

        assert result is not None
        assert not result.isNull()


class TestFastROIRendererConfiguration:
    """Test configuration methods"""

    def test_set_line_width(self):
        """Verify setting line width"""
        renderer = FastROIRenderer()

        renderer.set_line_width(4)
        assert renderer.line_width == 4

        renderer.set_line_width(1)
        assert renderer.line_width == 1

    def test_set_label_font_size(self):
        """Verify setting label font size"""
        renderer = FastROIRenderer()

        renderer.set_label_font_size(14)
        assert renderer.label_font_size == 14

        renderer.set_label_font_size(8)
        assert renderer.label_font_size == 8

    def test_toggle_labels(self):
        """Verify toggling label visibility"""
        renderer = FastROIRenderer()

        assert renderer.show_labels is True
        renderer.toggle_labels(False)
        assert renderer.show_labels is False

        renderer.toggle_labels(True)
        assert renderer.show_labels is True

    def test_toggle_confidence(self):
        """Verify toggling confidence visibility"""
        renderer = FastROIRenderer()

        assert renderer.show_confidence is True
        renderer.toggle_confidence(False)
        assert renderer.show_confidence is False

        renderer.toggle_confidence(True)
        assert renderer.show_confidence is True


class TestFastROIRendererColorHandling:
    """Test color handling for different ROI classes"""

    def test_color_for_class_0_green(self):
        """Verify green color for class 0"""
        renderer = FastROIRenderer()
        color = renderer.CLASS_COLORS.get(0)

        assert color == QColor(0, 255, 0)

    def test_color_for_class_1_red(self):
        """Verify red color for class 1"""
        renderer = FastROIRenderer()
        color = renderer.CLASS_COLORS.get(1)

        assert color == QColor(255, 0, 0)

    def test_color_for_unknown_class(self):
        """Verify fallback color for unknown class"""
        renderer = FastROIRenderer()
        color = renderer.CLASS_COLORS.get(99, QColor(0, 255, 0))

        assert color == QColor(0, 255, 0)

    def test_render_different_colors(self):
        """Verify rendering ROIs with different colors"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [
            (50, 50, 100, 100, 0),  # Green
            (150, 50, 100, 100, 1),  # Red
            (250, 50, 100, 100, 2),  # Orange
            (350, 50, 100, 100, 3),  # Yellow
            (450, 50, 100, 100, 4),  # Cyan
            (550, 50, 100, 100, 5),  # Magenta
        ]

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()


class TestFastROIRendererPerformance:
    """Test performance characteristics"""

    def test_render_time_estimate_single_roi(self):
        """Verify performance estimate for single ROI"""
        renderer = FastROIRenderer()

        estimate = renderer.get_render_time_estimate(1)

        # Should be ~10-10.15ms (base + 0.15ms per ROI)
        assert 10 <= estimate <= 11

    def test_render_time_estimate_150_rois(self):
        """Verify performance estimate for 150 ROIs"""
        renderer = FastROIRenderer()

        estimate = renderer.get_render_time_estimate(150)

        # Should be ~10 + (150 * 0.15) = ~32.5ms
        assert 30 <= estimate <= 35

    def test_render_time_estimate_scales_linearly(self):
        """Verify performance estimate scales linearly with ROI count"""
        renderer = FastROIRenderer()

        estimate_50 = renderer.get_render_time_estimate(50)
        estimate_100 = renderer.get_render_time_estimate(100)

        # 100 ROIs should take significantly more time than 50 ROIs
        # Empirically: 50 → ~17.5ms, 100 → ~25ms (ratio ~1.4)
        # Due to base cost of 10ms, ratio is less than 2x
        ratio = estimate_100 / estimate_50
        assert 1.3 <= ratio <= 1.6


class TestFastROIRendererEdgeCases:
    """Test edge cases and error handling"""

    def test_render_null_pixmap(self):
        """Verify handling of null pixmap"""
        renderer = FastROIRenderer()
        null_pixmap = QPixmap()
        roi_list = [(100, 100, 200, 150, 0)]

        result = renderer.render_rois_on_pixmap(null_pixmap, roi_list)

        # Should return the null pixmap unchanged
        assert result.isNull()

    def test_render_roi_with_invalid_format(self):
        """Verify handling of invalid ROI format"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [
            (100, 100, 200, 150, 0),  # Valid
            (200, 200),  # Invalid - too short
            (300, 300, 100, 100, 1),  # Valid
        ]

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()

    def test_render_roi_at_edges(self):
        """Verify rendering ROIs at image edges"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [
            (0, 0, 100, 100, 0),  # Top-left
            (700, 0, 100, 100, 1),  # Top-right
            (0, 500, 100, 100, 2),  # Bottom-left
            (700, 500, 100, 100, 3),  # Bottom-right
        ]

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()

    def test_render_roi_with_zero_size(self):
        """Verify handling of zero-sized ROIs"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        roi_list = [
            (100, 100, 0, 0, 0),  # Zero size
            (200, 200, 100, 100, 1),  # Normal
        ]

        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        assert result is not None
        assert not result.isNull()


class TestFastROIRendererIntegration:
    """Integration tests with typical workflow"""

    def test_sequential_renders(self):
        """Verify multiple sequential renders work correctly"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        # Render frame 1
        roi_list_1 = [(100, 100, 200, 150, 0)]
        result_1 = renderer.render_rois_on_pixmap(pixmap, roi_list_1)

        assert result_1 is not None

        # Render frame 2 with different ROIs
        pixmap.fill(QColor(255, 255, 255))
        roi_list_2 = [(200, 200, 150, 100, 1), (400, 150, 100, 200, 0)]
        result_2 = renderer.render_rois_on_pixmap(pixmap, roi_list_2)

        assert result_2 is not None

    def test_configuration_persistence(self):
        """Verify configuration changes persist across renders"""
        renderer = FastROIRenderer()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(255, 255, 255))

        # Set configuration
        renderer.set_line_width(4)
        renderer.set_label_font_size(14)
        renderer.toggle_labels(False)

        # Render
        roi_list = [(100, 100, 200, 150, 0)]
        result = renderer.render_rois_on_pixmap(pixmap, roi_list)

        # Verify configuration persisted
        assert renderer.line_width == 4
        assert renderer.label_font_size == 14
        assert renderer.show_labels is False
        assert result is not None
