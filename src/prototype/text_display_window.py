import tkinter as tk
from tkinter import font

class TextDisplayWindow:
    """A window to display text being read, with word highlighting."""

    def __init__(self, settings_manager):
        """Initialize the text display window."""
        self.settings_manager = settings_manager
        self.window = None
        self.text_widget = None
        self.current_text = ""
        self.is_autoscroll_enabled = True

    def create_window(self):
        """Create and configure the Tkinter window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Tk()
        self.window.title("Vorgelesener Text")
        
        # Apply dark mode to window if enabled
        dark_mode = self.settings_manager.get_setting("readAlongWindow.darkMode", True)
        if dark_mode:
            self.window.configure(bg="#2b2b2b")
        
        # Set window size to 3/4 of screen size
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.75)
        height = int(screen_height * 0.75)
        self.window.geometry(f"{width}x{height}")

        # Configure colors based on dark mode setting
        if dark_mode:
            bg_color = "#2b2b2b"  # Dark gray
            fg_color = "white"
            insert_color = "white"
        else:
            bg_color = "white"
            fg_color = "black"
            insert_color = "black"
            
        self.text_widget = tk.Text(
            self.window,
            wrap=tk.WORD,
            bg=bg_color,
            fg=fg_color,
            insertbackground=insert_color
        )
        
        # Load font size from settings
        font_size = self.settings_manager.get_setting("readAlongWindow.fontSize", 18)
        self.text_widget.configure(font=("Arial", font_size))
        
        # Add scrollbar with dark mode styling
        if dark_mode:
            scrollbar = tk.Scrollbar(
                self.window, 
                command=self.text_widget.yview,
                bg="#2b2b2b",
                troughcolor="#1e1e1e",
                activebackground="#404040"
            )
        else:
            scrollbar = tk.Scrollbar(self.window, command=self.text_widget.yview)
            
        self.text_widget.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(expand=True, fill=tk.BOTH)

        # Bind events to both window and text widget for better event handling
        self.window.bind("<Control-plus>", self.increase_font_size)
        self.window.bind("<Control-minus>", self.decrease_font_size)
        self.window.bind("<Control-MouseWheel>", self.change_font_size_on_scroll)
        self.window.bind("<KeyPress-space>", self.enable_autoscroll)
        
        self.text_widget.bind("<Control-plus>", self.increase_font_size)
        self.text_widget.bind("<Control-minus>", self.decrease_font_size)
        self.text_widget.bind("<Control-MouseWheel>", self.change_font_size_on_scroll)
        self.text_widget.bind("<KeyPress-space>", self.enable_autoscroll)
        self.text_widget.bind("<MouseWheel>", self.disable_autoscroll)
        self.text_widget.bind("<Button-1>", self.disable_autoscroll)  # Mouse click
        
        # Window closing events
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.bind("<Alt-F4>", self.on_close)
        self.window.bind("<Control-q>", self.on_close)
        self.window.bind("<Control-w>", self.on_close)
        
        # Make sure text widget can receive focus
        self.text_widget.focus_set()

    def show(self):
        """Show the window."""
        if not self.window or not self.window.winfo_exists():
            self.create_window()
        self.window.deiconify()

    def hide(self):
        """Hide the window."""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def set_text(self, text):
        """Set the text to be displayed."""
        if not self.window or not self.window.winfo_exists():
            self.create_window()
        self.current_text = text
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", text)

    def highlight_word(self, location, length):
        """Highlight the word at the given location with the given length."""
        if not self.window or not self.window.winfo_exists():
            return
            
        try:
            # Clear previous highlight
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            
            # Convert character position to tkinter index
            start_index = f"1.0 + {location}c"
            end_index = f"1.0 + {location + length}c"
            
            # Get settings with proper defaults
            dark_mode = self.settings_manager.get_setting("readAlongWindow.darkMode", True)
            highlight_color = self.settings_manager.get_setting("readAlongWindow.highlightColor", "yellow")
            
            # Ensure highlight_color is actually a color, not fontSize
            if isinstance(highlight_color, (int, float)) or str(highlight_color).isdigit():
                highlight_color = "yellow"  # Fallback to default
            
            if dark_mode:
                highlight_fg = "black"
            else:
                highlight_fg = "black"
                
            self.text_widget.tag_add("highlight", start_index, end_index)
            self.text_widget.tag_config("highlight", background=highlight_color, foreground=highlight_fg)

            # Auto-scroll to keep highlighted word visible
            if self.is_autoscroll_enabled:
                self.text_widget.see(start_index)
                
        except tk.TclError as e:
            print(f"❌ Error highlighting word at location {location}, length {length}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in highlight_word: {e}")

    def increase_font_size(self, event=None):
        """Increase the font size."""
        current_font = font.Font(font=self.text_widget["font"])
        new_size = current_font.actual("size") + 2
        self.text_widget.configure(font=(current_font.actual("family"), new_size))

    def decrease_font_size(self, event=None):
        """Decrease the font size."""
        current_font = font.Font(font=self.text_widget["font"])
        new_size = max(8, current_font.actual("size") - 2)
        self.text_widget.configure(font=(current_font.actual("family"), new_size))

    def change_font_size_on_scroll(self, event):
        """Change font size with Ctrl+MouseWheel."""
        if event.delta > 0:
            self.increase_font_size()
        else:
            self.decrease_font_size()

    def enable_autoscroll(self, event=None):
        """Enable autoscrolling."""
        self.is_autoscroll_enabled = True
        # Try to scroll to any existing highlight
        try:
            current_highlight = self.text_widget.tag_ranges("highlight")
            if current_highlight:
                self.text_widget.see(current_highlight[0])
        except tk.TclError:
            pass

    def disable_autoscroll(self, event=None):
        """Disable autoscrolling."""
        self.is_autoscroll_enabled = False

    def on_close(self, event=None):
        """Handle window closing."""
        # Persist font size
        current_font = font.Font(font=self.text_widget["font"])
        font_size = current_font.actual("size")
        self.settings_manager.save_setting("readAlongWindow.fontSize", font_size)
        
        self.hide()

    def update(self):
        """Update the Tkinter window only if it's visible - thread-safe version."""
        try:
            if (self.window and 
                self.window.winfo_exists() and 
                self.window.state() != 'withdrawn'):
                self.window.update()
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                pass  # Ignore thread-related errors - Tkinter will handle itself
            else:
                raise
        except Exception:
            pass  # Ignore other update errors
