# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import copy
import time

import torch
import torch.nn as nn


class Agent(nn.Module):
    """An `Agent` is a `torch.nn.Module` that reads and writes into a `bbrl.Workspace`"""

    def __init__(self, name: str = None, verbose=False):
        """To create a new Agent

        Args:
            name ([type], optional): An agent can have a name that will allow to perform operations
            on agents that are composed into more complex agents.
        """
        super().__init__()
        self._name = name
        self.__trace_file = None
        self.verbose = verbose
        self.workspace = None

    def seed(self, seed: int):
        """Provide a seed to this agent. Useful is the agent is stochastic.

        Args:
            seed (str): [description]
        """
        pass

    def set_name(self, n):
        """Set the name of this agent

        Args:
            n (str): The name
        """
        self._name = n

    def get_name(self):
        """Returns the name of the agent

        Returns:
            str: the name
        """
        return self._name

    def set_trace_file(self, filename):
        print("[TRACE]: Tracing agent in file " + filename)
        self.__trace_file = open(filename, "wt")

    def __call__(self, workspace, **kwargs):
        """Execute an agent of a `bbrl.Workspace`

        Args:
            workspace (bbrl.Workspace): the workspace on which the agent operates
        """
        assert workspace is not None, "[Agent.__call__] workspace must not be None"
        self.workspace = workspace
        self.forward(**kwargs)
        self.workspace = None

    def _asynchronous_call(self, workspace, **kwargs):
        """Execute the `__call__` in non-blocking mode (if the agent is in another process)

        Args:
             workspace (bbrl.Workspace): the workspace on which the agent operates
        """
        self.__call__(workspace, **kwargs)

    def is_running(self):
        """Returns True if the agent is currently executing (for remote agents)"""
        return False

    def forward(self, **kwargs):
        """The generic function to override when defining a new agent"""
        raise NotImplementedError

    def clone(self):
        """Create a clone of the agent

        Returns:
            bbrl.Agent: A clone
        """
        self.workspace = None
        self.zero_grad()
        return copy.deepcopy(self)

    def get(self, index):
        """Returns the value of a particular variable in the agent workspace

        Args:
            index (str or tuple(str,int)): if str, returns the variable workspace[str].
            If tuple(var_name,t), returns workspace[var_name] at time t
        """
        if self.__trace_file is not None:
            t = time.time()
            self.__trace_file.write(
                str(self) + " type = " + type(self) + " time = ",
                t,
                " get ",
                index,
                "\n",
            )
        if isinstance(index, str):
            return self.workspace.get_full(index)
        else:
            return self.workspace.get(index[0], index[1])

    def get_time_truncated(self, var_name, from_time, to_time):
        """Return a variable truncated between from_time and to_time"""
        return self.workspace.get_time_truncated(var_name, from_time, to_time)

    def set(self, index, value):
        """Write a variable in the workspace

        Args:
            index (str or tuple(str,int)):
            value (torch.Tensor): the value to write
        """
        if self.__trace_file is not None:
            t = time.time()
            self.__trace_file.write(
                str(self) + " type = " + type(self) + " time = ",
                t,
                " set ",
                index,
                " = ",
                value.size(),
                "/",
                value.dtype,
                "\n",
            )
        if isinstance(index, str):
            self.workspace.set_full(index, value)
        else:
            self.workspace.set(index[0], index[1], value)

    def get_by_name(self, n):
        """Returns the list of agents included in this agent that have a particular name."""
        if n == self._name:
            return [self]
        return []

    def save_model(self, filename) -> None:
        """
        Save a neural network model into a file
        :param filename: the filename, including the path
        :return: nothing
        """
        torch.save(self, filename)

    def load_model(self, filename) -> nn.Module:
        """
        Load a neural network model from a file
        :param filename: the filename, including the path
        :return: the resulting pytorch network
        """
        return torch.load(filename)
