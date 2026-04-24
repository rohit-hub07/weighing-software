import csv
import os
import shutil
from datetime import datetime
from typing import Callable
import tkinter as tk
from tkinter import messagebox, ttk


class AdminTab:
    def __init__(
        self,
        container: ttk.Frame,
        get_db_connection,
        db_file: str,
        messaging_vars: dict[str, tk.StringVar],
        save_credentials_fn: Callable[[], bool] | None = None,
    ) -> None:
        self.container = container
        self.get_db_connection = get_db_connection
        self.db_file = db_file
        self.messaging_vars = messaging_vars
        self.save_credentials_fn = save_credentials_fn

        self.status_var = tk.StringVar(value="Admin: Ready")

        self.total_records_var = tk.StringVar(value="0")
        self.today_records_var = tk.StringVar(value="0")
        self.today_net_var = tk.StringVar(value="0 kg")
        self.last_serial_var = tk.StringVar(value="0")
        self.db_size_var = tk.StringVar(value="0 KB")
        self.messaging_health_var = tk.StringVar(value="Not configured")

        self.recent_tree = None

    def build(self) -> None:
        top_row = ttk.Frame(self.container)
        top_row.pack(fill="x")

        summary_card = ttk.LabelFrame(top_row, text="System Summary", padding=10)
        summary_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ttk.Label(summary_card, text="Total Records").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.total_records_var).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_card, text="Records Today").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.today_records_var).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_card, text="Net Today").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.today_net_var).grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_card, text="Last Serial").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.last_serial_var).grid(row=3, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_card, text="DB Size").grid(row=4, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.db_size_var).grid(row=4, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(summary_card, text="Messaging Config").grid(row=5, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(summary_card, textvariable=self.messaging_health_var).grid(row=5, column=1, sticky="w", padx=6, pady=4)

        actions_card = ttk.LabelFrame(top_row, text="Maintenance", padding=10)
        actions_card.pack(side="left", fill="y", padx=(8, 0))

        ttk.Button(actions_card, text="Refresh Summary", command=self.refresh_summary).pack(fill="x", pady=4)
        ttk.Button(actions_card, text="Backup Database", command=self.backup_database).pack(fill="x", pady=4)
        ttk.Button(actions_card, text="Export CSV", command=self.export_csv).pack(fill="x", pady=4)

        messaging_card = ttk.LabelFrame(self.container, text="Messaging Configuration", padding=10)
        messaging_card.pack(fill="x", pady=(10, 0))

        ttk.Label(messaging_card, text="Twilio SID").grid(row=0, column=0, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["twilio_sid"], width=36).grid(
            row=0, column=1, sticky="w", padx=6, pady=5
        )
        ttk.Label(messaging_card, text="Twilio Token").grid(row=0, column=2, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["twilio_token"], width=30, show="*").grid(
            row=0, column=3, sticky="w", padx=6, pady=5
        )

        ttk.Label(messaging_card, text="SMS From").grid(row=1, column=0, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["sms_from"], width=36).grid(
            row=1, column=1, sticky="w", padx=6, pady=5
        )
        ttk.Label(messaging_card, text="SMS To").grid(row=1, column=2, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["sms_to"], width=30).grid(
            row=1, column=3, sticky="w", padx=6, pady=5
        )

        ttk.Label(messaging_card, text="WhatsApp From").grid(row=2, column=0, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["whatsapp_from"], width=36).grid(
            row=2, column=1, sticky="w", padx=6, pady=5
        )
        ttk.Label(messaging_card, text="WhatsApp To").grid(row=2, column=2, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["whatsapp_to"], width=30).grid(
            row=2, column=3, sticky="w", padx=6, pady=5
        )

        ttk.Label(messaging_card, text="Telegram Bot Token").grid(row=3, column=0, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["telegram_token"], width=36, show="*").grid(
            row=3, column=1, sticky="w", padx=6, pady=5
        )
        ttk.Label(messaging_card, text="Telegram Chat ID").grid(row=3, column=2, sticky="w", padx=6, pady=5)
        ttk.Entry(messaging_card, textvariable=self.messaging_vars["telegram_chat_id"], width=30).grid(
            row=3, column=3, sticky="w", padx=6, pady=5
        )

        action_row = ttk.Frame(messaging_card)
        action_row.grid(row=4, column=0, columnspan=4, sticky="w", padx=6, pady=(8, 2))

        ttk.Button(action_row, text="Save Credentials", command=self._save_credentials).pack(side="left", padx=(0, 10))
        ttk.Button(action_row, text="Check Configuration", command=self.refresh_summary).pack(side="left")

        recent_card = ttk.LabelFrame(self.container, text="Recent Weighments", padding=10)
        recent_card.pack(fill="both", expand=True, pady=(10, 0))

        columns = ("serial_no", "vehicle_no", "weighment_date", "weighment_time", "net_weight")
        self.recent_tree = ttk.Treeview(recent_card, columns=columns, show="headings", height=8)
        self.recent_tree.pack(fill="both", expand=True)

        self.recent_tree.heading("serial_no", text="Serial")
        self.recent_tree.heading("vehicle_no", text="Vehicle")
        self.recent_tree.heading("weighment_date", text="Date")
        self.recent_tree.heading("weighment_time", text="Time")
        self.recent_tree.heading("net_weight", text="Net (kg)")

        self.recent_tree.column("serial_no", width=80, anchor="center")
        self.recent_tree.column("vehicle_no", width=160, anchor="center")
        self.recent_tree.column("weighment_date", width=120, anchor="center")
        self.recent_tree.column("weighment_time", width=100, anchor="center")
        self.recent_tree.column("net_weight", width=100, anchor="e")

        ttk.Label(self.container, textvariable=self.status_var).pack(fill="x", pady=(8, 0))

        self.refresh_summary()

    def _save_credentials(self) -> None:
        if not self.save_credentials_fn:
            messagebox.showerror("Save Error", "Credential save handler is not configured.")
            return

        if self.save_credentials_fn():
            self.status_var.set("Admin: Credentials saved")
            messagebox.showinfo("Saved", "Messaging credentials saved successfully.")
            self.refresh_summary()

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _messaging_status(self) -> str:
        has_twilio = all(
            [
                self.messaging_vars["twilio_sid"].get().strip(),
                self.messaging_vars["twilio_token"].get().strip(),
            ]
        )
        has_telegram = all(
            [
                self.messaging_vars["telegram_token"].get().strip(),
                self.messaging_vars["telegram_chat_id"].get().strip(),
            ]
        )

        if has_twilio and has_telegram:
            return "Twilio + Telegram configured"
        if has_twilio:
            return "Twilio configured"
        if has_telegram:
            return "Telegram configured"
        return "Not configured"

    def refresh_summary(self) -> None:
        today = datetime.now().strftime("%d-%m-%Y")

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(MAX(serial_no), 0) FROM weighment_records")
            total_records, last_serial = cursor.fetchone()

            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(net_weight), 0) FROM weighment_records WHERE weighment_date = ?",
                (today,),
            )
            today_records, today_net = cursor.fetchone()

            cursor.execute(
                "SELECT serial_no, vehicle_no, weighment_date, weighment_time, net_weight "
                "FROM weighment_records ORDER BY serial_no DESC LIMIT 10"
            )
            recent_rows = cursor.fetchall()

        db_size = os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0

        self.total_records_var.set(str(total_records))
        self.today_records_var.set(str(today_records))
        self.today_net_var.set(f"{today_net} kg")
        self.last_serial_var.set(str(last_serial))
        self.db_size_var.set(self._format_size(db_size))
        self.messaging_health_var.set(self._messaging_status())

        if self.recent_tree:
            self.recent_tree.delete(*self.recent_tree.get_children())
            for row in recent_rows:
                self.recent_tree.insert("", "end", values=row)

        self.status_var.set("Admin: Summary refreshed")

    def backup_database(self) -> None:
        if not os.path.exists(self.db_file):
            messagebox.showerror("Backup Error", "Database file not found.")
            return

        backup_dir = os.path.join(os.getcwd(), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"weighment_backup_{stamp}.db")

        try:
            shutil.copy2(self.db_file, backup_path)
            self.status_var.set(f"Admin: Backup created at {backup_path}")
            messagebox.showinfo("Backup", f"Backup created successfully.\n{backup_path}")
            self.refresh_summary()
        except Exception as exc:
            messagebox.showerror("Backup Error", str(exc))

    def export_csv(self) -> None:
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = os.path.join(export_dir, f"weighment_export_{stamp}.csv")

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT serial_no, vehicle_no, weighment_date, weighment_time, challan, customer_code, "
                "customer_name, product_code, product_name, source_code, source_name, destination_code, "
                "destination_name, transporter_code, transporter_name, gross_weight, tare_weight, net_weight "
                "FROM weighment_records ORDER BY serial_no DESC"
            )
            rows = cursor.fetchall()

        headers = [
            "serial_no",
            "vehicle_no",
            "weighment_date",
            "weighment_time",
            "challan",
            "customer_code",
            "customer_name",
            "product_code",
            "product_name",
            "source_code",
            "source_name",
            "destination_code",
            "destination_name",
            "transporter_code",
            "transporter_name",
            "gross_weight",
            "tare_weight",
            "net_weight",
        ]

        try:
            with open(export_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(rows)

            self.status_var.set(f"Admin: CSV exported at {export_path}")
            messagebox.showinfo("Export", f"CSV export completed.\n{export_path}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))
