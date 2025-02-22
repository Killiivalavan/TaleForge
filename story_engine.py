import json
import re
import os
from datetime import datetime
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class StoryEngine:
    def __init__(self, log_file='story_context_log.json'):
        self.llm = Ollama(model="llama3.2")
        self.log_file = os.path.join(os.path.dirname(__file__), log_file)
        self.min_turns = 10  # Minimum number of turns before allowing ending
        self.max_turns = 15  # Maximum number of turns before forcing ending
        self.story_prompt = PromptTemplate(
            input_variables=["genre", "context", "instructions", "turn_count", "min_turns", "max_turns"],
            template="""You are an expert interactive storyteller creating a {genre} genre story.

CONTEXT OVERVIEW:
- Genre: {genre}
- Turn Count: {turn_count} out of {max_turns} maximum turns
- Previous Choices: {history}
- Characters: {characters}
- Locations: {locations}
- Key Events: {key_events}
- Player Attributes: {player_attributes}

Story Generation Instructions:
{instructions}
- Create a concise, focused story segment that advances the plot
- Ensure each choice leads to meaningful story progression
- Maintain the tone and style of the {genre} genre

Story Structure Guidelines (Current Turn: {turn_count}, Min: {min_turns}, Max: {max_turns}):
- Turns 1-3: Establish the setting and introduce the main conflict
- Turns 4-6: Develop the plot and reveal key information
- Turns 7-9: Build tension and complications
- Turns 10-12: Lead to climactic moments
- Turns 13-15: Provide resolution opportunities

IMPORTANT:
- DO NOT end the story before turn {min_turns}
- Story MUST continue until at least turn {min_turns}
- Only start offering ending choices after turn {min_turns}
- Force story ending at turn {max_turns}

Respond EXACTLY in this JSON format (NO EXTRA TEXT):
{{
    "story_text": "Your story segment text here, incorporating previous context",
    "choices": [
        {{
            "text": "Choice 1 description",
            "action": "Specific action for Choice 1"
        }},
        {{
            "text": "Choice 2 description",
            "action": "Specific action for Choice 2"
        }},
        {{
            "text": "Choice 3 description",
            "action": "Specific action for Choice 3"
        }}
    ],
    "is_ending": false,
    "context_update": {{
        "new_characters": {{"Character Name": "Brief description"}},
        "new_locations": {{"Location Name": "Brief description"}},
        "key_event": "Significant event that occurred"
    }}
}}"""
        )

    def _log_story_context(self, context, story_response):
        """
        Log the story context and generation to a JSON file.
        """
        try:
            # Read existing log
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "genre": context.get('genre', 'Unknown'),
                "previous_choices": context.get('history', []),
                "story_text": story_response.get('story_text', ''),
                "choices": story_response.get('choices', []),
                "context_update": story_response.get('context_update', {}),
                "is_ending": story_response.get('is_ending', False)
            }
            
            # Add to log sessions
            log_data.setdefault('story_sessions', []).append(log_entry)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        
        except Exception as e:
            print(f"Error logging story context: {e}")

    def _clean_json_response(self, response):
        """
        Clean and prepare the JSON response for parsing.
        """
        try:
            # Remove any text before the first {
            start_idx = response.find('{')
            if start_idx != -1:
                response = response[start_idx:]
            
            # Remove any text after the last }
            end_idx = response.rfind('}')
            if end_idx != -1:
                response = response[:end_idx + 1]
            
            # Remove newlines and extra spaces between JSON elements
            response = re.sub(r'\s+(?=[^"]*(?:"[^"]*"[^"]*)*$)', ' ', response)
            
            # Fix common JSON formatting issues
            response = response.replace('\\"', '"')  # Fix escaped quotes
            response = re.sub(r'(?<!\\)\\n', ' ', response)  # Remove newlines
            response = re.sub(r'\\+(?!["\\/bfnrtu])', '', response)  # Remove invalid escapes
            
            # Fix missing quotes around property names
            response = re.sub(r'(\s*{|\s*,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', response)
            
            # Fix trailing commas
            response = re.sub(r',(\s*[}\]])', r'\1', response)
            
            # Add missing quotes around string values
            response = re.sub(r':\s*([^"{}\[\],\s][^{}\[\],\s]*)\s*([,}])', r': "\1"\2', response)
            
            return response
            
        except Exception as e:
            raise ValueError(f"Error cleaning JSON response: {str(e)}\nOriginal response: {response}")

    def _process_story_response(self, response_text, turn_count):
        """Process and validate the story response."""
        try:
            # First try direct JSON parsing
            try:
                story_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract and clean JSON
                cleaned_response = self._clean_json_response(response_text)
                try:
                    story_data = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    # If still fails, try to construct a valid response from the text
                    story_data = self._construct_valid_response(response_text, turn_count >= self.max_turns)
            
            # Validate required fields
            required_fields = ['story_text', 'choices', 'is_ending']
            if not all(field in story_data for field in required_fields):
                missing_fields = [field for field in required_fields if field not in story_data]
                story_data = self._repair_story_data(story_data, missing_fields)
            
            # Force ending if at max turns
            if turn_count >= self.max_turns:
                story_data['is_ending'] = True
                story_data['choices'] = []
            # Prevent ending if below min turns
            elif turn_count < self.min_turns:
                story_data['is_ending'] = False
            
            # Normalize choices
            normalized_choices = []
            choices = story_data.get('choices', [])
            
            # Handle if choices is a string
            if isinstance(choices, str):
                choices = [choices]
            # Handle if choices is not iterable
            elif not hasattr(choices, '__iter__'):
                choices = [str(choices)]
            
            for choice in choices:
                if isinstance(choice, str):
                    normalized_choices.append({
                        "text": choice,
                        "action": choice
                    })
                elif isinstance(choice, dict):
                    # Handle if choice is a dict but values are not strings
                    text = str(choice.get('text', choice.get('action', 'Unnamed choice')))
                    action = str(choice.get('action', choice.get('text', 'Unnamed action')))
                    description = str(choice.get('description', ''))
                    
                    normalized_choice = {
                        "text": text,
                        "action": action
                    }
                    if description:
                        normalized_choice["description"] = description
                    
                    normalized_choices.append(normalized_choice)
                else:
                    normalized_choices.append({
                        "text": str(choice),
                        "action": str(choice)
                    })
            
            # Ensure there are choices if not ending
            if not story_data['is_ending'] and not normalized_choices:
                normalized_choices = [
                    {"text": "Continue the investigation", "action": "Continue the investigation"},
                    {"text": "Take a different approach", "action": "Take a different approach"},
                    {"text": "Search for more clues", "action": "Search for more clues"}
                ]
            
            story_data['choices'] = normalized_choices
            
            # Normalize context_update
            context_update = story_data.get('context_update', {})
            if not isinstance(context_update, dict):
                context_update = {}
            
            # Ensure new_characters is a dict
            new_characters = context_update.get('new_characters', {})
            if not isinstance(new_characters, dict):
                new_characters = {}
            context_update['new_characters'] = new_characters
            
            # Ensure new_locations is a dict
            new_locations = context_update.get('new_locations', {})
            if not isinstance(new_locations, dict):
                new_locations = {}
            context_update['new_locations'] = new_locations
            
            # Remove None values
            context_update = {k: v for k, v in context_update.items() if v is not None}
            story_data['context_update'] = context_update
            
            return story_data
            
        except Exception as e:
            raise ValueError(f"Error processing story response: {str(e)}\nResponse text: {response_text}")

    def _repair_story_data(self, story_data, missing_fields):
        """Repair incomplete story data by adding missing required fields."""
        if 'story_text' in missing_fields:
            story_data['story_text'] = "The story continues..."
        
        if 'choices' in missing_fields:
            story_data['choices'] = [
                {"text": "Continue the story", "action": "Continue the story"},
                {"text": "Take a different path", "action": "Take a different path"}
            ]
        
        if 'is_ending' in missing_fields:
            story_data['is_ending'] = False
        
        if 'context_update' not in story_data:
            story_data['context_update'] = {}
        
        return story_data

    def _construct_valid_response(self, text, force_ending=False):
        """Construct a valid story response from raw text."""
        # Try to extract story text and choices
        story_text = text
        choices = []
        
        # Look for choices in the text
        choice_matches = re.finditer(r'"(?:text|action)":\s*"([^"]+)"', text)
        found_choices = [match.group(1) for match in choice_matches]
        
        if found_choices:
            choices = [{"text": choice, "action": choice} for choice in found_choices[:3]]
        else:
            # If no choices found, provide default choices
            choices = [
                {"text": "Continue the journey", "action": "Continue the journey"},
                {"text": "Take a different approach", "action": "Take a different approach"}
            ]
        
        # Construct a valid response
        return {
            "story_text": story_text,
            "choices": choices if not force_ending else [],
            "is_ending": force_ending,
            "context_update": {}
        }

    def generate_story_segment(self, context, is_start=False):
        """
        Generate the next story segment based on the context and genre.
        Returns a dictionary with story text, choices, and whether it's an ending.
        """
        # Get turn count from context
        turn_count = len(context.get('history', [])) + 1
        
        # Prepare context details
        if is_start:
            instructions = """
            - Introduce the main setting and characters
            - Establish the central conflict or mystery
            - Create an engaging hook for the player
            - DO NOT resolve the story yet - this is just the beginning
            """
        elif turn_count >= self.max_turns:
            instructions = """
            - Provide a satisfying conclusion to the story
            - Resolve the main conflict
            - Tie up loose plot threads
            """
            story_data = self._generate_ending(context)
            return story_data
        elif turn_count >= self.min_turns and turn_count < self.max_turns - 2:
            instructions = """
            - Continue building toward the story's climax
            - Offer meaningful choices that advance the plot
            - Introduce new complications or revelations
            - Maintain story tension and engagement
            """
        elif turn_count >= self.max_turns - 2:
            instructions = """
            - Begin preparing for story resolution
            - Start converging plot threads
            - Hint at potential story conclusions
            - Create choices that lead toward final resolution
            """
        else:
            instructions = """
            - Advance the plot meaningfully
            - Reveal new information or complications
            - Keep the story focused and engaging
            - DO NOT end the story yet - minimum turns not reached
            """
        
        # Extract context details
        story_context = context.get('story_context', {})
        
        # Format context for the prompt
        context_format = {
            'genre': context['genre'],
            'turn_count': turn_count,
            'min_turns': self.min_turns,
            'max_turns': self.max_turns,
            'history': ', '.join(context.get('history', [])) or "No previous choices",
            'characters': json.dumps(story_context.get('characters', {})),
            'locations': json.dumps(story_context.get('locations', {})),
            'key_events': ', '.join(story_context.get('key_events', [])) or "No key events yet",
            'player_attributes': json.dumps(story_context.get('player_attributes', {}))
        }
        
        # Create the prompt
        prompt = self.story_prompt.format(
            **context_format,
            instructions=instructions
        )
        
        try:
            # Get response from Ollama using invoke
            response = self.llm.invoke(prompt)
            
            # Clean the response
            cleaned_response = self._clean_json_response(response)
            
            # Parse and process the response
            story_data = self._process_story_response(cleaned_response, turn_count)
            
            # Ensure story doesn't end too early
            if turn_count < self.min_turns:
                story_data['is_ending'] = False
                if not story_data['choices']:
                    story_data['choices'] = [
                        {"text": "Continue investigating", "action": "Continue investigating"},
                        {"text": "Explore another approach", "action": "Explore another approach"},
                        {"text": "Search for more clues", "action": "Search for more clues"}
                    ]
            
            # Force story continuation if not near ending
            if turn_count < self.max_turns - 2:
                story_data['is_ending'] = False
            
            # Log the story context
            self._log_story_context(context, story_data)
            
            return story_data
            
        except Exception as e:
            return self._create_fallback_response(str(e), turn_count >= self.max_turns)

    def _generate_ending(self, context):
        """Generate a satisfying ending to the story."""
        # Extract context details
        story_context = context.get('story_context', {})
        
        # Prepare ending prompt with full context
        ending_prompt = PromptTemplate(
            input_variables=["genre", "context", "characters", "locations", "key_events"],
            template="""You are crafting a satisfying conclusion to a {genre} story.

Story Context:
- Genre: {genre}
- Characters: {characters}
- Locations: {locations}
- Key Events: {key_events}

Ending Generation Guidelines:
1. Provide a clear and meaningful resolution to the main conflict
2. Address the character arcs and journeys
3. Tie together key plot threads
4. Create a sense of closure while leaving a little room for imagination
5. Reflect the tone and style of the {genre} genre

Respond EXACTLY in this JSON format:
{{
    "story_text": "Comprehensive ending narrative that wraps up the story",
    "choices": [],
    "is_ending": true,
    "context_update": {{
        "final_outcome": "Summary of the story's conclusion"
    }}
}}"""
        )
        
        # Format context for the ending prompt
        context_format = {
            'genre': context['genre'],
            'characters': json.dumps(story_context.get('characters', {})),
            'locations': json.dumps(story_context.get('locations', {})),
            'key_events': ', '.join(story_context.get('key_events', [])) or "No key events"
        }
        
        # Create the ending prompt
        prompt = ending_prompt.format(**context_format)
        
        try:
            # Get ending response from Ollama
            response = self.llm.invoke(prompt)
            
            # Clean and process the response
            cleaned_response = self._clean_json_response(response)
            ending_data = json.loads(cleaned_response)
            
            # Ensure ending data has required fields
            if 'story_text' not in ending_data:
                ending_data['story_text'] = "The story reaches its conclusion, bringing closure to the adventure."
            
            ending_data['is_ending'] = True
            ending_data['choices'] = []
            
            return ending_data
        
        except Exception as e:
            # Fallback ending if generation fails
            return {
                "story_text": f"The story concludes unexpectedly. An error occurred during ending generation: {str(e)}",
                "choices": [],
                "is_ending": True,
                "context_update": {
                    "final_outcome": "Unexpected story conclusion"
                }
            }

    def _create_fallback_response(self, error_message, force_ending=False):
        """Create a fallback response in case of errors."""
        if force_ending:
            return {
                "story_text": "Your journey has reached its conclusion. Despite the challenges along the way, your story has come to an end.",
                "choices": [],
                "is_ending": True,
                "context_update": {}
            }
        else:
            return {
                "story_text": f"The story continues... (Error: {error_message})",
                "choices": [
                    {
                        "text": "Continue cautiously",
                        "action": "Continue cautiously"
                    },
                    {
                        "text": "Try something else",
                        "action": "Try something else"
                    }
                ],
                "is_ending": False,
                "context_update": {}
            }

    def _format_context(self, context):
        """Format the context for the prompt."""
        if not context['history']:
            return "Story is just beginning."
        
        return "\n".join([
            "Previous choices:",
            *[f"- {choice}" for choice in context['history'][-3:]]  # Last 3 choices
        ])
