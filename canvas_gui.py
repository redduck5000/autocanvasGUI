#!/usr/bin/env python3
"""Simple Tkinter GUI for managing Canvas course enrollments.

This interface wraps the existing :mod:`autocanvas` utilities and exposes
basic operations for course administrators:

* Retrieve all courses available to the supplied API key.
* Display current enrollments for a selected course.
* Add or remove students from the course by supplying a list of identifiers.

The GUI keeps a local cache of course and enrollment data to avoid repeated
API calls when working with large institutions.  The cache is refreshed when
changes are made so the view stays in sync with Canvas.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List

from canvasapi import Canvas

from autocanvas import CanvasManager


class CanvasGUI:
    """Main window class that wires the Canvas manager with Tkinter widgets."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Autocanvas GUI")

        # API configuration frame
        api_frame = ttk.Frame(root, padding=5)
        api_frame.grid(row=0, column=0, sticky="ew")
        api_frame.columnconfigure(1, weight=1)

        ttk.Label(api_frame, text="API URL:").grid(row=0, column=0, sticky="e")
        self.api_url_var = tk.StringVar(value="https://canvas.vu.nl")
        ttk.Entry(api_frame, textvariable=self.api_url_var, width=40).grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky="e")
        self.api_key_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=40).grid(
            row=1, column=1, sticky="ew"
        )

        ttk.Button(api_frame, text="Load Courses", command=self.load_courses).grid(
            row=2, column=0, columnspan=2, pady=(5, 0)
        )

        # Course selection
        ttk.Label(root, text="Course:").grid(row=1, column=0, sticky="w", padx=5)
        self.course_var = tk.StringVar()
        self.course_combo = ttk.Combobox(root, textvariable=self.course_var, state="readonly", width=60)
        self.course_combo.grid(row=2, column=0, padx=5, sticky="ew")
        self.course_combo.bind("<<ComboboxSelected>>", self.load_students)

        # Student input
        ttk.Label(root, text="Students (one per line):").grid(row=3, column=0, sticky="w", padx=5)
        self.students_text = tk.Text(root, height=8, width=60)
        self.students_text.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        action_frame = ttk.Frame(root)
        action_frame.grid(row=5, column=0, pady=5)
        ttk.Button(action_frame, text="Add Students", command=self.add_students).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Remove Students", command=self.remove_students).grid(row=0, column=1, padx=5)

        # Current enrollment list
        ttk.Label(root, text="Current Students:").grid(row=6, column=0, sticky="w", padx=5)
        self.student_list = tk.Listbox(root, height=15, width=60)
        self.student_list.grid(row=7, column=0, padx=5, pady=5, sticky="nsew")
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.student_list.yview)
        scrollbar.grid(row=7, column=1, sticky="ns")
        self.student_list.configure(yscrollcommand=scrollbar.set)

        root.columnconfigure(0, weight=1)
        root.rowconfigure(7, weight=1)

        # Canvas interaction state
        self.canvas: Canvas | None = None
        self.manager: CanvasManager | None = None
        self.courses: List[Canvas] = []
        self.enrollment_cache: Dict[int, List] = {}

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _selected_course_id(self) -> int | None:
        course_info = self.course_var.get()
        if not course_info:
            return None
        try:
            return int(course_info.split(":", 1)[0])
        except ValueError:
            return None

    def _parse_student_ids(self) -> List[str]:
        text = self.students_text.get("1.0", tk.END)
        ids = [line.strip() for line in text.splitlines() if line.strip()]
        return ids

    def _determine_id_type(self, ids: List[str]) -> str:
        # Heuristic: numeric IDs are treated as sis_user_id, otherwise login_id
        if ids and all(s.isdigit() for s in ids):
            return "sis_user_id"
        return "login_id"

    def _ensure_manager(self) -> bool:
        if not self.canvas:
            messagebox.showerror("Error", "Load courses first.")
            return False
        if not self.manager:
            self.manager = CanvasManager(logging.WARNING)
            self.manager.canvas = self.canvas
        return True

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def load_courses(self) -> None:
        api_url = self.api_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        if not api_url or not api_key:
            messagebox.showerror("Error", "API URL and key are required.")
            return
        try:
            self.canvas = Canvas(api_url, api_key)
            self.courses = sorted(list(self.canvas.get_courses()), key=lambda c: c.name.lower())
            course_names = [f"{c.id}: {c.name}" for c in self.courses]
            self.course_combo["values"] = course_names
            if course_names:
                self.course_combo.current(0)
                self.load_students()
            messagebox.showinfo("Courses Loaded", f"Retrieved {len(course_names)} courses.")
        except Exception as exc:  # pragma: no cover - canvasapi provides rich errors
            messagebox.showerror("Error", str(exc))

    def load_students(self, event: tk.Event | None = None) -> None:
        if not self._ensure_manager():
            return
        course_id = self._selected_course_id()
        if not course_id:
            return
        if course_id not in self.enrollment_cache:
            try:
                self.manager.course = self.canvas.get_course(course_id)
                enrollments = list(self.manager.course.get_enrollments(role=["StudentEnrollment"]))
                self.enrollment_cache[course_id] = enrollments
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
        enrollments = self.enrollment_cache[course_id]
        self.student_list.delete(0, tk.END)
        for e in enrollments:
            u = e.user
            self.student_list.insert(tk.END, f"{u['sortable_name']} ({u['id']})")

    def add_students(self) -> None:
        if not self._ensure_manager():
            return
        course_id = self._selected_course_id()
        if not course_id:
            messagebox.showerror("Error", "Select a course first.")
            return
        ids = self._parse_student_ids()
        if not ids:
            messagebox.showerror("Error", "Enter at least one student ID.")
            return
        id_type = self._determine_id_type(ids)
        try:
            self.manager.course = self.canvas.get_course(course_id)
            enrollments = self.manager.get_target_enrollments(
                ids, id_type, "new", [], ["StudentEnrollment"]
            )
            self.manager.handle_enrollments("new-active", enrollments)
            self.enrollment_cache.pop(course_id, None)
            self.load_students()
            messagebox.showinfo("Success", f"Added {len(ids)} students.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def remove_students(self) -> None:
        if not self._ensure_manager():
            return
        course_id = self._selected_course_id()
        if not course_id:
            messagebox.showerror("Error", "Select a course first.")
            return
        ids = self._parse_student_ids()
        if not ids:
            messagebox.showerror("Error", "Enter at least one student ID.")
            return
        id_type = self._determine_id_type(ids)
        try:
            self.manager.course = self.canvas.get_course(course_id)
            enrollments = self.manager.get_target_enrollments(
                ids, id_type, "targets", [], ["StudentEnrollment"]
            )
            self.manager.handle_enrollments("delete", enrollments)
            self.enrollment_cache.pop(course_id, None)
            self.load_students()
            messagebox.showinfo("Success", f"Removed {len(enrollments)} students.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main() -> None:
    root = tk.Tk()
    CanvasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
