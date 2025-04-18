# main.py
import sys
import os
import time # For pausing after reset

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulation import Simulation
from visualizer import Visualizer # Import the new Visualizer class

DT = 1/60.0 # Physics timestep
# Move dummy start pos further right
DUMMY_START_POS = (250, 150)

def main():
    print("Initializing simulation and visualizer...")
    # Initialize simulation and visualizer ONCE
    sim = Simulation()
    viz = Visualizer() # Uses new default height

    # Add the first dummy
    print("Adding initial dummy...")
    sim.add_dummy(position=DUMMY_START_POS)
    generation = 1

    print("Starting simulation generations (Press ESC or close window to quit)...")

    # Outer loop for handling runs and resets
    while viz.running:
        # Inner loop for a single simulation run (until death or quit)
        run_active = True
        while run_active and viz.running:
            # Check for user quit first
            # process_events is called within viz.draw, updating viz.running
            if not viz.running:
                break

            # Check if the dummy was hit by the laser
            if sim.dummy_is_dead:
                print(f"End of Generation {generation}. Dummy hit by laser.")
                run_active = False # End this inner loop
                break # Go to reset logic

            # Step the physics simulation
            sim.step(DT)

            # Draw the current state (also handles Pygame events)
            # Pass the simulation object for camera focus
            if not viz.draw(sim): # viz.draw now returns True if still running
                run_active = False # End this inner loop if user quit
                break # Go to outer loop check

        # --- End of single run --- 

        # If the visualizer is still running, calculate fitness and reset
        if viz.running:
            fitness = sim.get_fitness()
            print(f"Generation {generation} Fitness: {fitness:.2f}")
            if sim.dummy:
                print(f"Final X position: {sim.dummy.get_body_position().x:.2f}")
            
            # Reset for the next generation
            generation += 1
            print(f"\nResetting for Generation {generation}...")
            sim.reset(dummy_start_pos=DUMMY_START_POS)
            time.sleep(0.5) # Brief pause to see the reset
        else:
            # Visualizer was closed, break outer loop
            break

    # --- Simulation ended (user quit) --- 
    print("\nSimulation program finished.")

    # Clean up Pygame
    viz.close()

if __name__ == "__main__":
    main() 