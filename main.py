import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from sqlite3 import Error
import datetime
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class ExpenseTrackerGUI:
    def __init__(self, root, db_file='expense_tracker.db'):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x700")

        # Database connection
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
            self.create_table()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")
            self.root.destroy()

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('Treeview', font=('Arial', 10), rowheight=25)

        # Create GUI elements
        self.create_widgets()

        # Load initial data
        self.refresh_expenses()

    def create_table(self):
        """Create expenses table if it doesn't exist"""
        sql = """CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    date TEXT NOT NULL
                );"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to create table:\n{e}")

    def create_widgets(self):
        """Create all GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel (input/controls)
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Right panel (display)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add Expense Section
        add_frame = ttk.LabelFrame(left_panel, text="Add New Expense", padding="10")
        add_frame.pack(fill=tk.X, pady=5)

        ttk.Label(add_frame, text="Amount (₹):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.amount_entry = ttk.Entry(add_frame)
        self.amount_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(add_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.category_entry = ttk.Entry(add_frame)
        self.category_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(add_frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.date_entry = ttk.Entry(add_frame)
        self.date_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)
        self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        add_btn = ttk.Button(add_frame, text="Add Expense", command=self.add_expense_gui)
        add_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.EW)

        # Actions Section
        action_frame = ttk.LabelFrame(left_panel, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(action_frame, text="View Summary", command=self.view_summary_gui).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Filter by Date", command=self.filter_by_date_gui).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Delete Expense", command=self.delete_expense_gui).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Clear All", command=self.clear_all_gui).pack(fill=tk.X, pady=2)

        # Expense List Section
        list_frame = ttk.LabelFrame(right_panel, text="Expense List", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for expenses
        self.tree = ttk.Treeview(list_frame, columns=('id', 'date', 'amount', 'category'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Date')
        self.tree.heading('amount', text='Amount (₹)')
        self.tree.heading('category', text='Category')
        self.tree.column('id', width=50, anchor=tk.CENTER)
        self.tree.column('date', width=100, anchor=tk.CENTER)
        self.tree.column('amount', width=100, anchor=tk.E)
        self.tree.column('category', width=150, anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Summary/Chart Section (initially hidden)
        self.summary_frame = ttk.Frame(right_panel)
        self.summary_canvas = None

    def _validate_date(self, date_str):
        """Helper to validate YYYY-MM-DD format."""
        if not date_str:
            return False
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False

    def add_expense_gui(self):
        """Add expense from GUI inputs"""
        amount = self.amount_entry.get()
        category = self.category_entry.get().strip().title()
        date = self.date_entry.get().strip()

        if not amount or not category:
            messagebox.showwarning("Input Error", "Amount and Category are required!")
            return

        try:
            amount = float(amount)
            if amount <= 0:
                messagebox.showwarning("Input Error", "Amount must be positive!")
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid amount! Please enter a number.")
            return

        if not self._validate_date(date):
            messagebox.showwarning("Input Error", "Invalid date format! Use YYYY-MM-DD.")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO expenses(amount, category, date) VALUES(?,?,?)",
                           (amount, category, date))
            self.conn.commit()

            # Clear inputs and refresh list
            self.amount_entry.delete(0, tk.END)
            self.category_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

            self.refresh_expenses()
            messagebox.showinfo("Success", f"Added ₹{amount:.2f} for {category} on {date}")

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to add expense:\n{e}")

    def refresh_expenses(self, filter_sql="1=1", params=()):
        """Refresh the expense list with optional filter"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"SELECT id, date, amount, category FROM expenses WHERE {filter_sql} ORDER BY date DESC, id DESC",
                params)
            rows = cursor.fetchall()

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add new items
            for row in rows:
                self.tree.insert('', tk.END, values=row)

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to load expenses:\n{e}")

    def filter_by_date_gui(self):
        """Show date range filter dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Filter by Date Range")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Start Date (YYYY-MM-DD):").pack(pady=5)
        start_date_entry = ttk.Entry(dialog)
        start_date_entry.pack(pady=5)

        ttk.Label(dialog, text="End Date (YYYY-MM-DD):").pack(pady=5)
        end_date_entry = ttk.Entry(dialog)
        end_date_entry.pack(pady=5)
        end_date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        def apply_filter():
            start_date = start_date_entry.get().strip()
            end_date = end_date_entry.get().strip()

            if not self._validate_date(start_date) or not self._validate_date(end_date):
                messagebox.showwarning("Input Error", "Invalid date format! Use YYYY-MM-DD.")
                return

            if start_date > end_date:
                messagebox.showwarning("Input Error", "Start date cannot be after end date!")
                return

            self.refresh_expenses("date BETWEEN ? AND ?", (start_date, end_date))
            dialog.destroy()

        ttk.Button(dialog, text="Apply Filter", command=apply_filter).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def delete_expense_gui(self):
        """Delete selected expense"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an expense to delete!")
            return

        expense_id = self.tree.item(selected[0], 'values')[0]

        if messagebox.askyesno("Confirm Delete", f"Delete expense ID {expense_id}?"):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
                self.conn.commit()
                self.refresh_expenses()
                messagebox.showinfo("Success", f"Deleted expense ID {expense_id}")
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to delete expense:\n{e}")

    def clear_all_gui(self):
        """Clear all expenses with confirmation"""
        if messagebox.askyesno("Confirm Delete", "Delete ALL expenses? This cannot be undone!",
                               icon='warning'):
            if messagebox.askyesno("Double Confirm", "Are you absolutely sure?"):
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("DELETE FROM expenses")
                    self.conn.commit()
                    self.refresh_expenses()
                    messagebox.showinfo("Success", "All expenses have been deleted")
                except Error as e:
                    messagebox.showerror("Database Error", f"Failed to clear expenses:\n{e}")

    def view_summary_gui(self):
        """Show summary window with chart"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Expense Summary")
        summary_window.geometry("800x600")

        # Period selection
        period_frame = ttk.Frame(summary_window, padding="10")
        period_frame.pack(fill=tk.X)

        ttk.Label(period_frame, text="Select Period:").pack(side=tk.LEFT)

        self.period_var = tk.StringVar(value="all")
        ttk.Radiobutton(period_frame, text="All Time", variable=self.period_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(period_frame, text="This Year", variable=self.period_var, value="year").pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Radiobutton(period_frame, text="This Month", variable=self.period_var, value="month").pack(side=tk.LEFT,
                                                                                                       padx=5)
        ttk.Radiobutton(period_frame, text="Custom", variable=self.period_var, value="custom").pack(side=tk.LEFT,
                                                                                                    padx=5)

        self.custom_frame = ttk.Frame(period_frame)

        ttk.Button(period_frame, text="Generate", command=lambda: self.generate_summary(summary_window)).pack(
            side=tk.RIGHT)

        # Placeholder for chart
        self.chart_frame = ttk.Frame(summary_window)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Table frame
        table_frame = ttk.Frame(summary_window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.summary_tree = ttk.Treeview(table_frame, columns=('category', 'amount', 'percentage'), show='headings')
        self.summary_tree.heading('category', text='Category')
        self.summary_tree.heading('amount', text='Amount (₹)')
        self.summary_tree.heading('percentage', text='Percentage')
        self.summary_tree.column('category', width=200)
        self.summary_tree.column('amount', width=100, anchor=tk.E)
        self.summary_tree.column('percentage', width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_tree.pack(fill=tk.BOTH, expand=True)

    def generate_summary(self, window):
        """Generate summary based on selected period"""
        period = self.period_var.get()

        where_clause = "1=1"
        params = ()
        title = "All Expenses"

        if period == "year":
            year = datetime.date.today().strftime('%Y')
            where_clause = "strftime('%Y', date) = ?"
            params = (year,)
            title = f"Expenses for {year}"
        elif period == "month":
            month = datetime.date.today().strftime('%Y-%m')
            where_clause = "strftime('%Y-%m', date) = ?"
            params = (month,)
            title = f"Expenses for {month}"
        elif period == "custom":
            # Implement custom date range dialog
            pass

        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT category, SUM(amount) as total 
                FROM expenses 
                WHERE {where_clause}
                GROUP BY category 
                HAVING total > 0 
                ORDER BY total DESC
            """, params)
            rows = cursor.fetchall()

            if not rows:
                messagebox.showinfo("No Data", "No expenses found for the selected period")
                return

            # Clear previous data
            for item in self.summary_tree.get_children():
                self.summary_tree.delete(item)

            # Clear previous chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # Calculate total and percentages
            total = sum(row[1] for row in rows)

            # Add data to treeview
            for category, amount in rows:
                percentage = (amount / total) * 100
                self.summary_tree.insert('', tk.END, values=(
                    category,
                    f"{amount:.2f}",
                    f"{percentage:.1f}%"
                ))

            # Create pie chart
            fig, ax = plt.subplots(figsize=(6, 4))
            categories = [row[0] for row in rows]
            amounts = [row[1] for row in rows]

            ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle
            ax.set_title(title)

            # Embed chart in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to generate summary:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerGUI(root)
    root.mainloop()