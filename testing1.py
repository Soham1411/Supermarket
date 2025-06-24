import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import pandas as pd
import os
from datetime import datetime

INVENTORY_FILE = "inventory.csv"
USERS_FILE = "users.csv"
SALES_FILE = "sales.csv"


def load_inventory():
    if not os.path.exists(INVENTORY_FILE):
        df = pd.DataFrame(columns=["Item", "Price", "Stock"])
        df.to_csv(INVENTORY_FILE, index=False)
    return pd.read_csv(INVENTORY_FILE)


def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)


def log_sale(user, item, qty, price, total):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[now, user, item, qty, price, total]],
                         columns=["Datetime", "User", "Item", "Quantity", "Price", "Total"])
    if os.path.exists(SALES_FILE):
        entry.to_csv(SALES_FILE, mode='a', header=False, index=False)
    else:
        entry.to_csv(SALES_FILE, index=False)


class SupermarketApp:
    def __init__(self, root, role, username):
        self.root = root
        self.role = role
        self.username = username
        self.root.title(f"Supermarket - {role}")
        self.root.geometry("700x650")
        self.root.configure(bg="#fcfcfc")

        self.inventory = load_inventory()
        self.cart = []

        tk.Label(root, text=f"Welcome, {username} ({role})", font=("Helvetica", 14, "bold"), bg="#fcfcfc", fg="#003366").pack(pady=10)

        self.frame = tk.Frame(root, bg="#fcfcfc")
        self.frame.pack(pady=10)

        if self.role == "Cashier":
            tk.Label(self.frame, text="Search Item:", bg="#fcfcfc").grid(row=0, column=0, padx=5, pady=5)
            self.search_var = tk.StringVar()
            self.search_entry = tk.Entry(self.frame, textvariable=self.search_var, width=25)
            self.search_entry.grid(row=0, column=1)
            self.search_entry.bind("<KeyRelease>", self.update_dropdown)

            tk.Label(self.frame, text="Select Item:", bg="#fcfcfc").grid(row=1, column=0, padx=5, pady=5)
            self.item_var = tk.StringVar()
            self.item_dropdown = ttk.Combobox(self.frame, textvariable=self.item_var, width=25, state="readonly")
            self.item_dropdown.grid(row=1, column=1)
            self.item_dropdown['values'] = list(self.inventory['Item'])

            tk.Label(self.frame, text="Quantity:", bg="#fcfcfc").grid(row=2, column=0, padx=5, pady=5)
            self.qty_entry = tk.Entry(self.frame, width=25)
            self.qty_entry.grid(row=2, column=1)

            tk.Button(self.frame, text="Add to Cart", command=self.add_to_cart, bg="#28a745", fg="white", width=20).grid(row=3, column=0, columnspan=2, pady=10)
            tk.Button(self.frame, text="Upload Sale", command=self.upload_cart, bg="#007bff", fg="white", width=20).grid(row=4, column=0, columnspan=2, pady=5)

        tk.Button(self.frame, text="Show Stock", command=self.show_stock, bg="#17a2b8", fg="white", width=20).grid(row=5, column=0, columnspan=2, pady=5)

        if self.role == "Admin":
            tk.Button(self.frame, text="Refill Stock", command=self.refill_stock, bg="#ffc107", fg="black", width=20).grid(row=6, column=0, columnspan=2, pady=5)
            tk.Button(self.frame, text="View Sales History", command=self.view_sales_history, bg="#6c757d", fg="white", width=20).grid(row=7, column=0, columnspan=2, pady=5)
            tk.Button(self.frame, text="Visualize Market Data", command=self.show_dashboard, bg="#6610f2", fg="white", width=20).grid(row=8, column=0, columnspan=2, pady=5)

        tk.Button(self.frame, text="Logout", command=self.logout, bg="#dc3545", fg="white", width=20).grid(row=9, column=0, columnspan=2, pady=10)

        self.output = tk.Text(root, height=12, width=70, bg="#f5f5f5")
        self.output.pack(pady=10)

    def update_dropdown(self, event):
        search_text = self.search_var.get().lower()
        filtered = [item for item in self.inventory['Item'] if search_text in item.lower()]
        self.item_dropdown['values'] = filtered
        if filtered:
            self.item_dropdown.current(0)

    def add_to_cart(self):
        item = self.item_var.get()
        try:
            qty = int(self.qty_entry.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter valid quantity")
            return

        if item not in list(self.inventory['Item']):
            messagebox.showerror("Error", "Selected item not found")
            return

        idx = self.inventory[self.inventory['Item'] == item].index[0]
        stock = self.inventory.at[idx, 'Stock']
        price = self.inventory.at[idx, 'Price']

        if qty > stock:
            messagebox.showerror("Stock Error", f"Only {stock} in stock")
            return

        self.cart.append((item, qty, price))
        self.output.insert(tk.END, f"🛒 Added to Cart: {item} x{qty} (₹{qty * price})\n")
        self.qty_entry.delete(0, tk.END)

    def upload_cart(self):
        if not self.cart:
            messagebox.showinfo("Cart Empty", "No items to upload.")
            return

        for item, qty, price in self.cart:
            idx = self.inventory[self.inventory['Item'] == item].index[0]
            self.inventory.at[idx, 'Stock'] -= qty
            total = qty * price
            log_sale(self.username, item, qty, price, total)

        save_inventory(self.inventory)
        self.output.insert(tk.END, f"\n✅ Sale Uploaded for {len(self.cart)} items\n")
        self.cart.clear()

    def refill_stock(self):
        item = simpledialog.askstring("Refill", "Item name:")
        if item not in list(self.inventory['Item']):
            messagebox.showerror("Not Found", "Item not in inventory")
            return

        try:
            qty = simpledialog.askinteger("Refill Quantity", f"Refill quantity for {item}:")
            if qty is None or qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter valid quantity")
            return

        idx = self.inventory[self.inventory['Item'] == item].index[0]
        self.inventory.at[idx, 'Stock'] += qty
        save_inventory(self.inventory)
        messagebox.showinfo("Refilled", f"{item} refilled by {qty}")

    def show_stock(self):
        self.inventory = load_inventory()
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "\n📦 Current Inventory:\n\n")
        for _, row in self.inventory.iterrows():
            self.output.insert(tk.END, f"{row['Item']} - ₹{row['Price']} - {row['Stock']} in stock\n")

    def view_sales_history(self):
        self.output.delete("1.0", tk.END)
        if not os.path.exists(SALES_FILE):
            self.output.insert(tk.END, "No sales found.\n")
            return
        sales = pd.read_csv(SALES_FILE)
        for _, row in sales.iterrows():
            self.output.insert(tk.END, f"{row['Datetime']} | {row['User']} sold {row['Quantity']} {row['Item']} for ₹{row['Total']}\n")

    def show_dashboard(self):
        if not os.path.exists(SALES_FILE):
            messagebox.showinfo("No Data", "No sales to visualize.")
            return
        sales_df = pd.read_csv(SALES_FILE)
        sales_df["Datetime"] = pd.to_datetime(sales_df["Datetime"])

        dash = tk.Toplevel(self.root)
        dash.title("📊 Market Dashboard")
        dash.geometry("800x600")

        fig, axs = plt.subplots(2, 1, figsize=(8, 8), constrained_layout=True)
        fig.suptitle("Market Overview", fontsize=14)

        profit_df = sales_df.groupby("Item").sum(numeric_only=True)
        axs[0].bar(profit_df.index, profit_df["Total"], color="teal")
        axs[0].set_title("Profit per Item")
        axs[0].set_ylabel("₹")
        axs[0].grid(True)

        daily = sales_df.groupby(sales_df["Datetime"].dt.date).sum(numeric_only=True)
        axs[1].plot(daily.index, daily["Total"], marker="o", color="orange")
        axs[1].set_title("Sales Over Time")
        axs[1].set_xlabel("Date")
        axs[1].set_ylabel("₹")
        axs[1].grid(True)

        canvas = FigureCanvasTkAgg(fig, master=dash)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def logout(self):
        self.root.destroy()
        main()


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("350x250")
        self.root.configure(bg="#f0f0f0")

        tk.Label(root, text="Supermarket Login", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="#003366").pack(pady=15)

        tk.Label(root, text="Username:", bg="#f0f0f0").pack()
        self.username = tk.Entry(root, width=25)
        self.username.pack(pady=5)

        tk.Label(root, text="Password:", bg="#f0f0f0").pack()
        self.password = tk.Entry(root, show="*", width=25)
        self.password.pack(pady=5)

        tk.Button(root, text="Login", bg="#0055aa", fg="white", width=20, command=self.login).pack(pady=15)

    def login(self):
        try:
            users_df = pd.read_csv(USERS_FILE)
        except:
            messagebox.showerror("Error", "users.csv not found")
            return

        username = self.username.get()
        password = self.password.get()
        user = users_df[(users_df["Username"] == username) & (users_df["Password"] == password)]

        if not user.empty:
            role = user.iloc[0]["Role"]
            self.root.destroy()
            open_app(role, username)
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")


def open_app(role, username):
    root = tk.Tk()
    SupermarketApp(root, role, username)
    root.mainloop()


def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    if not os.path.exists(INVENTORY_FILE):
        pd.DataFrame(columns=["Item", "Price", "Stock"]).to_csv(INVENTORY_FILE, index=False)
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([
            {"Username": "admin", "Password": "admin123", "Role": "Admin"},
            {"Username": "cashier", "Password": "cashier123", "Role": "Cashier"}
        ]).to_csv(USERS_FILE, index=False)

    main()
