# TaleForge

An interactive, text-based adventure game where players make decisions that influence the progression and outcome of the story. Stories are dynamically generated using an AI model (via Ollama) based on user choices and selected genres.

## Features

- Multiple genre selection (Action, Horror, Adventure, Mystery, Fantasy)
- Dynamic story generation using AI
- Branching narrative paths based on user choices
- Multiple possible endings
- Command-line interface
- High replayability

## Requirements

- Python 3.8+
- Ollama (with a running LLM model)
- Required Python packages (install via requirements.txt)

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Ensure Ollama is running with your preferred LLM model
4. Run the game:
   ```
   python story_generator.py
   ```

## How to Play

1. Select a genre when prompted
2. Read the story segments as they're presented
3. Make choices when prompted to influence the story
4. Experience different outcomes based on your decisions
5. Replay with different choices and genres for new experiences

## Project Structure

- `story_generator.py`: Main game logic
- `story_engine.py`: Story generation and AI integration
- `game_state.py`: Game state management
- `utils.py`: Utility functions
