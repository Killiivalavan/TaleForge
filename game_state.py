class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the game state to initial values."""
        self.genre = None
        self.choice_history = []
        self.story_context = {
            'characters': {},
            'locations': {},
            'key_events': [],
            'player_attributes': {
                'mood': 'neutral',
                'knowledge': [],
                'inventory': []
            }
        }
        self.game_over = False

    def set_genre(self, genre):
        """Set the story genre."""
        self.genre = genre

    def add_choice(self, choice):
        """Add a choice to the history and update context."""
        self.choice_history.append(choice)
        
        # Update context based on the choice
        self._update_context(choice)

    def _update_context(self, choice):
        """
        Update the story context based on the latest choice.
        This method can be expanded to add more sophisticated context tracking.
        """
        # Example of context updating logic
        if 'investigate' in choice.lower():
            self.story_context['player_attributes']['knowledge'].append('investigative')
        elif 'fight' in choice.lower():
            self.story_context['player_attributes']['mood'] = 'aggressive'
        elif 'hide' in choice.lower():
            self.story_context['player_attributes']['mood'] = 'cautious'

    def add_character(self, name, attributes):
        """Add or update a character in the context."""
        self.story_context['characters'][name] = attributes

    def add_location(self, name, description):
        """Add or update a location in the context."""
        self.story_context['locations'][name] = description

    def add_key_event(self, event):
        """Add a key event to the context."""
        self.story_context['key_events'].append(event)

    def get_context(self):
        """Get the current game context."""
        return {
            'genre': self.genre,
            'history': self.choice_history,
            'story_context': self.story_context
        }

    def is_game_over(self):
        """Check if the game is over."""
        return self.game_over

    def set_game_over(self):
        """Set the game as over."""
        self.game_over = True
