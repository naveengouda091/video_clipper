"""
Styles and theme tokens for Clipper Desktop Application.
Conforms to modern dark-theme design tokens, accessible contrast,
and snappy interaction feedback.
"""

DARK_THEME_QSS = """
/* Base Window & Widget Defaults */
QWidget {
    background-color: #0b0f17;
    color: #f1f5f9;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Inter", Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #38bdf8;
    selection-color: #0b0f17;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Main Container Panels */
QFrame#cardFrame {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
}

QFrame#dropZone {
    background-color: #0f172a;
    border: 2px dashed #334155;
    border-radius: 14px;
    padding: 24px;
}
QFrame#dropZone:hover {
    border-color: #38bdf8;
    background-color: #14213d;
}

/* Typography Labels */
QLabel#headerTitle {
    font-size: 24px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
}
QLabel#headerSubtitle {
    font-size: 13px;
    color: #94a3b8;
}
QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #38bdf8;
    letter-spacing: 0.2px;
    margin-bottom: 4px;
}
QLabel#metaBadge {
    background-color: #1e293b;
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #334155;
}
QLabel#statusText {
    font-size: 13px;
    color: #94a3b8;
    font-weight: 500;
}

/* Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #283548;
    border-color: #475569;
}
QPushButton:pressed {
    background-color: #0f172a;
}
QPushButton:disabled {
    background-color: #131b2e;
    color: #475569;
    border-color: #1e293b;
}

/* Primary Action Button (Minimum 44px touch target) */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 700;
    min-height: 38px;
}
QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0284c7);
}
QPushButton#primaryButton:pressed {
    background-color: #075985;
}
QPushButton#primaryButton:disabled {
    background: #1e293b;
    color: #64748b;
}

/* Danger / Cancel Button */
QPushButton#dangerButton {
    background-color: #3f1d24;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton#dangerButton:hover {
    background-color: #7f1d1d;
    color: #ffffff;
}

/* Preset Chips */
QPushButton.presetChip {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 24px;
}
QPushButton.presetChip:hover {
    background-color: #283548;
    border-color: #38bdf8;
    color: #f8fafc;
}
QPushButton.presetChip[checked="true"] {
    background-color: #0369a1;
    border-color: #38bdf8;
    color: #ffffff;
}

/* Line Edits & Spinboxes */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0b0f17;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #38bdf8;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #131b2e;
    color: #f8fafc;
    border: 1px solid #334155;
    selection-background-color: #0369a1;
    padding: 4px;
}

/* Progress Bar */
QProgressBar {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    text-align: center;
    color: #f8fafc;
    font-weight: 700;
    font-size: 12px;
    height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 7px;
}

/* List Widget for Finished Clips */
QListWidget {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 6px;
}
QListWidget::item {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 6px;
    margin-bottom: 4px;
    padding: 8px 12px;
    color: #e2e8f0;
}
QListWidget::item:hover {
    background-color: #1e293b;
    border-color: #38bdf8;
}
"""
