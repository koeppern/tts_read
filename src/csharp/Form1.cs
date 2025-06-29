using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;
using System.Speech.Synthesis;
using System.Threading;
using System.Windows.Forms;
using System.Linq;

namespace TtsRead
{
    public class Form1 : Form
    {
        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool DestroyIcon(IntPtr hIcon);
        private readonly SettingsManager _settingsManager;
        private HotkeyListener? _hotkeyListener;
        private SpeechSynthesizer _speechSynthesizer;
        private readonly NotifyIcon _notifyIcon;
        private readonly string _logPath;
        private Icon? _customIcon;
        private IntPtr _iconHandle;

        public Form1()
        {
            _logPath = Path.Combine(AppContext.BaseDirectory, "debug.log");
            LogMessage("Form1 constructor starting...");
            
            try
            {
                this.WindowState = FormWindowState.Minimized;
                this.ShowInTaskbar = false;
                LogMessage("Form window state set to minimized");

                _settingsManager = new SettingsManager();
                LogMessage("SettingsManager created");
                
                _speechSynthesizer = new SpeechSynthesizer();
                LogMessage("SpeechSynthesizer created");

                // Create tray icon first
                _customIcon = CreateTrayIcon();
                _notifyIcon = new NotifyIcon
                {
                    Icon = _customIcon,
                    Visible = true,
                    Text = "TTS Read - Starting..."
                };
                LogMessage("NotifyIcon created and set visible");

                var contextMenu = new ContextMenuStrip();
                contextMenu.Items.Add("Open Settings", null, (s, e) => OpenSettings());
                contextMenu.Items.Add("Exit", null, (s, e) => Close());
                _notifyIcon.ContextMenuStrip = contextMenu;
                LogMessage("Context menu created");

                if (AdminHelper.IsAdmin())
                {
                    LogMessage("Running as administrator - initializing hotkeys");
                    _hotkeyListener = new HotkeyListener();
                    RegisterHotkeys();
                    _notifyIcon.Text = "TTS Read - Running as Admin";
                }
                else
                {
                    LogMessage("NOT running as administrator");
                    _notifyIcon.Text = "TTS Read - No Admin Rights";
                }

                LogMessage("Form1 constructor completed successfully");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR in Form1 constructor: {ex.Message}");
                LogMessage($"Stack trace: {ex.StackTrace}");
                throw;
            }
        }

