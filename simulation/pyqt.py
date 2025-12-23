import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class WaterSystemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Water System Control')
        self.setGeometry(100, 100, 1000, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)
        
        # Title
        title_label = QLabel("Water System Control Panel")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        left_layout.addWidget(title_label)
        
        # Sensor sliders
        left_layout.addSpacing(20)
        
        # PH Sensor
        self.ph_slider, ph_layout = self.create_slider("pH Sensor", 0, 14, 7)
        left_layout.addLayout(ph_layout)
        
        # Turbidity Sensor
        self.turbidity_slider, turbidity_layout = self.create_slider("Turbidity Sensor", 0, 100, 25, "NTU")
        left_layout.addLayout(turbidity_layout)
        
        # Salinity Sensor
        self.salinity_slider, salinity_layout = self.create_slider("Salinity Sensor", 0, 50, 15, "ppt")
        left_layout.addLayout(salinity_layout)
        
        # Water Level Slider
        left_layout.addSpacing(30)
        self.water_level_slider, water_level_layout = self.create_slider("WATER LEVEL", 0, 100, 50, "%")
        left_layout.addLayout(water_level_layout)
        
        # Status indicators
        left_layout.addSpacing(30)
        status_label = QLabel("Pipeline Status")
        status_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(status_label)
        
        self.pipeline_status = QTextEdit()
        self.pipeline_status.setMaximumHeight(150)
        self.pipeline_status.setReadOnly(True)
        left_layout.addWidget(self.pipeline_status)
        
        # Reset button
        reset_button = QPushButton("Reset All Pipelines")
        reset_button.clicked.connect(self.reset_pipelines)
        reset_button.setStyleSheet("background-color: #f0f0f0; padding: 8px;")
        left_layout.addWidget(reset_button)
        
        left_layout.addStretch()
        
        # Right panel for visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Visualization widget
        self.viz_widget = VisualizationWidget()
        right_layout.addWidget(self.viz_widget)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Connect sliders
        self.ph_slider.valueChanged.connect(self.update_sensor_values)
        self.turbidity_slider.valueChanged.connect(self.update_sensor_values)
        self.salinity_slider.valueChanged.connect(self.update_sensor_values)
        self.water_level_slider.valueChanged.connect(self.viz_widget.set_water_level)
        
        # Initialize status display
        self.update_pipeline_status()
        
        # Connect pipeline clicks to status update
        self.viz_widget.pipeline_clicked.connect(self.update_pipeline_status)
        
    def create_slider(self, label_text, min_val, max_val, default_val, unit=""):
        layout = QVBoxLayout()
        
        # Label with value display
        label = QLabel(f"{label_text}: {default_val}{unit}")
        label.setFont(QFont("Arial", 10))
        layout.addWidget(label)
        
        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval((max_val - min_val) // 10)
        slider.setMinimumHeight(30)
        layout.addWidget(slider)
        
        # Connect slider to update label
        def update_label(value):
            label.setText(f"{label_text}: {value}{unit}")
        
        slider.valueChanged.connect(update_label)
        
        return slider, layout
    
    def update_sensor_values(self):
        # This method can be expanded to send sensor values to other parts of the system
        ph = self.ph_slider.value()
        turbidity = self.turbidity_slider.value()
        salinity = self.salinity_slider.value()
        
        # In a real application, you would send these values to the hardware
        print(f"Sensor values - pH: {ph}, Turbidity: {turbidity}, Salinity: {salinity}")
    
    def update_pipeline_status(self):
        status_text = "Pipeline Status:\n"
        for pipe_id, status in self.viz_widget.pipeline_status.items():
            status_text += f"{pipe_id}: {'OPEN (Green)' if status else 'CLOSED (Red)'}\n"
        self.pipeline_status.setText(status_text)
    
    def reset_pipelines(self):
        self.viz_widget.reset_pipelines()
        self.update_pipeline_status()


class VisualizationWidget(QWidget):
    pipeline_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.water_level = 50  # Percentage
        self.pipeline_status = {
            "A-B": True,   # Open by default
            "B-C": True,
            "C-TAP": True,
            "TANK-A": True
        }
        self.setMinimumSize(600, 600)
        
    def set_water_level(self, level):
        self.water_level = level
        self.update()
    
    def reset_pipelines(self):
        for key in self.pipeline_status.keys():
            self.pipeline_status[key] = True
        self.update()
    
    def mousePressEvent(self, event):
        # Check if a pipeline was clicked
        pos = event.pos()
        
        # Define pipeline clickable areas
        tank_center = QPoint(300, 150)
        node_a = QPoint(200, 350)
        node_b = QPoint(400, 350)
        node_c = QPoint(500, 500)
        tap_pos = QPoint(700, 500)
        
        # Check each pipeline
        pipelines = [
            ("TANK-A", tank_center, node_a),
            ("A-B", node_a, node_b),
            ("B-C", node_b, node_c),
            ("C-TAP", node_c, tap_pos)
        ]
        
        for pipe_id, p1, p2 in pipelines:
            if self.point_near_line(pos, p1, p2, 15):
                self.pipeline_status[pipe_id] = not self.pipeline_status[pipe_id]
                self.pipeline_clicked.emit()
                self.update()
                break
        
        super().mousePressEvent(event)
    
    def point_near_line(self, point, line_start, line_end, threshold):
        # Calculate distance from point to line segment
        line_vec = QPointF(line_end - line_start)
        point_vec = QPointF(point - line_start)
        
        line_length = (line_vec.x()**2 + line_vec.y()**2)**0.5
        if line_length == 0:
            return False
        
        line_unit_vec = QPointF(line_vec.x() / line_length, line_vec.y() / line_length)
        point_vec_scaled = QPointF(
            point_vec.x() / line_length,
            point_vec.y() / line_length
        )
        
        t = max(0, min(1, line_unit_vec.x() * point_vec_scaled.x() + line_unit_vec.y() * point_vec_scaled.y()))
        
        nearest = QPointF(
            line_start.x() + t * line_vec.x(),
            line_start.y() + t * line_vec.y()
        )
        
        distance = ((point.x() - nearest.x())**2 + (point.y() - nearest.y())**2)**0.5
        
        return distance <= threshold
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(240, 245, 250))
        
        # Define positions
        tank_center = QPoint(300, 150)
        tank_radius = 100
        water_height = tank_radius * 2 * self.water_level / 100
        
        node_a = QPoint(200, 350)
        node_b = QPoint(400, 350)
        node_c = QPoint(500, 500)
        tap_pos = QPoint(700, 500)
        
        # Draw pipelines first (so they're behind nodes)
        self.draw_pipelines(painter, tank_center, node_a, node_b, node_c, tap_pos)
        
        # Draw tank with water level
        self.draw_tank(painter, tank_center, tank_radius, water_height)
        
        # Draw nodes
        self.draw_nodes(painter, node_a, node_b, node_c, tap_pos)
        
        # Draw labels
        self.draw_labels(painter, tank_center, node_a, node_b, node_c, tap_pos)
    
    def draw_tank(self, painter, center, radius, water_height):
        # Tank outline
        painter.setPen(QPen(QColor(50, 50, 100), 3))
        painter.setBrush(QBrush(QColor(230, 230, 240)))
        painter.drawEllipse(center, radius, radius)
        
        # Water inside tank
        water_rect = QRect(
            center.x() - radius,
            center.y() - radius + (radius * 2 - water_height),
            radius * 2,
            water_height
        )
        
        painter.setPen(Qt.NoPen)
        water_color = QColor(100, 150, 255, 180)
        painter.setBrush(QBrush(water_color))
        painter.drawEllipse(water_rect)
        
        # Water level indicator
        painter.setPen(QPen(QColor(0, 0, 100), 2))
        level_y = center.y() - radius + (radius * 2 - water_height)
        painter.drawLine(center.x() - radius - 10, level_y, center.x() + radius + 10, level_y)
        
        # Tank label
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(center.x() - 30, center.y() + 5, "TANK")
    
    def draw_pipelines(self, painter, tank_center, node_a, node_b, node_c, tap_pos):
        # Draw pipelines with different colors based on status
        pipelines = [
            ("TANK-A", tank_center, node_a),
            ("A-B", node_a, node_b),
            ("B-C", node_b, node_c),
            ("C-TAP", node_c, tap_pos)
        ]
        
        for pipe_id, p1, p2 in pipelines:
            if self.pipeline_status[pipe_id]:
                # Open pipeline - green
                pen = QPen(QColor(0, 180, 0), 6)
            else:
                # Closed pipeline - red
                pen = QPen(QColor(220, 0, 0), 6)
            
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(p1, p2)
    
    def draw_nodes(self, painter, node_a, node_b, node_c, tap_pos):
        # Draw nodes as circles
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        node_radius = 12
        for node, label in [(node_a, "A"), (node_b, "B"), (node_c, "C")]:
            painter.drawEllipse(node, node_radius, node_radius)
            
            # Label inside node
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(node.x() - 5, node.y() + 5, label)
            painter.setPen(QPen(QColor(80, 80, 80), 2))
        
        # Draw tap as a rectangle
        tap_rect = QRect(tap_pos.x() - 20, tap_pos.y() - 15, 40, 30)
        painter.setBrush(QBrush(QColor(200, 180, 100)))
        painter.drawRect(tap_rect)
        
        # Tap label
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(tap_rect, Qt.AlignCenter, "TAP")
    
    def draw_labels(self, painter, tank_center, node_a, node_b, node_c, tap_pos):
        # Draw labels for pipelines
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(QFont("Arial", 9))
        
        # Pipeline labels
        mid_point_tank_a = QPoint((tank_center.x() + node_a.x()) // 2, 
                                 (tank_center.y() + node_a.y()) // 2)
        painter.drawText(mid_point_tank_a.x() - 20, mid_point_tank_a.y() - 10, "TANK-A")
        
        mid_point_a_b = QPoint((node_a.x() + node_b.x()) // 2, 
                              (node_a.y() + node_b.y()) // 2)
        painter.drawText(mid_point_a_b.x() - 10, mid_point_a_b.y() - 10, "A-B")
        
        mid_point_b_c = QPoint((node_b.x() + node_c.x()) // 2, 
                              (node_b.y() + node_c.y()) // 2)
        painter.drawText(mid_point_b_c.x() - 10, mid_point_b_c.y() - 10, "B-C")
        
        mid_point_c_tap = QPoint((node_c.x() + tap_pos.x()) // 2, 
                                (node_c.y() + tap_pos.y()) // 2)
        painter.drawText(mid_point_c_tap.x() - 15, mid_point_c_tap.y() - 10, "C-TAP")
        
        # Instructions
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 30, "Click on pipelines to toggle OPEN/CLOSE")


def main():
    app = QApplication(sys.argv)
    window = WaterSystemGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()