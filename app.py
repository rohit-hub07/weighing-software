import os
import random
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from openpyxl import Workbook, load_workbook
except ImportError:
    raise ImportError("openpyxl is required. Install it using: pip install openpyxl")


EXCEL_FILE = "weighment_data.xlsx"
HEADERS = [
    "Serial No",
    "Vehicle No",
    "Date",
    "Time",
    "Challan",
    "Customer Code",
    "Customer Name",
    "Product Code",
    "Product Name",
    "Source Code",
    "Source Name",
    "Destination Code",
    "Destination Name",
    "Transporter Code",
    "Transporter Name",
    "Gross Weight",
    "Tare Weight",
    "Net Weight",
]


class WeighmentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weighment Section")
        self.root.geometry("980x680")
        self.root.minsize(920, 620)

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

        self.live_weight_var = tk.StringVar(value="00000 kg")
        self.gross_var = tk.StringVar(value="-")
        self.tare_var = tk.StringVar(value="-")
        self.net_var = tk.StringVar(value="-")

        self._build_ui()
        self._update_datetime()
        self.generate_weight()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

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

        display_frame = ttk.Frame(container, padding=(0, 14, 0, 10))
        display_frame.pack(fill="x")

        ttk.Label(display_frame, text="Live Weight", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(
            display_frame,
            textvariable=self.live_weight_var,
            font=("Consolas", 36, "bold"),
            bg="black",
            fg="#28ff6d",
            padx=20,
            pady=14,
            relief="sunken",
            bd=4,
        ).pack(fill="x", pady=(8, 0))

        button_row = ttk.Frame(container, padding=(0, 12, 0, 8))
        button_row.pack(fill="x")

        ttk.Button(button_row, text="Gross Weight", command=self.capture_gross_weight).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(button_row, text="Tare Weight", command=self.capture_tare_weight).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(button_row, text="Net Weight", command=self.calculate_net_weight).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(button_row, text="Save", command=self.save_to_excel).pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Clear", command=self.clear_fields).pack(side="left")

        result_card = ttk.LabelFrame(container, text="Captured Weights", padding=12)
        result_card.pack(fill="x", pady=(8, 0))

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

    def _get_next_serial_no(self) -> int:
        if not os.path.exists(EXCEL_FILE):
            return 1

        workbook = load_workbook(EXCEL_FILE)
        sheet = workbook.active

        if sheet.max_row <= 1:
            workbook.close()
            return 1

        last_serial = sheet.cell(row=sheet.max_row, column=1).value
        workbook.close()

        try:
            return int(last_serial) + 1
        except (TypeError, ValueError):
            return sheet.max_row

    def _ensure_workbook(self) -> None:
        if os.path.exists(EXCEL_FILE):
            return

        workbook = Workbook()
        sheet = workbook.active
        sheet.append(HEADERS)
        workbook.save(EXCEL_FILE)
        workbook.close()

    def save_to_excel(self) -> None:
        vehicle_no = self.vehicle_no_var.get().strip()
        if not vehicle_no:
            messagebox.showerror("Validation Error", "Vehicle No cannot be empty.")
            return

        if self.gross_weight is None or self.tare_weight is None:
            messagebox.showerror("Validation Error", "Capture both Gross and Tare weights before saving.")
            return

        self.calculate_net_weight()

        self._ensure_workbook()
        workbook = load_workbook(EXCEL_FILE)
        sheet = workbook.active

        row = [
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
        ]
        sheet.append(row)

        workbook.save(EXCEL_FILE)
        workbook.close()

        messagebox.showinfo("Saved", "Weighment record saved successfully.")
        self.clear_fields(increment_serial=True)

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
