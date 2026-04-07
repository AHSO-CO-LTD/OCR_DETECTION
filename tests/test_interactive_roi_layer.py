"""
Unit tests for InteractiveROILayer.

Coverage targets: 90%+ for interactive ROI selection and editing.
Tests verify: ROI display, selection signals, movement, reset, deletion.
"""

import pytest
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from lib.InteractiveROILayer import InteractiveROILayer


@pytest.fixture(autouse=True)
def qapp_fixture(qapp):
    """Ensure QApplication is available for all tests"""
    return qapp


class TestInteractiveROILayerInitialization:
    """Test InteractiveROILayer initialization"""

    def test_init_default(self):
        """Verify InteractiveROILayer initializes with correct defaults"""
        layer = InteractiveROILayer()

        assert layer.selected_roi_index is None
        assert layer.selected_item is None
        assert layer.original_roi is None
        assert layer.highlight_color == QColor(255, 255, 0)  # Yellow
        assert layer.highlight_width == 3
        assert layer.dash_style == Qt.DashLine

    def test_init_signal_existence(self):
        """Verify all signals are properly defined"""
        layer = InteractiveROILayer()

        # Check signals exist
        assert hasattr(layer, 'roi_selected')
        assert hasattr(layer, 'roi_moved')
        assert hasattr(layer, 'roi_resized')
        assert hasattr(layer, 'roi_deleted')


class TestInteractiveROILayerShowROI:
    """Test showing/displaying ROI for editing"""

    def test_show_single_roi(self):
        """Verify showing a single ROI"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        assert layer.selected_roi_index == 0
        assert layer.selected_item is not None
        assert layer.original_roi == (100, 100, 200, 150)

    def test_show_roi_clears_previous(self):
        """Verify showing new ROI clears previous"""
        layer = InteractiveROILayer()

        layer.show_roi(0, (100, 100, 200, 150, 0))
        initial_item = layer.selected_item

        layer.show_roi(1, (200, 200, 150, 100, 1))
        new_item = layer.selected_item

        # Item should be different
        assert initial_item != new_item
        assert layer.selected_roi_index == 1

    def test_show_roi_stores_original(self):
        """Verify original ROI bounds are stored"""
        layer = InteractiveROILayer()
        roi_data = (150, 150, 250, 200, 0)

        layer.show_roi(5, roi_data)

        assert layer.original_roi == (150, 150, 250, 200)

    def test_show_roi_with_list_format(self):
        """Verify showing ROI with list format instead of tuple"""
        layer = InteractiveROILayer()
        roi_data = [100, 100, 200, 150, 0]

        layer.show_roi(0, roi_data)

        assert layer.selected_roi_index == 0
        assert layer.original_roi == (100, 100, 200, 150)

    def test_show_roi_with_invalid_format(self):
        """Verify handling of invalid ROI format"""
        layer = InteractiveROILayer()
        roi_data = (100, 100)  # Too short

        layer.show_roi(0, roi_data)

        # Should be cleared since invalid
        assert layer.selected_item is None

    def test_show_roi_item_is_selectable(self):
        """Verify shown ROI item has selection enabled"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        assert layer.selected_item.flags() & layer.selected_item.ItemIsSelectable
        assert layer.selected_item.flags() & layer.selected_item.ItemIsMovable


class TestInteractiveROILayerGetBounds:
    """Test retrieving ROI bounds after editing"""

    def test_get_roi_bounds_initial(self):
        """Verify getting bounds immediately after show_roi"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)
        bounds = layer.get_roi_bounds()

        # QGraphicsRectItem stores position in item.pos() and rect dimensions separately
        # So bounds should match the original ROI data
        assert bounds is not None
        assert bounds[0] == 100  # x
        assert bounds[1] == 100  # y
        assert bounds[2] == 200  # w
        assert bounds[3] == 150  # h

    def test_get_roi_bounds_no_selection(self):
        """Verify get_roi_bounds returns None when nothing selected"""
        layer = InteractiveROILayer()

        bounds = layer.get_roi_bounds()

        assert bounds is None

    def test_get_roi_bounds_after_move(self):
        """Verify bounds reflect movement"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        # Simulate move by setting new position
        if layer.selected_item:
            layer.selected_item.setX(150)
            layer.selected_item.setY(150)

        bounds = layer.get_roi_bounds()

        assert bounds[0] == 150  # x
        assert bounds[1] == 150  # y
        assert bounds[2] == 200  # w (unchanged)
        assert bounds[3] == 150  # h (unchanged)


class TestInteractiveROILayerReset:
    """Test resetting ROI to original bounds"""

    def test_reset_roi_to_original(self):
        """Verify reset returns ROI to original bounds"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        # Move item
        if layer.selected_item:
            layer.selected_item.setX(200)
            layer.selected_item.setY(200)

        # Reset
        layer.reset_roi()

        bounds = layer.get_roi_bounds()
        assert bounds == (100, 100, 200, 150)

    def test_reset_roi_no_selection(self):
        """Verify reset does nothing when no ROI selected"""
        layer = InteractiveROILayer()

        # Should not raise exception
        layer.reset_roi()
        assert layer.selected_item is None

    def test_reset_preserves_original(self):
        """Verify original_roi is not modified by reset"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)
        original = layer.original_roi

        # Move and reset
        if layer.selected_item:
            layer.selected_item.setX(300)

        layer.reset_roi()

        # Original should be unchanged
        assert layer.original_roi == original


