import pandas as pd
import tkinter as tk
from PIL import ImageGrab
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, filedialog, messagebox

class Dashboard:

    def __init__(self, root):

        self.root = root
        self.root.title("Dashboard de Sensores")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg = "#FFFFFF")

        self.game_statistics = None
        self.data_right = None

        tk.Label(root,
                 text = "DASHBOARD",
                 font = ("Arial", 20, "bold"),
                 bg = "#333", fg = "#FFF").pack(fill = tk.X,
                                                padx = 10,
                                                pady = 10)

        self.button_frame = tk.Frame(root, bg = "#FFFFFF")
        self.button_frame.pack(pady = 10)

        self.game_statistics_button = tk.Button(self.button_frame,
                                                text = "Estatísticas do Jogo",
                                                command = self.upload_game_statistics,
                                                font = ("Arial", 12),
                                                bg = "#D3D3D3",
                                                fg = "black")
        self.game_statistics_button.pack(side = tk.LEFT, padx = 10)

        self.load_button = tk.Button(self.button_frame,
                                     text = "Sensores",
                                     command = self.load_right_csv,
                                     font = ("Arial", 12),
                                     bg = "#D3D3D3",
                                     fg = "black")
        self.load_button.pack(side = tk.LEFT, padx = 10)

        self.save_button = tk.Button(self.button_frame,
                                     text = "Salvar Dashboard",
                                     command = self.save_dashboard_as_pdf,
                                     font = ("Arial", 12),
                                     bg = "#D3D3D3",
                                     fg = "black")
        self.save_button.pack(side = tk.LEFT, padx = 10)
        self.save_button.config(state = tk.DISABLED)

        self.table_button = tk.Button(self.button_frame,
                                      text = "Ver Tabela",
                                      command = self.show_table_window,
                                      font = ("Arial", 12),
                                      bg = "#D3D3D3",
                                      fg = "black")
        self.table_button.pack(side = tk.LEFT, padx = 10)

        self.kpi_frame = tk.Frame(root, bg = "#FFFFFF")
        self.kpi_frame.pack(fill = tk.X, padx = 10, pady = 5)

        self.data_selection = tk.StringVar(value = "EMG")
        self.data_selection_menu = ttk.Combobox(root,
                                                textvariable = self.data_selection,
                                                values = ["EMG", "FSR1", "FSR2"],
                                                state = "readonly",
                                                width = 10)
        self.data_selection_menu.pack(pady = 5)
        self.data_selection_menu.bind("<<ComboboxSelected>>", self.update_kpis)

        self.create_kpi("Máx.", "N/A", "#33A1FD")
        self.create_kpi("Min.", "N/A", "#FF6F61")
        self.create_kpi("Média", "N/A", "#4CAF50")
        self.create_kpi("Desvio Padrão", "N/A", "#FFD700")

        self.graph_frame = tk.Frame(root, bg = "#FFFFFF")
        self.graph_frame.pack(fill = tk.BOTH,
                              expand = True,
                              padx = 10,
                              pady = 5)

        self.figures = []

        self.exit_button = tk.Button(root,
                                     text = "Sair",
                                     command = self.exit_application,
                                     font = ("Arial", 12),
                                     bg = "#FF5733",
                                     fg = "white")
        self.exit_button.pack(side = tk.BOTTOM, pady = 10)

    def create_kpi(self, title, value, color):

        kpi = tk.Frame(self.kpi_frame,
                       bg = color,
                       width = 280,
                       height = 80)
        kpi.pack(side = tk.LEFT,
                 padx = 5,
                 pady = 5,
                 fill = tk.BOTH,
                 expand = True)

        tk.Label(kpi,
                 text = title,
                 font = ("Arial", 14, "bold"),
                 bg = color,
                 fg = "#FFF").pack(pady = (5, 2))

        self.kpi_label = tk.Label(kpi,
                                  tex = value,
                                  font = ("Arial", 18, "bold"),
                                  bg = "#D3D3D3",
                                  fg = "#333")
        self.kpi_label.pack(fill = tk.BOTH, expand = True)

    def upload_game_statistics(self):

        file_path = filedialog.askopenfilename(filetypes = [("Arquivos CSV", "*.csv")])

        if not file_path:

            return

        try:

            self.game_statistics = pd.read_csv(file_path, encoding = "ISO-8859-1")
            
        except Exception as e:

            messagebox.showerror("Erro ao carregar arquivo", f"Ocorreu um erro ao processar o arquivo:\n{e}")

    def load_right_csv(self):

        file_path = filedialog.askopenfilename(filetypes = [("Arquivos CSV", "*.csv")])

        if not file_path:

            return

        try:

            self.data_right = pd.read_csv(file_path, encoding = "ISO-8859-1")

            self.update_kpis()
            self.create_graphs()

            self.save_button.config(state = tk.NORMAL)

        except Exception as e:

            messagebox.showerror("Erro ao carregar arquivo", f"Ocorreu um erro ao processar o arquivo:\n{e}")

    def update_kpis(self, event = None):

        selected_data = self.data_selection.get()
        
        if selected_data == "EMG":

            data_column = self.data_right.iloc[:, 1]

        elif selected_data == "FSR1":

            data_column = self.data_right.iloc[:, 2]

        else:

            data_column = self.data_right.iloc[:, 3]

        data_max = data_column.max()
        data_min = data_column.min()
        data_mean = data_column.mean()
        data_std = data_column.std()

        kpi_values = [f"{data_max:.2f}",
                      f"{data_min:.2f}",
                      f"{data_mean:.2f}",
                      f"{data_std:.2f}"]

        for widget, value in zip(self.kpi_frame.winfo_children(), kpi_values):

            widget.winfo_children()[1].config(text = value)

    def create_graphs(self):

        for widget in self.graph_frame.winfo_children():

            widget.destroy()

        self.figures = []

        self.graph_frame.columnconfigure(0, weight = 1)
        self.graph_frame.columnconfigure(1, weight = 1)
        self.graph_frame.rowconfigure(0, weight = 2)
        self.graph_frame.rowconfigure(1, weight = 1)

        fig1 = Figure(figsize = (5, 2.5), dpi = 100)
        ax1 = fig1.add_subplot(111)
        ax1.plot(self.data_right.iloc[:, 0], self.data_right.iloc[:, 2], label = "Força 1")
        ax1.set_title("Força no Antebraço ao Longo do Tempo")
        ax1.set_ylabel("N")
        ax1.set_xlabel("Tempo")
        ax1.legend(loc = 'lower right')
        ax1.grid(True, linestyle = '--', alpha = 0.7)
        fig1.tight_layout()
        self.figures.append(fig1)

        canvas1 = FigureCanvasTkAgg(fig1, master = self.graph_frame)
        canvas1.get_tk_widget().grid(row = 0,
                                     column = 0,
                                     padx = 10,
                                     pady = 10)

        fig2 = Figure(figsize = (5, 2.5), dpi = 100)
        ax2 = fig2.add_subplot(111)
        ax2.plot(self.data_right.iloc[:, 0],
                 self.data_right.iloc[:, 1],
                 label = "EMG",
                 color = "#FF6F61")
        ax2.set_title("Atividade EMG ao Longo do Tempo")
        ax2.set_ylabel("mV")
        ax2.set_xlabel("Tempo")
        ax2.legend(loc = 'lower right')
        ax2.grid(True, linestyle = '--', alpha = 0.7)
        fig2.tight_layout()
        self.figures.append(fig2)

        canvas2 = FigureCanvasTkAgg(fig2, master = self.graph_frame)
        canvas2.get_tk_widget().grid(row = 0,
                                     column = 1,
                                     padx = 10,
                                     pady = 10)

        fig3 = Figure(figsize = (5, 2.5), dpi = 100)
        ax3 = fig3.add_subplot(111)
        ax3.plot(self.data_right.iloc[:, 0],
                 self.data_right.iloc[:, 3],
                 label = "Força 2",
                 color = "#4CAF50")
        ax3.set_title("Força no Dedo ao Longo do Tempo")
        ax3.set_ylabel("N")
        ax3.set_xlabel("Tempo")
        ax3.legend(loc = 'lower right')
        ax3.grid(True, linestyle = '--', alpha = 0.7)
        fig3.tight_layout()
        self.figures.append(fig3)

        canvas3 = FigureCanvasTkAgg(fig3, master = self.graph_frame)
        canvas3.get_tk_widget().grid(row = 1,
                                     column = 0,
                                     padx = 10,
                                     pady = 10)

        if self.game_statistics.shape[1] == 3:

            tempos = self.game_statistics.iloc[:, 1]
            max_tempo = tempos.max()
            intervalos_tempo = list(range(0, int(max_tempo) + 2, 2))

        elif self.game_statistics.shape[1] == 4:

            tempos = self.game_statistics.iloc[:, 1]
            max_tempo = tempos.max()
            intervalos_tempo = list(range(0, int(max_tempo) + 1))

        else:

            raise ValueError("O DataFrame 'game_statistics' deve ter 3 ou 4 colunas.")

        grupo_tempo = pd.cut(tempos, bins = intervalos_tempo, right = False)
        media_precisao_por_intervalo = self.game_statistics.groupby(grupo_tempo).mean().iloc[:, -1]

        fig4 = Figure(figsize = (5, 2.5), dpi = 100)
        ax4 = fig4.add_subplot(111)

        largura_barra = 0.8

        ax4.bar(media_precisao_por_intervalo.index.astype(str),
                media_precisao_por_intervalo,
                color = "blue", 
                label = "Média de Precisão por Intervalo de Tempo",
                width = largura_barra)
        ax4.set_title("Precisão Média por Intervalo de Tempo")
        ax4.set_xlabel("Intervalos de Tempo (s)")
        ax4.set_ylabel("Precisão Média")
        ax4.legend(loc = 'lower right')
        ax4.grid(True, linestyle = "--", alpha = 0.7)
        fig4.tight_layout()

        self.figures.append(fig4)
        canvas4 = FigureCanvasTkAgg(fig4, master = self.graph_frame)
        canvas4.get_tk_widget().grid(row = 1,
                                     column = 1,
                                     padx = 10,
                                     pady = 10)

    def show_table_window(self):

        if self.game_statistics is None:

            messagebox.showwarning("Aviso", "Carregue um arquivo CSV no botão esquerdo antes de abrir a tabela.")

            return

        table_window = tk.Toplevel(self.root)
        table_window.title("Tabela de Dados")
        table_window.geometry("600x400")

        table = ttk.Treeview(table_window, columns = list(self.game_statistics.columns), show = "headings")
        table.pack(fill = tk.BOTH, expand = True)

        for col in self.game_statistics.columns:

            table.heading(col, text = col)
            table.column(col, width = 100)

        for _, row in self.game_statistics.iterrows():

            table.insert("", tk.END, values=list(row))

    def save_dashboard_as_pdf(self):

        file_path = filedialog.asksaveasfilename(defaultextension = ".pdf", filetypes = [("Arquivos PDF", "*.pdf")])

        if not file_path:

            return

        try:

            screen = ImageGrab.grab(bbox = None)
            screen.save(file_path, "PDF")

            messagebox.showinfo("Sucesso", "Dashboard salvo com sucesso!")

        except Exception as e:

            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo:\n{e}")

    def exit_application(self):

        self.root.quit()

if __name__ == "__main__":

    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()