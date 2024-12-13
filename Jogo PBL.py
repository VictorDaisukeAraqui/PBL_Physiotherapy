import pygame
import os
import csv
import math
import time
import random
import serial
import threading
import statistics
import numpy as np
from scipy.signal import butter, filtfilt

class Config:

    SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
    COLORS = {"WHITE": (255, 255, 255),
              "BLACK": (0, 0, 0),
              "RED": (255, 0, 0),
              "GREEN": (0, 255, 0),
              "BLUE": (0, 0, 255)}
    FPS = 60

class Utils:

    @staticmethod
    def calculate_distance(point1, point2):

        return math.hypot(point1[0] - point2[0], point1[1] - point2[1])

    @staticmethod
    def calculate_precision(distance, max_radius):

        return max(0, 100 * (1 - (distance / max_radius))) if distance > 0 else 100.0

    @staticmethod
    def draw_text(screen, text, position, font, color):

        text_surface = font.render(text, True, color)
        screen.blit(text_surface, position)

class DataCollector:

    def __init__(self, port = "COM5", baud_rate = 9600, output_folder = "Results"):

        self.port = port
        self.baud_rate = baud_rate
        self.emg_data = []
        self.fsr1_data = []
        self.fsr2_data = []
        self.time_stamps = []
        self.ser = None
        self.collecting = False
        self.output_folder = output_folder
        self.create_output_folder()

    def create_output_folder(self):

        if not os.path.exists(self.output_folder):

            os.makedirs(self.output_folder)

    def start_collection(self):

        if self.ser is None or not self.ser.is_open:

            try:

                self.ser = serial.Serial(self.port, self.baud_rate, timeout = 1)

                time.sleep(1)

                self.collecting = True

                threading.Thread(target = self.read_data, daemon = True).start()

                print("Coleta de dados iniciada.")

            except serial.SerialException as e:

                print(f"Erro ao conectar ao dispositivo serial: {e}")

    def stop_collection(self):

        self.collecting = False

        if self.ser and self.ser.is_open:

            self.ser.close()

            print("Conexão serial encerrada.")

    def read_data(self):

        try:

            while self.collecting:

                if self.ser.in_waiting > 0:

                    line = self.ser.readline().decode("utf-8").strip()

                    try:

                        emg_str, fsr1_str, fsr2_str = line.split(",")

                        emg_value = float(emg_str)
                        fsr1_value = float(fsr1_str)
                        fsr2_value = float(fsr2_str)
                        self.emg_data.append(emg_value)
                        self.fsr1_data.append(fsr1_value)
                        self.fsr2_data.append(fsr2_value)
                        self.time_stamps.append(time.time())

                    except ValueError:

                        continue

                time.sleep(0.1)

        except serial.SerialException:

            print("Erro na comunicação com o dispositivo serial.")

    def apply_bandpass_filter(self, data, lowcut = 20, highcut = 500, fs = 1000, order = 4):

        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype = 'band')

        return filtfilt(b, a, data)

    def apply_moving_average(self, data, window_size = 5):

        return np.convolve(data, np.ones(window_size) / window_size, mode = 'same')

    def process_data(self):

        if self.emg_data:

            self.emg_data = self.apply_bandpass_filter(self.emg_data)

        if self.fsr2_data:

            self.fsr2_data = self.apply_moving_average(self.fsr2_data)

    def save_sensor_data_to_csv(self, filename = "sensor_data.csv"):

        if not self.time_stamps:

            return

        csv_path = os.path.join(self.output_folder, filename)

        with open(csv_path, mode = "w", newline = "", encoding = "utf-8") as file:

            writer = csv.writer(file)
            writer.writerow(["Tempo (s)", "Eletromiografia (μV)", "Força no Antebraço (N)", "Força no Dedo (N)"])
            relative_time = [t - self.time_stamps[0] for t in self.time_stamps]

            for t, emg, fsr1, fsr2 in zip(relative_time, self.emg_data, self.fsr1_data, self.fsr2_data):

                writer.writerow([f"{t:.2f}", f"{emg:.2f}", f"{fsr1:.2f}", f"{fsr2:.2f}"])