class TestInteractiveROILayerDelete:
    """Test deleting ROI"""

    def test_delete_roi_emits_signal(self):
        """Verify delete_roi emits deletion signal"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        signal_emitted = []

        def on_deleted(roi_id):
            signal_emitted.append(roi_id)

        layer.roi_deleted.connect(on_deleted)

        layer.delete_roi()

        assert len(signal_emitted) == 1
        assert signal_emitted[0] == 0

    def test_delete_roi_clears_selection(self):
        """Verify delete_roi clears the selection"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)
        assert layer.selected_item is not None

        layer.delete_roi()

        assert layer.selected_item is None
        assert layer.selected_roi_index is None

    def test_delete_roi_no_selection(self):
        """Verify delete_roi does nothing when no ROI selected"""
        layer = InteractiveROILayer()

        signal_emitted = []
        layer.roi_deleted.connect(lambda x: signal_emitted.append(x))

        layer.delete_roi()

        assert len(signal_emitted) == 0


class TestInteractiveROILayerClearSelection:
    """Test clearing selection"""

    def test_clear_selection_removes_item(self):
        """Verify clear_selection removes the item"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)
        assert layer.selected_item is not None

        layer.clear_selection()

        assert layer.selected_item is None
        assert layer.selected_roi_index is None
        assert layer.original_roi is None

    def test_clear_selection_when_empty(self):
        """Verify clear_selection works when nothing selected"""
        layer = InteractiveROILayer()

        # Should not raise exception
        layer.clear_selection()

        assert layer.selected_item is None


class TestInteractiveROILayerHighlighting:
    """Test highlight color management"""

    def test_set_highlight_color(self):
        """Verify setting highlight color"""
        layer = InteractiveROILayer()

        new_color = QColor(0, 255, 0)
        layer.set_highlight_color(new_color)

        assert layer.highlight_color == new_color

    def test_highlight_color_changes_pen(self):
        """Verify highlight color affects pen of selected item"""
        layer = InteractiveROILayer()
        roi_data = (100, 100, 200, 150, 0)

        layer.show_roi(0, roi_data)

        new_color = QColor(0, 255, 0)
        layer.set_highlight_color(new_color)

        # The pen should have the new color
        assert layer.selected_item.pen().color() == new_color


class TestInteractiveROILayerGetSelectedIndex:
    """Test getting selected ROI index"""

    def test_get_selected_roi_index(self):
        """Verify getting selected ROI index"""
        layer = InteractiveROILayer()

        layer.show_roi(5, (100, 100, 200, 150, 0))

        assert layer.get_selected_roi_index() == 5

    def test_get_selected_roi_index_none(self):
        """Verify getting index when nothing selected"""
        layer = InteractiveROILayer()

        assert layer.get_selected_roi_index() is None


class TestInteractiveROILayerSignals:
    """Test signal emission"""

    def test_roi_selected_signal(self):
        """Verify roi_selected signal is emitted"""
        layer = InteractiveROILayer()

        signal_received = []

        def on_selected(roi_id):
            signal_received.append(roi_id)

        layer.roi_selected.connect(on_selected)

        layer.show_roi(3, (100, 100, 200, 150, 0))

        assert len(signal_received) == 1
        assert signal_received[0] == 3

    def test_multiple_roi_selections(self):
        """Verify selecting multiple ROIs in sequence"""
        layer = InteractiveROILayer()

        signal_received = []
        layer.roi_selected.connect(lambda x: signal_received.append(x))

        layer.show_roi(0, (100, 100, 200, 150, 0))
        layer.show_roi(1, (200, 200, 150, 100, 1))
        layer.show_roi(2, (300, 300, 100, 200, 0))

        assert signal_received == [0, 1, 2]


class TestInteractiveROILayerIntegration:
    """Integration tests"""

    def test_complete_workflow(self):
        """Test complete workflow: show, move, reset, delete"""
        layer = InteractiveROILayer()

        # Show ROI
        roi_data = (100, 100, 200, 150, 0)
        layer.show_roi(0, roi_data)
        assert layer.selected_roi_index == 0

        # Get initial bounds
        bounds = layer.get_roi_bounds()
        assert bounds is not None
        assert bounds[0] == 100  # x
        assert bounds[1] == 100  # y
        assert bounds[2] == 200  # w
        assert bounds[3] == 150  # h

        # Reset (no-op if not moved)
        layer.reset_roi()
        assert layer.get_roi_bounds() == (100, 100, 200, 150)

        # Select different ROI
        layer.show_roi(1, (200, 200, 150, 100, 1))
        assert layer.selected_roi_index == 1

        # Delete
        deletion_list = []
        layer.roi_deleted.connect(lambda x: deletion_list.append(x))
        layer.delete_roi()

        assert layer.selected_item is None
        assert len(deletion_list) == 1
        assert deletion_list[0] == 1

    def test_multiple_roi_edits(self):
        """Test editing multiple ROIs in sequence"""
        layer = InteractiveROILayer()

        roi_list = [
            (100, 100, 200, 150, 0),
            (200, 200, 150, 100, 1),
            (300, 300, 100, 200, 2),
        ]

        for idx, roi_data in enumerate(roi_list):
            layer.show_roi(idx, roi_data)
            assert layer.get_selected_roi_index() == idx

            bounds = layer.get_roi_bounds()
            assert bounds is not None
            # Verify all components match
            assert bounds[0] == roi_data[0]  # x
            assert bounds[1] == roi_data[1]  # y
            assert bounds[2] == roi_data[2]  # w
            assert bounds[3] == roi_data[3]  # h

        # Clear at end
        layer.clear_selection()
        assert layer.get_selected_roi_index() is None
