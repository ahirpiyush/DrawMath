import tkinter as tk
from PIL import Image, ImageDraw
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt

class ProjectDrawApp:
    def __init__(self):
        # Default folders
        desktop = Path.home() / "Desktop"
        self.project_folder = desktop / "project1_drawings"
        os.makedirs(self.project_folder, exist_ok=True)

        self.points_folder = desktop / "project1_points"
        os.makedirs(self.points_folder, exist_ok=True)

        # Image counter
        self.image_counter = len(list(self.project_folder.glob("project1_image*.png"))) + 1

        # Canvas
        self.root = tk.Tk()
        self.root.title("Project1 Drawing")

        self.width, self.height = 500, 500
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()

        # PIL image to save drawing
        self.image = Image.new("L", (self.width, self.height), color=255)
        self.draw = ImageDraw.Draw(self.image)

        # Multi-stroke storage
        self.strokes = []         # list of strokes
        self.current_stroke = []  # points of current stroke

        self.last_x, self.last_y = None, None

        # Level selection
        self.level_label = tk.Label(self.root, text="Select Level for Points:")
        self.level_label.pack()

        self.level_var = tk.IntVar(value=1)
        levels_frame = tk.Frame(self.root)
        levels_frame.pack()

        tk.Radiobutton(levels_frame, text="Level 1 (100 pts)", variable=self.level_var, value=1).pack(side="left")
        tk.Radiobutton(levels_frame, text="Level 2 (300 pts)", variable=self.level_var, value=2).pack(side="left")
        tk.Radiobutton(levels_frame, text="Level 3 (600 pts)", variable=self.level_var, value=3).pack(side="left")

        # Buttons
        save_btn = tk.Button(self.root, text="Save & Generate Points", command=self.save_and_process)
        save_btn.pack(pady=5)
        exit_btn = tk.Button(self.root, text="Exit", command=self.exit_app)
        exit_btn.pack(pady=5)

        # Mouse bindings
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)

        self.root.mainloop()

    # Drawing function
    def paint(self, event):
        x, y = event.x, event.y
        radius = 3
        if self.last_x is not None and self.last_y is not None:
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=radius*2, fill="black", capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, x, y], fill=0, width=radius*2)
            self.current_stroke.append((x, y))
        else:
            self.current_stroke.append((x, y))
        self.last_x, self.last_y = x, y

    def end_stroke(self, event):
        if self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = []
        self.last_x, self.last_y = None, None

    # Save drawing, generate equally spaced points per stroke, visualize
    def save_and_process(self):
        if not self.strokes:
            print("No drawing detected.")
            return

        # Save drawing
        filename = self.project_folder / f"project1_image{self.image_counter}.png"
        self.image.save(filename)
        print(f"Saved drawing as {filename}")

        # Level points
        level_points = {1:100, 2:300, 3:600}
        total_points = level_points[self.level_var.get()]

        # Compute total stroke length
        stroke_lengths = []
        for stroke in self.strokes:
            stroke = np.array(stroke)
            deltas = np.diff(stroke, axis=0)
            lengths = np.sqrt((deltas**2).sum(axis=1))
            stroke_lengths.append(lengths.sum())
        total_length = sum(stroke_lengths)

        # Points per stroke proportional
        points_per_stroke = [max(1, int(total_points * (l/total_length))) for l in stroke_lengths]

        sampled_points = []

        # Sample points along each stroke
        for stroke, num_pts in zip(self.strokes, points_per_stroke):
            stroke = np.array(stroke)
            if len(stroke) < 2:
                continue
            deltas = np.diff(stroke, axis=0)
            dist = np.sqrt((deltas**2).sum(axis=1))
            cumulative = np.insert(np.cumsum(dist), 0, 0)
            even_distances = np.linspace(0, cumulative[-1], num_pts)
            interp_x = np.interp(even_distances, cumulative, stroke[:,0])
            interp_y = np.interp(even_distances, cumulative, stroke[:,1])
            sampled_points.extend(list(zip(interp_x, interp_y)))

        sampled_points = np.array(sampled_points)

        # Save points as text
        points_file = self.points_folder / f"project1_points{self.image_counter}.txt"
        with open(points_file, "w") as f:
            for pt in sampled_points:
                f.write(f"({pt[0]:.2f}, {pt[1]:.2f})\n")  # rounded to 2 decimals
        print(f"Saved points as {points_file}")

        # Visualize
        self.visualize_points(sampled_points)

        # Clear for next drawing
        self.strokes = []
        self.image_counter += 1
        self.canvas.delete("all")
        self.image = Image.new("L", (self.width, self.height), color=255)
        self.draw = ImageDraw.Draw(self.image)

    # Visualization
    def visualize_points(self, points):
        fig, axs = plt.subplots(1,2, figsize=(10,5))

        # Left: original drawing
        axs[0].imshow(np.array(self.image), cmap='gray', alpha=0.3,
                      origin='upper', extent=[0,self.width,0,self.height])
        axs[0].set_title("Original Drawing")
        axs[0].set_xlim(0,self.width)
        axs[0].set_ylim(0,self.height)

        # Right: sampled points
        points_flipped = points.copy()
        # fliping y-axis for correct display
        points_flipped[:,1] = self.height - points_flipped[:,1]
        axs[1].scatter(points_flipped[:,0], points_flipped[:,1], c='red', s=20)
        axs[1].set_xlim(0,self.width)
        axs[1].set_ylim(0,self.height)
        axs[1].set_title("Sampled Points")

        plt.tight_layout()
        plt.show()

    def exit_app(self):
        print("Exiting app.")
        self.root.destroy()


if __name__ == "__main__":
    ProjectDrawApp()