class PhaseOne:

    def __init__(self, output_folder = "Results"):

        super().__init__()

        self.clicks = 0
        self.points = 0
        self.clicks_to_hit = 0
        self.max_time = 10
        self.phase_goal = 100
        self.start_time = time.time()
        self.target = self.create_target()
        self.last_target_time = time.time()
        self.target_creation_time = time.time()
        self.target_data = []
        self.output_folder = output_folder

    def display_dashboard(self, screen, font):

        elapsed_time = time.time() - self.start_time

        Utils.draw_text(screen, f"Tempo: {int(elapsed_time)} segundos", (10, 10), font, Config.COLORS["BLACK"])
        Utils.draw_text(screen, f"Cliques: {self.clicks}", (10, 50), font, Config.COLORS["BLACK"])
        Utils.draw_text(screen, f"Pontos: {self.points} / {self.phase_goal}", (10, 90), font, Config.COLORS["BLACK"])

    def calculate_statistics(self):

        if not self.target_data:

            return {k: 0 for k in ("time_mean", "time_stdev", "clicks_mean", "clicks_stdev", "precision_mean", "precision_stdev")}

        times = [d["time"] for d in self.target_data]
        clicks = [d["clicks"] for d in self.target_data]
        precisions = [d["precision"] for d in self.target_data]

        return {"time_mean": statistics.mean(times),
                "time_stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "clicks_mean": statistics.mean(clicks),
                "clicks_stdev": statistics.stdev(clicks) if len(clicks) > 1 else 0,
                "precision_mean": statistics.mean(precisions),
                "precision_stdev": statistics.stdev(precisions) if len(precisions) > 1 else 0}

    def create_target(self):

        return (random.randint(50, Config.SCREEN_WIDTH - 110),
                random.randint(50, Config.SCREEN_HEIGHT - 110),
                random.randint(10, 110))

    def update_target(self):

        self.clicks_to_hit = 0
        self.target = self.create_target()
        self.last_target_time = time.time()
        self.target_creation_time = time.time()

    def check_target_timeout(self):

        if time.time() - self.last_target_time > self.max_time:

            self.target = self.create_target()
            self.last_target_time = time.time()

    def handle_click(self, mouse_pos):

        self.clicks += 1
        self.clicks_to_hit += 1

        distance = Utils.calculate_distance(mouse_pos, (self.target[0], self.target[1]))

        if distance <= self.target[2]:

            self.points += self.calculate_score(distance)

            time_to_hit = time.time() - self.last_target_time
            precision = Utils.calculate_precision(distance, self.target[2])
            self.target_data.append({"time": time_to_hit,
                                     "clicks": self.clicks_to_hit,
                                     "precision": precision})

            self.update_target()

    def calculate_score(self, distance):

        if self.target[2] <= 30:

            section_scores = [9, 10, 11, 12, 13]

        elif self.target[2] <= 50:

            section_scores = [7, 8, 9, 10, 11]

        elif self.target[2] <= 70:

            section_scores = [5, 6, 7, 8, 9]

        elif self.target[2] <= 90:

            section_scores = [3, 4, 5, 6, 7]

        else:

            section_scores = [1, 2, 3, 4, 5]

        if distance <= self.target[2] * (1 / 5):

            return section_scores[4]

        elif distance <= self.target[2] * (2 / 5):

            return section_scores[3]

        elif distance <= self.target[2] * (3 / 5):

            return section_scores[2]

        elif distance <= self.target[2] * (4 / 5):

            return section_scores[1]

        else:

            return section_scores[0]

    def save_statistics_to_csv(self, filename = "phase_one.csv"):

        if not self.target_data:

            return

        csv_path = os.path.join(self.output_folder, filename)

        with open(csv_path, mode = "w", newline = "") as file:

            writer = csv.writer(file)
            writer.writerow(["Interação", "Tempo (s)", "Cliques", "Precisão (%)"])

            for i, d in enumerate(self.target_data, start = 1):

                writer.writerow([i, f"{d['time']:.2f}", d["clicks"], f"{d['precision']:.2f}"])