        private void LogMessage(string message)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                File.AppendAllText(_logPath, $"[{timestamp}] {message}\n");
            }
            catch
            {
                // Ignore logging errors
            }
        }

        private void LogSpeechState(string context)
        {
            try
            {
                LogMessage($"SPEECH STATE [{context}]: State={_speechSynthesizer.State}, Rate={_speechSynthesizer.Rate}, Voice={_speechSynthesizer.Voice?.Name ?? "Unknown"}");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR getting speech state: {ex.Message}");
            }
        }

        private void LogHotkeyEvent(string hotkey, string action)
        {
            LogMessage($"HOTKEY PRESSED: {hotkey} -> Action: {action}");
            LogSpeechState("Before Hotkey Processing");
        }

        private Icon CreateTrayIcon()
        {
            try
            {
                // Create a 32x32 icon with TTS theme
                var bitmap = new Bitmap(32, 32);
                using (var graphics = Graphics.FromImage(bitmap))
                {
                    graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
                    graphics.Clear(Color.Transparent);
                    
                    // Draw a modern speaker/sound icon
                    using (var brush = new SolidBrush(Color.FromArgb(0, 120, 215))) // Windows blue
                    using (var pen = new Pen(Color.White, 2))
                    {
                        // Speaker base (rectangle)
                        graphics.FillRectangle(brush, 4, 12, 8, 8);
                        graphics.DrawRectangle(pen, 4, 12, 8, 8);
                        
                        // Speaker cone (triangle)
                        Point[] cone = { new Point(12, 10), new Point(12, 22), new Point(20, 18), new Point(20, 14) };
                        graphics.FillPolygon(brush, cone);
                        graphics.DrawPolygon(pen, cone);
                        
                        // Sound waves
                        using (var wavePen = new Pen(Color.FromArgb(0, 120, 215), 1.5f))
                        {
                            graphics.DrawArc(wavePen, 18, 8, 8, 16, -45, 90);   // Inner wave
                            graphics.DrawArc(wavePen, 20, 6, 10, 20, -45, 90);  // Middle wave  
                            graphics.DrawArc(wavePen, 22, 4, 12, 24, -45, 90);  // Outer wave
                        }
                        
                        // Add "T" for TTS
                        using (var font = new Font("Segoe UI", 8, FontStyle.Bold))
                        using (var textBrush = new SolidBrush(Color.White))
                        {
                            graphics.DrawString("T", font, textBrush, 6, 14);
                        }
                    }
                }
                
                // Convert bitmap to icon
                _iconHandle = bitmap.GetHicon();
                Icon icon = Icon.FromHandle(_iconHandle);
                LogMessage("Custom TTS icon created successfully");
                return icon;
            }
            catch (Exception ex)
            {
                LogMessage($"Error creating custom icon: {ex.Message}");
                // Fallback to a better system icon
                return SystemIcons.Information;
            }
        }

        private void RegisterHotkeys()
        {
            try
            {
                LogMessage("Starting hotkey registration...");
                
                if (_settingsManager.Config?.Hotkeys == null)
                {
                    LogMessage("No hotkeys configuration found");
                    return;
                }

                foreach (var hotkey in _settingsManager.Config.Hotkeys)
                {
                    LogMessage($"Processing hotkey: {hotkey.Key} = {hotkey.Value}");
                    
                    if (string.IsNullOrEmpty(hotkey.Value) || hotkey.Value.ToLower() == "none")
                    {
                        LogMessage($"Skipping disabled hotkey: {hotkey.Key}");
                        continue;
                    }

                    var (key, modifiers, success) = ParseHotkey(hotkey.Value);
                    if (!success)
                    {
                        LogMessage($"Failed to parse hotkey: {hotkey.Value}");
                        continue;
                    }

                    Action? action = hotkey.Key switch
                    {
                        "action_1" => () => { LogHotkeyEvent(hotkey.Value, "action_1 (German Voice)"); SpeakFromClipboard("action_1"); },
                        "action_2" => () => { LogHotkeyEvent(hotkey.Value, "action_2 (English Voice)"); SpeakFromClipboard("action_2"); },
                        "action_pause" => () => { LogHotkeyEvent(hotkey.Value, "action_pause (Pause/Resume)"); PauseResumeSpeech(); },
                        _ => null
                    };

                    if (action != null)
                    {
                        bool registered = _hotkeyListener!.RegisterHotKey(key, modifiers, action);
                        LogMessage($"Hotkey {hotkey.Value} for {hotkey.Key}: {(registered ? "SUCCESS" : "FAILED")}");
                    }
                    else
                    {
                        LogMessage($"No action found for hotkey: {hotkey.Key}");
                    }
                }
                
                LogMessage("Hotkey registration completed");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR in RegisterHotkeys: {ex.Message}");
                LogMessage($"Stack trace: {ex.StackTrace}");
            }
        }

        private (Keys key, HotkeyListener.Modifiers modifiers, bool success) ParseHotkey(string hotkeyString)
        {
            try
            {
                var parts = hotkeyString.ToLower().Split('+');
                if (parts.Length != 2)
                {
                    LogMessage($"Invalid hotkey format: {hotkeyString} (expected modifier+key)");
                    return (Keys.None, HotkeyListener.Modifiers.None, false);
                }

                // Parse modifier
                var modifierString = parts[0].Trim();
                HotkeyListener.Modifiers modifiers = modifierString switch
                {
                    "ctrl" or "control" => HotkeyListener.Modifiers.Control,
                    "alt" => HotkeyListener.Modifiers.Alt,
                    "shift" => HotkeyListener.Modifiers.Shift,
                    "win" => HotkeyListener.Modifiers.Win,
                    _ => HotkeyListener.Modifiers.None
                };

                if (modifiers == HotkeyListener.Modifiers.None)
                {
                    LogMessage($"Unknown modifier: {modifierString}");
                    return (Keys.None, HotkeyListener.Modifiers.None, false);
                }

                // Parse key
                var keyString = parts[1].Trim();
                Keys key = keyString switch
                {
                    "1" => Keys.D1,
                    "2" => Keys.D2,
                    "3" => Keys.D3,
                    "4" => Keys.D4,
                    "5" => Keys.D5,
                    "6" => Keys.D6,
                    "7" => Keys.D7,
                    "8" => Keys.D8,
                    "9" => Keys.D9,
                    "0" => Keys.D0,
                    "numpad0" => Keys.NumPad0,
                    "numpad1" => Keys.NumPad1,
                    "numpad2" => Keys.NumPad2,
                    "numpad3" => Keys.NumPad3,
                    "numpad4" => Keys.NumPad4,
                    "numpad5" => Keys.NumPad5,
                    "numpad6" => Keys.NumPad6,
                    "numpad7" => Keys.NumPad7,
                    "numpad8" => Keys.NumPad8,
                    "numpad9" => Keys.NumPad9,
                    _ => Keys.None
                };

                // Try to parse as regular key if numeric parsing failed
                if (key == Keys.None)
                {
                    if (Enum.TryParse<Keys>(keyString, true, out var parsedKey))
                    {
                        key = parsedKey;
                    }
                }

                if (key == Keys.None)
                {
                    LogMessage($"Unknown key: {keyString}");
                    return (Keys.None, HotkeyListener.Modifiers.None, false);
                }

                LogMessage($"Parsed hotkey: {hotkeyString} -> {modifiers}+{key}");
                return (key, modifiers, true);
            }
            catch (Exception ex)
            {
                LogMessage($"Exception parsing hotkey {hotkeyString}: {ex.Message}");
                return (Keys.None, HotkeyListener.Modifiers.None, false);
            }
        }

        private void SpeakFromClipboard(string actionName)
        {
            try
            {
                LogMessage($"=================== SPEAK FROM CLIPBOARD START ===================");
                LogMessage($"SpeakFromClipboard called for action: {actionName}");
                LogSpeechState("Entry Point");
                
                if (!Clipboard.ContainsText())
                {
                    LogMessage("ERROR: No text in clipboard");
                    LogMessage($"=================== SPEAK FROM CLIPBOARD END (NO TEXT) ===================");
                    return;
                }

                string text = Clipboard.GetText();
                LogMessage($"Got text from clipboard: {text.Length} characters - Preview: \"{text.Substring(0, Math.Min(50, text.Length))}...\"");

                var actionConfig = _settingsManager.Config?.Actions?.GetValueOrDefault(actionName);
                if (actionConfig == null || !actionConfig.Enabled)
                {
                    LogMessage($"ERROR: Action {actionName} not found or disabled");
                    LogMessage($"=================== SPEAK FROM CLIPBOARD END (NO CONFIG) ===================");
                    return;
                }

                LogMessage($"Action Config Found: Name='{actionConfig.Name}', Voice='{actionConfig.Voice}', Speed={actionConfig.Speed}, Enabled={actionConfig.Enabled}");

                // STEP 1: Force immediate stop and reset (no waiting)
                LogMessage($"STEP 1: IMMEDIATE STOP AND RESET");
                ForceImmediateReset();

                // STEP 2: Configure voice and rate after reset
                LogMessage($"STEP 2: CONFIGURE VOICE AND RATE");
                ConfigureVoiceAndRate(actionConfig);

                // STEP 3: Start new speech
                LogMessage($"STEP 3: START NEW SPEECH");
                LogSpeechState("Before Starting New Speech");
                LogMessage($"STARTING NEW SPEECH: Text length = {text.Length} characters");
                _speechSynthesizer.SpeakAsync(text);
                LogMessage($"SUCCESS: SpeakAsync called");
                LogSpeechState("After Starting New Speech");
                LogMessage($"=================== SPEAK FROM CLIPBOARD END ===================");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR in SpeakFromClipboard: {ex.Message}");
                LogMessage($"Stack trace: {ex.StackTrace}");
            }
        }

        private void ForceImmediateReset()
        {
            LogMessage($"Current speech state: {_speechSynthesizer.State}");
            
            if (_speechSynthesizer.State != SynthesizerState.Ready)
            {
                LogMessage($"FORCE RESET: Stopping and resetting immediately (no waiting)");
                try
                {
                    _speechSynthesizer.SpeakAsyncCancelAll();
                    _speechSynthesizer.Dispose();
                    _speechSynthesizer = new SpeechSynthesizer();
                    LogMessage("SUCCESS: Force reset completed");
                    LogSpeechState("After Force Reset");
                }
                catch (Exception resetEx)
                {
                    LogMessage($"ERROR in force reset: {resetEx.Message}");
                }
            }
            else
            {
                LogMessage("No reset needed - synthesizer already ready");
            }
        }

        private void ConfigureVoiceAndRate(dynamic actionConfig)
        {
            try
            {
                // Set rate first (fast operation)
                int targetRate = (int)((actionConfig.Speed - 1) * 10);
                LogMessage($"Setting speech rate: Speed={actionConfig.Speed} -> Rate={targetRate}");
                _speechSynthesizer.Rate = targetRate;
                LogMessage($"SUCCESS: Set speech rate to: {_speechSynthesizer.Rate}");

                // Set voice (potentially slow operation)
                if (!string.IsNullOrEmpty(actionConfig.Voice))
                {
                    LogMessage($"VOICE SELECTION: Requesting '{actionConfig.Voice}' (monitoring timing...)");
                    var startTime = DateTime.Now;
                    
                    try
                    {
                        var voices = _speechSynthesizer.GetInstalledVoices();
                        bool voiceFound = voices.Any(v => v.VoiceInfo.Name == actionConfig.Voice);
                        
                        if (voiceFound)
                        {
                            _speechSynthesizer.SelectVoice(actionConfig.Voice);
                            var elapsed = DateTime.Now - startTime;
                            LogMessage($"SUCCESS: Voice '{actionConfig.Voice}' selected in {elapsed.TotalMilliseconds:F0}ms");
                        }
                        else
                        {
                            LogMessage($"WARNING: Voice '{actionConfig.Voice}' not found in available voices");
                            // List available voices for debugging
                            LogMessage($"Available voices:");
                            for (int i = 0; i < voices.Count; i++)
                            {
                                LogMessage($"  {i+1}. {voices[i].VoiceInfo.Name} (Culture: {voices[i].VoiceInfo.Culture})");
                            }
                        }
                    }
                    catch (Exception voiceEx)
                    {
                        var elapsed = DateTime.Now - startTime;
                        LogMessage($"ERROR selecting voice '{actionConfig.Voice}' after {elapsed.TotalMilliseconds:F0}ms: {voiceEx.Message}");
                    }
                }

                LogSpeechState("After Voice and Rate Configuration");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR in ConfigureVoiceAndRate: {ex.Message}");
            }
        }

                private void PauseResumeSpeech()
        {
            try
            {
                LogMessage($"=================== PAUSE/RESUME START ===================");
                LogSpeechState("Entry Point");
                LogMessage($"PauseResumeSpeech called, current state: {_speechSynthesizer.State}");
                
                if (_speechSynthesizer.State == SynthesizerState.Speaking)
                {
                    LogMessage("PAUSING: Speech is currently speaking, calling Pause()");
                    _speechSynthesizer.Pause();
                    LogMessage("SUCCESS: Pause() called");
                    LogSpeechState("After Pause");
                }
                else if (_speechSynthesizer.State == SynthesizerState.Paused)
                {
                    LogMessage("RESUMING: Speech is currently paused, calling Resume()");
                    _speechSynthesizer.Resume();
                    LogMessage("SUCCESS: Resume() called");
                    LogSpeechState("After Resume");
                }
                else
                {
                    LogMessage($"WARNING: No active speech to pause/resume (Current state: {_speechSynthesizer.State})");
                }
                
                LogMessage($"=================== PAUSE/RESUME END ===================");
            }
            catch (Exception ex)
            {
                LogMessage($"CRITICAL ERROR in PauseResumeSpeech: {ex.Message}");
                LogMessage($"Stack trace: {ex.StackTrace}");
            }
        }

        private void OpenSettings()
        {
            try
            {
                LogMessage("Opening settings file");
                string settingsPath = _settingsManager.GetSettingsPath();
                Process.Start(new ProcessStartInfo(settingsPath) { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR opening settings: {ex.Message}");
                MessageBox.Show($"Error opening settings: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            try
            {
                LogMessage("Form closing...");
                _hotkeyListener?.Dispose();
                _notifyIcon.Dispose();
                _customIcon?.Dispose();
                if (_iconHandle != IntPtr.Zero)
                {
                    DestroyIcon(_iconHandle);
                }
                _speechSynthesizer?.Dispose();
                LogMessage("Form closed successfully");
            }
            catch (Exception ex)
            {
                LogMessage($"ERROR in OnFormClosing: {ex.Message}");
            }
            
            base.OnFormClosing(e);
        }
    }
}
