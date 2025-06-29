
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class HotkeyListener : IDisposable
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    private const int WM_HOTKEY = 0x0312;

    private readonly IntPtr _hWnd;
    private int _currentId = 0;
    private readonly Dictionary<int, Action> _hotkeyActions = new Dictionary<int, Action>();

    private readonly Window _window;

    public HotkeyListener()
    {
        _window = new Window();
        _window.HotkeyPressed += (s, e) =>
        {
            if (_hotkeyActions.TryGetValue(e.HotkeyId, out var action))
            {
                action?.Invoke();
            }
        };
        _hWnd = _window.Handle;
    }

    public bool RegisterHotKey(Keys key, Modifiers modifiers, Action action)
    {
        _currentId++;
        if (RegisterHotKey(_hWnd, _currentId, (uint)modifiers, (uint)key))
        {
            _hotkeyActions[_currentId] = action;
            return true;
        }
        return false;
    }

    public void Dispose()
    {
        for (int i = 1; i <= _currentId; i++)
        {
            UnregisterHotKey(_hWnd, i);
        }
        _window.Dispose();
    }

    [Flags]
    public enum Modifiers : uint
    {
        None = 0,
        Alt = 1,
        Control = 2,
        Shift = 4,
        Win = 8
    }

    private class Window : NativeWindow, IDisposable
    {
        public event EventHandler<HotkeyPressedEventArgs> HotkeyPressed;

        public Window()
        {
            CreateHandle(new CreateParams());
        }

        protected override void WndProc(ref Message m)
        {
            base.WndProc(ref m);
            if (m.Msg == WM_HOTKEY)
            {
                HotkeyPressed?.Invoke(this, new HotkeyPressedEventArgs(m.WParam.ToInt32()));
            }
        }

        public void Dispose()
        {
            DestroyHandle();
        }
    }

    public class HotkeyPressedEventArgs : EventArgs
    {
        public int HotkeyId { get; }

        public HotkeyPressedEventArgs(int hotkeyId)
        {
            HotkeyId = hotkeyId;
        }
    }
}
