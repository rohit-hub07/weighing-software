import tkinter as tk
from tkinter import ttk
from datetime import datetime


class ReportTab:
    def __init__(self, container: ttk.Frame, get_db_connection) -> None:
        self.container = container
        self.get_db_connection = get_db_connection

        self.filter_mode_var = tk.StringVar(value="vehicle")
        self.vehicle_filter_var = tk.StringVar()
        self.serial_filter_var = tk.StringVar()
        self.date_from_filter_var = tk.StringVar()
        self.date_to_filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Report: Ready")

        self.report_tree = None
        self.filter_inputs_frame = None

    def build(self) -> None:
        filters = ttk.LabelFrame(self.container, text="Filters", style="Card.TLabelframe", padding=16)
        filters.pack(fill="x")

        ttk.Label(filters, text="Filter By", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)

        modes = ttk.Frame(filters)
        modes.grid(row=0, column=1, columnspan=3, sticky="w", padx=6, pady=6)
        ttk.Radiobutton(
            modes,
            text="Vehicle No",
            value="vehicle",
            variable=self.filter_mode_var,
            command=self._render_filter_inputs,
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            modes,
            text="Serial No",
            value="serial",
            variable=self.filter_mode_var,
            command=self._render_filter_inputs,
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            modes,
            text="Date Range",
            value="date",
            variable=self.filter_mode_var,
            command=self._render_filter_inputs,
        ).pack(side="left")

        self.filter_inputs_frame = ttk.Frame(filters)
        self.filter_inputs_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=6, pady=(4, 6))
        self._render_filter_inputs()

        ttk.Button(filters, text="Search", command=self.refresh_table, style="Primary.TButton").grid(
            row=0, column=4, rowspan=2, sticky="w", padx=(14, 8), pady=6
        )
        ttk.Button(filters, text="Clear", command=self.clear_filters, style="Danger.TButton").grid(
            row=0, column=5, rowspan=2, sticky="w", padx=8, pady=6
        )

        table_card = ttk.LabelFrame(self.container, text="Weighment Records", style="Card.TLabelframe", padding=16)
        table_card.pack(fill="both", expand=True, pady=(10, 0))

        columns = (
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
        )

        table_grid = ttk.Frame(table_card)
        table_grid.pack(fill="both", expand=True)
        table_grid.rowconfigure(0, weight=1)
        table_grid.columnconfigure(0, weight=1)

        self.report_tree = ttk.Treeview(table_grid, columns=columns, show="headings", height=16, style="Modern.Treeview")
        self.report_tree.configure(takefocus=0)

        self.report_tree.heading("serial_no", text="Serial")
        self.report_tree.heading("vehicle_no", text="Vehicle No")
        self.report_tree.heading("weighment_date", text="Date")
        self.report_tree.heading("weighment_time", text="Time")
        self.report_tree.heading("challan", text="Challan")
        self.report_tree.heading("customer_code", text="Customer Code")
        self.report_tree.heading("customer_name", text="Customer")
        self.report_tree.heading("product_code", text="Product Code")
        self.report_tree.heading("product_name", text="Product Name")
        self.report_tree.heading("source_code", text="Source Code")
        self.report_tree.heading("source_name", text="Source Name")
        self.report_tree.heading("destination_code", text="Destination Code")
        self.report_tree.heading("destination_name", text="Destination Name")
        self.report_tree.heading("transporter_code", text="Transporter Code")
        self.report_tree.heading("transporter_name", text="Transporter Name")
        self.report_tree.heading("gross_weight", text="Gross (kg)")
        self.report_tree.heading("tare_weight", text="Tare (kg)")
        self.report_tree.heading("net_weight", text="Net (kg)")

        self.report_tree.column("serial_no", width=70, anchor="center")
        self.report_tree.column("vehicle_no", width=140, anchor="center")
        self.report_tree.column("weighment_date", width=110, anchor="center")
        self.report_tree.column("weighment_time", width=100, anchor="center")
        self.report_tree.column("challan", width=120, anchor="w")
        self.report_tree.column("customer_code", width=120, anchor="w")
        self.report_tree.column("customer_name", width=220, anchor="w")
        self.report_tree.column("product_code", width=120, anchor="w")
        self.report_tree.column("product_name", width=180, anchor="w")
        self.report_tree.column("source_code", width=120, anchor="w")
        self.report_tree.column("source_name", width=180, anchor="w")
        self.report_tree.column("destination_code", width=140, anchor="w")
        self.report_tree.column("destination_name", width=180, anchor="w")
        self.report_tree.column("transporter_code", width=140, anchor="w")
        self.report_tree.column("transporter_name", width=180, anchor="w")
        self.report_tree.column("gross_weight", width=90, anchor="e")
        self.report_tree.column("tare_weight", width=90, anchor="e")
        self.report_tree.column("net_weight", width=90, anchor="e")

        yscroll = ttk.Scrollbar(table_grid, orient="vertical", command=self.report_tree.yview)
        xscroll = ttk.Scrollbar(table_grid, orient="horizontal", command=self.report_tree.xview)
        self.report_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.report_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        def _on_tree_mousewheel(event) -> None:
            self.report_tree.yview_scroll(int(-event.delta / 120), "units")

        def _on_tree_shift_mousewheel(event) -> None:
            self.report_tree.xview_scroll(int(-event.delta / 120), "units")

        self.report_tree.bind("<MouseWheel>", _on_tree_mousewheel)
        self.report_tree.bind("<Shift-MouseWheel>", _on_tree_shift_mousewheel)

        ttk.Label(self.container, textvariable=self.status_var).pack(fill="x", pady=(8, 0))
        self.refresh_table()

    def _render_filter_inputs(self) -> None:
        if not self.filter_inputs_frame:
            return

        for child in self.filter_inputs_frame.winfo_children():
            child.destroy()

        mode = self.filter_mode_var.get()
        if mode == "vehicle":
            ttk.Label(self.filter_inputs_frame, text="Vehicle No", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=2)
            ttk.Entry(self.filter_inputs_frame, textvariable=self.vehicle_filter_var, width=34, style="Field.TEntry").grid(
                row=0, column=1, sticky="w", padx=6, pady=2
            )
        elif mode == "serial":
            ttk.Label(self.filter_inputs_frame, text="Serial No", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=2)
            ttk.Entry(self.filter_inputs_frame, textvariable=self.serial_filter_var, width=34, style="Field.TEntry").grid(
                row=0, column=1, sticky="w", padx=6, pady=2
            )
        else:
            ttk.Label(self.filter_inputs_frame, text="From (DD-MM-YYYY)", style="Muted.TLabel").grid(
                row=0, column=0, sticky="w", padx=6, pady=2
            )
            ttk.Entry(self.filter_inputs_frame, textvariable=self.date_from_filter_var, width=18, style="Field.TEntry").grid(
                row=0, column=1, sticky="w", padx=6, pady=2
            )
            ttk.Label(self.filter_inputs_frame, text="To (DD-MM-YYYY)", style="Muted.TLabel").grid(
                row=0, column=2, sticky="w", padx=(12, 6), pady=2
            )
            ttk.Entry(self.filter_inputs_frame, textvariable=self.date_to_filter_var, width=18, style="Field.TEntry").grid(
                row=0, column=3, sticky="w", padx=6, pady=2
            )

    def _validate_date(self, value: str, label: str) -> tuple[bool, str]:
        value = value.strip()
        if not value:
            return True, ""
        try:
            dt = datetime.strptime(value, "%d-%m-%Y")
            return True, dt.strftime("%Y-%m-%d")
        except ValueError:
            self.status_var.set(f"Report: Invalid {label} date. Use DD-MM-YYYY")
            return False, ""

    def _fetch_rows(self) -> list[tuple]:
        query = (
            "SELECT serial_no, vehicle_no, weighment_date, weighment_time, challan, customer_code, "
            "customer_name, product_code, product_name, source_code, source_name, destination_code, "
            "destination_name, transporter_code, transporter_name, gross_weight, tare_weight, net_weight "
            "FROM weighment_records"
        )
        params: list = []
        mode = self.filter_mode_var.get()

        if mode == "vehicle":
            query += " WHERE LOWER(vehicle_no) LIKE ?"
            params.append(f"%{self.vehicle_filter_var.get().strip().lower()}%")
        elif mode == "serial":
            serial_text = self.serial_filter_var.get().strip()
            if serial_text:
                if not serial_text.isdigit():
                    self.status_var.set("Report: Serial No must be numeric")
                    return []
                query += " WHERE serial_no = ?"
                params.append(int(serial_text))
        else:
            from_ok, from_iso = self._validate_date(self.date_from_filter_var.get(), "from")
            to_ok, to_iso = self._validate_date(self.date_to_filter_var.get(), "to")
            if not from_ok or not to_ok:
                return []

            date_sql = "(substr(weighment_date, 7, 4) || '-' || substr(weighment_date, 4, 2) || '-' || substr(weighment_date, 1, 2))"
            if from_iso and to_iso and from_iso > to_iso:
                self.status_var.set("Report: From date cannot be after To date")
                return []

            if from_iso and to_iso:
                query += f" WHERE {date_sql} BETWEEN ? AND ?"
                params.extend([from_iso, to_iso])
            elif from_iso:
                query += f" WHERE {date_sql} >= ?"
                params.append(from_iso)
            elif to_iso:
                query += f" WHERE {date_sql} <= ?"
                params.append(to_iso)

        query += " ORDER BY serial_no DESC"

        with self.get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def refresh_table(self) -> None:
        if not self.report_tree:
            return

        rows = self._fetch_rows()

        self.report_tree.delete(*self.report_tree.get_children())
        for row in rows:
            self.report_tree.insert("", "end", values=row)

        active_mode = self.filter_mode_var.get().capitalize()
        self.status_var.set(f"Report: {len(rows)} record(s) found ({active_mode} filter)")

    def clear_filters(self) -> None:
        self.filter_mode_var.set("vehicle")
        self.vehicle_filter_var.set("")
        self.serial_filter_var.set("")
        self.date_from_filter_var.set("")
        self.date_to_filter_var.set("")
        self._render_filter_inputs()
        self.refresh_table()
