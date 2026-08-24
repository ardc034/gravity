import matplotlib.pyplot as plt

class EnergyGraph:
    def __init__(self):
        plt.ion()

        self.fig, self.ax = plt.subplots()

        # Three curves: total, KE, PE
        self.line_total, = self.ax.plot([], [], 'r-', linewidth=2, label="Total Energy")
        self.line_ke,    = self.ax.plot([], [], 'g-', linewidth=2, label="Kinetic Energy")
        self.line_pe,    = self.ax.plot([], [], 'b-', linewidth=2, label="Potential Energy")

        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Energy")
        self.ax.set_title("Energy Diagnostics Over Time")
        self.ax.legend()

        # Data buffers
        self.time_history = []
        self.total_history = []
        self.ke_history = []
        self.pe_history = []


    def update(self, total_energy, kinetic_energy, potential_energy, time):
        self.time_history.append(time)
        self.total_history.append(total_energy)
        self.ke_history.append(kinetic_energy)
        self.pe_history.append(potential_energy)

        # Update graph every 1s
        if time % 1 < 0.016:
            self.line_total.set_xdata(self.time_history)
            self.line_total.set_ydata(self.total_history)

            self.line_ke.set_xdata(self.time_history)
            self.line_ke.set_ydata(self.ke_history)

            self.line_pe.set_xdata(self.time_history)
            self.line_pe.set_ydata(self.pe_history)

            self.ax.relim()
            self.ax.autoscale_view()

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

