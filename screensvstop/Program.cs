using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ScreenSvStop
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ScreenSvStopContext());
        }
    }

    public class ScreenSvStopContext : ApplicationContext
    {
        private NotifyIcon trayIcon;
        private ContextMenuStrip contextMenu;
        private Timer revertTimer;
        private DateTime? revertEndTime;
        private Timer uiUpdateTimer;
        private System.Threading.SynchronizationContext syncContext;
        
        private ToolStripMenuItem statusMenuItem;
        private ToolStripMenuItem enablePermMenuItem;
        private ToolStripMenuItem enable30MenuItem;
        private ToolStripMenuItem enable60MenuItem;
        private ToolStripMenuItem disableMenuItem;
        private ToolStripMenuItem exitMenuItem;

        public ScreenSvStopContext()
        {
            contextMenu = new ContextMenuStrip();
            
            statusMenuItem = new ToolStripMenuItem("ステータス: 未使用") { Enabled = false };
            enablePermMenuItem = new ToolStripMenuItem("抑止 (永続的)", null, EnablePermanent);
            enable30MenuItem = new ToolStripMenuItem("抑止 (30分)", null, Enable30Min);
            enable60MenuItem = new ToolStripMenuItem("抑止 (1時間)", null, Enable60Min);
            disableMenuItem = new ToolStripMenuItem("抑止を解除 (デフォルト)", null, DisablePrevention);
            exitMenuItem = new ToolStripMenuItem("終了", null, Exit);

            contextMenu.Items.Add(statusMenuItem);
            contextMenu.Items.Add(new ToolStripSeparator());
            contextMenu.Items.Add(enablePermMenuItem);
            contextMenu.Items.Add(enable30MenuItem);
            contextMenu.Items.Add(enable60MenuItem);
            contextMenu.Items.Add(disableMenuItem);
            contextMenu.Items.Add(new ToolStripSeparator());
            contextMenu.Items.Add(exitMenuItem);

            trayIcon = new NotifyIcon
            {
                Icon = GenerateIcon(Color.Gray, "Zzz"),
                ContextMenuStrip = contextMenu,
                Visible = true,
                Text = "ScreenSvStop"
            };

            revertTimer = new Timer();
            revertTimer.Tick += RevertTimer_Tick;

            uiUpdateTimer = new Timer();
            uiUpdateTimer.Interval = 1000;
            uiUpdateTimer.Tick += UiUpdateTimer_Tick;
            uiUpdateTimer.Start();

            UpdateStateUI(false, "未使用");
            
            syncContext = System.Threading.SynchronizationContext.Current;
            SystemEvents.SessionSwitch += SystemEvents_SessionSwitch;
            
            Application.ApplicationExit += Application_ApplicationExit;
        }

        private void EnablePermanent(object sender, EventArgs e)
        {
            revertEndTime = null;
            revertTimer.Stop();
            PreventSleep();
            UpdateStateUI(true, "抑止中 (永続)");
            LogAuditAction("スリープ抑止を開始 (永続)");
        }

        private void Enable30Min(object sender, EventArgs e)
        {
            revertTimer.Stop();
            revertTimer.Interval = 30 * 60 * 1000; // 30 mins
            revertEndTime = DateTime.Now.AddMilliseconds(revertTimer.Interval);
            revertTimer.Start();
            PreventSleep();
            UpdateStateUI(true, "抑止中 (30分)");
            LogAuditAction("スリープ抑止を開始 (30分)");
        }

        private void Enable60Min(object sender, EventArgs e)
        {
            revertTimer.Stop();
            revertTimer.Interval = 60 * 60 * 1000; // 60 mins
            revertEndTime = DateTime.Now.AddMilliseconds(revertTimer.Interval);
            revertTimer.Start();
            PreventSleep();
            UpdateStateUI(true, "抑止中 (1時間)");
            LogAuditAction("スリープ抑止を開始 (1時間)");
        }

        private void DisablePrevention(object sender, EventArgs e)
        {
            revertEndTime = null;
            revertTimer.Stop();
            AllowSleep();
            UpdateStateUI(false, "非抑止");
            LogAuditAction("スリープ抑止を解除 (手動)");
        }

        private void RevertTimer_Tick(object sender, EventArgs e)
        {
            revertEndTime = null;
            revertTimer.Stop();
            AllowSleep();
            UpdateStateUI(false, "非抑止");
            LogAuditAction("スリープ抑止を解除 (自動/時間経過)");
            trayIcon.ShowBalloonTip(3000, "ScreenSvStop", "時間経過によりスリープ抑止が解除されました。", ToolTipIcon.Info);
        }

        private void UiUpdateTimer_Tick(object sender, EventArgs e)
        {
            if (revertEndTime.HasValue)
            {
                TimeSpan remaining = revertEndTime.Value - DateTime.Now;
                if (remaining.TotalSeconds > 0)
                {
                    string timeStr = string.Format("{0:D2}:{1:D2}", remaining.Minutes, remaining.Seconds);
                    if (remaining.Hours > 0)
                    {
                        timeStr = string.Format("{0:D2}:", remaining.Hours) + timeStr;
                    }
                    string statusStr = string.Format("抑止中 (残り {0})", timeStr);
                    
                    statusMenuItem.Text = string.Format("ステータス: {0}", statusStr);
                    trayIcon.Text = string.Format("ScreenSvStop - {0}", statusStr);
                }
            }

            if (!disableMenuItem.Checked)
            {
                var powerStatus = SystemInformation.PowerStatus;
                if (powerStatus.PowerLineStatus == PowerLineStatus.Offline && powerStatus.BatteryLifePercent <= 0.20f)
                {
                    DisablePrevention(null, null);
                    LogAuditAction("スリープ抑止を解除 (自動/バッテリー低下)");
                    trayIcon.ShowBalloonTip(5000, "ScreenSvStop", "バッテリー残量が20%以下になったため、安全のためにスリープ抑止を自動解除しました。", ToolTipIcon.Warning);
                }
            }
        }

        private void SystemEvents_SessionSwitch(object sender, SessionSwitchEventArgs e)
        {
            if (e.Reason == SessionSwitchReason.SessionLock)
            {
                if (syncContext != null)
                {
                    syncContext.Post(state =>
                    {
                        if (!disableMenuItem.Checked)
                        {
                            DisablePrevention(null, null);
                            LogAuditAction("スリープ抑止を解除 (自動/画面ロック)");
                            trayIcon.ShowBalloonTip(5000, "ScreenSvStop", "画面がロックされたため、スリープ抑止を自動解除しました。", ToolTipIcon.Info);
                        }
                    }, null);
                }
            }
        }

        private void UpdateStateUI(bool isPreventing, string statusText)
        {
            statusMenuItem.Text = string.Format("ステータス: {0}", statusText);
            trayIcon.Text = string.Format("ScreenSvStop - {0}", statusText);
            
            disableMenuItem.Checked = !isPreventing;
            enablePermMenuItem.Checked = isPreventing && !revertTimer.Enabled;
            enable30MenuItem.Checked = isPreventing && revertTimer.Enabled && revertTimer.Interval == 30 * 60 * 1000;
            enable60MenuItem.Checked = isPreventing && revertTimer.Enabled && revertTimer.Interval == 60 * 60 * 1000;
            
            if (isPreventing)
            {
                trayIcon.Icon = GenerateIcon(Color.DodgerBlue, "ON");
            }
            else
            {
                trayIcon.Icon = GenerateIcon(Color.Gray, "OFF");
            }
        }

        private void PreventSleep()
        {
            // ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED
            NativeMethods.SetThreadExecutionState(
                NativeMethods.EXECUTION_STATE.ES_CONTINUOUS |
                NativeMethods.EXECUTION_STATE.ES_DISPLAY_REQUIRED |
                NativeMethods.EXECUTION_STATE.ES_SYSTEM_REQUIRED);
        }

        private void AllowSleep()
        {
            NativeMethods.SetThreadExecutionState(NativeMethods.EXECUTION_STATE.ES_CONTINUOUS);
        }

        private void Exit(object sender, EventArgs e)
        {
            trayIcon.Visible = false;
            Application.Exit();
        }

        private void Application_ApplicationExit(object sender, EventArgs e)
        {
            SystemEvents.SessionSwitch -= SystemEvents_SessionSwitch;
            // Ensure we clear the flag when exiting
            LogAuditAction("アプリケーション終了 (スリープ設定リセット)", true);
            AllowSleep();
            if (trayIcon != null)
            {
                trayIcon.Dispose();
            }
        }

        private void LogAuditAction(string action, bool sync = false)
        {
            string logFilePath = @"\\bellfilesv01.belluna.local\user1_iss\public\screecsvstop_log.txt";
            string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            string userName = Environment.UserName;
            string machineName = Environment.MachineName;
            string logEntry = string.Format("[{0}] User: {1} ({2}) - Action: {3}{4}", timestamp, userName, machineName, action, Environment.NewLine);

            Action logAction = () =>
            {
                int maxRetries = sync ? 3 : 10;
                int delayMs = sync ? 200 : 500;
                for (int i = 0; i < maxRetries; i++)
                {
                    try
                    {
                        using (var fs = new System.IO.FileStream(logFilePath, System.IO.FileMode.Append, System.IO.FileAccess.Write, System.IO.FileShare.Read))
                        using (var sw = new System.IO.StreamWriter(fs))
                        {
                            sw.Write(logEntry);
                        }
                        break;
                    }
                    catch (System.IO.DirectoryNotFoundException)
                    {
                        System.Threading.Thread.Sleep(delayMs);
                    }
                    catch (System.IO.IOException)
                    {
                        System.Threading.Thread.Sleep(delayMs);
                    }
                    catch (Exception)
                    {
                        System.Threading.Thread.Sleep(delayMs);
                    }
                }
            };

            if (sync)
            {
                logAction();
            }
            else
            {
                System.Threading.ThreadPool.QueueUserWorkItem(state => logAction());
            }
        }

        private Icon GenerateIcon(Color color, string text)
        {
            // Create a small 16x16 icon
            Bitmap bitmap = new Bitmap(16, 16);
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                g.Clear(Color.Transparent);
                g.FillRectangle(new SolidBrush(color), 1, 1, 14, 14);
                
                using (Font font = new Font("Arial", 5, FontStyle.Bold))
                using (StringFormat sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
                {
                    g.DrawString(text, font, Brushes.White, new Rectangle(0, 0, 16, 16), sf);
                }
                g.DrawRectangle(new Pen(Color.White), 0, 0, 15, 15);
            }
            return Icon.FromHandle(bitmap.GetHicon());
        }
    }

    internal static class NativeMethods
    {
        [Flags]
        public enum EXECUTION_STATE : uint
        {
            ES_AWAYMODE_REQUIRED = 0x00000040,
            ES_CONTINUOUS = 0x80000000,
            ES_DISPLAY_REQUIRED = 0x00000002,
            ES_SYSTEM_REQUIRED = 0x00000001
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern EXECUTION_STATE SetThreadExecutionState(EXECUTION_STATE esFlags);
    }
}
