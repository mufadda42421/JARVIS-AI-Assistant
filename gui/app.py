
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
)

from gui.styles import STYLESHEET


class CommandWorker(QThread):
    finished_message = Signal(str)
    failed = Signal(str)
    assistant_exit = Signal()

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            from assistant import process_command_for_gui
            keep_running, response = process_command_for_gui(self.command)
            if response:
                self.finished_message.emit(str(response))
            if not keep_running:
                self.assistant_exit.emit()
        except Exception as error:
            self.failed.emit(str(error))


class VoiceCommandWorker(QThread):
    listening_started = Signal()
    recognized = Signal(str)
    finished_message = Signal(str)
    failed = Signal(str)
    assistant_exit = Signal()

    def run(self):
        try:
            from voice import listen
            from assistant import process_command_for_gui
            self.listening_started.emit()
            command = listen()
            if not command or not command.strip():
                self.failed.emit("I didn't catch that. Please try again.")
                return
            command = command.strip()
            self.recognized.emit(command)
            keep_running, response = process_command_for_gui(command)
            if response:
                self.finished_message.emit(str(response))
            if not keep_running:
                self.assistant_exit.emit()
        except Exception as error:
            self.failed.emit(str(error))


def label(text, object_name=None):
    item = QLabel(text)
    if object_name:
        item.setObjectName(object_name)
    return item


def make_panel(title, subtitle=None):
    frame = QFrame()
    frame.setObjectName("panel")
    box = QVBoxLayout(frame)
    box.setContentsMargins(12, 10, 12, 11)
    box.setSpacing(8)
    head = QHBoxLayout()
    head.addWidget(label(title.upper(), "sectionLabel"))
    head.addStretch()
    if subtitle:
        head.addWidget(label(subtitle, "muted"))
    box.addLayout(head)
    return frame, box


class ReactorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(250, 190)
        self.state = "idle"
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        self.angle = (self.angle + (3 if self.state == "listening" else 1.5)) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width() * .29, self.height() * .43)
        color = QColor("#38dafa" if self.state == "idle" else
                       "#55aaff" if self.state == "listening" else "#ffc36b")

        # Soft radial glow
        grad = QRadialGradient(cx, cy, radius * 1.65)
        glow = QColor(color); glow.setAlpha(45)
        grad.setColorAt(0, glow)
        grad.setColorAt(1, QColor(4, 18, 31, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(QRectF(cx-radius*1.65, cy-radius*1.65,
                             radius*3.3, radius*3.3))

        # Orbital ellipses
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        for i in range(3):
            pen = QPen(QColor(67, 211, 246, 125 - i*25), 1.2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(-radius*(1.35+i*.12), -radius*(.47+i*.05),
                          radius*(2.7+i*.24), radius*(.94+i*.1))
            p.drawEllipse(rect)
        p.restore()

        # Core outline + fill
        p.setPen(QPen(color, 2))
        fill = QColor(color); fill.setAlpha(28)
        p.setBrush(fill)
        p.drawEllipse(QRectF(cx-radius, cy-radius, radius*2, radius*2))
        p.setPen(QPen(QColor("#a9f5ff"), 1))
        p.drawEllipse(QRectF(cx-radius*.77, cy-radius*.77,
                             radius*1.54, radius*1.54))

        p.setPen(QColor("#68edff"))
        f = QFont("Segoe UI", 18, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        p.setFont(f)
        p.drawText(QRectF(cx-radius*.9, cy-13, radius*1.8, 28),
                   Qt.AlignmentFlag.AlignCenter, "JARVIS")
        p.setPen(QColor("#9acbdc"))
        f2 = QFont("Segoe UI", 8, QFont.Weight.Bold)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(f2)
        p.drawText(QRectF(cx-radius, cy+17, radius*2, 20),
                   Qt.AlignmentFlag.AlignCenter, "A I   C O R E")


class InfoTile(QFrame):
    def __init__(self, icon, title, value, accent="#49d9f4"):
        super().__init__()
        self.setObjectName("panelAlt")
        row = QHBoxLayout(self)
        row.setContentsMargins(9, 7, 9, 7)
        badge = QLabel(icon)
        badge.setFixedSize(27, 27)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:#102f45; color:{accent}; border:1px solid {accent};"
            "border-radius:7px; font-weight:800;"
        )
        texts = QVBoxLayout()
        texts.setSpacing(1)
        texts.addWidget(label(title, "muted"))
        self.value_label = label(value)
        self.value_label.setStyleSheet(f"color:{accent}; font-size:11px; font-weight:700;")
        texts.addWidget(self.value_label)
        row.addWidget(badge)
        row.addLayout(texts, 1)


class ChatWindow(QMainWindow):
    """Dedicated chat workspace. Commands are routed through JarvisWindow."""
    send_requested = Signal(str)
    new_chat_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("J.A.R.V.I.S. | Chat Workspace")
        self.resize(900, 720)
        self.setMinimumSize(620, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setStyleSheet(STYLESHEET)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(label("CHAT WORKSPACE", "pageTitle"))
        title_box.addWidget(label("A dedicated space for conversations and commands", "muted"))
        header.addLayout(title_box)
        header.addStretch()
        new_button = QPushButton("＋  NEW CHAT")
        new_button.setObjectName("smallButton")
        new_button.clicked.connect(self.new_chat_requested.emit)
        header.addWidget(new_button)
        layout.addLayout(header)

        self.transcript = QTextEdit()
        self.transcript.setObjectName("chat")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("Your conversation with J.A.R.V.I.S. will appear here.")
        layout.addWidget(self.transcript, 1)

        composer = QFrame()
        composer.setObjectName("panelAlt")
        row = QHBoxLayout(composer)
        row.setContentsMargins(10, 9, 10, 9)
        row.setSpacing(8)
        row.addWidget(label("◉", "metric"))
        self.input = QLineEdit()
        self.input.setObjectName("commandInput")
        self.input.setPlaceholderText("Message J.A.R.V.I.S. ...")
        self.input.returnPressed.connect(self.send_message)
        row.addWidget(self.input, 1)
        send = QPushButton("SEND  ➤")
        send.setObjectName("primaryButton")
        send.clicked.connect(self.send_message)
        row.addWidget(send)
        layout.addWidget(composer)
        self.input.setFocus()

    def send_message(self):
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.send_requested.emit(message)

    def append_html(self, html):
        self.transcript.append(html)
        bar = self.transcript.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear_transcript(self):
        self.transcript.clear()

    def closeEvent(self, event):
        # Keep the workspace alive; closing it simply hides the window.
        event.ignore()
        self.hide()


class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.closing_after_exit = False
        self.message_history = []
        self.chat_window = ChatWindow(self)
        self.chat_window.send_requested.connect(self.send_chat_command)
        self.chat_window.new_chat_requested.connect(self.start_new_chat)
        self.setWindowTitle("J.A.R.V.I.S. | Command Center")
        self.resize(1500, 940)
        self.setMinimumSize(1120, 760)
        self.setStyleSheet(STYLESHEET)

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.build_sidebar())

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(10)
        main_layout.addLayout(self.build_topbar())
        main_layout.addLayout(self.build_top_grid(), 4)
        main_layout.addLayout(self.build_middle_grid(), 2)
        main_layout.addLayout(self.build_bottom_grid(), 2)
        main_layout.addWidget(self.build_command_bar())
        outer.addWidget(main, 1)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()
        self.add_message("J.A.R.V.I.S.", "All systems initialized. Awaiting your command.")

    def build_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(190)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(13, 20, 13, 14)
        layout.setSpacing(7)

        layout.addWidget(label("◉  JARVIS", "brand"))
        layout.addWidget(label("C O M M A N D   C E N T E R", "brandSub"))
        layout.addSpacing(17)

        nav = [
            ("▦   Command Center", True), ("◉   AI Core", False),
            ("♙   Agents", False), ("▤   Tasks", False),
            ("▦   Calendar", False), ("▣   Memory", False),
            ("▱   Conversations", False), ("◇   Knowledge Base", False),
            ("⌘   Tools & Skills", False), ("⇄   Workflows", False),
        ]
        self.nav_buttons = []
        for name, active in nav:
            b = QPushButton(name)
            b.setObjectName("navButton")
            b.setProperty("active", active)
            b.setMinimumHeight(35)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked=False, button=b: self.select_navigation(button))
            layout.addWidget(b)
            self.nav_buttons.append(b)

        chat_button = QPushButton("▱   Open Chat Window")
        chat_button.setObjectName("chatNavButton")
        chat_button.setMinimumHeight(39)
        chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        chat_button.clicked.connect(self.open_chat_window)
        layout.addWidget(chat_button)

        layout.addStretch()
        voice, vbox = make_panel("Voice Status")
        vbox.addWidget(label("▂▅▇▅▃▆▇▅▂", "metric"))
        vbox.addWidget(label("Voice capture is started on demand.", "muted"))
        self.sidebar_mic = QPushButton("🎙  START VOICE")
        self.sidebar_mic.setObjectName("smallButton")
        self.sidebar_mic.clicked.connect(self.start_voice_command)
        vbox.addWidget(self.sidebar_mic)
        layout.addWidget(voice)

        focus = QPushButton("ϟ  Focus Mode")
        focus.setObjectName("smallButton")
        focus.clicked.connect(lambda: self.add_message("SYSTEM", "Focus mode is a UI placeholder in this build."))
        layout.addWidget(focus)
        layout.addWidget(label("LOCAL DESKTOP BUILD 04", "muted"))
        return side

    def build_topbar(self):
        row = QHBoxLayout()
        status, _ = make_panel("System Status", "● LOCAL UI ONLINE")
        status.setMaximumWidth(220)
        row.addWidget(status)
        row.addStretch()
        self.date_label = label("", "muted")
        self.clock_label = label("", "metric")
        clock_box = QVBoxLayout()
        clock_box.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignRight)
        clock_box.addWidget(self.clock_label, 0, Qt.AlignmentFlag.AlignRight)
        row.addLayout(clock_box)
        search = QLineEdit()
        search.setPlaceholderText("⌕   Search dashboard...")
        search.setMaximumWidth(190)
        search.setMinimumHeight(34)
        row.addWidget(search)
        for text in ("▦", "♧", "⚙"):
            b = QPushButton(text)
            b.setObjectName("smallButton")
            b.setFixedSize(34, 34)
            b.clicked.connect(lambda checked=False, t=text: self.add_message("SYSTEM", f"{t} control is not connected yet."))
            row.addWidget(b)
        return row

    def build_top_grid(self):
        row = QHBoxLayout()
        row.setSpacing(9)

        overview, ov = make_panel("AI Core Overview")
        for icon, title, value, color in [
            ("◉", "AI Core", "Active", "#49d9f4"),
            ("▤", "Memory", "Connected to local module", "#64b9ff"),
            ("♬", "Voice", "Ready to test", "#45e3bd"),
            ("◇", "Agents", "Not configured", "#b78aff"),
            ("✧", "LLM", "Gemini backend", "#ffc66d"),
            ("⌂", "System", "Desktop online", "#45e3bd"),
        ]:
            ov.addWidget(InfoTile(icon, title, value, color))
        overview.setMinimumWidth(185)
        row.addWidget(overview, 1)

        core, corebox = make_panel("J.A.R.V.I.S. AI Core", "V3 • DESKTOP")
        self.core_state = label("● SYSTEM IDLE", "good")
        corebox.addWidget(self.core_state, 0, Qt.AlignmentFlag.AlignHCenter)
        self.reactor = ReactorWidget()
        corebox.addWidget(self.reactor, 1)
        corebox.addWidget(label("INTELLIGENCE  •  AUTOMATION  •  VOICE", "sectionLabel"),
                          0, Qt.AlignmentFlag.AlignHCenter)
        row.addWidget(core, 3)

        feed, fb = make_panel("Live Intelligence Feed", "LOCAL ACTIVITY")
        self.chat = QTextEdit()
        self.chat.setObjectName("chat")
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("System activity and your conversation will appear here...")
        self.chat.setMinimumHeight(155)
        self.chat.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fb.addWidget(self.chat, 1)
        feed.setMinimumWidth(230)
        row.addWidget(feed, 1)
        return row

    def build_middle_grid(self):
        row = QHBoxLayout()
        row.setSpacing(9)

        agents, ab = make_panel("Active Agents", "MODULE OVERVIEW")
        grid = QGridLayout()
        grid.setSpacing(7)
        agent_data = [
            ("⌘", "Coding Agent", "Not configured", "#48dfc0"),
            ("⌕", "Research Agent", "Not configured", "#4ad8f4"),
            ("▤", "Memory Agent", "Local memory module", "#b58cff"),
            ("◎", "Browser Agent", "Not connected", "#ffc66d"),
        ]
        for i, (icon, name, state, color) in enumerate(agent_data):
            tile = InfoTile(icon, name, state, color)
            grid.addWidget(tile, i // 2, i % 2)
        ab.addLayout(grid)
        ab.addStretch()
        row.addWidget(agents, 2)

        timeline, tb = make_panel("Mission Timeline", "TODAY")
        for time, title, state in [
            ("NOW", "Desktop session started", "LIVE"),
            ("NEXT", "Awaiting command", "PENDING"),
            ("—", "No scheduled missions", "IDLE"),
        ]:
            line = QHBoxLayout()
            line.addWidget(label(time, "good"))
            line.addWidget(label(title))
            line.addStretch()
            line.addWidget(label(state, "muted"))
            tb.addLayout(line)
        tb.addStretch()
        row.addWidget(timeline, 1)

        quick, qb = make_panel("Quick Commands")
        for text, command in [
            ("＋  Start New Conversation", "Hello JARVIS"),
            ("◉  Ask the Time", "What time is it?"),
            ("▣  Ask the Date", "What is the date?"),
        ]:
            b = QPushButton(text)
            b.setObjectName("smallButton")
            b.clicked.connect(lambda checked=False, cmd=command: self.run_quick_command(cmd))
            qb.addWidget(b)
        qb.addStretch()
        row.addWidget(quick, 1)
        return row

    def build_bottom_grid(self):
        row = QHBoxLayout()
        row.setSpacing(9)

        monitor, mb = make_panel("System Monitor", "LIVE VALUES NOT CONNECTED")
        gauges = QHBoxLayout()
        for title in ("CPU", "RAM", "DISK"):
            box = QVBoxLayout()
            box.addWidget(label("◌", "metric"), 0, Qt.AlignmentFlag.AlignHCenter)
            box.addWidget(label(title, "sectionLabel"), 0, Qt.AlignmentFlag.AlignHCenter)
            box.addWidget(label("—", "muted"), 0, Qt.AlignmentFlag.AlignHCenter)
            gauges.addLayout(box)
        mb.addLayout(gauges)
        row.addWidget(monitor, 1)

        memory, mem = make_panel("Memory Insights", "LOCAL MODULE")
        mem.addWidget(label("Memory integration is available through your existing backend.", "muted"))
        self.memory_status = label("● STATUS: NOT LIVE-CHECKED", "warn")
        mem.addWidget(self.memory_status)
        row.addWidget(memory, 1)

        llm, lb = make_panel("LLM Status", "CONFIGURATION")
        lb.addWidget(InfoTile("✧", "Gemini", "Configured through existing brain.py", "#4ad8f4"))
        lb.addWidget(label("Provider connectivity is checked when you send a prompt.", "muted"))
        row.addWidget(llm, 2)
        return row

    def build_command_bar(self):
        panel = QFrame()
        panel.setObjectName("panelAlt")
        row = QHBoxLayout(panel)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(8)
        row.addWidget(label("◉", "metric"))
        self.command_input = QLineEdit()
        self.command_input.setObjectName("commandInput")
        self.command_input.setPlaceholderText("Talk to J.A.R.V.I.S.  —  type a command and press Enter...")
        self.command_input.returnPressed.connect(self.send_command)
        row.addWidget(self.command_input, 1)
        self.mic_button = QPushButton("🎙  VOICE")
        self.mic_button.setObjectName("smallButton")
        self.mic_button.setMinimumHeight(40)
        self.mic_button.clicked.connect(self.start_voice_command)
        row.addWidget(self.mic_button)
        self.send_button = QPushButton("SEND  ➤")
        self.send_button.setObjectName("primaryButton")
        self.send_button.setMinimumHeight(40)
        self.send_button.clicked.connect(self.send_command)
        row.addWidget(self.send_button)
        return panel

    def select_navigation(self, selected):
        for button in self.nav_buttons:
            button.setProperty("active", button is selected)
            button.style().unpolish(button)
            button.style().polish(button)
        self.add_message("SYSTEM", f"{selected.text().strip()} selected. This section's dedicated page is planned for a later build.")

    def update_clock(self):
        now = datetime.now()
        self.date_label.setText(now.strftime("%A, %d %B %Y").upper())
        self.clock_label.setText(now.strftime("%I:%M:%S %p"))

    def add_message(self, sender, message):
        safe_sender = str(sender).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_message = (str(message).replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;").replace("\n", "<br>"))
        color = "#63e8bd" if sender == "J.A.R.V.I.S." else "#68dfff" if sender == "YOU" else "#89a9bd"
        html = (
            f'<p style="margin:7px 0 2px"><b style="color:{color}">{safe_sender}</b></p>'
            f'<p style="color:#d9efff;margin:0 0 8px">{safe_message}</p>'
        )
        self.message_history.append(html)
        self.chat.append(html)
        bar = self.chat.verticalScrollBar()
        bar.setValue(bar.maximum())
        if self.chat_window:
            self.chat_window.append_html(html)

    def open_chat_window(self):
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()
        self.chat_window.input.setFocus()

    def send_chat_command(self, command):
        self.open_chat_window()
        self.run_command(command)

    def start_new_chat(self):
        self.message_history.clear()
        self.chat.clear()
        self.chat_window.clear_transcript()
        self.add_message("SYSTEM", "New conversation started. Previous messages remain available only in the earlier session view if you saved them externally.")
        self.chat_window.input.setFocus()

    def chat_append_if_present(self, html):
        # Kept for compatibility with earlier Build 04 code paths.
        self.chat.append(html)

    def run_quick_command(self, command):
        self.command_input.setText(command)
        self.send_command()

    def set_busy(self, busy):
        self.send_button.setDisabled(busy)
        self.mic_button.setDisabled(busy)
        self.sidebar_mic.setDisabled(busy)
        self.command_input.setDisabled(busy)
        self.chat_window.input.setDisabled(busy)

    def set_core_state(self, state):
        self.reactor.set_state(state)
        if state == "listening":
            self.core_state.setText("● LISTENING")
            self.core_state.setObjectName("warn")
        elif state == "thinking":
            self.core_state.setText("● PROCESSING")
            self.core_state.setObjectName("warn")
        else:
            self.core_state.setText("● SYSTEM IDLE")
            self.core_state.setObjectName("good")
        self.core_state.style().unpolish(self.core_state)
        self.core_state.style().polish(self.core_state)

    def start_worker(self, worker):
        self.worker = worker
        worker.finished_message.connect(self.command_finished)
        worker.failed.connect(self.command_failed)
        worker.assistant_exit.connect(self.handle_assistant_exit)
        worker.finished.connect(self.worker_finished)
        self.set_busy(True)
        worker.start()

    def send_command(self):
        command = self.command_input.text().strip()
        if not command:
            return
        self.command_input.clear()
        self.run_command(command)

    def run_command(self, command):
        if not command or (self.worker and self.worker.isRunning()):
            self.add_message("SYSTEM", "J.A.R.V.I.S. is busy. Please wait for the current task to finish.")
            return
        self.add_message("YOU", command)
        self.set_core_state("thinking")
        self.add_message("SYSTEM", "Processing command...")
        self.start_worker(CommandWorker(command))

    def start_voice_command(self):
        if self.worker and self.worker.isRunning():
            return
        self.add_message("SYSTEM", "Microphone activated. Speak after the listening prompt.")
        worker = VoiceCommandWorker()
        worker.listening_started.connect(lambda: self.set_core_state("listening"))
        worker.recognized.connect(self.voice_command_recognized)
        worker.finished_message.connect(self.command_finished)
        worker.failed.connect(self.command_failed)
        worker.assistant_exit.connect(self.handle_assistant_exit)
        worker.finished.connect(self.worker_finished)
        self.worker = worker
        self.set_busy(True)
        self.set_core_state("listening")
        worker.start()

    def voice_command_recognized(self, command):
        self.add_message("YOU", command)
        self.add_message("SYSTEM", "Voice command recognized. Processing...")
        self.set_core_state("thinking")

    def command_finished(self, message):
        self.add_message("J.A.R.V.I.S.", message)

    def command_failed(self, error):
        self.add_message("SYSTEM", str(error))

    def worker_finished(self):
        self.set_busy(False)
        self.command_input.setFocus()
        if not self.closing_after_exit:
            self.set_core_state("idle")
        self.worker = None

    def handle_assistant_exit(self):
        self.closing_after_exit = True
        self.add_message("SYSTEM", "J.A.R.V.I.S. is shutting down...")
        self.close()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(1500)
        event.accept()


def launch_app():
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S.")
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
