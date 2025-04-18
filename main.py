# main.py
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulation import Simulation
from visualizer import Visualizer # Import the new Visualizer class

DT = 1/60.0 # Physics timestep

def main():
    print("Initializing simulation and visualizer...")
    sim = Simulation()
    viz = Visualizer() # Initialize the visualizer

    print("Adding dummy...")
    # Place the dummy slightly above the ground
    dummy_start_pos = (100, 150)
    sim.add_dummy(position=dummy_start_pos)

    print("Running simulation loop (Press ESC or close window to quit)...")

    # Main simulation loop
    while viz.running:
        # Step the physics simulation
        sim.step(DT)

        # Draw the current state
        # The draw method returns False if the user quits
        if not viz.draw(sim.space):
            break # Exit loop if visualization window is closed

    # --- Simulation finished --- 
    fitness = sim.get_fitness()
    print(f"\nSimulation loop ended.")
    print(f"Dummy initial X: {dummy_start_pos[0]:.2f}")
    if sim.dummy:
         print(f"Dummy final X:   {sim.dummy.get_body_position().x:.2f}")
    print(f"Fitness (Leftward distance): {fitness:.2f}")

    # Clean up Pygame
    viz.close()

if __name__ == "__main__":
    main() 