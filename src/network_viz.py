import pygame
import math

class NetworkVisualizer:
    def __init__(self, width=400, height=500):
        """Initialize the network visualizer with given dimensions."""
        self.width = width
        self.height = height
        
        # Colors for different node types and connections
        self.colors = {
            'background': (240, 240, 240),
            'input_node': (50, 150, 50),     # Green
            'hidden_node': (255, 165, 0),   # Orange
            'output_node': (70, 130, 180),  # Steel Blue
            'positive_conn': (255, 0, 0),   # Red
            'negative_conn': (0, 0, 255),   # Blue
            'text': (10, 10, 10),           # Near black
            'title': (255, 255, 255)        # White
        }
        
        # Font for labels
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 10)
        self.title_font = pygame.font.SysFont('Arial', 16)
        self.node_radius = 6
        self.show_labels = True
        
    def draw_network(self, genome, config):
        """
        Draw a neural network on a new surface based on genome and config.
        Returns the surface with the network visualization.
        """
        if not genome:
            return None
            
        try:
            # Create a new surface for the network visualization
            surface = pygame.Surface((self.width, self.height))
            surface.fill((50, 50, 50))  # Dark background
            
            # Draw title
            title = self.title_font.render("Neural Network", True, self.colors['title'])
            surface.blit(title, (self.width // 2 - title.get_width() // 2, 10))
            
            # Identify nodes by type - directly use config input/output keys
            input_keys = config.genome_config.input_keys
            output_keys = config.genome_config.output_keys
            hidden_keys = [k for k in genome.nodes.keys() if k not in input_keys and k not in output_keys]
            
            # Calculate node positions
            node_positions = self._calculate_node_positions(input_keys, hidden_keys, output_keys)
            
            # Draw connections first (to be behind nodes)
            for cg in genome.connections.values():
                if not cg.enabled:
                    continue
                    
                input_node, output_node = cg.key
                if input_node not in node_positions or output_node not in node_positions:
                    continue
                    
                x1, y1 = node_positions[input_node]
                x2, y2 = node_positions[output_node]
                
                # Determine connection color and width based on weight
                weight = cg.weight
                if weight > 0:
                    color = self.colors['positive_conn']
                else:
                    color = self.colors['negative_conn']
                    
                # Scale line width based on weight strength
                width = max(1, min(3, int(abs(weight) * 2)))
                
                # Draw the connection line
                pygame.draw.line(surface, color, (x1, y1), (x2, y2), width)
            
            # Draw all nodes
            # Input nodes
            for i, node_id in enumerate(input_keys):
                if node_id in node_positions:
                    pos = node_positions[node_id]
                    pygame.draw.circle(surface, self.colors['input_node'], pos, self.node_radius)
                    pygame.draw.circle(surface, (20, 20, 20), pos, self.node_radius, 1)  # Border
                    
                    # Label for input node
                    if self.show_labels:
                        label = f"{i}"
                        text = self.font.render(label, True, self.colors['text'])
                        surface.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))
            
            # Hidden nodes
            for i, node_id in enumerate(hidden_keys):
                if node_id in node_positions:
                    pos = node_positions[node_id]
                    pygame.draw.circle(surface, self.colors['hidden_node'], pos, self.node_radius)
                    pygame.draw.circle(surface, (20, 20, 20), pos, self.node_radius, 1)  # Border
                    
                    # Label for hidden node
                    if self.show_labels:
                        label = f"{node_id}"
                        text = self.font.render(label, True, self.colors['text'])
                        surface.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))
            
            # Output nodes
            for i, node_id in enumerate(output_keys):
                if node_id in node_positions:
                    pos = node_positions[node_id]
                    pygame.draw.circle(surface, self.colors['output_node'], pos, self.node_radius)
                    pygame.draw.circle(surface, (20, 20, 20), pos, self.node_radius, 1)  # Border
                    
                    # Label for output node
                    if self.show_labels:
                        label = f"{i}"
                        text = self.font.render(label, True, self.colors['text'])
                        surface.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))
            
            # Draw legend
            self._draw_legend(surface)
            
            return surface
            
        except Exception as e:
            print(f"Network visualization error: {e}")
            # Return a fallback surface with an error message
            fallback = pygame.Surface((self.width, self.height))
            fallback.fill((50, 50, 50))
            font = pygame.font.Font(None, 20)
            text = font.render(f"Network error: {str(e)[:40]}", True, (255, 0, 0))
            fallback.blit(text, (20, 20))
            return fallback
    
    def _calculate_node_positions(self, input_keys, hidden_keys, output_keys):
        """Calculate positions for all nodes with multiple columns for inputs if needed."""
        positions = {}
        
        # Layout parameters
        margin_left = 40
        margin_right = 40
        margin_top = 50
        margin_bottom = 100  # Leave space for legend
        
        # Width and height of the drawable area
        drawable_width = self.width - margin_left - margin_right
        drawable_height = self.height - margin_top - margin_bottom
        
        # Position input nodes in multiple columns on the left if needed
        num_inputs = len(input_keys)
        if num_inputs > 0:
            # Use multiple columns if too many inputs
            max_inputs_per_col = 10
            num_input_cols = math.ceil(num_inputs / max_inputs_per_col)
            inputs_per_col = math.ceil(num_inputs / num_input_cols)
            
            for i, node_id in enumerate(input_keys):
                col = i // inputs_per_col
                row = i % inputs_per_col
                
                # Calculate position within this column
                x = margin_left + col * (drawable_width / (num_input_cols * 2 + 2))
                y_spacing = drawable_height / (inputs_per_col + 1)
                y = margin_top + (row + 1) * y_spacing
                
                positions[node_id] = (int(x), int(y))
        
        # Position output nodes in a column on the right
        num_outputs = len(output_keys)
        if num_outputs > 0:
            output_x = self.width - margin_right
            output_spacing = drawable_height / (num_outputs + 1)
            for i, node_id in enumerate(output_keys):
                y = margin_top + (i + 1) * output_spacing
                positions[node_id] = (int(output_x), int(y))
        
        # Position hidden nodes in the middle
        num_hidden = len(hidden_keys)
        if num_hidden > 0:
            # Distribute hidden nodes in the middle area
            hidden_x = margin_left + drawable_width / 2
            
            if num_hidden <= 10:
                # If few hidden nodes, arrange in a single column
                hidden_spacing = drawable_height / (num_hidden + 1)
                for i, node_id in enumerate(hidden_keys):
                    y = margin_top + (i + 1) * hidden_spacing
                    positions[node_id] = (int(hidden_x), int(y))
            else:
                # For many hidden nodes, arrange in a grid pattern
                cols = min(3, math.ceil(math.sqrt(num_hidden)))
                rows = math.ceil(num_hidden / cols)
                
                for i, node_id in enumerate(hidden_keys):
                    col = i % cols
                    row = i // cols
                    
                    x = margin_left + drawable_width * (0.3 + 0.2 * col)
                    y_spacing = drawable_height / (rows + 1)
                    y = margin_top + (row + 1) * y_spacing
                    
                    positions[node_id] = (int(x), int(y))
        
        return positions
    
    def _draw_legend(self, surface):
        """Draw a legend explaining node and connection colors."""
        # Legend background
        legend_rect = pygame.Rect(10, self.height - 90, self.width - 20, 80)
        pygame.draw.rect(surface, (30, 30, 30), legend_rect)
        pygame.draw.rect(surface, (100, 100, 100), legend_rect, 1)
        
        # Title
        title = self.title_font.render("Legend", True, self.colors['title'])
        surface.blit(title, (legend_rect.centerx - title.get_width() // 2, legend_rect.y + 5))
        
        # Node types - first row
        y_pos = legend_rect.y + 30
        
        # Input node
        pygame.draw.circle(surface, self.colors['input_node'], (30, y_pos), 5)
        text = self.font.render("Input", True, self.colors['title'])
        surface.blit(text, (40, y_pos - text.get_height() // 2))
        
        # Hidden node
        pygame.draw.circle(surface, self.colors['hidden_node'], (120, y_pos), 5)
        text = self.font.render("Hidden", True, self.colors['title'])
        surface.blit(text, (130, y_pos - text.get_height() // 2))
        
        # Output node
        pygame.draw.circle(surface, self.colors['output_node'], (210, y_pos), 5)
        text = self.font.render("Output", True, self.colors['title'])
        surface.blit(text, (220, y_pos - text.get_height() // 2))
        
        # Connection types - second row
        y_pos += 25
        
        # Positive connection
        pygame.draw.line(surface, self.colors['positive_conn'], (20, y_pos), (40, y_pos), 2)
        text = self.font.render("Positive weight", True, self.colors['title'])
        surface.blit(text, (50, y_pos - text.get_height() // 2))
        
        # Negative connection
        pygame.draw.line(surface, self.colors['negative_conn'], (150, y_pos), (170, y_pos), 2)
        text = self.font.render("Negative weight", True, self.colors['title'])
        surface.blit(text, (180, y_pos - text.get_height() // 2))
        
        # Count summary - third row
        y_pos += 25
        
        # Show node counts
        num_inputs = 29  # Updated for new sensor count with knees
        num_hidden = 5
        num_outputs = 6  # Updated for new motor count with knees
        text = self.font.render(f"Inputs: {num_inputs} | Hidden: {num_hidden} | Outputs: {num_outputs}", True, self.colors['title'])
        surface.blit(text, (legend_rect.centerx - text.get_width() // 2, y_pos - text.get_height() // 2)) 