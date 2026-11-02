
STYLESHEET = """
* {
    font-family: "Segoe UI";
    font-size: 12px;
}
QMainWindow, QWidget {
    background: #06111e;
    color: #d9efff;
}
QWidget#sidebar {
    background: #071725;
    border-right: 1px solid #12334a;
}
QLabel#brand {
    color: #e7faff;
    font-size: 23px;
    font-weight: 800;
    letter-spacing: 5px;
}
QLabel#brandSub {
    color: #54cde9;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 3px;
}
QLabel#sectionLabel {
    color: #62b9d2;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
}
QLabel#pageTitle {
    color: #effaff;
    font-size: 19px;
    font-weight: 700;
}
QLabel#muted {
    color: #6f91a8;
    font-size: 10px;
}
QLabel#metric {
    color: #57e7ff;
    font-size: 20px;
    font-weight: 800;
}
QLabel#good {
    color: #42e6b5;
    font-size: 10px;
    font-weight: 700;
}
QLabel#warn {
    color: #ffc66d;
    font-size: 10px;
    font-weight: 700;
}
QFrame#panel {
    background: #091b2b;
    border: 1px solid #17415a;
    border-radius: 10px;
}
QFrame#panelAlt {
    background: #0a2032;
    border: 1px solid #1a4b65;
    border-radius: 9px;
}
QFrame#statusCard {
    background: #0b2234;
    border: 1px solid #1a4058;
    border-radius: 8px;
}
QPushButton#navButton {
    color: #9ab5c8;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    text-align: left;
    padding: 10px 11px;
}
QPushButton#navButton:hover {
    background: #102b40;
    color: #70eaff;
}
QPushButton#navButton[active="true"] {
    background: #10334a;
    border: 1px solid #1e6b87;
    color: #70eaff;
    font-weight: 700;
}
QPushButton#smallButton {
    background: #0d2a40;
    color: #9bdcf0;
    border: 1px solid #1a526d;
    border-radius: 6px;
    padding: 7px 10px;
}
QPushButton#smallButton:hover {
    background: #12405a;
    color: #ffffff;
}
QPushButton#primaryButton {
    background: #087e9f;
    color: #f2fdff;
    border: 1px solid #28c9ed;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 800;
}
QPushButton#primaryButton:hover {
    background: #0a9fc2;
}
QPushButton#primaryButton:disabled {
    background: #244354;
    color: #7892a2;
    border-color: #315266;
}
QLineEdit#commandInput {
    background: #071725;
    color: #eafaff;
    border: 1px solid #1b536d;
    border-radius: 8px;
    padding: 11px 14px;
    selection-background-color: #12617c;
}
QLineEdit#commandInput:focus {
    border: 1px solid #48dfff;
}
QTextEdit#chat {
    background: #071725;
    color: #d9efff;
    border: 1px solid #153b52;
    border-radius: 8px;
    padding: 8px;
}
QScrollBar:vertical {
    background: #071725;
    width: 7px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #1b536d;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QPushButton#chatNavButton {
    background: #12394f;
    color: #8cecff;
    border: 1px solid #2792b2;
    border-radius: 7px;
    text-align: left;
    padding: 10px 11px;
    font-weight: 800;
}
QPushButton#chatNavButton:hover {
    background: #18516b;
    color: #ffffff;
}
"""
