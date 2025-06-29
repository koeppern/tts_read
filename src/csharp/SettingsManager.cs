using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;

public class SettingsManager
{
    public Settings Config { get; private set; }
    private readonly string _settingsPath;

    public SettingsManager()
    {
        // First try to find config/settings.json (Python version)
        var configPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "config", "settings.json");
        configPath = Path.GetFullPath(configPath);
        
        if (File.Exists(configPath))
        {
            _settingsPath = configPath;
            LogMessage($"Using Python config file: {_settingsPath}");
        }
        else
        {
            // Fallback to local settings.json
            _settingsPath = Path.Combine(AppContext.BaseDirectory, "settings.json");
            LogMessage($"Using local config file: {_settingsPath}");
        }
        
        LoadSettings();
    }

    private void LogMessage(string message)
    {
        try
        {
            string logPath = Path.Combine(AppContext.BaseDirectory, "debug.log");
            File.AppendAllText(logPath, $"[{DateTime.Now:HH:mm:ss}] SettingsManager: {message}\n");
        }
        catch
        {
            // Ignore logging errors
        }
    }

    private void LoadSettings()
    {
        try
        {
            LogMessage($"Loading settings from: {_settingsPath}");
            
            if (File.Exists(_settingsPath))
            {
                var json = File.ReadAllText(_settingsPath);
                LogMessage($"Settings file content length: {json.Length} characters");
                
                // Try to deserialize as Python format first
                var pythonSettings = JsonSerializer.Deserialize<PythonSettings>(json, new JsonSerializerOptions 
                { 
                    PropertyNameCaseInsensitive = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });
                
                if (pythonSettings != null)
                {
                    // Convert Python format to C# format
                    Config = ConvertPythonSettings(pythonSettings);
                    LogMessage("Successfully loaded Python format settings");
                }
                else
                {
                    LogMessage("Failed to parse as Python format, trying C# format");
                    Config = JsonSerializer.Deserialize<Settings>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                    LogMessage("Successfully loaded C# format settings");
                }
            }
            else
            {
                LogMessage("Settings file not found, creating default settings");
                Config = CreateDefaultSettings();
                SaveSettings();
            }
            
            LogMessage($"Settings loaded: {Config?.Actions?.Count ?? 0} actions, {Config?.Hotkeys?.Count ?? 0} hotkeys");
        }
        catch (Exception ex)
        {
            LogMessage($"ERROR loading settings: {ex.Message}");
            LogMessage($"Stack trace: {ex.StackTrace}");
            Config = CreateDefaultSettings();
        }
    }

    private Settings ConvertPythonSettings(PythonSettings pythonSettings)
    {
        var settings = new Settings
        {
            Actions = new Dictionary<string, ActionConfig>(),
            Hotkeys = new Dictionary<string, string>()
        };

        // Convert actions
        if (pythonSettings.Actions != null)
        {
            foreach (var action in pythonSettings.Actions)
            {
                settings.Actions[action.Key] = new ActionConfig
                {
                    Name = action.Value.Name ?? action.Key,
                    Enabled = action.Value.Enabled,
                    Engine = action.Value.Engine ?? "SAPI",
                    Voice = action.Value.Voice ?? "",
                    Speed = action.Value.Speed
                };
            }
        }

        // Convert hotkeys - map from Python action names to C# action names
        if (pythonSettings.Hotkeys != null)
        {
            LogMessage($"Converting {pythonSettings.Hotkeys.Count} hotkeys from Python format");
            foreach (var hotkey in pythonSettings.Hotkeys)
            {
                LogMessage($"Processing hotkey: {hotkey.Key} = {hotkey.Value}");
                string csharpKey = hotkey.Key;
                
                // Map Python hotkey names to C# names
                if (hotkey.Key == "action_0") csharpKey = "action_1";
                // Keep action_1, action_2, action_pause as is (no mapping needed)
                
                LogMessage($"Mapped {hotkey.Key} -> {csharpKey}");
                settings.Hotkeys[csharpKey] = hotkey.Value;
            }
            LogMessage($"Final hotkeys count: {settings.Hotkeys.Count}");
        }

        return settings;
    }

    private Settings CreateDefaultSettings()
    {
        return new Settings
        {
            Actions = new Dictionary<string, ActionConfig>
            {
                ["action_1"] = new ActionConfig { Name = "Speaker 1", Enabled = true, Engine = "SAPI", Voice = "", Speed = 1.0f },
                ["action_2"] = new ActionConfig { Name = "Speaker 2", Enabled = true, Engine = "SAPI", Voice = "", Speed = 1.2f },
                ["action_pause"] = new ActionConfig { Name = "Pause/Resume", Enabled = true },
            },
            Hotkeys = new Dictionary<string, string>
            {
                ["action_1"] = "ctrl+5",
                ["action_2"] = "ctrl+6",
                ["action_pause"] = "ctrl+3"
            }
        };
    }

    public void SaveSettings()
    {
        try
        {
            var options = new JsonSerializerOptions { WriteIndented = true, PropertyNameCaseInsensitive = true };
            var json = JsonSerializer.Serialize(Config, options);
            File.WriteAllText(_settingsPath, json);
            LogMessage("Settings saved successfully");
        }
        catch (Exception ex)
        {
            LogMessage($"ERROR saving settings: {ex.Message}");
        }
    }
    
    public string GetSettingsPath()
    {
        return _settingsPath;
    }
}

// Python settings format classes
public class PythonSettings
{
    public Dictionary<string, PythonActionConfig>? Actions { get; set; }
    public Dictionary<string, string>? Hotkeys { get; set; }
    public PythonReadAlongWindow? ReadAlongWindow { get; set; }
    public bool Startup { get; set; }
}

public class PythonActionConfig
{
    public string? Name { get; set; }
    public string? Engine { get; set; }
    public string? Voice { get; set; }
    public float Rate { get; set; }
    public float Speed { get; set; }
    public bool Enabled { get; set; }
}

public class PythonReadAlongWindow
{
    public int FontSize { get; set; }
    public string? HighlightColor { get; set; }
    public bool DarkMode { get; set; }
}

// C# settings format classes
public class Settings
{
    public Dictionary<string, ActionConfig>? Actions { get; set; }
    public Dictionary<string, string>? Hotkeys { get; set; }
}

public class ActionConfig
{
    public string? Name { get; set; }
    public bool Enabled { get; set; }
    public string? Engine { get; set; }
    public string? Voice { get; set; }
    public float Speed { get; set; }
}
