# main.py
import sys
import os
# import time # No longer resetting

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulation import Simulation
from visualizer import Visualizer

DT = 1/60.0 # Physics timestep
DUMMY_START_POS = (250, 150)
NUM_DUMMIES = 100

def main():
    print("Initializing simulation and visualizer...")
    sim = Simulation()
    viz = Visualizer()

    # Add the dummies
    print(f"Adding {NUM_DUMMIES} dummies...")
    for i in range(NUM_DUMMIES):
        # Slightly stagger start positions vertically for visibility (optional)
        start_pos = (DUMMY_START_POS[0], DUMMY_START_POS[1] + i * 2)
        sim.add_dummy_instance(position=start_pos)

    print("Starting continuous simulation (Press ESC or close window to quit)...")

    # Main simulation loop (no generations/resets)
    while viz.running:
        # Step the physics simulation (includes NN updates for active dummies)
        sim.step(DT)

        # Draw the current state (handles Pygame events)
        # Pass the simulation object for camera focus
        if not viz.draw(sim):
            break # Exit loop if user quit

    # --- Simulation ended (user quit) --- 
    print("\nSimulation program finished.")

    # Clean up Pygame
    viz.close()

if __name__ == "__main__":
    main() 