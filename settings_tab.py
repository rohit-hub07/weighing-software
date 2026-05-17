import tkinter as tk
from tkinter import messagebox, ttk


class SettingsTab:
    def __init__(
        self,
        container: ttk.Frame,
        *,
        list_ports_fn,
        connect_fn,
        disconnect_fn,
        load_settings_fn,
        save_settings_fn,
        connection_status_fn,
    ) -> None:
        self.container = container
        self.list_ports_fn = list_ports_fn
        self.connect_fn = connect_fn
        self.disconnect_fn = disconnect_fn
        self.load_settings_fn = load_settings_fn
        self.save_settings_fn = save_settings_fn
        self.connection_status_fn = connection_status_fn

        self.port_var = tk.StringVar()
        self.baud_rate_var = tk.StringVar(value="2400")
        self.status_var = tk.StringVar(value="Port: Not connected")
        self.auto_refresh_ms = 5000
        self._auto_refresh_job = None
        self.port_combobox: ttk.Combobox | None = None

    def build(self) -> None:
        card = ttk.LabelFrame(self.container, text="Weighing Port Selection", style="Card.TLabelframe", padding=16)
        card.pack(fill="x", padx=4, pady=4)

        ttk.Label(card, text="Port", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=8)
        self.port_combobox = ttk.Combobox(
            card,
            textvariable=self.port_var,
            values=[],
            width=26,
            state="readonly",
            style="Field.TCombobox",
        )
        self.port_combobox.grid(row=0, column=1, sticky="w", padx=6, pady=8)
        self.port_combobox.configure(postcommand=self.refresh_ports)

        ttk.Label(card, text="Baud Rate", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=8)
        baud_combo = ttk.Combobox(
            card,
            textvariable=self.baud_rate_var,
            values=("1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"),
            width=26,
            state="readonly",
            style="Field.TCombobox",
        )
        baud_combo.grid(row=1, column=1, sticky="w", padx=6, pady=8)

        button_row = ttk.Frame(card)
        button_row.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(10, 6))

        ttk.Button(button_row, text="Refresh Ports", command=self.refresh_ports, style="Primary.TButton").pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Open Port", command=self.open_port, style="Success.TButton").pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Save Settings", command=self.save_settings, style="Primary.TButton").pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Close Port", command=self.close_port, style="Danger.TButton").pack(side="left")

        ttk.Label(card, textvariable=self.status_var, style="Value.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=(14, 4))

        card.columnconfigure(1, weight=1)

        self._load_saved_settings()
        self.refresh_ports()
        self._schedule_auto_refresh()

    def refresh_ports(self) -> None:
        available_ports = list(self.list_ports_fn())
        current_port = self.port_var.get().strip()
        connection_status = self.connection_status_fn()

        if self.port_combobox is not None:
            self.port_combobox.configure(values=available_ports)

        if not available_ports:
            self.status_var.set("Port: No COM ports detected")
        elif connection_status:
            self.status_var.set(connection_status)
        elif current_port and current_port in available_ports:
            self.status_var.set(f"Port: Ready on {self.port_var.get().strip()}")
        elif current_port:
            self.status_var.set(f"Port: {current_port} not available")
        else:
            self.status_var.set(f"Port: {len(available_ports)} port(s) detected")

    def open_port(self) -> None:
        port_name = self.port_var.get().strip()
        baud_text = self.baud_rate_var.get().strip()

        if not port_name:
            messagebox.showerror("COM Port", "Select a port first.")
            return

        try:
            baud_rate = int(baud_text)
        except ValueError:
            messagebox.showerror("COM Port", "Baud rate must be numeric.")
            return

        success, status_message = self.connect_fn(port_name, baud_rate)
        self.status_var.set(status_message)
        if not success:
            messagebox.showerror("COM Port", status_message)

    def close_port(self) -> None:
        status_message = self.disconnect_fn()
        self.status_var.set(status_message)

    def save_settings(self) -> None:
        if self.save_settings_fn(self.port_var.get().strip(), self.baud_rate_var.get().strip()):
            messagebox.showinfo("Settings", "Serial settings saved.")
        else:
            messagebox.showerror("Settings", "Unable to save serial settings.")

    def _load_saved_settings(self) -> None:
        saved_settings = self.load_settings_fn() or {}
        saved_port = saved_settings.get("serial_port", "")
        saved_baud = saved_settings.get("serial_baud_rate", "2400")

        if saved_port:
            self.port_var.set(saved_port)
        if saved_baud:
            self.baud_rate_var.set(str(saved_baud))

    def _schedule_auto_refresh(self) -> None:
        if self._auto_refresh_job is not None:
            try:
                self.container.after_cancel(self._auto_refresh_job)
            except Exception:
                pass

        def _refresh() -> None:
            if not self.container.winfo_exists():
                return
            self.refresh_ports()
            self._auto_refresh_job = self.container.after(self.auto_refresh_ms, _refresh)

        self._auto_refresh_job = self.container.after(self.auto_refresh_ms, _refresh)
