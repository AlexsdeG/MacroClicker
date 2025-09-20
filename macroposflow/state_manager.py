"""
State management module for MacroPosFlow.

This module provides functionality to manage application states for both
recording and execution processes with proper state transitions and callbacks.
"""

import logging
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from time import time

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """Enumeration of possible process states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class StateTransition:
    """Information about a state transition."""
    from_state: ProcessState
    to_state: ProcessState
    timestamp: float
    reason: str


@dataclass
class ProcessInfo:
    """Information about a process (recording or execution)."""
    state: ProcessState
    start_time: Optional[float]
    pause_time: Optional[float]
    total_duration: float
    action_count: int
    current_action_index: int
    loop_count: int
    current_loop: int
    transitions: List[StateTransition]


class StateManager:
    """
    Manages application states for recording and execution processes.
    
    This class provides a centralized state management system with proper
    state validation, transitions, and callbacks for both recording and execution.
    """
    
    def __init__(self):
        """Initialize the StateManager."""
        # Process states
        self.recording_state = ProcessState.STOPPED
        self.execution_state = ProcessState.STOPPED
        
        # Process information
        self.recording_info = ProcessInfo(
            state=ProcessState.STOPPED,
            start_time=None,
            pause_time=None,
            total_duration=0.0,
            action_count=0,
            current_action_index=0,
            loop_count=1,
            current_loop=1,
            transitions=[]
        )
        
        self.execution_info = ProcessInfo(
            state=ProcessState.STOPPED,
            start_time=None,
            pause_time=None,
            total_duration=0.0,
            action_count=0,
            current_action_index=0,
            loop_count=1,
            current_loop=1,
            transitions=[]
        )
        
        # Threading locks
        self.recording_lock = threading.Lock()
        self.execution_lock = threading.Lock()
        
        # Callbacks
        self.recording_state_callbacks: List[Callable[[ProcessState, ProcessState], None]] = []
        self.execution_state_callbacks: List[Callable[[ProcessState, ProcessState], None]] = []
        
        logger.info("StateManager initialized")
    
    # Recording state management
    def get_recording_state(self) -> ProcessState:
        """
        Get current recording state.
        
        Returns:
            Current recording state
        """
        with self.recording_lock:
            return self.recording_state
    
    def set_recording_state(self, new_state: ProcessState, reason: str = "") -> bool:
        """
        Set recording state with validation.
        
        Args:
            new_state: New state to transition to
            reason: Reason for the state transition
            
        Returns:
            True if transition was successful, False otherwise
        """
        with self.recording_lock:
            old_state = self.recording_state
            
            if not self._is_valid_transition(old_state, new_state):
                logger.warning(f"Invalid recording state transition: {old_state} -> {new_state}")
                return False
            
            # Update state
            self.recording_state = new_state
            self.recording_info.state = new_state
            
            # Record transition
            transition = StateTransition(
                from_state=old_state,
                to_state=new_state,
                timestamp=time(),
                reason=reason
            )
            self.recording_info.transitions.append(transition)
            
            # Update timing information
            if new_state == ProcessState.RUNNING:
                if old_state == ProcessState.STOPPED:
                    self.recording_info.start_time = time()
                elif old_state == ProcessState.PAUSED:
                    # Resume from pause
                    if self.recording_info.pause_time:
                        pause_duration = time() - self.recording_info.pause_time
                        self.recording_info.total_duration += pause_duration
                    self.recording_info.pause_time = None
                    
            elif new_state == ProcessState.PAUSED:
                self.recording_info.pause_time = time()
                
            elif new_state == ProcessState.STOPPED:
                # Calculate total duration
                if self.recording_info.start_time:
                    if self.recording_info.pause_time:
                        # Stopped while paused
                        pause_duration = time() - self.recording_info.pause_time
                        self.recording_info.total_duration += pause_duration
                    else:
                        # Stopped while running
                        self.recording_info.total_duration = time() - self.recording_info.start_time
                
                # Reset timing info
                self.recording_info.start_time = None
                self.recording_info.pause_time = None
            
            logger.info(f"Recording state transition: {old_state} -> {new_state} ({reason})")
            
            # Call callbacks
            self._call_state_callbacks(self.recording_state_callbacks, old_state, new_state)
            
            return True
    
    def start_recording(self, reason: str = "User request") -> bool:
        """
        Start recording.
        
        Args:
            reason: Reason for starting recording
            
        Returns:
            True if start was successful, False otherwise
        """
        return self.set_recording_state(ProcessState.RUNNING, reason)
    
    def pause_recording(self, reason: str = "User request") -> bool:
        """
        Pause recording.
        
        Args:
            reason: Reason for pausing recording
            
        Returns:
            True if pause was successful, False otherwise
        """
        return self.set_recording_state(ProcessState.PAUSED, reason)
    
    def resume_recording(self, reason: str = "User request") -> bool:
        """
        Resume recording from paused state.
        
        Args:
            reason: Reason for resuming recording
            
        Returns:
            True if resume was successful, False otherwise
        """
        return self.set_recording_state(ProcessState.RUNNING, reason)
    
    def stop_recording(self, reason: str = "User request") -> bool:
        """
        Stop recording.
        
        Args:
            reason: Reason for stopping recording
            
        Returns:
            True if stop was successful, False otherwise
        """
        return self.set_recording_state(ProcessState.STOPPED, reason)
    
    def is_recording_active(self) -> bool:
        """
        Check if recording is currently active (running or paused).
        
        Returns:
            True if recording is active, False otherwise
        """
        with self.recording_lock:
            return self.recording_state in [ProcessState.RUNNING, ProcessState.PAUSED]
    
    def is_recording_running(self) -> bool:
        """
        Check if recording is currently running.
        
        Returns:
            True if recording is running, False otherwise
        """
        with self.recording_lock:
            return self.recording_state == ProcessState.RUNNING
    
    def is_recording_paused(self) -> bool:
        """
        Check if recording is currently paused.
        
        Returns:
            True if recording is paused, False otherwise
        """
        with self.recording_lock:
            return self.recording_state == ProcessState.PAUSED
    
    # Execution state management
    def get_execution_state(self) -> ProcessState:
        """
        Get current execution state.
        
        Returns:
            Current execution state
        """
        with self.execution_lock:
            return self.execution_state
    
    def set_execution_state(self, new_state: ProcessState, reason: str = "") -> bool:
        """
        Set execution state with validation.
        
        Args:
            new_state: New state to transition to
            reason: Reason for the state transition
            
        Returns:
            True if transition was successful, False otherwise
        """
        with self.execution_lock:
            old_state = self.execution_state
            
            if not self._is_valid_transition(old_state, new_state):
                logger.warning(f"Invalid execution state transition: {old_state} -> {new_state}")
                return False
            
            # Update state
            self.execution_state = new_state
            self.execution_info.state = new_state
            
            # Record transition
            transition = StateTransition(
                from_state=old_state,
                to_state=new_state,
                timestamp=time(),
                reason=reason
            )
            self.execution_info.transitions.append(transition)
            
            # Update timing information
            if new_state == ProcessState.RUNNING:
                if old_state == ProcessState.STOPPED:
                    self.execution_info.start_time = time()
                elif old_state == ProcessState.PAUSED:
                    # Resume from pause
                    if self.execution_info.pause_time:
                        pause_duration = time() - self.execution_info.pause_time
                        self.execution_info.total_duration += pause_duration
                    self.execution_info.pause_time = None
                    
            elif new_state == ProcessState.PAUSED:
                self.execution_info.pause_time = time()
                
            elif new_state == ProcessState.STOPPED:
                # Calculate total duration
                if self.execution_info.start_time:
                    if self.execution_info.pause_time:
                        # Stopped while paused
                        pause_duration = time() - self.execution_info.pause_time
                        self.execution_info.total_duration += pause_duration
                    else:
                        # Stopped while running
                        self.execution_info.total_duration = time() - self.execution_info.start_time
                
                # Reset timing info
                self.execution_info.start_time = None
                self.execution_info.pause_time = None
            
            logger.info(f"Execution state transition: {old_state} -> {new_state} ({reason})")
            
            # Call callbacks
            self._call_state_callbacks(self.execution_state_callbacks, old_state, new_state)
            
            return True
    
    def start_execution(self, reason: str = "User request") -> bool:
        """
        Start execution.
        
        Args:
            reason: Reason for starting execution
            
        Returns:
            True if start was successful, False otherwise
        """
        return self.set_execution_state(ProcessState.RUNNING, reason)
    
    def pause_execution(self, reason: str = "User request") -> bool:
        """
        Pause execution.
        
        Args:
            reason: Reason for pausing execution
            
        Returns:
            True if pause was successful, False otherwise
        """
        return self.set_execution_state(ProcessState.PAUSED, reason)
    
    def resume_execution(self, reason: str = "User request") -> bool:
        """
        Resume execution from paused state.
        
        Args:
            reason: Reason for resuming execution
            
        Returns:
            True if resume was successful, False otherwise
        """
        return self.set_execution_state(ProcessState.RUNNING, reason)
    
    def stop_execution(self, reason: str = "User request") -> bool:
        """
        Stop execution.
        
        Args:
            reason: Reason for stopping execution
            
        Returns:
            True if stop was successful, False otherwise
        """
        return self.set_execution_state(ProcessState.STOPPED, reason)
    
    def is_execution_active(self) -> bool:
        """
        Check if execution is currently active (running or paused).
        
        Returns:
            True if execution is active, False otherwise
        """
        with self.execution_lock:
            return self.execution_state in [ProcessState.RUNNING, ProcessState.PAUSED]
    
    def is_execution_running(self) -> bool:
        """
        Check if execution is currently running.
        
        Returns:
            True if execution is running, False otherwise
        """
        with self.execution_lock:
            return self.execution_state == ProcessState.RUNNING
    
    def is_execution_paused(self) -> bool:
        """
        Check if execution is currently paused.
        
        Returns:
            True if execution is paused, False otherwise
        """
        with self.execution_lock:
            return self.execution_state == ProcessState.PAUSED
    
    # Process information management
    def update_recording_info(self, **kwargs) -> None:
        """
        Update recording information.
        
        Args:
            **kwargs: Key-value pairs to update in recording info
        """
        with self.recording_lock:
            for key, value in kwargs.items():
                if hasattr(self.recording_info, key):
                    setattr(self.recording_info, key, value)
    
    def update_execution_info(self, **kwargs) -> None:
        """
        Update execution information.
        
        Args:
            **kwargs: Key-value pairs to update in execution info
        """
        with self.execution_lock:
            for key, value in kwargs.items():
                if hasattr(self.execution_info, key):
                    setattr(self.execution_info, key, value)
    
    def get_recording_info(self) -> ProcessInfo:
        """
        Get recording information.
        
        Returns:
            Copy of recording information
        """
        with self.recording_lock:
            return ProcessInfo(
                state=self.recording_info.state,
                start_time=self.recording_info.start_time,
                pause_time=self.recording_info.pause_time,
                total_duration=self.recording_info.total_duration,
                action_count=self.recording_info.action_count,
                current_action_index=self.recording_info.current_action_index,
                loop_count=self.recording_info.loop_count,
                current_loop=self.recording_info.current_loop,
                transitions=self.recording_info.transitions.copy()
            )
    
    def get_execution_info(self) -> ProcessInfo:
        """
        Get execution information.
        
        Returns:
            Copy of execution information
        """
        with self.execution_lock:
            return ProcessInfo(
                state=self.execution_info.state,
                start_time=self.execution_info.start_time,
                pause_time=self.execution_info.pause_time,
                total_duration=self.execution_info.total_duration,
                action_count=self.execution_info.action_count,
                current_action_index=self.execution_info.current_action_index,
                loop_count=self.execution_info.loop_count,
                current_loop=self.execution_info.current_loop,
                transitions=self.execution_info.transitions.copy()
            )
    
    # Callback management
    def add_recording_state_callback(self, callback: Callable[[ProcessState, ProcessState], None]) -> None:
        """
        Add a callback for recording state changes.
        
        Args:
            callback: Function to call when recording state changes
        """
        self.recording_state_callbacks.append(callback)
    
    def remove_recording_state_callback(self, callback: Callable[[ProcessState, ProcessState], None]) -> None:
        """
        Remove a recording state callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.recording_state_callbacks:
            self.recording_state_callbacks.remove(callback)
    
    def add_execution_state_callback(self, callback: Callable[[ProcessState, ProcessState], None]) -> None:
        """
        Add a callback for execution state changes.
        
        Args:
            callback: Function to call when execution state changes
        """
        self.execution_state_callbacks.append(callback)
    
    def remove_execution_state_callback(self, callback: Callable[[ProcessState, ProcessState], None]) -> None:
        """
        Remove an execution state callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.execution_state_callbacks:
            self.execution_state_callbacks.remove(callback)
    
    # Utility methods
    def _is_valid_transition(self, from_state: ProcessState, to_state: ProcessState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is valid, False otherwise
        """
        if from_state == to_state:
            return True  # Same state is allowed
        
        # Define valid transitions
        valid_transitions = {
            ProcessState.STOPPED: [ProcessState.RUNNING],
            ProcessState.RUNNING: [ProcessState.PAUSED, ProcessState.STOPPED],
            ProcessState.PAUSED: [ProcessState.RUNNING, ProcessState.STOPPED]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _call_state_callbacks(self, callbacks: List[Callable], old_state: ProcessState, new_state: ProcessState) -> None:
        """
        Call state change callbacks.
        
        Args:
            callbacks: List of callback functions
            old_state: Previous state
            new_state: New state
        """
        for callback in callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def reset_all_states(self) -> None:
        """Reset all states to STOPPED."""
        with self.recording_lock:
            self.recording_state = ProcessState.STOPPED
            self.recording_info = ProcessInfo(
                state=ProcessState.STOPPED,
                start_time=None,
                pause_time=None,
                total_duration=0.0,
                action_count=0,
                current_action_index=0,
                loop_count=1,
                current_loop=1,
                transitions=[]
            )
        
        with self.execution_lock:
            self.execution_state = ProcessState.STOPPED
            self.execution_info = ProcessInfo(
                state=ProcessState.STOPPED,
                start_time=None,
                pause_time=None,
                total_duration=0.0,
                action_count=0,
                current_action_index=0,
                loop_count=1,
                current_loop=1,
                transitions=[]
            )
        
        logger.info("All states reset to STOPPED")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            Dictionary with system status information
        """
        recording_info = self.get_recording_info()
        execution_info = self.get_execution_info()
        
        return {
            'recording_state': self.recording_state.value,
            'execution_state': self.execution_state.value,
            'recording_duration': recording_info.total_duration,
            'execution_duration': execution_info.total_duration,
            'recording_actions': recording_info.action_count,
            'execution_actions': execution_info.action_count,
            'recording_loops': recording_info.loop_count,
            'execution_loops': execution_info.loop_count,
            'can_start_recording': not self.is_recording_active(),
            'can_start_execution': not self.is_execution_active(),
            'can_pause_recording': self.is_recording_running(),
            'can_pause_execution': self.is_execution_running(),
            'can_resume_recording': self.is_recording_paused(),
            'can_resume_execution': self.is_execution_paused(),
            'can_stop_recording': self.is_recording_active(),
            'can_stop_execution': self.is_execution_active()
        }