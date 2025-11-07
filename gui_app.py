#!/usr/bin/env python3
"""
Desktop GUI for Image Fetcher using tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from pathlib import Path
from config import Config
from image_fetcher import ImageFetcher


class ImageFetcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Fetcher")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        # Configuration
        self.config = Config()
        self.fetcher = ImageFetcher(self.config)
        self.is_running = False

        # Setup UI
        self.setup_ui()

        # Check API keys
        self.check_api_keys()

    def setup_ui(self):
        """Setup the user interface"""

        # Title
        title_frame = tk.Frame(self.root, bg="#667eea", height=100)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="Image Fetcher",
            font=("Helvetica", 28, "bold"),
            bg="#667eea",
            fg="white"
        )
        title_label.pack(pady=30)

        # Main content
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Search Theme
        tk.Label(content_frame, text="Search Theme:", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.theme_entry = tk.Entry(content_frame, font=("Helvetica", 11), width=50)
        self.theme_entry.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        self.theme_entry.insert(0, "sunset beach")

        # Sources and Count
        row2_frame = tk.Frame(content_frame)
        row2_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        row2_frame.columnconfigure(0, weight=1)
        row2_frame.columnconfigure(1, weight=1)

        # Sources
        sources_frame = tk.Frame(row2_frame)
        sources_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        tk.Label(sources_frame, text="Image Sources:", font=("Helvetica", 10, "bold")).pack(
            anchor="w", pady=(0, 5)
        )

        self.sources_var = tk.StringVar(value="all")
        sources_combo = ttk.Combobox(
            sources_frame,
            textvariable=self.sources_var,
            values=["all", "pexels", "pixabay", "duckduckgo"],
            state="readonly",
            font=("Helvetica", 10)
        )
        sources_combo.pack(fill=tk.X)

        # Count
        count_frame = tk.Frame(row2_frame)
        count_frame.grid(row=0, column=1, sticky="ew")

        tk.Label(count_frame, text="Number of Images:", font=("Helvetica", 10, "bold")).pack(
            anchor="w", pady=(0, 5)
        )

        self.count_var = tk.IntVar(value=10)
        count_spinbox = tk.Spinbox(
            count_frame,
            from_=1,
            to=100,
            textvariable=self.count_var,
            font=("Helvetica", 10),
            width=10
        )
        count_spinbox.pack(fill=tk.X)

        # Category
        tk.Label(content_frame, text="Category (Optional):", font=("Helvetica", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(0, 5)
        )
        self.category_entry = tk.Entry(content_frame, font=("Helvetica", 11))
        self.category_entry.grid(row=4, column=0, columnspan=2, pady=(0, 5), sticky="ew")

        category_hint = tk.Label(
            content_frame,
            text="Pixabay: nature, backgrounds, science, people | Pexels: landscape, portrait",
            font=("Helvetica", 8),
            fg="gray"
        )
        category_hint.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Buttons frame
        btn_frame = tk.Frame(content_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(0, 15))

        self.fetch_btn = tk.Button(
            btn_frame,
            text="Fetch Images",
            command=self.start_fetch,
            font=("Helvetica", 12, "bold"),
            bg="#667eea",
            fg="white",
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.fetch_btn.pack(side=tk.LEFT, padx=5)

        setup_btn = tk.Button(
            btn_frame,
            text="Setup API Keys",
            command=self.open_setup,
            font=("Helvetica", 10),
            bg="#ff9800",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        setup_btn.pack(side=tk.LEFT, padx=5)

        # Progress/Status
        tk.Label(content_frame, text="Status:", font=("Helvetica", 10, "bold")).grid(
            row=7, column=0, sticky="w", pady=(0, 5)
        )

        self.status_text = scrolledtext.ScrolledText(
            content_frame,
            height=10,
            font=("Courier", 9),
            state=tk.DISABLED
        )
        self.status_text.grid(row=8, column=0, columnspan=2, sticky="ew")

        # Configure grid weights
        content_frame.columnconfigure(0, weight=1)

    def check_api_keys(self):
        """Check if API keys are configured"""
        has_pexels = bool(self.config.get_api_key('pexels'))
        has_pixabay = bool(self.config.get_api_key('pixabay'))

        if not has_pexels and not has_pixabay:
            self.log_status(
                "⚠ No API keys configured. Click 'Setup API Keys' for better results!\n"
                "Currently only DuckDuckGo is available (no API key needed).\n",
                "orange"
            )

    def log_status(self, message, color=None):
        """Log message to status text area"""
        self.status_text.config(state=tk.NORMAL)
        if color:
            tag = f"color_{color}"
            self.status_text.tag_config(tag, foreground=color)
            self.status_text.insert(tk.END, message, tag)
        else:
            self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def start_fetch(self):
        """Start fetching images"""
        if self.is_running:
            messagebox.showwarning("Already Running", "A fetch operation is already in progress!")
            return

        theme = self.theme_entry.get().strip()
        if not theme:
            messagebox.showerror("Error", "Please enter a search theme!")
            return

        count = self.count_var.get()
        sources = self.sources_var.get()
        category = self.category_entry.get().strip() or None

        # Clear status
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

        # Disable button
        self.is_running = True
        self.fetch_btn.config(state=tk.DISABLED, text="Fetching...")

        # Run in background thread
        thread = threading.Thread(
            target=self.fetch_thread,
            args=(theme, count, sources, category),
            daemon=True
        )
        thread.start()

    def fetch_thread(self, theme, count, sources, category):
        """Background thread for fetching"""
        try:
            self.log_status(f"Starting fetch: '{theme}' ({count} images)\n", "blue")
            self.log_status(f"Sources: {sources}\n")
            if category:
                self.log_status(f"Category: {category}\n")
            self.log_status("-" * 60 + "\n")

            result_dir = self.fetcher.fetch_and_process(theme, count, sources, category)

            self.log_status("\n" + "=" * 60 + "\n", "green")
            self.log_status(f"✅ Success! Images saved to:\n", "green")
            self.log_status(f"{result_dir}\n", "blue")
            self.log_status("=" * 60 + "\n", "green")

            messagebox.showinfo("Success", f"Successfully fetched {count} images!\n\nSaved to:\n{result_dir}")

        except Exception as e:
            self.log_status(f"\n❌ Error: {str(e)}\n", "red")
            messagebox.showerror("Error", f"Failed to fetch images:\n{str(e)}")

        finally:
            self.is_running = False
            self.fetch_btn.config(state=tk.NORMAL, text="Fetch Images")

    def open_setup(self):
        """Open API key setup dialog"""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("API Key Setup")
        setup_window.geometry("500x300")
        setup_window.resizable(False, False)

        # Title
        title_label = tk.Label(
            setup_window,
            text="Configure API Keys",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=20)

        # Content
        content = tk.Frame(setup_window, padx=30)
        content.pack(fill=tk.BOTH, expand=True)

        # Pexels
        tk.Label(content, text="Pexels API Key:", font=("Helvetica", 10, "bold")).pack(
            anchor="w", pady=(10, 5)
        )
        pexels_entry = tk.Entry(content, font=("Helvetica", 10), width=50)
        pexels_entry.pack(fill=tk.X, pady=(0, 5))
        pexels_entry.insert(0, self.config.get_api_key('pexels'))

        pexels_link = tk.Label(
            content,
            text="Get free key at: https://www.pexels.com/api/",
            font=("Helvetica", 8),
            fg="blue",
            cursor="hand2"
        )
        pexels_link.pack(anchor="w", pady=(0, 10))

        # Pixabay
        tk.Label(content, text="Pixabay API Key:", font=("Helvetica", 10, "bold")).pack(
            anchor="w", pady=(10, 5)
        )
        pixabay_entry = tk.Entry(content, font=("Helvetica", 10), width=50)
        pixabay_entry.pack(fill=tk.X, pady=(0, 5))
        pixabay_entry.insert(0, self.config.get_api_key('pixabay'))

        pixabay_link = tk.Label(
            content,
            text="Get free key at: https://pixabay.com/api/docs/",
            font=("Helvetica", 8),
            fg="blue",
            cursor="hand2"
        )
        pixabay_link.pack(anchor="w", pady=(0, 20))

        # Save button
        def save_keys():
            pexels_key = pexels_entry.get().strip()
            pixabay_key = pixabay_entry.get().strip()

            if pexels_key:
                self.config.set_api_key('pexels', pexels_key)
            if pixabay_key:
                self.config.set_api_key('pixabay', pixabay_key)

            messagebox.showinfo("Success", "API keys saved successfully!")
            setup_window.destroy()

            # Refresh fetcher
            self.fetcher = ImageFetcher(self.config)
            self.check_api_keys()

        save_btn = tk.Button(
            content,
            text="Save Configuration",
            command=save_keys,
            font=("Helvetica", 12, "bold"),
            bg="#667eea",
            fg="white",
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        save_btn.pack()


def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app = ImageFetcherGUI(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
