import csv
import os
import shutil
from datetime import date, datetime, timedelta
from typing import Callable
import tkinter as tk
from tkinter import messagebox, ttk


class AdminTab:
    def __init__(
        self,
        container: ttk.Frame,
        get_db_connection,
        db_file: str,
        is_admin_fn: Callable[[], bool],
        refresh_subscriptions_fn: Callable[[], None],
        messaging_vars: dict[str, tk.StringVar],
        save_credentials_fn: Callable[[], bool] | None = None,
    ) -> None:
        self.container = container
        self.get_db_connection = get_db_connection
        self.db_file = db_file
        self.is_admin_fn = is_admin_fn
        self.refresh_subscriptions_fn = refresh_subscriptions_fn
        self.messaging_vars = messaging_vars
        self.save_credentials_fn = save_credentials_fn

        self.status_var = tk.StringVar(value="Admin: Ready")

        self.total_records_var = tk.StringVar(value="0")
        self.today_records_var = tk.StringVar(value="0")
        self.today_net_var = tk.StringVar(value="0 kg")
        self.last_serial_var = tk.StringVar(value="0")
        self.db_size_var = tk.StringVar(value="0 KB")
        self.messaging_health_var = tk.StringVar(value="Not configured")

        self.selected_user_id_var = tk.StringVar()
        self.selected_username_var = tk.StringVar()
        self.sub_start_var = tk.StringVar()
        self.sub_end_var = tk.StringVar()
        self.sub_status_var = tk.StringVar(value="active")
        self.extend_days_var = tk.StringVar(value="365")

        self.subscription_tree = None

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

        self._build_subscription_management()

        ttk.Label(self.container, textvariable=self.status_var).pack(fill="x", pady=(8, 0))

        self.refresh_summary()

    def _build_subscription_management(self) -> None:
        sub_card = ttk.LabelFrame(self.container, text="User Subscription Management", padding=10)
        sub_card.pack(fill="both", expand=True, pady=(10, 0))

        columns = ("user_id", "username", "start_date", "end_date", "status", "remaining_days")
        self.subscription_tree = ttk.Treeview(sub_card, columns=columns, show="headings", height=7)
        self.subscription_tree.pack(fill="x", padx=4, pady=(2, 8))

        self.subscription_tree.heading("user_id", text="User ID")
        self.subscription_tree.heading("username", text="Username")
        self.subscription_tree.heading("start_date", text="Start Date")
        self.subscription_tree.heading("end_date", text="End Date")
        self.subscription_tree.heading("status", text="Status")
        self.subscription_tree.heading("remaining_days", text="Remaining Days")

        self.subscription_tree.column("user_id", width=80, anchor="center")
        self.subscription_tree.column("username", width=150, anchor="center")
        self.subscription_tree.column("start_date", width=120, anchor="center")
        self.subscription_tree.column("end_date", width=120, anchor="center")
        self.subscription_tree.column("status", width=100, anchor="center")
        self.subscription_tree.column("remaining_days", width=120, anchor="center")

        self.subscription_tree.bind("<<TreeviewSelect>>", self._on_subscription_select)

        form = ttk.Frame(sub_card)
        form.pack(fill="x", padx=4, pady=(2, 2))

        ttk.Label(form, text="User").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.selected_username_var, state="readonly", width=22).grid(
            row=0, column=1, sticky="w", padx=6, pady=4
        )

        ttk.Label(form, text="Start (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.sub_start_var, width=16).grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="End (YYYY-MM-DD)").grid(row=0, column=4, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.sub_end_var, width=16).grid(row=0, column=5, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Status").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(
            form,
            textvariable=self.sub_status_var,
            state="readonly",
            values=("active", "expired"),
            width=19,
        ).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="Extend Days").grid(row=1, column=2, sticky="w", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.extend_days_var, width=16).grid(row=1, column=3, sticky="w", padx=6, pady=4)

        action_row = ttk.Frame(sub_card)
        action_row.pack(fill="x", padx=4, pady=(6, 2))

        ttk.Button(action_row, text="Refresh Users", command=self.refresh_user_subscriptions).pack(side="left", padx=(0, 8))
        ttk.Button(action_row, text="Save Dates/Status", command=self.save_subscription_changes).pack(side="left", padx=(0, 8))
        ttk.Button(action_row, text="Extend Subscription", command=self.extend_subscription).pack(side="left", padx=(0, 8))
        ttk.Button(action_row, text="Activate User", command=self.activate_user).pack(side="left", padx=(0, 8))
        ttk.Button(action_row, text="Deactivate User", command=self.deactivate_user).pack(side="left")

    def _require_admin_action(self) -> bool:
        if self.is_admin_fn():
            return True
        messagebox.showerror("Access Denied", "Only admin users can modify subscription details.")
        return False

    def _parse_iso_date(self, value: str, label: str) -> date | None:
        text = value.strip()
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Validation Error", f"Invalid {label}. Use YYYY-MM-DD.")
            return None

    def _on_subscription_select(self, _event=None) -> None:
        if not self.subscription_tree:
            return

        selection = self.subscription_tree.selection()
        if not selection:
            return

        values = self.subscription_tree.item(selection[0], "values")
        if not values:
            return

        self.selected_user_id_var.set(str(values[0]))
        self.selected_username_var.set(str(values[1]))
        self.sub_start_var.set(str(values[2]))
        self.sub_end_var.set(str(values[3]))
        self.sub_status_var.set(str(values[4]))

    def refresh_user_subscriptions(self, selected_user_id: int | None = None) -> None:
        if self.refresh_subscriptions_fn:
            self.refresh_subscriptions_fn()

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, s.start_date, s.end_date, s.status
                FROM users u
                JOIN subscriptions s ON s.user_id = u.id
                ORDER BY u.username ASC
                """
            )
            rows = cursor.fetchall()

        if self.subscription_tree:
            self.subscription_tree.delete(*self.subscription_tree.get_children())
            today = datetime.now().date()
            for row in rows:
                end_date = datetime.strptime(row[3], "%Y-%m-%d").date()
                remaining_days = (end_date - today).days
                item_id = self.subscription_tree.insert(
                    "", "end", values=(row[0], row[1], row[2], row[3], row[4], remaining_days)
                )
                if selected_user_id is not None and int(row[0]) == selected_user_id:
                    self.subscription_tree.selection_set(item_id)
                    self.subscription_tree.focus(item_id)

        if selected_user_id is not None:
            self._on_subscription_select()

        self.status_var.set(f"Admin: Loaded {len(rows)} user subscription(s)")

    def save_subscription_changes(self) -> None:
        if not self._require_admin_action():
            return

        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showerror("Validation Error", "Select a user to update subscription details.")
            return

        start_date = self._parse_iso_date(self.sub_start_var.get(), "start date")
        end_date = self._parse_iso_date(self.sub_end_var.get(), "end date")
        if not start_date or not end_date:
            return

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT start_date, end_date FROM subscriptions WHERE user_id = ?",
                (int(user_id),),
            )
            existing_row = cursor.fetchone()

        if not existing_row:
            messagebox.showerror("Update Error", "Subscription record not found for selected user.")
            return

        existing_start_text, existing_end_text = existing_row

        # If admin changes only the start date, preserve default 1-year duration automatically.
        if self.sub_start_var.get().strip() != existing_start_text and self.sub_end_var.get().strip() == existing_end_text:
            end_date = start_date + timedelta(days=365)
            self.sub_end_var.set(end_date.isoformat())

        if end_date < start_date:
            messagebox.showerror("Validation Error", "End date cannot be before start date.")
            return

        status = self.sub_status_var.get().strip().lower()
        if status not in {"active", "expired"}:
            messagebox.showerror("Validation Error", "Status must be active or expired.")
            return

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET start_date = ?, end_date = ?, status = ?
                WHERE user_id = ?
                """,
                (start_date.isoformat(), end_date.isoformat(), status, int(user_id)),
            )
            connection.commit()

        self.refresh_user_subscriptions(selected_user_id=int(user_id))
        self.status_var.set(f"Admin: Subscription updated for {self.selected_username_var.get().strip()}")

    def extend_subscription(self) -> None:
        if not self._require_admin_action():
            return

        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showerror("Validation Error", "Select a user to extend subscription.")
            return

        try:
            extra_days = int(self.extend_days_var.get().strip())
            if extra_days <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Extend Days must be a positive integer.")
            return

        current_end = self._parse_iso_date(self.sub_end_var.get(), "end date")
        if not current_end:
            return

        today = datetime.now().date()
        base_date = current_end if current_end >= today else today
        new_end = base_date + timedelta(days=extra_days)

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET end_date = ?, status = 'active'
                WHERE user_id = ?
                """,
                (new_end.isoformat(), int(user_id)),
            )
            connection.commit()

        self.refresh_user_subscriptions(selected_user_id=int(user_id))
        self.status_var.set(f"Admin: Extended subscription for {self.selected_username_var.get().strip()}")

    def activate_user(self) -> None:
        if not self._require_admin_action():
            return

        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showerror("Validation Error", "Select a user to activate.")
            return

        start_date = self._parse_iso_date(self.sub_start_var.get(), "start date")
        end_date = self._parse_iso_date(self.sub_end_var.get(), "end date")
        if not start_date or not end_date:
            return

        today = datetime.now().date()
        if end_date < today:
            start_date = today
            end_date = today + timedelta(days=365)

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET start_date = ?, end_date = ?, status = 'active'
                WHERE user_id = ?
                """,
                (start_date.isoformat(), end_date.isoformat(), int(user_id)),
            )
            connection.commit()

        self.refresh_user_subscriptions(selected_user_id=int(user_id))
        self.status_var.set(f"Admin: Activated {self.selected_username_var.get().strip()}")

    def deactivate_user(self) -> None:
        if not self._require_admin_action():
            return

        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showerror("Validation Error", "Select a user to deactivate.")
            return

        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE subscriptions
                SET end_date = ?, status = 'expired'
                WHERE user_id = ?
                """,
                (yesterday, int(user_id)),
            )
            connection.commit()

        self.refresh_user_subscriptions(selected_user_id=int(user_id))
        self.status_var.set(f"Admin: Deactivated {self.selected_username_var.get().strip()}")

    def _save_credentials(self) -> None:
        if not self._require_admin_action():
            return

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

        db_size = os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0

        self.total_records_var.set(str(total_records))
        self.today_records_var.set(str(today_records))
        self.today_net_var.set(f"{today_net} kg")
        self.last_serial_var.set(str(last_serial))
        self.db_size_var.set(self._format_size(db_size))
        self.messaging_health_var.set(self._messaging_status())

        self.refresh_user_subscriptions()

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
