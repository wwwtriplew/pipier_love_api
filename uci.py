#!/usr/bin/env python3
"""
UCI (Universal Chess Interface) Protocol Implementation

The UCI protocol is a standard way for chess engines to communicate with
chess GUIs (like Arena, Fritz, ChessBase, etc.).

Protocol Specification: http://wbec-ridderkerk.nl/html/UCIProtocol.html

This implementation provides a complete UCI interface for the Piper Love
Chess Engine, allowing it to be used with any UCI-compatible chess GUI.

Key UCI Commands:
    - uci: Tell engine to use UCI protocol
    - isready: Ping engine, responds with "readyok"
    - ucinewgame: Start new game
    - position: Set up position
    - go: Start calculating
    - stop: Stop calculating
    - quit: Exit engine

Usage:
    python3 uci.py
    
    Or from a chess GUI that supports UCI engines.
"""

import sys
import time
from typing import Optional, List, Dict, Any
from io import StringIO

# Import our chess engine
sys.path.insert(0, '.')
from src.board_state import Position, new_game, from_fen


# =============================================================================
# ENGINE INFORMATION
# =============================================================================

ENGINE_NAME = "Piper Love"
ENGINE_VERSION = "1.0.0"
ENGINE_AUTHOR = "Ng Ho Hin"


# =============================================================================
# UCI ENGINE CLASS
# =============================================================================

