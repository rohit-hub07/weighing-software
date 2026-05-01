import os
import random
import re
import sqlite3
import threading
import tempfile
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import unquote

import bcrypt
import requests
from PIL import Image, ImageTk
from admin_tab import AdminTab
from report_tab import ReportTab

try:
    from twilio.rest import Client
except ImportError:
    raise ImportError("twilio is required. Install it using: pip install twilio")


DB_FILE = "weighment_data.db"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin@123"
DEFAULT_USER_USERNAME = "operator"
DEFAULT_USER_PASSWORD = "User@123"


class WeighmentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weighment Section")
        self.root.geometry("1080x760")
        self.root.minsize(900, 620)

        self.colors = {
            "background": "#f8fafc",
            "surface": "#ffffff",
            "surface_alt": "#f1f5f9",
            "shadow": "#dbe4ee",
            "border": "#e2e8f0",
            "text": "#0f172a",
            "muted_text": "#475569",
            "field": "#f8fafc",
            "success": "#16a34a",
            "success_hover": "#15803d",
            "blue": "#2563eb",
            "blue_hover": "#1d4ed8",
            "blue_pressed": "#1e40af",
            "orange": "#f97316",
            "orange_hover": "#ea580c",
            "red": "#dc2626",
            "red_hover": "#b91c1c",
        }

        self._setup_modern_theme()

        self.current_weight = 0
        self.gross_weight = None
        self.tare_weight = None
        self.net_weight = None

        self.session_user: str | None = None
        self.session_user_id: int | None = None
        self.session_role: str | None = None
        self.session_status_var = tk.StringVar(value="Not logged in")
        self.subscription_info_var = tk.StringVar(value="")
        self.login_username_var = tk.StringVar()
        self.login_password_var = tk.StringVar()
        self.subscription_warning_shown = False
        self.last_subscription_check: datetime | None = None
        self.login_background_image = None
        self.login_background_photo = None
        self.login_background_window = None
        self.login_card_window = None
        self.login_canvas = None

        self.serial_no_var = tk.StringVar(value=str(self._get_next_serial_no()))
        self.vehicle_no_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.challan_var = tk.StringVar()
        self.customer_code_var = tk.StringVar()
        self.customer_name_var = tk.StringVar()
        self.product_code_var = tk.StringVar()
        self.product_name_var = tk.StringVar()
        self.source_code_var = tk.StringVar()
        self.source_name_var = tk.StringVar()
        self.desti_code_var = tk.StringVar()
        self.desti_name_var = tk.StringVar()
        self.transporter_code_var = tk.StringVar()
        self.transporter_name_var = tk.StringVar()

        self.twilio_sid_var = tk.StringVar(value=os.getenv("TWILIO_ACCOUNT_SID", ""))
        self.twilio_token_var = tk.StringVar(value=os.getenv("TWILIO_AUTH_TOKEN", ""))
        self.twilio_sms_from_var = tk.StringVar(value=os.getenv("TWILIO_SMS_FROM", ""))
        self.twilio_whatsapp_from_var = tk.StringVar(value=os.getenv("TWILIO_WHATSAPP_FROM", ""))
        self.sms_to_var = tk.StringVar(value=os.getenv("SMS_TO", ""))
        self.whatsapp_to_var = tk.StringVar(value=os.getenv("WHATSAPP_TO", ""))
        self.telegram_bot_token_var = tk.StringVar(value=os.getenv("TELEGRAM_BOT_TOKEN", ""))
        self.telegram_chat_id_var = tk.StringVar(value=os.getenv("TELEGRAM_CHAT_ID", ""))
        self.message_status_var = tk.StringVar(value="Messaging: Ready")

        self.live_weight_var = tk.StringVar(value="00000 kg")
        self.gross_var = tk.StringVar(value="-")
        self.tare_var = tk.StringVar(value="-")
        self.net_var = tk.StringVar(value="-")

        self.notebook: ttk.Notebook | None = None
        self.weighment_frame: ttk.Frame | None = None
        self.admin_frame: ttk.Frame | None = None
        self.report_frame: ttk.Frame | None = None

        self._ensure_database()
        self._load_saved_messaging_settings()
        self._show_login_screen()
        self._update_datetime()
        self.generate_weight()

    def _setup_modern_theme(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.root.configure(bg=self.colors["background"])
        self.root.option_add("*Font", ("Segoe UI", 10))

        style.configure(".", background=self.colors["background"], foreground=self.colors["text"])
        style.configure("App.TFrame", background=self.colors["background"])
        style.configure("Card.TFrame", background=self.colors["surface"])
        style.configure("Card.TLabelframe", background=self.colors["surface"], borderwidth=0, relief="flat", padding=18)
        style.configure(
            "Card.TLabelframe.Label",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure("SectionTitle.TLabel", background=self.colors["surface"], foreground=self.colors["text"], font=("Segoe UI Semibold", 11))
        style.configure("Muted.TLabel", background=self.colors["surface"], foreground=self.colors["muted_text"])
        style.configure("Value.TLabel", background=self.colors["surface"], foreground=self.colors["text"], font=("Segoe UI Semibold", 11))
        style.configure("HeroValue.TLabel", background=self.colors["surface"], foreground=self.colors["success"], font=("Consolas", 48, "bold"))
        style.configure("HeroNote.TLabel", background=self.colors["surface"], foreground=self.colors["muted_text"], font=("Segoe UI", 9))
        style.configure("StatusBar.TLabel", background=self.colors["background"], foreground=self.colors["muted_text"])

        style.configure(
            "Field.TEntry",
            fieldbackground=self.colors["field"],
            background=self.colors["field"],
            foreground=self.colors["text"],
            padding=(10, 8),
            relief="flat",
            borderwidth=0,
        )
        style.map("Field.TEntry", fieldbackground=[("focus", self.colors["surface"]), ("!disabled", self.colors["field"])])

        style.configure(
            "Primary.TButton",
            background=self.colors["blue"],
            foreground="white",
            padding=(16, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("Primary.TButton", background=[("active", self.colors["blue_hover"]), ("pressed", self.colors["blue_pressed"])])

        style.configure(
            "Success.TButton",
            background=self.colors["success"],
            foreground="white",
            padding=(16, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("Success.TButton", background=[("active", self.colors["success_hover"]), ("pressed", self.colors["success_hover"])])

        style.configure(
            "Warning.TButton",
            background=self.colors["orange"],
            foreground="white",
            padding=(16, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("Warning.TButton", background=[("active", self.colors["orange_hover"]), ("pressed", self.colors["orange_hover"])])

        style.configure(
            "Danger.TButton",
            background=self.colors["red"],
            foreground="white",
            padding=(16, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("Danger.TButton", background=[("active", self.colors["red_hover"]), ("pressed", self.colors["red_hover"])])

        style.configure(
            "Ghost.TButton",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            padding=(14, 9),
            borderwidth=0,
            relief="flat",
        )
        style.map("Ghost.TButton", background=[("active", self.colors["surface_alt"]), ("pressed", self.colors["border"])])

        style.configure("Modern.TNotebook", background=self.colors["background"], borderwidth=0)
        style.configure(
            "Modern.TNotebook.Tab",
            background=self.colors["border"],
            foreground=self.colors["muted_text"],
            padding=(16, 10),
            borderwidth=0,
        )
        style.map(
            "Modern.TNotebook.Tab",
            background=[("selected", self.colors["surface"]), ("active", self.colors["surface_alt"])],
            foreground=[("selected", self.colors["text"])],
        )

        style.configure(
            "Modern.Treeview",
            background=self.colors["surface"],
            fieldbackground=self.colors["surface"],
            foreground=self.colors["text"],
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=self.colors["surface_alt"],
            foreground=self.colors["text"],
            relief="flat",
            padding=(8, 8),
        )
        style.map("Modern.Treeview", background=[("selected", self.colors["blue"])], foreground=[("selected", "white")])

    def _create_shadow_card(
        self,
        parent: tk.Widget,
        *,
        fill: str = "x",
        expand: bool = False,
        padx: tuple[int, int] | int = 0,
        pady: tuple[int, int] | int = 0,
        offset: int = 6,
    ) -> ttk.Frame:
        shadow = tk.Frame(parent, bg=self.colors["shadow"], bd=0, highlightthickness=0)
        shadow.pack(fill=fill, expand=expand, padx=padx, pady=pady)

        card = ttk.Frame(shadow, style="Card.TFrame", padding=0)
        card.pack(fill="both", expand=True, padx=(0, offset), pady=(0, offset))
        return card

    def _show_login_screen(self, use_background: bool = True) -> None:
        self._clear_root()
        self.root.title("Weighment Section - Login")

        self.login_background_window = None
        self.login_card_window = None
        self.login_canvas = None

        background_color = self.colors["background"]
        wrapper = tk.Frame(self.root, bg=background_color)
        wrapper.pack(fill="both", expand=True)

        self.login_canvas = tk.Canvas(wrapper, highlightthickness=0, bd=0, bg=background_color)
        self.login_canvas.pack(fill="both", expand=True)
        self.login_canvas.bind("<Configure>", self._update_login_background)

        if use_background:
            background_path = self._get_login_background_path()
            if background_path:
                self._load_login_background(background_path)
            else:
                self.login_background_image = None
                self.login_background_photo = None
        else:
            self.login_background_image = None
            self.login_background_photo = None

        shadow = tk.Frame(self.login_canvas, bg=self.colors["shadow"], bd=0, highlightthickness=0)
        self.login_card_window = self.login_canvas.create_window(0, 0, window=shadow, anchor="center")

        card = ttk.Frame(shadow, style="Card.TFrame", padding=24)
        card.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))

        ttk.Label(card, text="Weighbridge Access", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(card, text="Sign in to the operator dashboard", style="HeroNote.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )

        ttk.Label(card, text="Username", style="Muted.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        username_entry = ttk.Entry(card, textvariable=self.login_username_var, width=34, style="Field.TEntry")
        username_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(card, text="Password", style="Muted.TLabel").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        password_entry = ttk.Entry(card, textvariable=self.login_password_var, show="*", width=34, style="Field.TEntry")
        password_entry.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

        ttk.Button(card, text="Login", command=self.login, style="Success.TButton").grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=6, pady=(16, 0)
        )

        card.columnconfigure(1, weight=1)

        password_entry.bind("<Return>", lambda _e: self.login())
        username_entry.focus_set()
        self._update_login_background()

    def _get_login_background_path(self) -> str | None:
        image_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "images",
            "weighing_bridge_img.jpeg",
        )
        return image_path if os.path.exists(image_path) else None

    def _load_login_background(self, image_path: str) -> None:
        try:
            self.login_background_image = Image.open(image_path)
        except Exception:
            self.login_background_image = None

    def _update_login_background(self, event: tk.Event | None = None) -> None:
        if not self.login_canvas:
            return

        canvas_width = max(1, self.login_canvas.winfo_width())
        canvas_height = max(1, self.login_canvas.winfo_height())

        if self.login_background_image is not None:
            image = self.login_background_image.copy()
            image_ratio = image.width / image.height
            canvas_ratio = canvas_width / canvas_height

            if canvas_ratio > image_ratio:
                new_width = canvas_width
                new_height = max(1, int(canvas_width / image_ratio))
            else:
                new_height = canvas_height
                new_width = max(1, int(canvas_height * image_ratio))

            image = image.resize((new_width, new_height), Image.LANCZOS)
            self.login_background_photo = ImageTk.PhotoImage(image)

            if self.login_background_window is None:
                self.login_background_window = self.login_canvas.create_image(
                    0,
                    0,
                    image=self.login_background_photo,
                    anchor="nw",
                )
            else:
                self.login_canvas.itemconfigure(self.login_background_window, image=self.login_background_photo)

            self.login_canvas.tag_lower(self.login_background_window)
            self.login_canvas.coords(
                self.login_background_window,
                (canvas_width - new_width) // 2,
                (canvas_height - new_height) // 2,
            )
        elif self.login_background_window is not None:
            self.login_canvas.delete(self.login_background_window)
            self.login_background_window = None

        if self.login_card_window is not None:
            self.login_canvas.coords(self.login_card_window, canvas_width // 2, canvas_height // 2)

    def _clear_root(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

    def login(self) -> None:
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Login Error", "Username and password are required.")
            return

        role = None
        if self._authenticate("admins", username, password):
            role = "admin"
        else:
            user = self._get_user_with_subscription(username)
            if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
                self._refresh_user_subscription_status(user["user_id"])
                user = self._get_user_with_subscription(username)

                if user and user["subscription_status"] == "active":
                    role = "user"
                    self.session_user_id = int(user["user_id"])
                    self.subscription_warning_shown = False
                    self.last_subscription_check = None

                    end_date = datetime.strptime(user["subscription_end"], "%Y-%m-%d").date()
                    remaining_days = (end_date - datetime.now().date()).days
                    self.subscription_info_var.set(f"Subscription active: {remaining_days} day(s) remaining")
                    if remaining_days <= 7:
                        messagebox.showwarning(
                            "Subscription Warning",
                            f"Your subscription will expire in {remaining_days} day(s).",
                        )
                else:
                    messagebox.showerror("Access Denied", "Subscription expired. Please contact admin.")
                    return

        if not role:
            messagebox.showerror("Login Error", "Invalid username or password.")
            return

        self.session_user = username
        self.session_role = role
        if role == "admin":
            self.session_user_id = None
            self.subscription_info_var.set("Admin access: unrestricted")
        self.session_status_var.set(f"Logged in as {username} ({role})")
        self.login_password_var.set("")
        self._build_ui()

    def logout(self) -> None:
        if not self.session_user:
            return

        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return

        self.session_user = None
        self.session_user_id = None
        self.session_role = None
        self.session_status_var.set("Not logged in")
        self.subscription_info_var.set("")
        self.subscription_warning_shown = False
        self.last_subscription_check = None
        self.clear_fields()
        self._show_login_screen()

    def _force_logout_due_subscription_expiry(self) -> None:
        self.session_user = None
        self.session_user_id = None
        self.session_role = None
        self.session_status_var.set("Not logged in")
        self.subscription_info_var.set("")
        self.subscription_warning_shown = False
        self.last_subscription_check = None
        self.clear_fields()
        self._show_login_screen()

    def _refresh_current_user_subscription_state(self) -> None:
        if self.session_role != "user" or not self.session_user_id:
            return

        now = datetime.now()
        if self.last_subscription_check and (now - self.last_subscription_check).total_seconds() < 30:
            return
        self.last_subscription_check = now

        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT start_date, end_date, status FROM subscriptions WHERE user_id = ?",
                (self.session_user_id,),
            )
            row = cursor.fetchone()

        if not row:
            return

        end_date = datetime.strptime(row[1], "%Y-%m-%d").date()
        remaining_days = (end_date - now.date()).days
        self.subscription_info_var.set(f"Subscription active: {remaining_days} day(s) remaining")

        if remaining_days <= 7 and not self.subscription_warning_shown:
            self.subscription_warning_shown = True
            self._show_error("Subscription Warning", f"Your subscription will expire in {remaining_days} day(s).")

        if row[2] != "active" or remaining_days < 0:
            with self._get_db_connection(system=True) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE subscriptions SET status = 'expired' WHERE user_id = ?",
                    (self.session_user_id,),
                )
                connection.commit()

            self._show_error("Access Denied", "Subscription expired. Please contact admin.")
            self._force_logout_due_subscription_expiry()

    def _get_user_with_subscription(self, username: str) -> dict | None:
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.password, s.start_date, s.end_date, s.status
                FROM users u
                LEFT JOIN subscriptions s ON s.user_id = u.id
                WHERE u.username = ?
                """,
                (username,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        if row[3] is None or row[4] is None or row[5] is None:
            self._create_default_subscription_for_user(int(row[0]))
            return self._get_user_with_subscription(username)

        return {
            "user_id": row[0],
            "username": row[1],
            "password": row[2],
            "subscription_start": row[3],
            "subscription_end": row[4],
            "subscription_status": row[5],
        }

    def _create_default_subscription_for_user(self, user_id: int) -> None:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=365)
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO subscriptions (user_id, start_date, end_date, status)
                VALUES (?, ?, ?, 'active')
                """,
                (user_id, start_date.isoformat(), end_date.isoformat()),
            )
            connection.commit()

    def _refresh_user_subscription_status(self, user_id: int) -> None:
        today = datetime.now().date().isoformat()
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET status = CASE
                    WHEN date(end_date) < date(?) THEN 'expired'
                    ELSE status
                END
                WHERE user_id = ?
                """,
                (today, user_id),
            )
            connection.commit()

    def refresh_all_subscription_statuses(self) -> None:
        today = datetime.now().date().isoformat()
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET status = CASE
                    WHEN date(end_date) < date(?) THEN 'expired'
                    ELSE status
                END
                """,
                (today,),
            )
            connection.commit()

    def is_admin_authenticated(self) -> bool:
        return self.session_role == "admin"

    def _authenticate(self, table_name: str, username: str, password: str) -> bool:
        if table_name not in {"users", "admins"}:
            return False

        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT password FROM {table_name} WHERE username = ?", (username,))
            row = cursor.fetchone()

        if not row:
            return False

        try:
            return bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8"))
        except ValueError:
            return False

    def _admin_reauthentication_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Admin Authentication")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.colors["background"])

        username_var = tk.StringVar()
        password_var = tk.StringVar()

        frame = ttk.Frame(dialog, style="App.TFrame", padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Admin username", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        user_entry = ttk.Entry(frame, textvariable=username_var, width=30, style="Field.TEntry")
        user_entry.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(frame, text="Admin password", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        pass_entry = ttk.Entry(frame, textvariable=password_var, show="*", width=30, style="Field.TEntry")
        pass_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        def _do_auth() -> None:
            username = username_var.get().strip()
            password = password_var.get().strip()
            if not username or not password:
                messagebox.showerror("Auth Error", "Admin username and password are required.", parent=dialog)
                return

            if not self._authenticate("admins", username, password):
                messagebox.showerror("Auth Error", "Invalid admin credentials.", parent=dialog)
                return

            self.session_user = username
            self.session_role = "admin"
            self.session_status_var.set(f"Logged in as {username} (admin)")
            dialog.destroy()
            self._build_ui(select_admin=True)
            messagebox.showinfo("Authenticated", "Admin access granted.")

        action_row = ttk.Frame(frame)
        action_row.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(8, 4))
        ttk.Button(action_row, text="Authenticate", command=_do_auth, style="Success.TButton").pack(side="left", padx=(0, 10))
        ttk.Button(action_row, text="Cancel", command=dialog.destroy, style="Ghost.TButton").pack(side="left")

        pass_entry.bind("<Return>", lambda _e: _do_auth())
        user_entry.focus_set()

    def _build_admin_locked_tab(self, container: ttk.Frame) -> None:
        card = ttk.LabelFrame(container, text="Admin Access Required", style="Card.TLabelframe", padding=18)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            card,
            text=(
                "Admin data is protected. To access admin dashboard, "
                "authenticate with admin credentials."
            ),
            wraplength=500,
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(card, text="Login as Admin", command=self._admin_reauthentication_dialog, style="Primary.TButton").pack(anchor="w")

    def _sqlite_authorizer(self, action, arg1, _arg2, _db_name, _trigger_name) -> int:
        restricted_tables = {"admins", "subscriptions"}
        table_name = (arg1 or "").lower()
        blocked_actions = {
            sqlite3.SQLITE_READ,
            sqlite3.SQLITE_INSERT,
            sqlite3.SQLITE_UPDATE,
            sqlite3.SQLITE_DELETE,
            sqlite3.SQLITE_DROP_TABLE,
            sqlite3.SQLITE_ALTER_TABLE,
        }

        if self.session_role != "admin" and table_name in restricted_tables and action in blocked_actions:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def _build_ui(self, select_admin: bool = False) -> None:
        if not self.session_user:
            self._show_login_screen()
            return

        self._clear_root()
        self.root.title("Weighment Section")
        self.root.configure(bg=self.colors["background"])

        outer = ttk.Frame(self.root, style="App.TFrame", padding=16)
        outer.pack(fill="both", expand=True)

        header = self._create_shadow_card(outer, fill="x", pady=(0, 14), offset=4)
        header.columnconfigure(0, weight=1)
        header_body = ttk.Frame(header, style="Card.TFrame")
        header_body.pack(fill="x", expand=True)

        ttk.Label(header_body, textvariable=self.session_status_var, style="SectionTitle.TLabel").pack(side="left")
        if self.session_role == "user":
            ttk.Label(header_body, textvariable=self.subscription_info_var, style="Muted.TLabel").pack(side="left", padx=(14, 0))
        if self.session_role != "admin":
            ttk.Button(header_body, text="Admin Login", command=self._admin_reauthentication_dialog, style="Ghost.TButton").pack(
                side="right", padx=(8, 0), pady=2
            )
        ttk.Button(header_body, text="Logout", command=self.logout, style="Ghost.TButton").pack(side="right", pady=2)

        notebook = ttk.Notebook(outer, style="Modern.TNotebook")
        notebook.pack(fill="both", expand=True)
        self.notebook = notebook

        weighment_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        admin_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        report_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        self.weighment_frame = weighment_tab
        self.admin_frame = admin_tab
        self.report_frame = report_tab

        notebook.add(weighment_tab, text="Weighment")
        notebook.add(admin_tab, text="Admin")
        notebook.add(report_tab, text="Report")

        self._build_weighment_tab(weighment_tab)
        if self.session_role == "admin":
            self._build_admin_tab(admin_tab)
        else:
            self._build_admin_locked_tab(admin_tab)
        self._build_report_tab(report_tab)

        if select_admin:
            notebook.select(admin_tab)

        ttk.Label(
            outer,
            text="© Copyright Helping Hands Technologies. All Rights Reserved",
            anchor="center",
            justify="center",
            style="StatusBar.TLabel",
        ).pack(fill="x", pady=(10, 0))

    def _build_weighment_tab(self, container: ttk.Frame) -> None:
        hero_card = self._create_shadow_card(container, fill="x", pady=(0, 14), offset=4)
        ttk.Label(hero_card, text="Live Weight", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hero_card, textvariable=self.live_weight_var, style="HeroValue.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(hero_card, text="Auto-updating every second", style="HeroNote.TLabel").grid(row=2, column=0, sticky="w", pady=(2, 0))
        hero_card.columnconfigure(0, weight=1)

        entry_card = self._create_shadow_card(container, fill="x", pady=(0, 14), offset=4)
        sections_row = ttk.Frame(entry_card, style="Card.TFrame")
        sections_row.pack(fill="x")
        sections_row.columnconfigure(0, weight=1)
        sections_row.columnconfigure(1, weight=1)
        sections_row.columnconfigure(2, weight=1)

        vehicle_card = ttk.LabelFrame(sections_row, text="Vehicle Info", style="Card.TLabelframe", padding=16)
        customer_card = ttk.LabelFrame(sections_row, text="Customer Info", style="Card.TLabelframe", padding=16)
        transport_card = ttk.LabelFrame(sections_row, text="Transport Info", style="Card.TLabelframe", padding=16)

        vehicle_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        customer_card.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        transport_card.grid(row=0, column=2, sticky="nsew")

        self._render_labeled_fields(
            vehicle_card,
            [
                ("Serial No", self.serial_no_var, True),
                ("Vehicle No", self.vehicle_no_var, False),
                ("Date", self.date_var, True),
                ("Time", self.time_var, True),
                ("Challan", self.challan_var, False),
            ],
        )
        self._render_labeled_fields(
            customer_card,
            [
                ("Customer Code", self.customer_code_var, False),
                ("Customer Name", self.customer_name_var, False),
                ("Product Code", self.product_code_var, False),
                ("Product Name", self.product_name_var, False),
            ],
        )
        self._render_labeled_fields(
            transport_card,
            [
                ("Source Code", self.source_code_var, False),
                ("Source Name", self.source_name_var, False),
                ("Destination Code", self.desti_code_var, False),
                ("Destination Name", self.desti_name_var, False),
                ("Transporter Code", self.transporter_code_var, False),
                ("Transporter Name", self.transporter_name_var, False),
            ],
        )

        lower_row = ttk.Frame(container, style="App.TFrame")
        lower_row.pack(fill="x")
        lower_row.columnconfigure(0, weight=1)
        lower_row.columnconfigure(1, weight=1)

        result_shadow = tk.Frame(lower_row, bg=self.colors["shadow"], bd=0, highlightthickness=0)
        result_shadow.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        result_card = ttk.Frame(result_shadow, style="Card.TFrame", padding=18)
        result_card.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 4))

        action_shadow = tk.Frame(lower_row, bg=self.colors["shadow"], bd=0, highlightthickness=0)
        action_shadow.grid(row=0, column=1, sticky="nsew")
        action_card = ttk.Frame(action_shadow, style="Card.TFrame", padding=18)
        action_card.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 4))

        ttk.Label(result_card, text="Captured Weights", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(result_card, text="Gross Weight", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.gross_var, style="Value.TLabel").grid(row=1, column=1, sticky="e", padx=6, pady=8)
        ttk.Label(result_card, text="Tare Weight", style="Muted.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.tare_var, style="Value.TLabel").grid(row=2, column=1, sticky="e", padx=6, pady=8)
        ttk.Label(result_card, text="Net Weight", style="Muted.TLabel").grid(row=3, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.net_var, style="Value.TLabel").grid(row=3, column=1, sticky="e", padx=6, pady=8)
        result_card.columnconfigure(0, weight=1)
        result_card.columnconfigure(1, weight=0)

        ttk.Label(action_card, text="Actions", style="SectionTitle.TLabel").pack(anchor="w", pady=(0, 10))
        button_grid = ttk.Frame(action_card, style="Card.TFrame")
        button_grid.pack(fill="x")
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)

        ttk.Button(button_grid, text="Gross Weight", command=self.capture_gross_weight, style="Primary.TButton").grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=6
        )
        ttk.Button(button_grid, text="Tare Weight", command=self.capture_tare_weight, style="Primary.TButton").grid(
            row=0, column=1, sticky="ew", pady=6
        )
        ttk.Button(button_grid, text="Net Weight", command=self.calculate_net_weight, style="Primary.TButton").grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=6
        )
        ttk.Button(button_grid, text="Save", command=self.save_to_db, style="Success.TButton").grid(
            row=1, column=1, sticky="ew", pady=6
        )
        ttk.Button(button_grid, text="Print", command=self.print_slip, style="Warning.TButton").grid(
            row=2, column=0, sticky="ew", padx=(0, 10), pady=6
        )
        ttk.Button(button_grid, text="Clear", command=self.clear_fields, style="Danger.TButton").grid(
            row=2, column=1, sticky="ew", pady=6
        )

        self._build_messaging_actions(container, pady=(14, 0))

    def _render_labeled_fields(
        self,
        card: ttk.LabelFrame,
        fields: list[tuple[str, tk.StringVar, bool]],
    ) -> None:
        for index, (label_text, variable, readonly) in enumerate(fields):
            ttk.Label(card, text=label_text, style="Muted.TLabel").grid(row=index, column=0, sticky="w", padx=6, pady=6)
            entry = ttk.Entry(card, textvariable=variable, width=28, style="Field.TEntry")
            if readonly:
                entry.configure(state="readonly")
            entry.grid(row=index, column=1, sticky="ew", padx=6, pady=6)

        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)

    def _build_admin_tab(self, container: ttk.Frame) -> None:
        if self.session_role != "admin":
            self._build_admin_locked_tab(container)
            return

        self.admin_tab = AdminTab(
            container=container,
            get_db_connection=self._get_db_connection,
            db_file=DB_FILE,
            is_admin_fn=self.is_admin_authenticated,
            refresh_subscriptions_fn=self.refresh_all_subscription_statuses,
            save_credentials_fn=self._save_messaging_settings,
            messaging_vars={
                "twilio_sid": self.twilio_sid_var,
                "twilio_token": self.twilio_token_var,
                "sms_from": self.twilio_sms_from_var,
                "sms_to": self.sms_to_var,
                "whatsapp_from": self.twilio_whatsapp_from_var,
                "whatsapp_to": self.whatsapp_to_var,
                "telegram_token": self.telegram_bot_token_var,
                "telegram_chat_id": self.telegram_chat_id_var,
            },
        )
        self.admin_tab.build()

    def _build_messaging_actions(self, container: ttk.Frame, pady: tuple[int, int] = (0, 10)) -> None:
        messaging_card = self._create_shadow_card(container, fill="x", pady=pady, offset=4)

        ttk.Label(
            messaging_card,
            text="Configure credentials in Admin tab. Use the buttons below to send current slip.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=6, pady=(0, 8))

        messaging_buttons = ttk.Frame(messaging_card)
        messaging_buttons.grid(row=1, column=0, columnspan=4, sticky="w", padx=6, pady=(4, 2))

        ttk.Button(messaging_buttons, text="Send SMS", command=self.send_sms, style="Primary.TButton").pack(side="left", padx=(0, 12), pady=4)
        ttk.Button(messaging_buttons, text="Send WhatsApp", command=self.send_whatsapp, style="Primary.TButton").pack(
            side="left", padx=(0, 12), pady=4
        )
        ttk.Button(messaging_buttons, text="Send Telegram", command=self.send_telegram, style="Primary.TButton").pack(side="left", pady=4)

        ttk.Label(messaging_card, textvariable=self.message_status_var, style="Muted.TLabel").grid(
            row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 0)
        )

    def _build_report_tab(self, container: ttk.Frame) -> None:
        self.report_tab = ReportTab(container=container, get_db_connection=self._get_db_connection)
        self.report_tab.build()

    def refresh_report_table(self) -> None:
        if not hasattr(self, "report_tab"):
            return
        self.report_tab.refresh_table()

    def clear_report_filters(self) -> None:
        if hasattr(self, "report_tab"):
            self.report_tab.clear_filters()

    def _update_datetime(self) -> None:
        now = datetime.now()
        self.date_var.set(now.strftime("%d-%m-%Y"))
        self.time_var.set(now.strftime("%H:%M:%S"))
        self._refresh_current_user_subscription_state()
        self.root.after(1000, self._update_datetime)

    def generate_weight(self) -> None:
        self.current_weight = random.randint(1000, 50000)
        self.live_weight_var.set(f"{self.current_weight:05d} kg")
        self.root.after(1000, self.generate_weight)

    def capture_gross_weight(self) -> None:
        self.gross_weight = self.current_weight
        self.gross_var.set(f"{self.gross_weight} kg")
        self.calculate_net_weight()

    def capture_tare_weight(self) -> None:
        self.tare_weight = self.current_weight
        self.tare_var.set(f"{self.tare_weight} kg")
        self.calculate_net_weight()

    def calculate_net_weight(self) -> None:
        if self.gross_weight is None or self.tare_weight is None:
            self.net_weight = None
            self.net_var.set("-")
            return

        self.net_weight = self.gross_weight - self.tare_weight
        self.net_var.set(f"{self.net_weight} kg")

    def _get_db_connection(self, system: bool = False) -> sqlite3.Connection:
        connection = sqlite3.connect(DB_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        if not system:
            connection.set_authorizer(self._sqlite_authorizer)
        return connection

    def _get_next_serial_no(self) -> int:
        self._ensure_database()
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COALESCE(MAX(serial_no), 0) + 1 FROM weighment_records")
            return int(cursor.fetchone()[0])

    def _ensure_database(self) -> None:
        with self._get_db_connection(system=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS weighment_records (
                    serial_no INTEGER PRIMARY KEY,
                    vehicle_no TEXT NOT NULL,
                    weighment_date TEXT,
                    weighment_time TEXT,
                    challan TEXT,
                    customer_code TEXT,
                    customer_name TEXT,
                    product_code TEXT,
                    product_name TEXT,
                    source_code TEXT,
                    source_name TEXT,
                    destination_code TEXT,
                    destination_name TEXT,
                    transporter_code TEXT,
                    transporter_name TEXT,
                    gross_weight INTEGER NOT NULL,
                    tare_weight INTEGER NOT NULL,
                    net_weight INTEGER NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active', 'expired')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )

            self._seed_default_accounts(cursor)
            self._seed_default_subscriptions(cursor)
            connection.commit()

        self.refresh_all_subscription_statuses()

    def _seed_default_accounts(self, cursor: sqlite3.Cursor) -> None:
        admin_hash = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user_hash = bcrypt.hashpw(DEFAULT_USER_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        cursor.execute(
            "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
            (DEFAULT_ADMIN_USERNAME, admin_hash),
        )
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
            (DEFAULT_USER_USERNAME, user_hash),
        )

    def _seed_default_subscriptions(self, cursor: sqlite3.Cursor) -> None:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=365)
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]

        for user_id in user_ids:
            cursor.execute(
                """
                INSERT OR IGNORE INTO subscriptions (user_id, start_date, end_date, status)
                VALUES (?, ?, ?, 'active')
                """,
                (user_id, start_date.isoformat(), end_date.isoformat()),
            )

    def _messaging_settings(self) -> dict[str, tk.StringVar]:
        return {
            "twilio_sid": self.twilio_sid_var,
            "twilio_token": self.twilio_token_var,
            "sms_from": self.twilio_sms_from_var,
            "sms_to": self.sms_to_var,
            "whatsapp_from": self.twilio_whatsapp_from_var,
            "whatsapp_to": self.whatsapp_to_var,
            "telegram_token": self.telegram_bot_token_var,
            "telegram_chat_id": self.telegram_chat_id_var,
        }

    def _save_messaging_settings(self) -> bool:
        if self.session_role != "admin":
            self._show_error("Access Denied", "Admin authentication is required to save messaging credentials.")
            return False

        try:
            settings_payload = [(key, var.get().strip()) for key, var in self._messaging_settings().items()]
            with self._get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.executemany(
                    """
                    INSERT INTO app_settings (setting_key, setting_value)
                    VALUES (?, ?)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                    """,
                    settings_payload,
                )
                connection.commit()
            return True
        except Exception as exc:
            self._show_error("Save Error", f"Could not save messaging credentials: {exc}")
            return False

    def _load_saved_messaging_settings(self) -> None:
        with self._get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT setting_key, setting_value FROM app_settings "
                "WHERE setting_key IN ('twilio_sid', 'twilio_token', 'sms_from', 'sms_to', "
                "'whatsapp_from', 'whatsapp_to', 'telegram_token', 'telegram_chat_id')"
            )
            rows = cursor.fetchall()

        if not rows:
            return

        settings = self._messaging_settings()
        for key, value in rows:
            if key in settings and value:
                settings[key].set(value)

    def _compose_message(self) -> str:
        self.calculate_net_weight()
        gross_text = str(self.gross_weight) if self.gross_weight is not None else "N/A"
        tare_text = str(self.tare_weight) if self.tare_weight is not None else "N/A"
        net_text = str(self.net_weight) if self.net_weight is not None else "N/A"

        return (
            f"Weighment Slip\n"
            f"Serial: {self.serial_no_var.get()}\n"
            f"Vehicle: {self.vehicle_no_var.get().strip() or 'N/A'}\n"
            f"Date: {self.date_var.get()}  Time: {self.time_var.get()}\n"
            f"Challan: {self.challan_var.get().strip() or 'N/A'}\n"
            f"Customer: {self.customer_name_var.get().strip() or 'N/A'} ({self.customer_code_var.get().strip() or 'N/A'})\n"
            f"Product: {self.product_name_var.get().strip() or 'N/A'} ({self.product_code_var.get().strip() or 'N/A'})\n"
            f"Source: {self.source_name_var.get().strip() or 'N/A'} ({self.source_code_var.get().strip() or 'N/A'})\n"
            f"Destination: {self.desti_name_var.get().strip() or 'N/A'} ({self.desti_code_var.get().strip() or 'N/A'})\n"
            f"Transporter: {self.transporter_name_var.get().strip() or 'N/A'} ({self.transporter_code_var.get().strip() or 'N/A'})\n"
            f"Gross: {gross_text} kg\n"
            f"Tare: {tare_text} kg\n"
            f"Net: {net_text} kg"
        )

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.message_status_var.set(text))

    def _show_info(self, title: str, text: str) -> None:
        self.root.after(0, lambda: messagebox.showinfo(title, text))

    def _show_error(self, title: str, text: str) -> None:
        self.root.after(0, lambda: messagebox.showerror(title, text))

    def _run_in_background(self, send_fn, channel_name: str) -> None:
        message_text = self._compose_message()

        def _task() -> None:
            try:
                self._set_status(f"Messaging: Sending {channel_name}...")
                send_fn(message_text)
                self._set_status(f"Messaging: {channel_name} sent successfully")
                self._show_info("Message Sent", f"{channel_name} message sent successfully.")
            except Exception as exc:
                self._set_status(f"Messaging: {channel_name} failed")
                self._show_error("Messaging Error", str(exc))

        threading.Thread(target=_task, daemon=True).start()

    def send_sms(self) -> None:
        sid = self.twilio_sid_var.get().strip()
        token = self.twilio_token_var.get().strip()
        from_number = self.twilio_sms_from_var.get().strip()
        to_number = self.sms_to_var.get().strip()

        if not all([sid, token, from_number, to_number]):
            messagebox.showerror("Validation Error", "Fill Twilio SID, Token, SMS From and SMS To.")
            return

        def _send(message_text: str) -> None:
            client = Client(sid, token)
            client.messages.create(body=message_text, from_=from_number, to=to_number)

        self._run_in_background(_send, "SMS")

    def send_whatsapp(self) -> None:
        sid = self.twilio_sid_var.get().strip()
        token = self.twilio_token_var.get().strip()
        from_number = self.twilio_whatsapp_from_var.get().strip()
        to_number = self.whatsapp_to_var.get().strip()

        if not all([sid, token, from_number, to_number]):
            messagebox.showerror(
                "Validation Error", "Fill Twilio SID, Token, WhatsApp From and WhatsApp To."
            )
            return

        def _wa(number: str) -> str:
            return number if number.startswith("whatsapp:") else f"whatsapp:{number}"

        def _send(message_text: str) -> None:
            client = Client(sid, token)
            client.messages.create(body=message_text, from_=_wa(from_number), to=_wa(to_number))

        self._run_in_background(_send, "WhatsApp")

    def send_telegram(self) -> None:
        raw_token = self.telegram_bot_token_var.get().strip()
        raw_chat_id = self.telegram_chat_id_var.get().strip()

        # Allow users to paste env-style values such as BOT_TOKEN=... and CHAT_ID=...
        bot_token = re.sub(r"^\s*(?:TELEGRAM_)?BOT_TOKEN\s*=\s*", "", unquote(raw_token), flags=re.IGNORECASE)
        bot_token = bot_token.strip().strip('"').strip("'").replace(" ", "")

        chat_id = re.sub(r"^\s*(?:TELEGRAM_)?CHAT_ID\s*=\s*", "", unquote(raw_chat_id), flags=re.IGNORECASE)
        chat_id = chat_id.strip().strip('"').strip("'").replace(" ", "")

        if not bot_token or not chat_id:
            messagebox.showerror("Validation Error", "Fill Telegram Bot Token and Telegram Chat ID.")
            return

        if not re.fullmatch(r"\d{6,}:[A-Za-z0-9_-]{20,}", bot_token):
            messagebox.showerror(
                "Validation Error",
                "Telegram Bot Token looks invalid. Paste only the value after '=' (example: 123456789:ABC...).",
            )
            return

        if not (chat_id.startswith("@") or re.fullmatch(r"-?\d+", chat_id)):
            messagebox.showerror(
                "Validation Error",
                "Telegram Chat ID must be numeric (example: 5087327068 or -100...) or start with '@'.",
            )
            return

        def _send(message_text: str) -> None:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message_text},
                timeout=20,
            )
            payload = response.json()
            if response.status_code >= 400:
                raise RuntimeError(payload.get("description", f"Telegram API error: HTTP {response.status_code}"))
            if not payload.get("ok"):
                raise RuntimeError(payload.get("description", "Telegram API returned an unknown error."))

        self._run_in_background(_send, "Telegram")

    def save_to_db(self) -> None:
        vehicle_no = self.vehicle_no_var.get().strip()
        if not vehicle_no:
            messagebox.showerror("Validation Error", "Vehicle No cannot be empty.")
            return

        if self.gross_weight is None or self.tare_weight is None:
            messagebox.showerror("Validation Error", "Capture both Gross and Tare weights before saving.")
            return

        self.calculate_net_weight()

        self._ensure_database()
        with self._get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO weighment_records (
                    serial_no,
                    vehicle_no,
                    weighment_date,
                    weighment_time,
                    challan,
                    customer_code,
                    customer_name,
                    product_code,
                    product_name,
                    source_code,
                    source_name,
                    destination_code,
                    destination_name,
                    transporter_code,
                    transporter_name,
                    gross_weight,
                    tare_weight,
                    net_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(self.serial_no_var.get()),
                    vehicle_no,
                    self.date_var.get(),
                    self.time_var.get(),
                    self.challan_var.get().strip(),
                    self.customer_code_var.get().strip(),
                    self.customer_name_var.get().strip(),
                    self.product_code_var.get().strip(),
                    self.product_name_var.get().strip(),
                    self.source_code_var.get().strip(),
                    self.source_name_var.get().strip(),
                    self.desti_code_var.get().strip(),
                    self.desti_name_var.get().strip(),
                    self.transporter_code_var.get().strip(),
                    self.transporter_name_var.get().strip(),
                    self.gross_weight,
                    self.tare_weight,
                    self.net_weight,
                ),
            )
            connection.commit()

        messagebox.showinfo("Saved", "Weighment record saved successfully to SQLite.")
        self.serial_no_var.set(str(int(self.serial_no_var.get()) + 1))
        self.refresh_report_table()
        if hasattr(self, "admin_tab"):
            self.admin_tab.refresh_summary()

    def print_slip(self) -> None:
        if self.gross_weight is None or self.tare_weight is None:
            messagebox.showerror("Validation Error", "Capture both Gross and Tare weights before printing.")
            return

        slip_text = self._compose_message()

        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as temp_file:
                temp_file.write(slip_text)
                temp_path = temp_file.name

            if os.name == "nt":
                os.startfile(temp_path, "print")
                messagebox.showinfo("Print", "Print command sent to your default printer.")
            else:
                messagebox.showinfo("Print", f"Printing is only supported on Windows. Slip saved at: {temp_path}")
        except Exception as exc:
            messagebox.showerror("Print Error", f"Failed to print slip: {exc}")

    def clear_fields(self, increment_serial: bool = False) -> None:
        if increment_serial:
            self.serial_no_var.set(str(int(self.serial_no_var.get()) + 1))

        self.vehicle_no_var.set("")
        self.challan_var.set("")
        self.customer_code_var.set("")
        self.customer_name_var.set("")
        self.product_code_var.set("")
        self.product_name_var.set("")
        self.source_code_var.set("")
        self.source_name_var.set("")
        self.desti_code_var.set("")
        self.desti_name_var.set("")
        self.transporter_code_var.set("")
        self.transporter_name_var.set("")
        self.gross_weight = None
        self.tare_weight = None
        self.net_weight = None

        self.gross_var.set("-")
        self.tare_var.set("-")
        self.net_var.set("-")


def main() -> None:
    root = tk.Tk()
    app = WeighmentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
