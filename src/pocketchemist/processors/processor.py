"""
Processor base classes
"""
import abc
import typing as t

import click

__all__ = ('Processor', 'GroupProcessor')

# The number of spaces to add for printing sub-levels of processors
space_level = 2


class Processor:
    """A processor for data and other objects"""

    #: The name of the processor
    name: str = None

    #: Parameters used for processing
    params: t.Dict[str, t.Union[str, int, float, 'lmfit.Parameter']] = None

    #: A listing of required and optional parameters
    required_params: tuple = ()
    optional_params: tuple = ()

    #: Options for printing the processor to the terminal
    print_cls_fg_color = 'cyan'  # fg color to use in print processor cls names

    def __init__(self, name=None, *args, **kwargs):
        # Set the processor name
        if name is not None:
            self.name = name

        # Setup other attributes
        self.params = dict()

        # Set the parameters
        # First check if there are missing parameters
        missing_params = set(self.required_params) - kwargs.keys()
        if len(missing_params) > 0:
            raise ValueError(f"The {self.__class__.__name__} processor is "
                             f"missing the following required kwargs "
                             f"parameters: {missing_params}")

        # Collect the specified parameters
        available_params = (set(self.required_params) |
                            set(self.optional_params))
        specified_params = available_params.intersection(kwargs.keys())
        for specified_param in specified_params:
            self.params[specified_param] = kwargs[specified_param]

    def __repr__(self):
        name = self.name if self.name is not None else self.__class__.__name__
        return f"{name}"

    def __getattr__(self, name):
        """Search the params dict for an attribute"""
        if isinstance(self.params, dict) and name in self.params:
            return self.params.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no "
                             f"attribute '{name}'")

    @abc.abstractmethod
    def process(self, **kwargs: dict):
        """Conduct the processing

        Parameters
        ----------
        kwargs
            The input and output parameters for the process. Processed data
            should be placed in the kwargs for subsequent processors
        """
        pass

    def print(self, level: int = 0, space_level: int = 0,
              item_number: t.Optional[str] = "") -> None:
        """Print information on the processor to the terminal.

        Parameters
        ----------
        level
            The level of the processor for processors that are nested in
            groups.
        space_level
            The number of spaces to separate a level
        item_number
            An optional character to prepend the printed processing string.
        """
        name = self.name if self.name is not None else self.__class__.__name__
        item_number = str(item_number) + '. ' if item_number else ""
        params = ", ".join("=".join((k, v)) for k, v in self.params.items())
        params = f"({params})" if params else ""

        click.echo(" " * (level * space_level) +
                   item_number +
                   click.style(f"{name}", fg=self.print_cls_fg_color) +
                   params, err=True)


class GroupProcessor(Processor):
    """A processor comprising multiple subprocessors"""

    #: A list of (sub-)processors owned by this group
    processors: t.List[Processor] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = []

    def __repr__(self):
        name = self.name if self.name is not None else self.__class__.__name__
        num_processors = len(self.processors)
        return f"{name}(number_processors={num_processors})"

    def __iadd__(self, other):
        self.add(other)
        return self

    def add(self, processor: Processor):
        """Add a processor to the list of processors

        Parameters
        ----------
        processor
            The processor to add to the self.processors list
        """
        if isinstance(processor, Processor):
            self.processors.append(processor)
        else:
            raise TypeError(f"The {self.__class__.__name__} class can only "
                            f"append Processor type objects.")

    def process(self, **kwargs):
        """Conduct the group processing"""
        if not hasattr(self.processors, '__iter__'):
            return None

        # Iterate and process the processors
        for processor in self.processors:
            rv = processor.process(**kwargs)

    def print(self, level=0, space_level=space_level):
        """Print information on the processor to the terminal"""
        super().print(level=level, space_level=space_level)

        for count, processor in enumerate(self.processors, 1):
            processor.print(level=level + 1, space_level=space_level,
                            item_number=count)
