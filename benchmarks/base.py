from abc import ABC, abstractmethod


class DatabaseAdapter(ABC):
    """
    Common interface that every database adapter must implement.
    """

    @abstractmethod
    def connect(self):
        """Connect to the database."""
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """Close the database connection."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, query, parameters=None):
        """Execute a database query."""
        raise NotImplementedError

    @abstractmethod
    def load_dataset(self, nodes_file, relationships_file):
        """Load the benchmark dataset."""
        raise NotImplementedError

    @abstractmethod
    def get_counts(self):
        """Return node and relationship counts."""
        raise NotImplementedError