class PhaseTwo: 

    def __init__(self, output_folder = "Results"):

        super().__init__()

        self.level = 0
        self.total_levels = 3
        self.checkpoints = self.generate_checkpoints()
        self.current_checkpoints = self.checkpoints.copy()
        self.checkpoint_status = [False] * len(self.checkpoints)
        self.user_line = []
        self.draw_data = []
        self.start_time = None
        self.user_active = False
        self.output_folder = output_folder

    def display_dashboard(self, screen, font):

        elapsed_time = 0 if self.start_time is None else time.time() - self.start_time

        Utils.draw_text(screen, f"Tempo: {int(elapsed_time)} segundos", (10, 10), font, Config.COLORS["BLACK"])
        Utils.draw_text(screen, f"Checkpoints: {self.checkpoint_status.count(True)} / {len(self.checkpoints)}", (10, 50), font, Config.COLORS["BLACK"])

    def calculate_statistics(self):

        if not self.draw_data:

            return {k: 0 for k in ("time_mean", "time_stdev", "precision_mean", "precision_stdev")}

        times = [d["time"] for d in self.draw_data]
        precisions = [d["precision"] for d in self.draw_data]

        return {"time_mean": statistics.mean(times),
                "time_stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "precision_mean": statistics.mean(precisions),
                "precision_stdev": statistics.stdev(precisions) if len(precisions) > 1 else 0}

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:

            self.user_active, self.user_line = True, [pygame.mouse.get_pos()]
            self.start_time = time.time()

        elif event.type == pygame.MOUSEMOTION and self.user_active:

            self.user_line.append(pygame.mouse.get_pos())

            for i, cp in enumerate(self.checkpoints):

                if i == 0 or self.checkpoint_status[i - 1]:

                    if (not self.checkpoint_status[i] and 
                        math.hypot(cp[0] - self.user_line[-1][0], cp[1] - self.user_line[-1][1]) <= 10):

                        self.checkpoint_status[i] = True

        elif event.type == pygame.MOUSEBUTTONUP and self.user_active:

            self.advance_level()

            self.user_line, self.start_time, self.user_active = [], None, False

    def advance_level(self):

        if all(self.checkpoint_status):

            self.level += 1
            self.current_checkpoints = self.checkpoints.copy()

            elapsed_time = time.time() - self.start_time
            accuracy = self.calculate_accuracy()
            self.draw_data.append({"time": elapsed_time,
                                   "precision": accuracy})

            if self.level == self.total_levels:

                return False

            self.checkpoints = self.generate_checkpoints()
            self.checkpoint_status = [False] * len(self.checkpoints)

        return True

    def generate_checkpoints(self, num_checkpoints = 5):

        return [(random.randint(100, Config.SCREEN_WIDTH - 100),
                 random.randint(100, Config.SCREEN_HEIGHT - 100)) for _ in range(num_checkpoints)]

    def draw_checkpoints_and_lines(self, screen, font):

        pygame.draw.lines(screen, Config.COLORS["BLACK"], False, self.checkpoints, 5)

        for i, (point, status) in enumerate(zip(self.checkpoints, self.checkpoint_status)):

            color = Config.COLORS["GREEN"] if status else Config.COLORS["RED"]
            pygame.draw.circle(screen, color, point, 10)
            checkpoint_text = font.render(str(i + 1), True, Config.COLORS["BLACK"])
            screen.blit(checkpoint_text, (point[0] - 10, point[1] - 10))

    def draw_user_line(self, screen):

        if len(self.user_line) > 1:

            pygame.draw.lines(screen, Config.COLORS["BLUE"], False, self.user_line, 3)

    def rasterize_line(self, start, end):

        pixels = []
        x1, y1 = start
        x2, y2 = end
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:

            pixels.append((x1, y1))

            if x1 == x2 and y1 == y2:

                break

            e2 = err * 2

            if e2 > -dy:

                err -= dy
                x1 += sx

            if e2 < dx:

                err += dx
                y1 += sy

        return pixels

    def calculate_accuracy(self, tolerance = 5):

        if not self.user_line or not self.current_checkpoints:

            return 0

        user_pixels = []

        for i in range(len(self.user_line) - 1):

            user_pixels.extend(self.rasterize_line(self.user_line[i], self.user_line[i + 1]))

        target_pixels = []

        for i in range(len(self.current_checkpoints) - 1):

            target_pixels.extend(self.rasterize_line(self.current_checkpoints[i], self.current_checkpoints[i + 1]))

        user_pixels_set = set(user_pixels)
        target_pixels_set = set(target_pixels)

        def is_within_tolerance(pixel1, pixel2, tolerance):

            return abs(pixel1[0] - pixel2[0]) <= tolerance and abs(pixel1[1] - pixel2[1]) <= tolerance

        intersection = set()

        for user_pixel in user_pixels_set:

            for target_pixel in target_pixels_set:

                if is_within_tolerance(user_pixel, target_pixel, tolerance):

                    intersection.add(user_pixel)

                    break

        if len(target_pixels_set) == 0:

            return 0

        return (len(intersection) / len(user_pixels_set)) * 100

    def save_statistics_to_csv(self, filename = "phase_two.csv"):

        if not self.draw_data:

            return

        csv_path = os.path.join(self.output_folder, filename)

        with open(csv_path, mode = "w", newline = "") as file:

            writer = csv.writer(file)
            writer.writerow(["Nível", "Tempo (s)", "Precisão (%)"])

            for i, d in enumerate(self.draw_data, start = 1):

                writer.writerow([i, f"{d['time']:.2f}", f"{d['precision']:.2f}"])

