import tkinter as tk
from tkinter import font
import threading
import queue
import time

class TextDisplayWindow:
    """A window to display text being read, with word highlighting."""

    def __init__(self, settings_manager):
        """Initialize the text display window."""
        self.settings_manager = settings_manager
        self.window = None
        self.text_widget = None
        self.current_text = ""
        self.is_autoscroll_enabled = True
        
        # Threading support
        self.gui_thread = None
        self.command_queue = queue.Queue()
        self.is_running = False
        self.window_ready = threading.Event()
        
        # Start GUI thread
        self._start_gui_thread()

    def _start_gui_thread(self):
        """Start the GUI thread for Tkinter."""
        print("🧵 DEBUG: Starte GUI-Thread für Tkinter...")
        self.is_running = True
        self.gui_thread = threading.Thread(target=self._gui_thread_worker, daemon=True)
        self.gui_thread.start()
        
        # Wait for window to be ready
        print("⏳ DEBUG: Warte auf GUI-Thread...")
        self.window_ready.wait(timeout=5.0)
        print("✅ DEBUG: GUI-Thread ist bereit")
    
    def _gui_thread_worker(self):
        """Worker function for the GUI thread."""
        try:
            print("🖥️ DEBUG: GUI-Thread gestartet, erstelle Tkinter-Fenster...")
            
            # Create Tkinter window in this thread
            self.window = tk.Tk()
            self.window.title("Vorgelesener Text")
            
            # Initially hide the window
            self.window.withdraw()
            
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
            self.window.bind("<Control-plus>", self._increase_font_size)
            self.window.bind("<Control-minus>", self._decrease_font_size)
            self.window.bind("<Control-MouseWheel>", self._change_font_size_on_scroll)
            self.window.bind("<KeyPress-space>", self._enable_autoscroll)
            
            self.text_widget.bind("<Control-plus>", self._increase_font_size)
            self.text_widget.bind("<Control-minus>", self._decrease_font_size)
            self.text_widget.bind("<Control-MouseWheel>", self._change_font_size_on_scroll)
            self.text_widget.bind("<KeyPress-space>", self._enable_autoscroll)
            self.text_widget.bind("<MouseWheel>", self._disable_autoscroll)
            self.text_widget.bind("<Button-1>", self._disable_autoscroll)  # Mouse click
            
            # Window closing events
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
            self.window.bind("<Alt-F4>", self._on_close)
            self.window.bind("<Control-q>", self._on_close)
            self.window.bind("<Control-w>", self._on_close)
            
            print("✅ DEBUG: Tkinter-Fenster erstellt, signalisiere Bereitschaft...")
            self.window_ready.set()
            
            # Main event loop with command processing
            self._run_event_loop()
            
        except Exception as e:
            print(f"❌ DEBUG: Fehler im GUI-Thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("🔚 DEBUG: GUI-Thread beendet")
    
    def _run_event_loop(self):
        """Run the Tkinter event loop with command processing."""
        while self.is_running:
            try:
                # Process Tkinter events
                self.window.update()
                
                # Process commands from other threads
                try:
                    while True:
                        command, args, kwargs = self.command_queue.get_nowait()
                        self._execute_command(command, args, kwargs)
                except queue.Empty:
                    pass
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)
                
            except tk.TclError:
                # Window was destroyed
                break
            except Exception as e:
                print(f"❌ DEBUG: Fehler in Event-Loop: {e}")
                break
    
    def _execute_command(self, command, args, kwargs):
        """Execute a command in the GUI thread."""
        try:
            if command == "show":
                self._show_window()
            elif command == "hide":
                self._hide_window()
            elif command == "set_text":
                self._set_text_internal(args[0])
            elif command == "highlight_word":
                self._highlight_word_internal(args[0], args[1])
            else:
                print(f"❌ DEBUG: Unbekannter Befehl: {command}")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Ausführen von Befehl {command}: {e}")
    
    def _show_window(self):
        """Internal method to show window (runs in GUI thread)."""
        print("📄 DEBUG: _show_window() aufgerufen im GUI-Thread")
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.attributes('-topmost', True)
            self.window.focus_force()
            self.window.after(2000, lambda: self.window.attributes('-topmost', False))
            print("✅ DEBUG: Fenster erfolgreich angezeigt (GUI-Thread)")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Anzeigen (GUI-Thread): {e}")
    
    def _hide_window(self):
        """Internal method to hide window (runs in GUI thread)."""
        self.window.withdraw()
    
    def _set_text_internal(self, text):
        """Internal method to set text (runs in GUI thread)."""
        print(f"📝 DEBUG: Setze Text im GUI-Thread: {len(text)} Zeichen")
        try:
            self.current_text = text
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", text)
            print("✅ DEBUG: Text erfolgreich gesetzt")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Setzen des Textes: {e}")
    
    def _highlight_word_internal(self, location, length):
        """Internal method to highlight word (runs in GUI thread)."""
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

    def show(self):
        """Show the window (thread-safe)."""
        print("🎯 DEBUG: show() method aufgerufen (thread-safe)")
        self.command_queue.put(("show", (), {}))

    def hide(self):
        """Hide the window (thread-safe)."""
        self.command_queue.put(("hide", (), {}))

    def set_text(self, text):
        """Set the text to be displayed (thread-safe)."""
        print(f"📝 DEBUG: set_text() aufgerufen: {len(text)} Zeichen")
        self.command_queue.put(("set_text", (text,), {}))

    def highlight_word(self, location, length):
        """Highlight the word at the given location (thread-safe)."""
        self.command_queue.put(("highlight_word", (location, length), {}))

    def _increase_font_size(self, event=None):
        """Increase the font size (GUI thread)."""
        current_font = font.Font(font=self.text_widget["font"])
        new_size = current_font.actual("size") + 2
        self.text_widget.configure(font=(current_font.actual("family"), new_size))

    def _decrease_font_size(self, event=None):
        """Decrease the font size (GUI thread)."""
        current_font = font.Font(font=self.text_widget["font"])
        new_size = max(8, current_font.actual("size") - 2)
        self.text_widget.configure(font=(current_font.actual("family"), new_size))

    def _change_font_size_on_scroll(self, event):
        """Change font size with Ctrl+MouseWheel (GUI thread)."""
        if event.delta > 0:
            self._increase_font_size()
        else:
            self._decrease_font_size()

    def _enable_autoscroll(self, event=None):
        """Enable autoscrolling (GUI thread)."""
        self.is_autoscroll_enabled = True
        # Try to scroll to any existing highlight
        try:
            current_highlight = self.text_widget.tag_ranges("highlight")
            if current_highlight:
                self.text_widget.see(current_highlight[0])
        except tk.TclError:
            pass

    def _disable_autoscroll(self, event=None):
        """Disable autoscrolling (GUI thread)."""
        self.is_autoscroll_enabled = False

    def _on_close(self, event=None):
        """Handle window closing (GUI thread)."""
        # Persist font size
        current_font = font.Font(font=self.text_widget["font"])
        font_size = current_font.actual("size")
        self.settings_manager.save_setting("readAlongWindow.fontSize", font_size)
        
        self._hide_window()
    
    def cleanup(self):
        """Clean up resources and stop GUI thread."""
        print("🧹 DEBUG: TextDisplayWindow cleanup aufgerufen")
        self.is_running = False
        if self.gui_thread and self.gui_thread.is_alive():
            try:
                self.gui_thread.join(timeout=2.0)
            except:
                pass
        print("✅ DEBUG: TextDisplayWindow cleanup abgeschlossen")

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
