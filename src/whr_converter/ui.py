import os
import sys
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCalendarWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtGui import QFont
from whr_converter.medirecords_client import MedirecordsProprietaryClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.medirecords = MedirecordsProprietaryClient(os.environ["PRACTICE_ID"])
        self.appointment_types = {
            t["id"]: t["name"] for t in self.medirecords.get_appointment_types()["data"]
        }
        self.setWindowTitle("WHR Converter - Data Synchronization")
        self.setGeometry(100, 100, 600, 700)

        # Set up the main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Apply modern styling
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QCalendarWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 12px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2c3e50;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton#todayButton {
                background-color: #27ae60;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton#todayButton:hover {
                background-color: #229954;
            }
            QPushButton#todayButton:pressed {
                background-color: #1e8449;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
        """
        )

        # Create title
        title_label = QLabel("Data Synchronization Interface")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.Alignment.AlignCenter)
        main_layout.addWidget(title_label)

        # Create calendar section
        calendar_label = QLabel("Select Date:")
        calendar_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(calendar_label)

        # Create calendar and today button container
        calendar_container = QHBoxLayout()
        calendar_container.setSpacing(10)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setDateEditEnabled(True)
        calendar_container.addWidget(self.calendar)

        # Create today button
        self.today_button = QPushButton("Today")
        self.today_button.setObjectName("todayButton")
        self.today_button.setMaximumWidth(80)
        self.today_button.setMaximumHeight(40)
        self.today_button.clicked.connect(self.set_today)
        calendar_container.addWidget(self.today_button)

        # Add calendar container to main layout
        calendar_widget = QWidget()
        calendar_widget.setLayout(calendar_container)
        main_layout.addWidget(calendar_widget)

        # Create names table section
        names_label = QLabel("Person Names:")
        names_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(names_label)

        # Create table widget
        self.names_table = QTableWidget()
        self.names_table.setColumnCount(3)
        self.names_table.setHorizontalHeaderLabels(["Time", "Type", "Name"])
        self.names_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.names_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)

        # Set column widths
        header = self.names_table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )  # Time column fixed width
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )  # Name column stretches
        self.names_table.setColumnWidth(0, 100)  # Time column width

        # Add names table with stretch factor to make it expand
        main_layout.addWidget(self.names_table, 1)  # stretch factor of 1

        # Create synchronize button at the bottom
        self.sync_button = QPushButton("Synchronize")
        self.sync_button.clicked.connect(self.synchronize_data)
        main_layout.addWidget(self.sync_button)

        # Connect calendar date change signal
        self.calendar.selectionChanged.connect(self.on_date_changed)

        # Store selected date
        self.set_today()

    def on_date_changed(self):
        """Handle date selection change"""
        self.selected_date = self.calendar.selectedDate()
        selected_date = self.selected_date.toString("yyyy-MM-dd")
        print(f"Selected date: {selected_date}")
        appointments = [
            a
            for a in self.medirecords.get_appointments(selected_date, selected_date)
            if a.get("patientId") and a.get("appointmentTypeId")
        ]
        self.patients = {
            a["patientId"]: self.medirecords.get_patient(a["patientId"])
            for a in appointments
        }

        self.names_table.setRowCount(len(appointments))
        for row, a in enumerate(sorted(appointments, key=lambda a: a["scheduleTime"])):
            patient = self.patients[a["patientId"]]
            name = QTableWidgetItem(patient["fullName"])
            name.setData(Qt.UserRole, a["patientId"])
            self.names_table.setItem(
                row, 0, QTableWidgetItem(a["scheduleTime"].split("T")[1])
            )
            self.names_table.setItem(
                row,
                1,
                QTableWidgetItem(self.appointment_types.get(a["appointmentTypeId"])),
            )
            self.names_table.setItem(row, 2, name)
        self.names_table.resizeColumnsToContents()

    def set_today(self):
        """Set calendar to today's date"""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.selected_date = today
        print(f"Set to today's date: {today.toString('yyyy-MM-dd')}")

    def synchronize_data(self):
        """Handle synchronize button click"""
        selected_date = self.calendar.selectedDate()
        selected_rows = self.names_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self, "Warning", "Please select at least one person from the table."
            )
            return

        # Get selected data (time and name)
        selected_data = []
        for row in selected_rows:
            name_item = self.names_table.item(row.row(), 2)
            selected_data.append(name_item.data(Qt.UserRole))

        # Create confirmation message
        date_str = selected_date.toString("yyyy-MM-dd")
        names_str = ", ".join([str(patient_id) for patient_id in selected_data])

        msg = QMessageBox()
        msg.setWindowTitle("Synchronization Confirmation")
        msg.setText("Synchronize data for the following:")
        msg.setInformativeText(f"Date: {date_str}\nSelected: {names_str}")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)

        if msg.exec() == QMessageBox.StandardButton.Ok:
            # Here you would implement the actual synchronization logic
            QMessageBox.information(
                self,
                "Success",
                f"Data synchronized successfully!\n"
                f"Date: {date_str}\n"
                f"Selected: {len(selected_data)} persons",
            )
            print(f"Synchronizing data for date: {date_str}")
            print(f"Selected data: {selected_data}")


def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("WHR Converter")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("WHR")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
