import tkinter as tk
from tkinter import ttk

import database as db
from ui.dashboard import TeacherDashboard
from ui.login import LoginFrame
from ui.theme import ThemeManager


class ReservationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.title("Facility Reservation System")
        self.geometry("1200x760")
        self.minsize(1020, 680)
        self.apply_theme()

        db.init_db()
        db.seed_data()

        self.current_teacher = None
        self.login_form_values = {
            "teacher_id": "",
            "password": "",
            "show_password": False,
        }
        self.container = tk.Frame(self, bg=self.theme_manager.colors["bg"])
        self.container.pack(fill="both", expand=True)
        self.show_login()

    @property
    def colors(self):
        return self.theme_manager.colors

    def apply_theme(self):
        colors = self.theme_manager.colors
        self.configure(bg=colors["bg"])
        self.theme_manager.apply_ttk(ttk.Style(self))

    def clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.container.configure(bg=self.colors["bg"])

    def toggle_theme(self):
        self.theme_manager.toggle()
        self.apply_theme()
        if self.current_teacher:
            self.show_dashboard(self.current_teacher)
        else:
            self.show_login()

    def show_login(self):
        self.current_teacher = None
        self.apply_theme()
        self.clear_screen()
        LoginFrame(self.container, self).pack(fill="both", expand=True)

    def show_dashboard(self, teacher):
        self.current_teacher = teacher
        self.login_form_values = {
            "teacher_id": "",
            "password": "",
            "show_password": False,
        }
        self.apply_theme()
        self.clear_screen()
        TeacherDashboard(self.container, self, teacher).pack(fill="both", expand=True)


if __name__ == "__main__":
    app = ReservationApp()
    app.mainloop()
