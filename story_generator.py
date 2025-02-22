from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import sys
import logging
from story_engine import StoryEngine
from game_state import GameState

# Configure logging to prevent duplicate console output
logging.getLogger('root').setLevel(logging.ERROR)

console = Console()

class StoryGenerator:
    def __init__(self):
        self.console = Console()
        self.game_state = GameState()
        self.story_engine = StoryEngine()
        self.genres = {
            "1": "Action",
            "2": "Horror",
            "3": "Adventure",
            "4": "Mystery",
            "5": "Fantasy"
        }

    def display_welcome(self):
        console.print(Panel.fit(
            "[bold yellow]Welcome to the Interactive Story Generator![/bold yellow]\n\n"
            "Embark on a unique adventure where your choices shape the story.",
            title="🎮 Story Generator",
            border_style="yellow"
        ))

    def select_genre(self):
        console.print("\n[bold cyan]Select your story genre:[/bold cyan]")
        for key, genre in self.genres.items():
            console.print(f"{key}. {genre}")
        
        while True:
            choice = Prompt.ask("\nEnter your choice", choices=list(self.genres.keys()))
            return self.genres[choice]

    def run(self):
        """Run the story generator."""
        # Initialize story
        story_response = self.story_engine.generate_story_segment(
            self.game_state.get_context(),
            is_start=True
        )
        
        # Main story loop
        while True:
            # Display story text
            console.print(f"\n{story_response['story_text']}\n")
            
            # Update game context with new characters, locations, events
            context_update = story_response.get('context_update', {}) or {}
            
            # Ensure context_update is a dictionary
            if context_update is None:
                context_update = {}
            
            # Add new characters (only if not None and not an empty dictionary)
            new_characters = context_update.get('new_characters', {}) or {}
            if new_characters:
                for name, desc in new_characters.items():
                    self.game_state.add_character(name, desc)
            
            # Add new locations (only if not None and not an empty dictionary)
            new_locations = context_update.get('new_locations', {}) or {}
            if new_locations:
                for name, desc in new_locations.items():
                    self.game_state.add_location(name, desc)
            
            # Add key event if exists and not None
            key_event = context_update.get('key_event')
            if key_event:
                self.game_state.add_key_event(key_event)
            
            # Check if this is the story ending
            if story_response.get('is_ending', False):
                console.print("\n[bold cyan]THE END[/bold cyan]")
                console.print("\n[dim]Your journey has come to an end. Thank you for playing![/dim]")
                break
            
            # Display choices
            console.print("[bold cyan]What would you like to do?[/bold cyan]")
            for i, choice in enumerate(story_response['choices'], 1):
                # Handle both dictionary and string choices
                if isinstance(choice, dict):
                    # Display text if available, with description if present
                    choice_text = choice.get('text', choice.get('action', f'Choice {i}'))
                    description = choice.get('description', '')
                    console.print(f"[bold]{i}.[/bold] {choice_text}")
                    if description:
                        console.print(f"   [dim]{description}[/dim]")
                else:
                    # Fallback for string choices
                    console.print(f"[bold]{i}.[/bold] {choice}")
            
            # Get user choice
            while True:
                try:
                    choice_input = input(f"\nEnter your choice [1-{len(story_response['choices'])}]: ").strip()
                    chosen_index = int(choice_input) - 1
                    
                    # Validate choice index
                    if 0 <= chosen_index < len(story_response['choices']):
                        chosen_choice = story_response['choices'][chosen_index]
                        break
                    else:
                        console.print(f"[bold red]Invalid choice. Please enter a number between 1 and {len(story_response['choices'])}.[/bold red]")
                except ValueError:
                    console.print("[bold red]Please enter a valid number.[/bold red]")
            
            # Handle different choice formats
            if isinstance(chosen_choice, dict):
                # Extract context update and action
                context_update = chosen_choice.get('context_update', {}) or {}
                
                # Ensure context_update is a dictionary
                if context_update is None:
                    context_update = {}
                
                # Add new characters (only if not None and not an empty dictionary)
                new_characters = context_update.get('new_characters', {}) or {}
                if new_characters:
                    for name, desc in new_characters.items():
                        self.game_state.add_character(name, desc)
                
                # Add new locations (only if not None and not an empty dictionary)
                new_locations = context_update.get('new_locations', {}) or {}
                if new_locations:
                    for name, desc in new_locations.items():
                        self.game_state.add_location(name, desc)
                
                # Add key event if exists and not None
                key_event = context_update.get('key_event')
                if key_event:
                    self.game_state.add_key_event(key_event)
                
                # Use action or text for choice tracking
                chosen_action = chosen_choice.get('action', chosen_choice.get('text', 'Unnamed action'))
                self.game_state.add_choice(chosen_action)
            else:
                # For simple string choices
                self.game_state.add_choice(chosen_choice)
            
            # Generate next story segment
            story_response = self.story_engine.generate_story_segment(
                self.game_state.get_context()
            )

    def start_game(self):
        self.display_welcome()
        genre = self.select_genre()
        self.game_state.set_genre(genre)
        
        console.print(f"\n[bold green]Starting a new {genre} story...[/bold green]")
        
        self.run()

        console.print("\n[bold green]Thanks for playing![/bold green]")
        
        if Prompt.ask("\nWould you like to play again?", choices=["y", "n"]) == "y":
            self.game_state.reset()
            self.start_game()

def main():
    try:
        game = StoryGenerator()
        game.start_game()
    except KeyboardInterrupt:
        console.print("\n[bold red]Game terminated by user.[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