class UCIEngine:
    """
    Main UCI engine class that handles communication between chess GUIs
    and the Piper Love chess engine.
    
    This class:
    1. Parses UCI commands from stdin
    2. Executes commands using the chess engine
    3. Sends responses to stdout in UCI format
    """
    
    def __init__(self):
        """
        Initialize the UCI engine.
        
        Sets up:
        - Current position (starts with standard starting position)
        - Engine state tracking
        - Search parameters
        """
        # Current chess position
        self.position: Position = new_game()
        
        # Engine state
        self.debug_mode: bool = False
        self.is_searching: bool = False
        
        # Search parameters (can be configured by GUI)
        self.max_depth: int = 6  # Default search depth
        self.max_time_ms: Optional[int] = None  # Max time per move in milliseconds
        
        # Performance tracking
        self.nodes_searched: int = 0
        self.search_start_time: float = 0.0
        
    # =========================================================================
    # MAIN UCI LOOP
    # =========================================================================
    
    def main_loop(self):
        """
        Main UCI command loop.
        
        Continuously reads commands from stdin and processes them.
        This is the main entry point for UCI communication.
        
        The loop runs until:
        - 'quit' command is received
        - EOF is reached (stdin closed)
        - An unhandled exception occurs
        """
        while True:
            try:
                # Read command from stdin (sent by chess GUI)
                command = input().strip()
                
                # Skip empty lines
                if not command:
                    continue
                
                # Debug logging (if enabled)
                if self.debug_mode:
                    self._log(f"Received: {command}")
                
                # Process the command
                self._process_command(command)
                
            except EOFError:
                # stdin closed, exit gracefully
                break
            except KeyboardInterrupt:
                # User interrupted, exit gracefully
                break
            except Exception as e:
                # Unexpected error, log and continue
                self._log(f"Error: {e}")
                if self.debug_mode:
                    import traceback
                    self._log(traceback.format_exc())
    
    # =========================================================================
    # COMMAND PROCESSING
    # =========================================================================
    
    def _process_command(self, command: str):
        """
        Process a UCI command.
        
        Args:
            command: UCI command string (e.g., "uci", "position startpos", etc.)
        
        This method routes commands to their appropriate handlers.
        """
        # Split command into tokens for easier parsing
        tokens = command.split()
        if not tokens:
            return
        
        # Get the main command (first token)
        cmd = tokens[0].lower()
        
        # Route to appropriate handler
        if cmd == "uci":
            self._handle_uci()
        elif cmd == "isready":
            self._handle_isready()
        elif cmd == "ucinewgame":
            self._handle_ucinewgame()
        elif cmd == "position":
            self._handle_position(tokens[1:])
        elif cmd == "go":
            self._handle_go(tokens[1:])
        elif cmd == "stop":
            self._handle_stop()
        elif cmd == "quit":
            self._handle_quit()
        elif cmd == "debug":
            self._handle_debug(tokens[1:])
        elif cmd == "setoption":
            self._handle_setoption(tokens[1:])
        elif cmd == "perft":
            # Custom command for performance testing
            self._handle_perft(tokens[1:])
        elif cmd == "d":
            # Custom command to display board
            self._handle_display()
        else:
            # Unknown command, log if debug enabled
            if self.debug_mode:
                self._log(f"Unknown command: {cmd}")
    
    # =========================================================================
    # UCI COMMAND HANDLERS
    # =========================================================================
    
    def _handle_uci(self):
        """
        Handle 'uci' command.
        
        This is the first command sent by the GUI when starting communication.
        The engine must respond with:
        1. id name <engine name>
        2. id author <author name>
        3. List of options (if any)
        4. uciok (indicates UCI mode is enabled)
        """
        # Send engine identification
        self._send(f"id name {ENGINE_NAME} {ENGINE_VERSION}")
        self._send(f"id author {ENGINE_AUTHOR}")
        
        # Send engine options
        # Format: option name <name> type <type> default <value> min <min> max <max>
        self._send("option name Hash type spin default 128 min 1 max 1024")
        self._send("option name Threads type spin default 1 min 1 max 128")
        self._send("option name Move Overhead type spin default 10 min 0 max 5000")
        
        # Indicate UCI mode is ready
        self._send("uciok")
    
    def _handle_isready(self):
        """
        Handle 'isready' command.
        
        This is a synchronization command. The GUI sends this to check if
        the engine is ready to receive commands. The engine must respond
        with 'readyok' when it's ready.
        
        This is useful after:
        - Engine initialization
        - Setting options
        - Loading positions
        """
        # Perform any necessary initialization here
        # (currently, engine is always ready)
        
        # Respond that engine is ready
        self._send("readyok")
    
    def _handle_ucinewgame(self):
        """
        Handle 'ucinewgame' command.
        
        Sent when a new game is starting. The engine should:
        1. Clear any game-specific data (hash tables, history, etc.)
        2. Reset to starting position
        3. Prepare for a new game
        
        Note: The actual position will be set by a subsequent 'position' command.
        """
        # Reset to starting position
        self.position = new_game()
        
        # Clear search statistics
        self.nodes_searched = 0
        
        # Clear any cached data (if we had transposition tables, etc.)
        # (Not implemented yet, but this is where it would go)
        
        if self.debug_mode:
            self._log("New game started")
    
    def _handle_position(self, tokens: List[str]):
        """
        Handle 'position' command.
        
        Sets up a chess position. Two formats:
        1. position startpos [moves <move1> <move2> ...]
        2. position fen <fen_string> [moves <move1> <move2> ...]
        
        Args:
            tokens: Command tokens after 'position'
        
        Examples:
            position startpos
            position startpos moves e2e4 e7e5 g1f3
            position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
            position fen <fen> moves e2e4
        """
        if not tokens:
            self._log("Error: position command requires arguments")
            return
        
        # Check if starting position or FEN
        if tokens[0] == "startpos":
            # Standard starting position
            self.position = new_game()
            tokens = tokens[1:]  # Remove 'startpos' token
        
        elif tokens[0] == "fen":
            # FEN position
            # FEN string can be multiple tokens (space-separated)
            # Find where 'moves' starts (if present)
            try:
                moves_index = tokens.index("moves") if "moves" in tokens else len(tokens)
            except ValueError:
                moves_index = len(tokens)
            
            # FEN is everything between 'fen' and 'moves' (or end)
            fen_tokens = tokens[1:moves_index]
            fen_string = " ".join(fen_tokens)
            
            # Set up position from FEN
            try:
                self.position = from_fen(fen_string)
            except Exception as e:
                self._log(f"Error parsing FEN: {e}")
                return
            
            # Continue with moves (if any)
            tokens = tokens[moves_index:]
        
        else:
            self._log(f"Error: Unknown position type: {tokens[0]}")
            return
        
        # Apply moves if present
        if tokens and tokens[0] == "moves":
            for move_str in tokens[1:]:
                # Make the move on the board
                success = self.position.make_move(move_str)
                if not success:
                    self._log(f"Error: Illegal move: {move_str}")
                    return
        
        if self.debug_mode:
            self._log(f"Position set: {self.position.get_fen()}")
    
    def _handle_go(self, tokens: List[str]):
        """
        Handle 'go' command.
        
        Start calculating best move. Many options:
        - go infinite: Search until 'stop' command
        - go depth <n>: Search to depth n
        - go movetime <ms>: Search for exactly ms milliseconds
        - go wtime <ms> btime <ms>: Time controls
        - go nodes <n>: Search exactly n nodes
        - go perft <n>: Run perft test to depth n
        
        Args:
            tokens: Command tokens after 'go'
        
        Examples:
            go infinite
            go depth 10
            go movetime 5000
            go wtime 60000 btime 60000 winc 1000 binc 1000
        """
        # Parse go parameters
        search_params = self._parse_go_params(tokens)
        
        # Start search
        self.is_searching = True
        self.search_start_time = time.time()
        self.nodes_searched = 0
        
        # Get best move (currently just picks first legal move)
        # TODO: Implement actual search algorithm here
        best_move = self._search(search_params)
        
        # Send result
        if best_move:
            self._send(f"bestmove {best_move}")
        else:
            # No legal moves (checkmate or stalemate)
            self._send("bestmove (none)")
        
        self.is_searching = False
    
    def _handle_stop(self):
        """
        Handle 'stop' command.
        
        Stop the current search and return the best move found so far.
        This is sent by the GUI when:
        - Time is up
        - User wants to stop analysis
        - Moving to next position
        
        The engine should:
        1. Stop searching immediately
        2. Send 'bestmove' with the best move found
        """
        # Set flag to stop search
        self.is_searching = False
        
        if self.debug_mode:
            self._log("Search stopped by GUI")
        
        # Note: In a real search implementation, you would check
        # self.is_searching in the search loop and exit cleanly
    
    def _handle_quit(self):
        """
        Handle 'quit' command.
        
        Exit the engine gracefully. The engine should:
        1. Stop any ongoing search
        2. Clean up resources
        3. Exit the program
        """
        if self.debug_mode:
            self._log("Quitting engine")
        
        # Stop any ongoing search
        self.is_searching = False
        
        # Exit program
        sys.exit(0)
    
    def _handle_debug(self, tokens: List[str]):
        """
        Handle 'debug' command.
        
        Enable or disable debug mode.
        Format: debug on|off
        
        In debug mode, the engine sends additional information
        to help with troubleshooting.
        
        Args:
            tokens: ['on'] or ['off']
        """
        if tokens and tokens[0].lower() == "on":
            self.debug_mode = True
            self._log("Debug mode enabled")
        elif tokens and tokens[0].lower() == "off":
            self.debug_mode = False
        else:
            self._log("Usage: debug on|off")
    
    def _handle_setoption(self, tokens: List[str]):
        """
        Handle 'setoption' command.
        
        Set engine options.
        Format: setoption name <name> value <value>
        
        Args:
            tokens: Tokens after 'setoption'
        
        Example:
            setoption name Hash value 256
            setoption name Threads value 4
        """
        # Parse option name and value
        try:
            name_index = tokens.index("name")
            value_index = tokens.index("value")
            
            # Option name is between 'name' and 'value'
            option_name = " ".join(tokens[name_index + 1:value_index])
            # Option value is after 'value'
            option_value = " ".join(tokens[value_index + 1:])
            
            # Process the option
            self._set_option(option_name, option_value)
            
        except (ValueError, IndexError) as e:
            self._log(f"Error parsing setoption: {e}")
    
    def _handle_perft(self, tokens: List[str]):
        """
        Handle custom 'perft' command (not part of UCI standard).
        
        Run a perft (performance test) to verify move generation
        correctness and measure speed.
        
        Format: perft <depth>
        
        Args:
            tokens: ['<depth>']
        
        Example:
            perft 5
        """
        if not tokens:
            self._log("Usage: perft <depth>")
            return
        
        try:
            depth = int(tokens[0])
        except ValueError:
            self._log("Error: depth must be an integer")
            return
        
        # Run perft
        self._log(f"Running perft({depth})...")
        start_time = time.time()
        nodes = self.position.perft(depth)
        elapsed = time.time() - start_time
        
        # Report results
        nps = nodes / elapsed if elapsed > 0 else 0
        self._log(f"Nodes: {nodes:,}")
        self._log(f"Time: {elapsed:.3f}s")
        self._log(f"NPS: {nps:,.0f}")
    
    def _handle_display(self):
        """
        Handle custom 'd' command (not part of UCI standard).
        
        Display the current board position in a human-readable format.
        Useful for debugging.
        """
        self._log("\nCurrent position:")
        self._log(str(self.position))
        self._log(f"FEN: {self.position.get_fen()}")
        self._log(f"To move: {self.position.to_move}")
        self._log(f"In check: {self.position.in_check}")
        self._log(f"Legal moves: {len(self.position.legal_moves())}")
    
    # =========================================================================
    # SEARCH IMPLEMENTATION
    # =========================================================================
    
    def _search(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Main search function to find the best move.
        
        This is a placeholder implementation that just picks the first
        legal move. In a real engine, this would implement:
        - Minimax/Negamax search
        - Alpha-beta pruning
        - Move ordering
        - Quiescence search
        - Transposition tables
        - Iterative deepening
        
        Args:
            params: Search parameters (depth, time, nodes, etc.)
        
        Returns:
            Best move in UCI format (e.g., 'e2e4', 'e7e8q')
        """
        # Get legal moves
        legal_moves = self.position.legal_moves()
        
        if not legal_moves:
            # No legal moves (checkmate or stalemate)
            return None
        
        # TODO: Implement actual search here
        # For now, just pick the first legal move
        best_move = legal_moves[0]
        
        # Send search info (UCI 'info' command)
        self._send_search_info(
            depth=1,
            nodes=len(legal_moves),
            score=0,
            pv=[best_move]
        )
        
        return best_move
    
    def _send_search_info(self, depth: int, nodes: int, score: int, pv: List[str]):
        """
        Send search information to GUI.
        
        UCI 'info' command format:
        info depth <d> score cp <score> nodes <n> nps <nps> time <ms> pv <move1> <move2> ...
        
        Args:
            depth: Current search depth
            nodes: Nodes searched
            score: Position score in centipawns
            pv: Principal variation (best line)
        """
        # Calculate elapsed time
        elapsed_ms = int((time.time() - self.search_start_time) * 1000)
        
        # Calculate nodes per second
        nps = int(nodes / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0
        
        # Build info string
        info_parts = [
            "info",
            f"depth {depth}",
            f"score cp {score}",
            f"nodes {nodes}",
            f"nps {nps}",
            f"time {elapsed_ms}",
        ]
        
        # Add principal variation
        if pv:
            info_parts.append("pv")
            info_parts.extend(pv)
        
        self._send(" ".join(info_parts))
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _parse_go_params(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Parse 'go' command parameters.
        
        Args:
            tokens: Tokens after 'go'
        
        Returns:
            Dictionary of search parameters
        """
        params = {
            "infinite": False,
            "depth": None,
            "movetime": None,
            "wtime": None,
            "btime": None,
            "winc": None,
            "binc": None,
            "movestogo": None,
            "nodes": None,
        }
        
        i = 0
        while i < len(tokens):
            token = tokens[i].lower()
            
            if token == "infinite":
                params["infinite"] = True
                i += 1
            
            elif token in ["depth", "movetime", "wtime", "btime", "winc", "binc", "movestogo", "nodes"]:
                if i + 1 < len(tokens):
                    try:
                        params[token] = int(tokens[i + 1])
                    except ValueError:
                        self._log(f"Error: Invalid value for {token}")
                    i += 2
                else:
                    self._log(f"Error: Missing value for {token}")
                    i += 1
            
            else:
                # Unknown parameter, skip
                i += 1
        
        return params
    
    def _set_option(self, name: str, value: str):
        """
        Set an engine option.
        
        Args:
            name: Option name
            value: Option value
        """
        name_lower = name.lower()
        
        if name_lower == "hash":
            # Hash table size in MB
            try:
                hash_size = int(value)
                # TODO: Allocate hash table
                if self.debug_mode:
                    self._log(f"Hash size set to {hash_size} MB")
            except ValueError:
                self._log("Error: Hash value must be an integer")
        
        elif name_lower == "threads":
            # Number of search threads
            try:
                thread_count = int(value)
                # TODO: Set thread count
                if self.debug_mode:
                    self._log(f"Threads set to {thread_count}")
            except ValueError:
                self._log("Error: Threads value must be an integer")
        
        elif name_lower == "move overhead":
            # Move overhead in milliseconds
            try:
                overhead = int(value)
                # TODO: Set move overhead
                if self.debug_mode:
                    self._log(f"Move overhead set to {overhead} ms")
            except ValueError:
                self._log("Error: Move Overhead value must be an integer")
        
        else:
            if self.debug_mode:
                self._log(f"Unknown option: {name}")
    
    def _send(self, message: str):
        """
        Send a message to the GUI via stdout.
        
        All UCI communication goes through stdout. Messages must be
        followed by a newline and flushed immediately.
        
        Args:
            message: Message to send
        """
        print(message, flush=True)
    
    def _log(self, message: str):
        """
        Send a log message (info string) to the GUI.
        
        Uses UCI 'info string' command which the GUI can display
        to the user or log to a file.
        
        Args:
            message: Log message
        """
        self._send(f"info string {message}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """
    Main entry point for the UCI engine.
    
    Creates a UCIEngine instance and starts the main command loop.
    """
    # Create engine
    engine = UCIEngine()
    
    # Send startup message (optional)
    # Note: This should only be sent in debug mode or before UCI mode
    # is enabled, as UCI specification says no output before 'uci' command
    
    # Start main UCI loop
    engine.main_loop()


if __name__ == "__main__":
    main()
