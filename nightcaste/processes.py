"""Processs can be used to model timed event sequnces."""


class GameProcess:
    """Represents a timed process. A GameProcess can have predecessor and a
    successor."""

    def __init__(self):
        self.active = False
        self.dead = False
        self.next = None
        self.prev = None

    def initialize(self, entity_manager, event_manager):
        self.entity_manager = entity_manager
        self.event_manager = event_manager

    def kill(self):
        """Mark this process as dead."""
        self.dead = True

    def then(self, next_process):
        """Specify the next process after this one.

        Args:
            next_process (GameProcess): The process which will be executed after
                this one is finished.

        Returns:
            The next process so this method can be used for chain calls.

        """
        self.next = next_process
        next_process.prev = self
        return next_process

    def update(self, delta):
        pass


class ProcessManager:
    """Manages all added processes."""

    def __init__(self, entity_manager, event_manager):
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        self.active_procs = []

    def add_process(self, process):
        """Add a process to be executed in the next tick."""
        process.initialize(self.entity_manager, self.event_manager)
        self.active_procs.append(process)
        process.active = True

    def update(self, delta):
        """Update all active processes."""
        dead_procs = []
        new_procs = []
        for process in self.active_procs:
            if process.dead:
                if process.next is not None:
                    new_procs.append(process.next)
                dead_procs.append(process)
            else:
                process.update(delta)
        # Remove dead processes and activate new ones
        for dead_proc in dead_procs:
            self.active_procs.remove(dead_proc)
        for new_proc in new_procs:
            self.add_process(process)
