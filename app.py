import tkinter as tk
import database as db
from ui.constants import COLOR_BG
from ui.login import LoginFrame
from ui.dashboard import TeacherDashboard

class ReservationApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Facility Reservation System")
        self.geometry("1150x680")
        self.minsize(1000, 620)
        self.configure(bg=COLOR_BG)

        db.init_db()
        db.seed_data()

        self.current_teacher = None

        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def _clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.current_teacher = None
        self._clear()
        LoginFrame(self.container, self).pack(fill="both", expand=True)

    def show_dashboard(self, teacher):
        self.current_teacher = teacher
        self._clear()
        TeacherDashboard(self.container, self, teacher).pack(fill="both", expand=True)