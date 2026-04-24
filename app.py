import os
import random
import re
import sqlite3
import threading
import tempfile
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import unquote

import requests
from admin_tab import AdminTab
from report_tab import ReportTab

try:
    from twilio.rest import Client
except ImportError:
    raise ImportError("twilio is required. Install it using: pip install twilio")


DB_FILE = "weighment_data.db"


class WeighmentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weighment Section")
        self.root.geometry("1080x760")
        self.root.minsize(900, 620)

        self.current_weight = 0
        self.gross_weight = None
        self.tare_weight = None
        self.net_weight = None

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

        self._ensure_database()
        self._load_saved_messaging_settings()
        self._build_ui()
        self._update_datetime()
        self.generate_weight()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        weighment_tab = ttk.Frame(notebook, padding=12)
        admin_tab = ttk.Frame(notebook, padding=12)
        report_tab = ttk.Frame(notebook, padding=12)

        notebook.add(weighment_tab, text="Weighment")
        notebook.add(admin_tab, text="Admin")
        notebook.add(report_tab, text="Report")

        self._build_weighment_tab(weighment_tab)
        self._build_admin_tab(admin_tab)
        self._build_report_tab(report_tab)

        ttk.Label(
            outer,
            text="© Copyright Helping Hands Technologies. All Rights Reserved",
            anchor="center",
            justify="center",
            font=("Segoe UI", 9),
        ).pack(fill="x", pady=(8, 0))

    def _build_weighment_tab(self, container: ttk.Frame) -> None:
        input_card = ttk.LabelFrame(container, text="Weighment Entry", padding=12)
        input_card.pack(fill="x")

        ttk.Label(input_card, text="Serial No").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.serial_no_var, state="readonly", width=20).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="Vehicle No").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.vehicle_no_var, width=24).grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="Date").grid(row=0, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.date_var, state="readonly", width=20).grid(
            row=0, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="Time").grid(row=1, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.time_var, state="readonly", width=20).grid(
            row=1, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="CHALLAN").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.challan_var, width=24).grid(
            row=2, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="CUSTOMER Code").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.customer_code_var, width=24).grid(
            row=3, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(input_card, text="CUSTOMER Name").grid(row=3, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.customer_name_var, width=30).grid(
            row=3, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="PRODUCT Code").grid(row=4, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.product_code_var, width=24).grid(
            row=4, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(input_card, text="PRODUCT Name").grid(row=4, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.product_name_var, width=30).grid(
            row=4, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="SOURCE Code").grid(row=5, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.source_code_var, width=24).grid(
            row=5, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(input_card, text="SOURCE Name").grid(row=5, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.source_name_var, width=30).grid(
            row=5, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="DESTI Code").grid(row=6, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.desti_code_var, width=24).grid(
            row=6, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(input_card, text="DESTI Name").grid(row=6, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.desti_name_var, width=30).grid(
            row=6, column=3, sticky="w", padx=6, pady=6
        )

        ttk.Label(input_card, text="TRANSPOTER Code").grid(row=7, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.transporter_code_var, width=24).grid(
            row=7, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(input_card, text="TRANSPOTER Name").grid(row=7, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(input_card, textvariable=self.transporter_name_var, width=30).grid(
            row=7, column=3, sticky="w", padx=6, pady=6
        )

        weights_row = ttk.Frame(container, padding=(0, 14, 0, 10))
        weights_row.pack(fill="x")

        live_weight_card = ttk.LabelFrame(weights_row, text="Live Weight", padding=12)
        live_weight_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            live_weight_card,
            textvariable=self.live_weight_var,
            font=("Consolas", 36, "bold"),
            bg="black",
            fg="#28ff6d",
            padx=20,
            pady=14,
            relief="sunken",
            bd=4,
        ).pack(fill="both", expand=True)

        right_panel = ttk.Frame(weights_row)
        right_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        result_card = ttk.LabelFrame(right_panel, text="Captured Weights", padding=12)
        result_card.pack(fill="both", expand=True)

        ttk.Label(result_card, text="Gross Weight").grid(row=0, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.gross_var, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=1, sticky="w", padx=6, pady=8
        )

        ttk.Label(result_card, text="Tare Weight").grid(row=1, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.tare_var, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=1, sticky="w", padx=6, pady=8
        )

        ttk.Label(result_card, text="Net Weight").grid(row=2, column=0, sticky="w", padx=6, pady=8)
        ttk.Label(result_card, textvariable=self.net_var, font=("Segoe UI", 11, "bold")).grid(
            row=2, column=1, sticky="w", padx=6, pady=8
        )

        button_row = ttk.Frame(right_panel, padding=(0, 10, 0, 0))
        button_row.pack(fill="x")

        ttk.Button(button_row, text="Gross Weight", command=self.capture_gross_weight).pack(
            side="left", padx=(0, 12), pady=4
        )
        ttk.Button(button_row, text="Tare Weight", command=self.capture_tare_weight).pack(
            side="left", padx=(0, 12), pady=4
        )
        ttk.Button(button_row, text="Net Weight", command=self.calculate_net_weight).pack(
            side="left", padx=(0, 12), pady=4
        )
        ttk.Button(button_row, text="Save", command=self.save_to_db).pack(side="left", padx=(0, 12), pady=4)
        ttk.Button(button_row, text="Print", command=self.print_slip).pack(side="left", padx=(0, 12), pady=4)
        ttk.Button(button_row, text="Clear", command=self.clear_fields).pack(side="left", pady=4)

        self._build_messaging_actions(container, pady=(10, 0))

    def _build_admin_tab(self, container: ttk.Frame) -> None:
        self.admin_tab = AdminTab(
            container=container,
            get_db_connection=self._get_db_connection,
            db_file=DB_FILE,
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
        messaging_card = ttk.LabelFrame(container, text="Messaging Actions", padding=12)
        messaging_card.pack(fill="x", pady=pady)

        ttk.Label(
            messaging_card,
            text="Configure credentials in Admin tab. Use the buttons below to send current slip.",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=6, pady=(0, 8))

        messaging_buttons = ttk.Frame(messaging_card)
        messaging_buttons.grid(row=1, column=0, columnspan=4, sticky="w", padx=6, pady=(4, 2))

        ttk.Button(messaging_buttons, text="Send SMS", command=self.send_sms).pack(side="left", padx=(0, 12), pady=4)
        ttk.Button(messaging_buttons, text="Send WhatsApp", command=self.send_whatsapp).pack(
            side="left", padx=(0, 12), pady=4
        )
        ttk.Button(messaging_buttons, text="Send Telegram", command=self.send_telegram).pack(side="left", pady=4)

        ttk.Label(messaging_card, textvariable=self.message_status_var).grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 0))

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

    def _get_db_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_FILE)

    def _get_next_serial_no(self) -> int:
        self._ensure_database()
        with self._get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COALESCE(MAX(serial_no), 0) + 1 FROM weighment_records")
            return int(cursor.fetchone()[0])

    def _ensure_database(self) -> None:
        with self._get_db_connection() as connection:
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
            connection.commit()

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
