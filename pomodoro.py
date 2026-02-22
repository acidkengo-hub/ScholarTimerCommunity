import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import csv
import os
import re

# --- 設定 ---
WORK_MINUTES = 25
BREAK_MINUTES = 5
CYCLE_MINUTES = WORK_MINUTES + BREAK_MINUTES
TARGET_POMODORO_LIMIT = 4
DATA_FILE = "study_log.csv"

class PomodoroTrainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Task Manager")
        self.root.geometry("500x720") # 少し高さを調整
        self.root.attributes('-topmost', True)
        
        self.is_joined = False
        self.last_update_time = datetime.now()
        self.current_mode = ""
        self.today_total_seconds = 0
        
        self.tasks = {} 
        self.current_task_name = None 
        self.task_limit_seconds = TARGET_POMODORO_LIMIT * WORK_MINUTES * 60
        self.notified_tasks = [] 

        self.load_today_data()

        # --- UI構築 ---
        self.timer_frame = tk.Frame(root)
        self.timer_frame.pack(pady=10)
        
        self.status_label = tk.Label(self.timer_frame, text="準備完了", font=("Helvetica", 16, "bold"))
        self.status_label.pack()

        self.timer_label = tk.Label(self.timer_frame, text="00:00", font=("Menlo", 45))
        self.timer_label.pack()

        self.current_task_label = tk.Label(root, text="【タスク未選択】", font=("Helvetica", 12, "bold"), fg="blue")
        self.current_task_label.pack(pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        self.join_button = tk.Button(self.button_frame, text="参加(Start)", command=self.join_train, bg="#d1e7dd")
        self.join_button.pack(side=tk.LEFT, padx=5)

        self.leave_button = tk.Button(self.button_frame, text="離脱(Stop)", command=self.leave_train, state=tk.DISABLED)
        self.leave_button.pack(side=tk.LEFT, padx=5)
        
        self.finish_button = tk.Button(self.button_frame, text="日報保存", command=self.finish_day, bg="#f8d7da")
        self.finish_button.pack(side=tk.LEFT, padx=5)

        # --- リストエリア ---
        self.lists_frame = tk.Frame(root)
        self.lists_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左：To-Doリスト
        self.left_frame = tk.Frame(self.lists_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.list_header = tk.Frame(self.left_frame)
        self.list_header.pack(fill=tk.X)
        tk.Label(self.list_header, text="▼ To-Do", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        # リストクリアボタン
        tk.Button(self.list_header, text="クリア", command=self.clear_list, font=("Helvetica", 8)).pack(side=tk.RIGHT)

        self.task_listbox = tk.Listbox(self.left_frame, height=12, selectmode=tk.SINGLE, font=("Helvetica", 11))
        self.task_listbox.pack(fill=tk.BOTH, expand=True)
        self.task_listbox.bind('<<ListboxSelect>>', self.on_task_select)

        # 右：Doneリスト
        self.right_frame = tk.Frame(self.lists_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(self.right_frame, text="★ Done", font=("Helvetica", 10, "bold"), fg="green").pack()
        self.done_listbox = tk.Listbox(self.right_frame, height=12, font=("Helvetica", 11), fg="gray")
        self.done_listbox.pack(fill=tk.BOTH, expand=True)


        # --- タスク追加エリア（ボタンを上に移動！） ---
        
        # ヘッダーフレーム（ラベルとボタンを横並びにする）
        self.input_header = tk.Frame(root)
        self.input_header.pack(fill=tk.X, padx=10, pady=(15, 2)) # 上に少し余白

        # ラベル（左寄せ）
        tk.Label(self.input_header, text="▼ タスク追加 (手動 / Workflowy貼り付け)", font=("Helvetica", 9)).pack(side=tk.LEFT)

        # 追加ボタン（右寄せ・ここに移動しました！）
        self.add_paste_btn = tk.Button(self.input_header, text="↓ リストに追加", command=self.add_tasks, bg="#e2e6ea")
        self.add_paste_btn.pack(side=tk.RIGHT)

        # 入力欄（下に配置・横幅いっぱい）
        self.input_text = scrolledtext.ScrolledText(root, height=5, font=("Helvetica", 10))
        self.input_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.update_timer()

    # --- タスク追加ロジック ---
    def add_tasks(self):
        text = self.input_text.get("1.0", tk.END)
        lines = text.splitlines()
        
        count = 0
        for line in lines:
            line = line.strip()
            if not line: continue 
            
            # 行頭の記号を消す
            clean_name = re.sub(r"^[-・*•−－\d\.\s]+", "", line)
            
            if not clean_name:
                clean_name = line
            
            self.tasks[clean_name] = self.tasks.get(clean_name, 0)
            self.task_listbox.insert(tk.END, clean_name)
            count += 1
            
        if count > 0:
            self.input_text.delete("1.0", tk.END) 
            if count > 1:
                messagebox.showinfo("完了", f"{count}件 追加しました！")
        else:
            messagebox.showwarning("あれ？", "追加する文字がありませんでした")

    def clear_list(self):
        if messagebox.askyesno("確認", "To-Doリストを空にしますか？"):
            self.task_listbox.delete(0, tk.END)

    # ----------------------------------------

    def send_notification(self, title, message):
        os.system(f"osascript -e 'display notification \"{message}\" with title \"{title}\"'")
        os.system("afplay /System/Library/Sounds/Glass.aiff")

    def get_cycle_status(self):
        now = datetime.now()
        minutes_in_cycle = (now.minute % CYCLE_MINUTES)
        seconds_in_cycle = minutes_in_cycle * 60 + now.second
        work_seconds = WORK_MINUTES * 60
        
        if seconds_in_cycle < work_seconds:
            return "WORK", work_seconds - seconds_in_cycle
        else:
            return "BREAK", (CYCLE_MINUTES * 60) - seconds_in_cycle

    def update_timer(self):
        now = datetime.now()
        mode, remaining = self.get_cycle_status()
        
        minutes = remaining // 60
        seconds = remaining % 60
        self.timer_label.config(text=f"{minutes:02}:{seconds:02}")

        if mode != self.current_mode:
            if self.current_mode == "WORK" and mode == "BREAK" and self.is_joined and self.current_task_name:
                done_time = now.strftime("%H:%M")
                log_text = f"{done_time} - {self.current_task_name}"
                self.done_listbox.insert(0, log_text)
                self.done_listbox.itemconfig(0, {'fg': 'green'})
                self.send_notification("お疲れ様！", f"「{self.current_task_name}」1ポモドーロ完了！")

            if mode == "WORK":
                self.status_label.config(text="🔥 集中タイム", fg="#d9534f")
                self.root.configure(bg="#fff5f5")
                if self.current_mode != "": self.send_notification("集中開始", "タスクを進めましょう！")
            else:
                self.status_label.config(text="☕ 休憩タイム", fg="#5bc0de")
                self.root.configure(bg="#f0f8ff")
                if self.current_mode != "": self.send_notification("休憩", "脳を休めましょう。")
            self.current_mode = mode

        if self.is_joined and mode == "WORK":
            delta = (now - self.last_update_time).total_seconds()
            self.today_total_seconds += delta
            
            if self.current_task_name:
                if self.current_task_name not in self.tasks:
                    self.tasks[self.current_task_name] = 0.0
                self.tasks[self.current_task_name] += delta
                
                current_task_time = self.tasks[self.current_task_name]
                if current_task_time >= self.task_limit_seconds and self.current_task_name not in self.notified_tasks:
                    self.send_notification("⚠️ 強制終了！", f"「{self.current_task_name}」が4ポモドーロに達しました！")
                    self.notified_tasks.append(self.current_task_name)

            self.join_button.config(state=tk.DISABLED)
            self.leave_button.config(state=tk.NORMAL)
            self.update_listbox_display()
            
        elif not self.is_joined:
            self.join_button.config(state=tk.NORMAL)
            self.leave_button.config(state=tk.DISABLED)

        self.last_update_time = now
        self.root.after(1000, self.update_timer)

    def on_task_select(self, event):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            display_text = self.task_listbox.get(index)
            task_name = display_text.split(" (")[0]
            self.current_task_name = task_name
            self.current_task_label.config(text=f"選択中: {task_name}", fg="red")

    def update_listbox_display(self):
        if self.current_task_name:
            seconds = self.tasks.get(self.current_task_name, 0)
            pomo_count = int(seconds // (WORK_MINUTES * 60))
            
            status_text = f"選択中: {self.current_task_name} \n 🍅 {pomo_count}/{TARGET_POMODORO_LIMIT} セット経過"
            if pomo_count >= TARGET_POMODORO_LIMIT:
                status_text += " (終了！)"
                self.current_task_label.config(text=status_text, fg="red")
            else:
                self.current_task_label.config(text=status_text, fg="blue")

    def join_train(self):
        if not self.current_task_name:
            messagebox.showwarning("注意", "リストからタスクを選択してください！")
            return
        self.is_joined = True
        self.last_update_time = datetime.now()

    def leave_train(self):
        self.is_joined = False
    
    def finish_day(self):
        self.save_data()
        self.root.destroy()
        
    def load_today_data(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(DATA_FILE): return
        with open(DATA_FILE, "r") as f:
            for row in csv.reader(f):
                if row and row[0] == today_str:
                    try: self.today_total_seconds = float(row[1])
                    except: pass

    def save_data(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        new_rows = []
        found = False
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f: new_rows = list(csv.reader(f))
        
        data_row = [today_str, str(self.today_total_seconds), "{:.1f}時間".format(self.today_total_seconds/3600)]
        for i, row in enumerate(new_rows):
            if row and row[0] == today_str:
                new_rows[i] = data_row
                found = True
                break
        if not found: new_rows.append(data_row)

        with open(DATA_FILE, "w", newline="") as f:
            csv.writer(f).writerows(new_rows)

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTrainApp(root)
    root.mainloop()