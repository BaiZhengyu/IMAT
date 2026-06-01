<img width="1518" height="920" alt="image" src="https://github.com/user-attachments/assets/ca01182b-fc44-4ec3-9404-1cc408a51810" />One of the most painful moments in industrial vision or OpenCV development is having to measure pixels with a screenshot tool or repeatedly modify parameters, run the code, and check the results just to extract a Region of Interest (ROI).

To completely eliminate the need for "eye-based distance measurement," I developed a lightweight image annotation tool based on PySide6. 
It automatically handles image scaling, preserves original pixel coordinates, and supports rectangular and polygon annotations. 
Most importantly, the obtained coordinates can be directly fed into AI tools (such as Gemini or ChatGPT) to generate OpenCV cropping code with a single click, instantly boosting productivity!




python：


import sys
import os
import math
import cv2  # 引入 OpenCV 库
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QScrollArea, QMessageBox, QSizePolicy,
    QTextBrowser, QSpinBox
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QPolygon, QCursor, QImage
from PySide6.QtCore import Qt, QPoint, QRectF, QEvent, QSize


class ImageWidget(QWidget):  # 改变继承自 QWidget，完全自定义绘制
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.cv_image = None  # 存储 OpenCV 矩阵 (BGR)
        self.original_size = QSize(0, 0)
        self.scale_factor = 1.0

        self.scroll_area = None

        self.current_tool = "None"
        self.annotations = []
        self.current_polygon = []
        self.temp_rect_start = None
        self.temp_rect_end = None

        self.selected_index = None
        self.drag_start_point = None
        self.drag_start_coords = None

        self.grid_rows = 5
        self.grid_cols = 16

        self.setMouseTracking(True)

    def load_image(self, file_path):
        """ 使用 OpenCV 读取超大图像 """
        # 使用 cv2.IMREAD_UNCHANGED 保持原通道格式，避免 QPixmap 的尺寸限制
        self.cv_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if self.cv_image is None:
            return False

        h, w = self.cv_image.shape[:2]
        self.original_size = QSize(w, h)
        self.fit_to_window()
        self.clear_annotations()
        return True

    def fit_to_window(self):
        if self.cv_image is None or not self.scroll_area:
            return

        view_w = self.scroll_area.viewport().width()
        view_h = self.scroll_area.viewport().height()
        orig_w = self.original_size.width()
        orig_h = self.original_size.height()

        if orig_w == 0 or orig_h == 0: return

        scale_w = view_w / orig_w
        scale_h = view_h / orig_h

        self.scale_factor = min(scale_w, scale_h) * 0.98
        self._apply_scale()

    def zoom(self, factor, focus_point=None):
        if self.cv_image is None: return

        old_scale = self.scale_factor
        new_scale = old_scale * factor
        new_scale = max(0.005, min(new_scale, 50.0))  # 允许缩小到更小以看清全貌
        if new_scale == old_scale: return

        if focus_point is None and self.scroll_area:
            viewport = self.scroll_area.viewport()
            focus_point = QPoint(
                int(self.scroll_area.horizontalScrollBar().value() + viewport.width() / 2),
                int(self.scroll_area.verticalScrollBar().value() + viewport.height() / 2)
            )

        self.scale_factor = new_scale
        self._apply_scale()

        if focus_point and self.scroll_area:
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()
            shift_x = focus_point.x() * (new_scale / old_scale) - focus_point.x()
            shift_y = focus_point.y() * (new_scale / old_scale) - focus_point.y()
            h_bar.setValue(int(h_bar.value() + shift_x))
            v_bar.setValue(int(v_bar.value() + shift_y))

    def _apply_scale(self):
        new_w = int(self.original_size.width() * self.scale_factor)
        new_h = int(self.original_size.height() * self.scale_factor)
        # 设置 Widget 的虚拟大小，以便触发 QScrollArea 的滚动条
        self.setFixedSize(new_w, new_h)
        self.update()

    def wheelEvent(self, event):
        if self.cv_image is None: return
        angle = event.angleDelta().y()
        if angle > 0:
            self.zoom(1.15, event.position().toPoint())
        elif angle < 0:
            self.zoom(1 / 1.15, event.position().toPoint())
        event.accept()

    def set_tool(self, tool_name):
        if self.current_tool == "Polygon" and self.current_polygon:
            self.complete_polygon()

        self.current_tool = tool_name
        self.current_polygon = []
        self.temp_rect_start = None
        self.temp_rect_end = None
        self.selected_index = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def clear_annotations(self):
        self.annotations = []
        self.current_polygon = []
        self.temp_rect_start = None
        self.temp_rect_end = None
        self.selected_index = None
        self.update()

    def delete_selected(self):
        if self.selected_index is not None:
            del self.annotations[self.selected_index]
            self.selected_index = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
            self.window().update_tool_buttons()

    def get_original_coords(self, x_screen, y_screen):
        if not self.original_size: return None
        x_orig = x_screen / self.scale_factor
        y_orig = y_screen / self.scale_factor
        return x_orig, y_orig

    def get_screen_point(self, x_orig, y_orig):
        x_screen = int(x_orig * self.scale_factor)
        y_screen = int(y_orig * self.scale_factor)
        return QPoint(x_screen, y_screen)

    def _is_point_in_annotation(self, x_orig, y_orig, ann):
        if ann['type'] in ['Rect', 'Grid']:
            x1, y1, x2, y2 = ann['coords']
            return min(x1, x2) <= x_orig <= max(x1, x2) and min(y1, y2) <= y_orig <= max(y1, y2)
        elif ann['type'] == 'Polygon':
            xs = [p[0] for p in ann['coords']]
            ys = [p[1] for p in ann['coords']]
            return min(xs) <= x_orig <= max(xs) and min(ys) <= y_orig <= max(ys)
        elif ann['type'] == 'Line':
            x1, y1, x2, y2 = ann['coords']
            px, py = x2 - x1, y2 - y1
            norm = px * px + py * py
            if norm == 0:
                dist = math.hypot(x_orig - x1, y_orig - y1)
            else:
                u = ((x_orig - x1) * px + (y_orig - y1) * py) / float(norm)
                u = max(0.0, min(1.0, u))
                dist = math.hypot(x_orig - (x1 + u * px), y_orig - (y1 + u * py))
            return dist < (5 / self.scale_factor)
        return False

    def mousePressEvent(self, event):
        if self.cv_image is None or event.button() != Qt.LeftButton:
            return

        if event.type() == QEvent.Type.MouseButtonDblClick and len(self.current_polygon) >= 1:
            self.complete_polygon()
            return

        point = event.position().toPoint()
        orig_coords = self.get_original_coords(point.x(), point.y())
        if orig_coords is None: return
        x_orig, y_orig = orig_coords

        if self.current_tool == "Select":
            self.selected_index = None
            for i in range(len(self.annotations) - 1, -1, -1):
                if self._is_point_in_annotation(x_orig, y_orig, self.annotations[i]):
                    self.selected_index = i
                    self.drag_start_point = (x_orig, y_orig)
                    self.drag_start_coords = list(self.annotations[i]['coords'])
                    break
            self.window().update_tool_buttons()
            self.update()
            return

        if self.current_tool in ["Rect", "Grid", "Line"]:
            self.temp_rect_start = point
            self.temp_rect_end = point

        elif self.current_tool == "Polygon":
            x_orig = max(0, min(int(x_orig), self.original_size.width()))
            y_orig = max(0, min(int(y_orig), self.original_size.height()))
            self.current_polygon.append((x_orig, y_orig))
            self.update()

    def mouseMoveEvent(self, event):
        if self.cv_image is None: return

        point = event.position().toPoint()
        orig_coords = self.get_original_coords(point.x(), point.y())
        if orig_coords is None: return
        x_orig, y_orig = orig_coords

        if self.current_tool == "Select":
            if self.selected_index is not None and self.drag_start_point:
                dx = x_orig - self.drag_start_point[0]
                dy = y_orig - self.drag_start_point[1]
                ann = self.annotations[self.selected_index]

                if ann['type'] in ['Rect', 'Grid', 'Line']:
                    orig_c = self.drag_start_coords
                    ann['coords'] = [orig_c[0] + dx, orig_c[1] + dy, orig_c[2] + dx, orig_c[3] + dy]
                elif ann['type'] == 'Polygon':
                    orig_c = self.drag_start_coords
                    ann['coords'] = [(px + dx, py + dy) for px, py in orig_c]
                self.update()
            else:
                hovered = any(self._is_point_in_annotation(x_orig, y_orig, ann) for ann in self.annotations)
                self.setCursor(Qt.SizeAllCursor if hovered else Qt.ArrowCursor)
            return

        if self.current_tool in ["Rect", "Grid", "Line"] and self.temp_rect_start:
            self.temp_rect_end = point
            self.update()
        elif self.current_tool == "Polygon" and self.current_polygon:
            self.update()

    def mouseReleaseEvent(self, event):
        if self.cv_image is None or event.button() != Qt.LeftButton:
            return

        if self.current_tool == "Select":
            self.drag_start_point = None
            return

        if self.current_tool in ["Rect", "Grid", "Line"] and self.temp_rect_start:
            if self.temp_rect_start == self.temp_rect_end:
                self.temp_rect_start = None
                self.temp_rect_end = None
                return

            x1_orig, y1_orig = self.get_original_coords(self.temp_rect_start.x(), self.temp_rect_start.y())
            x2_orig, y2_orig = self.get_original_coords(self.temp_rect_end.x(), self.temp_rect_end.y())

            x1_orig = max(0, min(int(x1_orig), self.original_size.width()))
            y1_orig = max(0, min(int(y1_orig), self.original_size.height()))
            x2_orig = max(0, min(int(x2_orig), self.original_size.width()))
            y2_orig = max(0, min(int(y2_orig), self.original_size.height()))

            if self.current_tool == "Line":
                self.annotations.append({'type': 'Line', 'coords': [x1_orig, y1_orig, x2_orig, y2_orig]})
            else:
                coords = [min(x1_orig, x2_orig), min(y1_orig, y2_orig), max(x1_orig, x2_orig), max(y1_orig, y2_orig)]
                if self.current_tool == "Grid":
                    self.annotations.append(
                        {'type': 'Grid', 'coords': coords, 'rows': self.grid_rows, 'cols': self.grid_cols})
                else:
                    self.annotations.append({'type': 'Rect', 'coords': coords})

            self.temp_rect_start = None
            self.temp_rect_end = None
            self.update()

    def complete_polygon(self):
        if len(self.current_polygon) >= 3:
            self.annotations.append({'type': 'Polygon', 'coords': self.current_polygon})
        self.current_polygon = []
        self.update()
        self.current_tool = "None"
        self.window().update_tool_buttons()

    # ==================== 核心优化：动态视口渲染 ====================
    def paintEvent(self, event):
        if self.cv_image is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 计算当前的视口视窗区域（相对于 ImageWidget）
        viewport_rect = self.scroll_area.viewport().rect()
        visible_pos = self.scroll_area.widget().mapFrom(self.scroll_area.viewport(), viewport_rect.topLeft())

        # 得到当前能看到的屏幕逻辑矩形区域
        sc_x1, sc_y1 = max(0, visible_pos.x()), max(0, visible_pos.y())
        sc_x2 = min(self.width(), sc_x1 + viewport_rect.width())
        sc_y2 = min(self.height(), sc_y1 + viewport_rect.height())

        # 2. 将屏幕矩形反向映射到 OpenCV 图像的原图絕對像素坐标上
        orig_x1, orig_y1 = int(sc_x1 / self.scale_factor), int(sc_y1 / self.scale_factor)
        orig_x2, orig_y2 = int(sc_x2 / self.scale_factor), int(sc_y2 / self.scale_factor)

        # 边界安全限制
        orig_x1, orig_x2 = max(0, orig_x1), min(self.original_size.width(), orig_x2)
        orig_y1, orig_y2 = max(0, orig_y1), min(self.original_size.height(), orig_y2)

        # 3. 只有合法的局部切片才执行切片渲染
        if (orig_x2 > orig_x1) and (orig_y2 > orig_y1):
            # 切片裁剪 (仅取出当前视口对应大小的代码像素)
            tile = self.cv_image[orig_y1:orig_y2, orig_x1:orig_x2]

            # 计算切片缩放后的屏幕实际像素高宽
            tile_sc_w = int((orig_x2 - orig_x1) * self.scale_factor)
            tile_sc_h = int((orig_y2 - orig_y1) * self.scale_factor)

            if tile_sc_w > 0 and tile_sc_h > 0:
                # 缩放切片
                tile_resized = cv2.resize(tile, (tile_sc_w, tile_sc_h), interpolation=cv2.INTER_LINEAR)

                # 色彩转换 BGR/BGRA -> RGB (针对 Qt 渲染)
                if len(tile_resized.shape) == 3:
                    if tile_resized.shape[2] == 4:
                        tile_rgb = cv2.cvtColor(tile_resized, cv2.COLOR_BGRA2RGBA)
                        fmt = QImage.Format_RGBA8888
                    else:
                        tile_rgb = cv2.cvtColor(tile_resized, cv2.COLOR_BGR2RGB)
                        fmt = QImage.Format_RGB888
                else:
                    tile_rgb = tile_resized
                    fmt = QImage.Format_Grayscale8

                # 构造 QImage 贴图并画到对应的视口坐标上
                bytes_per_line = tile_rgb.strides[0]
                q_img = QImage(tile_rgb.data, tile_sc_w, tile_sc_h, bytes_per_line, fmt)

                # 重新映射回真实的屏幕渲染起始点
                render_x1 = int(orig_x1 * self.scale_factor)
                render_y1 = int(orig_y1 * self.scale_factor)
                painter.drawImage(render_x1, render_y1, q_img)

        # 4. 绘制原有的标注信息（保持你原来的坐标绘制体系不变）
        for i, ann in enumerate(self.annotations):
            is_selected = (self.current_tool == "Select" and i == self.selected_index)

            if ann['type'] == 'Rect':
                x1, y1, x2, y2 = ann['coords']
                p1, p2 = self.get_screen_point(x1, y1), self.get_screen_point(x2, y2)
                painter.setPen(QPen(QColor(255, 100, 0), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(p1.x(), p1.y(), p2.x() - p1.x(), p2.y() - p1.y())
                if is_selected:
                    painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
                    painter.drawRect(p1.x() - 3, p1.y() - 3, (p2.x() - p1.x()) + 6, (p2.y() - p1.y()) + 6)

            elif ann['type'] == 'Line':
                x1, y1, x2, y2 = ann['coords']
                p1, p2 = self.get_screen_point(x1, y1), self.get_screen_point(x2, y2)
                line_color = QColor(255, 255, 255) if is_selected else QColor(255, 0, 255)
                painter.setPen(QPen(line_color, 3, Qt.DashLine if is_selected else Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(p1, p2)

            elif ann['type'] == 'Grid':
                x1, y1, x2, y2 = ann['coords']
                rows, cols = ann['rows'], ann['cols']
                p1, p2 = self.get_screen_point(x1, y1), self.get_screen_point(x2, y2)
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.setBrush(Qt.NoBrush)
                w, h = p2.x() - p1.x(), p2.y() - p1.y()
                painter.drawRect(p1.x(), p1.y(), w, h)
                for r in range(1, rows):
                    y_line = p1.y() + r * (h / rows)
                    painter.drawLine(p1.x(), y_line, p2.x(), y_line)
                for c in range(1, cols):
                    x_line = p1.x() + c * (w / cols)
                    painter.drawLine(x_line, p1.y(), x_line, p2.y())
                if is_selected:
                    painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
                    painter.drawRect(p1.x() - 3, p1.y() - 3, w + 6, h + 6)

            elif ann['type'] == 'Polygon':
                poly = QPolygon()
                for x_orig, y_orig in ann['coords']:
                    poly.append(self.get_screen_point(x_orig, y_orig))
                border_color = QColor(255, 255, 255) if is_selected else QColor(0, 255, 255)
                fill_color = QColor(0, 255, 255, 100) if is_selected else QColor(0, 255, 255, 50)
                painter.setPen(QPen(border_color, 3, Qt.DashLine if is_selected else Qt.SolidLine))
                painter.setBrush(QBrush(fill_color))
                painter.drawPolygon(poly)

        # 绘制正在进行中的临时标注
        painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
        if self.current_tool in ["Rect", "Grid", "Line"] and self.temp_rect_start:
            painter.setBrush(Qt.NoBrush)
            if self.current_tool == "Line":
                painter.drawLine(self.temp_rect_start, self.temp_rect_end)
            else:
                w_temp = self.temp_rect_end.x() - self.temp_rect_start.x()
                h_temp = self.temp_rect_end.y() - self.temp_rect_start.y()
                painter.drawRect(self.temp_rect_start.x(), self.temp_rect_start.y(), w_temp, h_temp)
                if self.current_tool == "Grid":
                    painter.setPen(QPen(QColor(255, 0, 0, 150), 1, Qt.DashLine))
                    for r in range(1, self.grid_rows):
                        y_line = self.temp_rect_start.y() + r * (h_temp / self.grid_rows)
                        painter.drawLine(self.temp_rect_start.x(), y_line, self.temp_rect_end.x(), y_line)
                    for c in range(1, self.grid_cols):
                        x_line = self.temp_rect_start.x() + c * (w_temp / self.grid_cols)
                        painter.drawLine(x_line, self.temp_rect_start.y(), x_line, self.temp_rect_end.y())

        elif self.current_tool == "Polygon" and len(self.current_polygon) > 0:
            poly = QPolygon()
            for x_orig, y_orig in self.current_polygon:
                p = self.get_screen_point(x_orig, y_orig)
                poly.append(p)
                painter.setBrush(QColor(255, 0, 0))
                painter.drawEllipse(p, 5, 5)
            if len(poly) > 1:
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(poly)
                painter.drawLine(poly.last(), self.mapFromGlobal(self.cursor().pos()))

        painter.end()

    def _create_description_box(self):
        description_text = """
        <h3>🎨 图像标记工具说明</h3>
        <h4>✅ 性能增强：</h4>
        <p style='color: green;'>已开启 OpenCV 超大图像实时分块渲染内核，已完美支持 14684x48000 超长分辨率。</p>
        <h4>💡 功能特点:</h4>
        <ul>
            <li><strong>缩放:</strong> 鼠标悬停图像滑动滚轮。</li>
            <li><strong>移动调整:</strong> 点击“移动/选中”，拖拽已画好的标记。</li>
            <li><strong>删除标记:</strong> 选中状态下点击删除按钮，或按键盘 `Delete`。</li>
            <li><strong>网格阵列:</strong> 自动将大框切分为多个子ROI。</li>
            <li><strong>线条裁切:</strong> 单独记录两点之间的距离位置。</li>
        </ul>
        """
        text_browser = QTextBrowser()
        text_browser.setHtml(description_text)
        text_browser.setMaximumWidth(350)
        text_browser.setMinimumWidth(250)
        return text_browser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像标记与坐标输出工具 (支持超大图性能级内核)")
        self.setGeometry(100, 100, 1400, 850)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.content_layout = QHBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.image_widget = ImageWidget(self)
        self.image_widget.scroll_area = self.scroll_area

        # 核心：监听滚动条触发重绘切片
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.image_widget.update)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.image_widget.update)

        self.scroll_area.setWidget(self.image_widget)
        self.description_widget = self.image_widget._create_description_box()

        self.content_layout.addWidget(self.scroll_area, 3)
        self.content_layout.addWidget(self.description_widget, 1)
        self.main_layout.addLayout(self.content_layout)

        self.control_layout = QHBoxLayout()
        self.main_layout.addLayout(self.control_layout)

        self.setup_menu()
        self.setup_buttons()
        self.update_tool_buttons()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.image_widget.delete_selected()
        else:
            super().keyPressEvent(event)

    def setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("文件")
        open_action = file_menu.addAction("打开图像")
        open_action.triggered.connect(self.open_image)

    def setup_buttons(self):
        self.btn_zoom_in = QPushButton("放大 (+)")
        self.btn_zoom_in.clicked.connect(lambda: self.image_widget.zoom(1.2))
        self.control_layout.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("缩小 (-)")
        self.btn_zoom_out.clicked.connect(lambda: self.image_widget.zoom(1 / 1.2))
        self.control_layout.addWidget(self.btn_zoom_out)

        self.btn_fit = QPushButton("适应窗口")
        self.btn_fit.clicked.connect(self.image_widget.fit_to_window)
        self.control_layout.addWidget(self.btn_fit)

        self.control_layout.addWidget(QLabel(" | "))

        self.btn_select = QPushButton("🖱️ 移动/选中")
        self.btn_select.clicked.connect(lambda: self.set_tool("Select"))
        self.control_layout.addWidget(self.btn_select)

        self.btn_delete = QPushButton("🗑️ 删除选定")
        self.btn_delete.clicked.connect(self.image_widget.delete_selected)
        self.control_layout.addWidget(self.btn_delete)

        self.control_layout.addWidget(QLabel(" | "))

        self.btn_rect = QPushButton("矩形标记")
        self.btn_rect.clicked.connect(lambda: self.set_tool("Rect"))
        self.control_layout.addWidget(self.btn_rect)

        self.btn_line = QPushButton("线条标记")
        self.btn_line.clicked.connect(lambda: self.set_tool("Line"))
        self.control_layout.addWidget(self.btn_line)

        self.control_layout.addWidget(QLabel(" 网格行:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 100)
        self.spin_rows.setValue(5)
        self.spin_rows.valueChanged.connect(self.update_grid_params)
        self.control_layout.addWidget(self.spin_rows)

        self.control_layout.addWidget(QLabel("列:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 100)
        self.spin_cols.setValue(16)
        self.spin_cols.valueChanged.connect(self.update_grid_params)
        self.control_layout.addWidget(self.spin_cols)

        self.btn_grid = QPushButton("网格阵列")
        self.btn_grid.clicked.connect(lambda: self.set_tool("Grid"))
        self.control_layout.addWidget(self.btn_grid)

        self.btn_polygon = QPushButton("多边形")
        self.btn_polygon.clicked.connect(lambda: self.set_tool("Polygon"))
        self.control_layout.addWidget(self.btn_polygon)

        self.btn_complete_polygon = QPushButton("闭合")
        self.btn_complete_polygon.clicked.connect(self.image_widget.complete_polygon)
        self.control_layout.addWidget(self.btn_complete_polygon)

        self.control_layout.addStretch(1)

        self.btn_clear = QPushButton("清空全部")
        self.btn_clear.clicked.connect(self.image_widget.clear_annotations)
        self.control_layout.addWidget(self.btn_clear)

        self.btn_export = QPushButton("输出坐标")
        self.btn_export.clicked.connect(self.export_coordinates)
        self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.control_layout.addWidget(self.btn_export)

    def update_grid_params(self):
        self.image_widget.grid_rows = self.spin_rows.value()
        self.image_widget.grid_cols = self.spin_cols.value()

    def update_tool_buttons(self):
        tool = self.image_widget.current_tool
        has_selection = self.image_widget.selected_index is not None

        self.btn_select.setStyleSheet("background-color: lightgreen;" if tool == "Select" else "")
        self.btn_rect.setStyleSheet("background-color: lightgreen;" if tool == "Rect" else "")
        self.btn_line.setStyleSheet("background-color: lightgreen;" if tool == "Line" else "")
        self.btn_grid.setStyleSheet("background-color: lightgreen;" if tool == "Grid" else "")
        self.btn_polygon.setStyleSheet("background-color: lightgreen;" if tool == "Polygon" else "")

        self.btn_delete.setEnabled(has_selection)
        self.btn_delete.setStyleSheet("background-color: #ffcccc;" if has_selection else "")
        self.btn_complete_polygon.setEnabled(tool == "Polygon" or len(self.image_widget.current_polygon) >= 2)

    def set_tool(self, tool_name):
        self.image_widget.set_tool(tool_name)
        self.update_tool_buttons()

    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "打开图像文件", "",
                                                   "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
        if file_name:
            # 调用全新的 OpenCV 图像处理引擎加载方法
            success = self.image_widget.load_image(file_name)
            if not success:
                QMessageBox.critical(self, "错误",
                                     f"OpenCV 无法解析该超大图像:\n{file_name}\n请检查内存是否充足或文件是否损坏。")
                return

            self.set_tool("None")
            self.setWindowTitle(
                f"图像标记与坐标输出工具 - {os.path.basename(file_name)} (原图大小: {self.image_widget.original_size.width()}x{self.image_widget.original_size.height()})")

    def export_coordinates(self):
        annotations = self.image_widget.annotations
        if not annotations:
            QMessageBox.information(self, "提示", "没有检测到任何标记，请先进行标记。")
            return

        output = ["--- 图像标记原始像素坐标 (W={}, H={}) ---".format(
            self.image_widget.original_size.width(), self.image_widget.original_size.height()
        )]

        for i, ann in enumerate(annotations):
            ann_type = ann['type']
            coords = ann['coords']
            output.append(f"\n======== 标记块 {i + 1} ({ann_type}) ========")

            if ann_type == 'Rect':
                x_min, y_min, x_max, y_max = [max(0, int(c)) for c in coords]
                output.append(f"  类型: 单一矩形框\n  坐标: [{x_min}, {y_min}, {x_max}, {y_max}]")

            elif ann_type == 'Line':
                x1, y1, x2, y2 = [max(0, int(c)) for c in coords]
                output.append(
                    f"  类型: 线条标记 (两点线段)\n  起点 (X1, Y1): [{x1}, {y1}]\n  终点 (X2, Y2): [{x2}, {y2}]")

            elif ann_type == 'Grid':
                x_min, y_min, x_max, y_max = [float(c) for c in coords]
                rows, cols = ann['rows'], ann['cols']
                output.append(
                    f"  类型: 网格阵列 ({rows}行 x {cols}列)\n  总边界: [{int(x_min)}, {int(y_min)}, {int(x_max)}, {int(y_max)}]\n  > 各子 ROI 坐标 [x1, y1, x2, y2]:")
                sub_w = (x_max - x_min) / cols
                sub_h = (y_max - y_min) / rows
                for r in range(rows):
                    for c in range(cols):
                        sub_x1 = max(0, int(x_min + c * sub_w))
                        sub_y1 = max(0, int(y_min + r * sub_h))
                        sub_x2 = max(0, int(x_min + (c + 1) * sub_w))
                        sub_y2 = max(0, int(y_min + (r + 1) * sub_h))
                        output.append(f"    R{r + 1}_C{c + 1}: [{sub_x1}, {sub_y1}, {sub_x2}, {sub_y2}]")

            elif ann_type == 'Polygon':
                output.append(f"  类型: 多边形/轮廓 (共 {len(coords)} 个点)")
                for j, (x, y) in enumerate(coords):
                    output.append(f"    P{j + 1}: ({max(0, int(x))}, {max(0, int(y))})")

        output_text = "\n".join(output)
        print("\n" + "=" * 50 + "\n" + output_text + "\n" + "=" * 50 + "\n")

        output_file = "coordinates.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_text)
            QMessageBox.information(self, "导出成功", f"坐标已成功导出到:\n{os.path.abspath(output_file)}")
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出文件失败: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())









#新代码功能更多
<img width="1750" height="1101" alt="image" src="https://github.com/user-attachments/assets/da2dda8a-c677-4a0b-acc7-5c86af84f485" />

