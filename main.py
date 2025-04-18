# main.py
import sys
import os
import neat
import pickle # To save winner genome

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulation import Simulation

# --- Configuration --- 
NUM_GENERATIONS = 50
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config-feedforward.txt')
VISUALIZE = True # Set to False to run headless (faster)
WINNER_FILE = 'winner_genome.pkl'

# Global simulation and visualizer instances (managed by eval_genomes)
# We initialize them once to avoid recreating the Pygame window repeatedly
simulation: Simulation | None = None
visualizer = None
visualizer_closed = False  # Flag to track if visualizer was closed by user

# Custom exception for graceful termination
class VisualizerClosedException(Exception):
    """Raised when the user closes the visualizer window."""
    pass

def eval_genomes(genomes: list[tuple[int, neat.DefaultGenome]], config: neat.Config):
    """Evaluates the fitness of each genome in the current generation.
    
    NEAT calls this function for each generation. It receives a list of
    (genome_id, genome) pairs and the NEAT config object.
    We run our simulation, calculate fitness, and assign it back to each genome.
    """
    global simulation, visualizer, VISUALIZE, visualizer_closed

    # --- Check for Early Exit ---
    if visualizer_closed:
        # If user has closed visualizer, terminate by setting minimal fitness
        for _, genome in genomes:
            genome.fitness = -1000
        # This should exit quickly
        return

    # --- Initialize Simulation and Visualizer (if first run) --- 
    if simulation is None:
        print("Initializing Simulation instance for evaluation...")
        simulation = Simulation()
        if VISUALIZE:
            try:
                from visualizer import Visualizer
                print("Initializing Visualizer...")
                visualizer = Visualizer() 
                simulation.set_visualizer(visualizer) # Link visualizer to simulation
            except ImportError:
                print("Visualizer module not found or Pygame not installed. Running headless.")
                VISUALIZE = False # Ensure we don't try to use it later
            except Exception as e:
                 print(f"Error initializing visualizer: {e}. Running headless.")
                 VISUALIZE = False

    # --- Run the Simulation Generation --- 
    if simulation:
        simulation.run_generation(genomes, config)
    else:
        # Should not happen if initialization worked
        print("Error: Simulation object not initialized.")
        # Assign minimal fitness to all genomes
        for _, genome in genomes:
            genome.fitness = -1000

    # Check if user quit the visualizer during the generation
    if VISUALIZE and visualizer and not visualizer.running:
         # Signal NEAT to terminate by raising an exception or using a global flag
         print("Visualizer quit, ending evolution run.")
         visualizer_closed = True  # Set the flag so future calls will exit early
         # Raise an exception to stop the current run
         raise VisualizerClosedException("User closed the visualizer")


def run_neat(config_file: str):
    """Sets up and runs the NEAT algorithm."""
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add reporters to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # Optional: Checkpointer to save progress
    # p.add_reporter(neat.Checkpointer(5, filename_prefix='neat-checkpoint-'))

    # Run for up to NUM_GENERATIONS generations.
    try:
        winner = p.run(eval_genomes, NUM_GENERATIONS)
    except VisualizerClosedException as e:
        print(f"NEAT run terminated early: {e}")
        # Handle clean exit for visualizer closed case
        if visualizer:
             visualizer.close()
        print("Application terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"NEAT run terminated early: {e}")
        # Handle potential early exit from visualizer quit
        if visualizer:
             visualizer.close()
        sys.exit(1)

    # --- Evolution Finished --- 
    if visualizer:
        visualizer.close()

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # Show output of the most fit genome against training data (not applicable here).
    # print('\nOutput:')
    # winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    # You could run the winner one last time here if desired

    # Save the winner.
    with open(WINNER_FILE, 'wb') as f:
        pickle.dump(winner, f)
        print(f"Winner genome saved to {WINNER_FILE}")

    # Optional: Visualize statistics
    # neat.visualize.plot_stats(stats, ylog=False, view=True)
    # neat.visualize.plot_species(stats, view=True)
    # neat.visualize.draw_net(config, winner, True)


if __name__ == '__main__':
    # Ensure the config path is correct before passing to neat
    config_path = os.path.abspath(CONFIG_PATH)
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    print()
    run_neat(config_path) 