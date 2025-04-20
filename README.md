# Walking Neuro-Evolution

A physics-based evolution simulation where dummies learn to walk through neuro-evolution.

## Overview

This project simulates bipedal walking motion using:
- Physics simulation via PyMunk
- Visualization with PyGame
- Neural network evolution using NEAT (NeuroEvolution of Augmenting Topologies)

The dummies evolve to develop effective walking strategies over multiple generations, adapting their movement patterns to maximize distance traveled and avoid the advancing laser.

## Features

### Physics Simulation
- Fully articulated physics-based dummies with:
  - Head with limited range of motion (±30 degrees)
  - Body (torso)
  - Arms with shoulder joints
  - Legs with hip and knee joints
  - Realistic joint constraints and movement limits
  - Different power levels for arms and legs (legs have 2x the power of arms)
  - Knees with expanded range of motion (±90 degrees)
- Death conditions:
  - Laser contact causes explosion of dummy
  - Head touching ground immediately terminates the dummy

### Enhanced Sensor System
- 11 sensor inputs for neural network:
  - 4 relative joint angles (shoulders and hips)
  - 4 absolute body angles (head, torso, arms and legs)
  - 2 contact sensors (left and right foot)
  - Normalized to provide consistent input ranges

### Advanced Visualization
- Real-time visualization of the evolution process
- Dynamic camera that follows dummies and pans when laser reaches threshold (x=120)
- Custom face rendering on dummy heads with proper rotation
- Textured ground for better visual tracking of camera movement
- Red vertical line at the panning threshold position (x=120) 
- Stats panel showing:
  - Current generation number
  - Best and average fitness
  - Number of active dummies
  - Species count and stagnation info
  - Time elapsed
- Neural network visualization (toggle with 'N' key)

### Improved Evolution
- NEAT algorithm implementation with optimized parameters:
  - Increased population size (150)
  - 3 hidden layers for more complex behaviors
  - Modified mutation rates for better exploration
  - Sigmoid and ReLU activation functions
- Enhanced fitness function incorporating:
  - Survival time (frames alive)
  - Movement distance tracking
  - Head stability bonus
  - Improvements over previous performance
- Detailed fitness reporting after each generation
- Parallel processing for faster evaluation using ProcessPoolExecutor
- Clean state management between generations

## Controls
- ESC: Exit the simulation
- N: Toggle neural network visualization

## Technical Details

### Neural Network
- Inputs (11 total):
  - 4 relative joint angles
  - 4 absolute body orientation angles
  - 2 contact sensors (feet)
- Outputs (4 total):
  - Motor control signals for each joint group
- Evolves both network topology and weights

### Performance Optimizations
- Multi-process parallel evaluation when not in visualization mode
- Isolated simulation spaces for each dummy during parallel evaluation
- Efficient memory management and cleanup

### Physics Parameters
- Motor maximum force: 2,000,000 units (arms), 4,000,000 units (legs)
- Motor rate: 10 rad/s maximum angular velocity
- Head movement constrained to ±30 degrees with damped spring physics
- Knee joints allow -90 to +90 degrees of movement
- Camera panning threshold at x=120

## Requirements

- Python 3.12
- PyMunk
- PyGame
- NEAT-Python
- concurrent.futures (standard library)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Simulation

```bash
python main.py
```

This will start the evolutionary process and display the simulation window.

## Recent Improvements

1. **Enhanced Sensor System**: Added absolute rotation sensors for better body awareness
2. **Neural Network Optimization**: Increased network complexity with 3 hidden layers
3. **Camera Panning**: Dynamic camera that follows dummies, then pans right with the laser
4. **Face Visualization**: Added rotating faces on dummy heads for better visual tracking
5. **Textured Ground**: Added ground texture to better visualize camera movement
6. **Multiprocessing**: Improved parallel processing with concurrent.futures
7. **Fitness Calculation**: Enhanced fitness metrics to reward better walking behavior
8. **Head Stability**: Added bonus for keeping head upright during movement
9. **Network Visualization**: Fixed the network visualization to properly display connections
10. **Death on Head Contact**: Dummies now die immediately if their head touches the ground