class Game:

    def __init__(self):

        pygame.init()
        pygame.display.set_caption("Jogo de Precisão")

        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))

        self.phase_one_complete = False
        self.data_collector_one = DataCollector()
        self.phase_two_complete = False
        self.data_collector_two = DataCollector()

    def display_message_while_collecting(self, message, collector_function):

        start_time = pygame.time.get_ticks()
        collector_function()

        while True:

            self.screen.fill(Config.COLORS["WHITE"])
            text = self.font.render(message, True, Config.COLORS["BLACK"])
            text_rect = text.get_rect(center = (Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)

            pygame.display.flip()

            current_time = pygame.time.get_ticks()

            if current_time - start_time > 1000:

                break

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()

    def final_display_message(self, message):

        self.screen.fill(Config.COLORS["WHITE"])
        text = self.font.render(message, True, Config.COLORS["BLACK"])
        text_rect = text.get_rect(center = (Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        pygame.display.flip()

        time.sleep(0.9)

    def run(self):

        self.display_message_while_collecting("Fase 1: Iniciando...", self.data_collector_one.start_collection)
        phase_one = PhaseOne()
        phase_one_running = True

        while phase_one_running:

            self.screen.fill(Config.COLORS["WHITE"])
            phase_one.display_dashboard(self.screen, self.font)

            pygame.draw.circle(self.screen, Config.COLORS["RED"], (phase_one.target[0], phase_one.target[1]), phase_one.target[2])
            pygame.draw.circle(self.screen, Config.COLORS["WHITE"], (phase_one.target[0], phase_one.target[1]), int(phase_one.target[2] * (4 / 5)))
            pygame.draw.circle(self.screen, Config.COLORS["RED"], (phase_one.target[0], phase_one.target[1]), int(phase_one.target[2] * (3 / 5)))
            pygame.draw.circle(self.screen, Config.COLORS["WHITE"], (phase_one.target[0], phase_one.target[1]), int(phase_one.target[2] * (2 / 5)))
            pygame.draw.circle(self.screen, Config.COLORS["BLACK"], (phase_one.target[0], phase_one.target[1]), int(phase_one.target[2] * (1 / 5)))

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    phase_one_running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:

                    phase_one.handle_click(pygame.mouse.get_pos())

            if phase_one.points >= phase_one.phase_goal:

                phase_one_running = False

            pygame.display.flip()
            self.clock.tick(Config.FPS)

        self.final_display_message("Fase 1: Concluída!")
        self.data_collector_one.stop_collection()
        self.phase_one_complete = True

        phase_one.save_statistics_to_csv("phase_one.csv")
        self.data_collector_one.save_sensor_data_to_csv("phase_one_sensor_data.csv")

        while not self.phase_one_complete:

            time.sleep(0.1)

        self.display_message_while_collecting("Fase 2: Iniciando...", self.data_collector_two.start_collection)
        phase_two = PhaseTwo()
        phase_two_running = True

        while phase_two_running:

            self.screen.fill(Config.COLORS["WHITE"])
            phase_two.display_dashboard(self.screen, self.font)
            phase_two.draw_checkpoints_and_lines(self.screen, self.font)
            phase_two.draw_user_line(self.screen)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    phase_two_running = False

                    return

                phase_two.handle_event(event)

            if not phase_two.advance_level():

                phase_two_running = False

            pygame.display.flip()
            self.clock.tick(Config.FPS)

        self.final_display_message("Fase 2: Concluída!")
        self.data_collector_two.stop_collection()
        self.phase_two_complete = True

        phase_two.save_statistics_to_csv("phase_two.csv")
        self.data_collector_two.save_sensor_data_to_csv("phase_two_sensor_data.csv")

        while not self.phase_two_complete:

            time.sleep(0.1)

        pygame.quit()

if __name__ == "__main__":

    Game().run()