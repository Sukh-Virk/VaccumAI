"""
Search (Chapters 3-4)

The way to use this code is to subclass Problem to create a class of problems,
then create problem instances and solve them with calls to the various search
functions.
"""

import sys
import math
from collections import deque

from utils import *
from agents import *


"""
1- BFS: Breadth first search. Using tree or graph version, whichever makes more sense for the problem
2- DFS: Depth-First search. Again using tree or graph version.
3- UCS: Uniform-Cost-Search. Using the following cost function to optimise the path, from initial to current state.
4- Greedy: Uses Manhattan distance to the next closest dirty room as heuristic for greedy algorithm. To find the next closest dirty room, use Manhattan distance.
5- A*:  Using A star search.
"""
searchTypes = ['None', 'Reflex', 'BFS', 'DFS', 'UCS', 'Greedy', 'A*']
"""
Cost function used for UCS and A* search. 
-'Step' counts the numbers of steps from start
-'StepTurn' adds number of turns to Step cost
-'StayLeft' favors staying on the left side of the map
-'StayUp' favors staying on the top side of the map
"""
costFunctions = ['Step', 'StepTurn', 'StayLeft', 'StayUp']
heuristics = ['Manhattan', 'Euclid']

class Problem:
    """The abstract class for a formal problem. You should subclass
    this and implement the methods actions and result, and possibly
    __init__, goal_test, and path_cost. Then you will create instances
    of your subclass and solve them with the various search functions."""

    def __init__(self, initial, goal=None):
        """The constructor specifies the initial state, and possibly a goal
        state, if there is a unique goal. Your subclass's constructor can add
        other arguments."""
        self.initial = initial
        self.goal = goal

    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result would typically be a list, but if there are
        many actions, consider yielding them one at a time in an
        iterator, rather than building them all at once."""
        raise NotImplementedError

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        raise NotImplementedError

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal or checks for state in self.goal if it is a
        list, as specified in the constructor. Override this method if
        checking against a single self.goal is not enough."""
        if isinstance(self.goal, list):
            return is_in(state, self.goal)
        else:
            return state == self.goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2. If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def value(self, state):
        """For optimization problems, each state has a value. Hill Climbing
        and related algorithms try to maximize this value."""
        raise NotImplementedError


# ______________________________________________________________________________


class Node:
    """A node in a search tree. Contains a pointer to the parent (the node
    that this is a successor of) and to the actual state for this node. Note
    that if a state is arrived at by two paths, then there are two nodes with
    the same state. Also includes the action that got us to this state, and
    the total path_cost (also known as g) to reach the node. Other functions
    may add an f and h value; see best_first_graph_search and astar_search for
    an explanation of how the f and h values are handled. You will not need to
    subclass this class."""

    def __init__(self, state, parent=None, action=None, path_cost=0):
        """Create a search tree Node, derived from a parent by an action."""
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = 0
        if parent:
            self.depth = parent.depth + 1

    def __repr__(self):
        return "<Node {}>".format(self.state)

    def __lt__(self, node):
        return self.state < node.state

    def expand(self, problem):
        """
        List the nodes reachable in one step from this node.
        Prioritize LEFT action by sorting actions before expansion.
        """
        actions = problem.actions(self.state)
        # Sort actions so that 'LEFT' is always prioritized
        actions.sort(key=lambda action: 0 if action == 'LEFT' else 1)
        return [self.child_node(problem, action) for action in actions]

    def child_node(self, problem, action):
        """[Figure 3.10]"""
        next_state = problem.result(self.state, action)
        pathCost = problem.path_cost(self, self.state, action, next_state)
        next_node = Node(next_state, self, action, pathCost)
        return next_node

    def solution(self):
        """Return the sequence of actions to go from the root to this node."""
        return [node.action for node in self.path()[1:]]


    def path(self):
        """Return a list of nodes forming the path from the root to this node."""
        node, path_back = self, []
        while node:
            path_back.append(node)
            node = node.parent
        return list(reversed(path_back))

    # We want for a queue of nodes in breadth_first_graph_search or
    # astar_search to have no duplicated states, so we treat nodes
    # with the same state as equal. [Problem: this may not be what you
    # want in other contexts.]

    def __eq__(self, other):
        return isinstance(other, Node) and self.state == other.state

    def __hash__(self):
        # We use the hash value of the state
        # stored in the node instead of the node
        # object itself to quickly search a node
        # with the same state in a Hash Table
        return hash(self.state)



class VacuumPlanning(Problem):
    """ The problem of find the next room to clean in a grid of m x n rooms.
    A state is represented by state of the grid cells locations. Each room is specified by index set
    (i, j), i in range(m) and j in range (n). Final goal is to clean all dirty rooms. We go by performing sub-goals, each being cleaning the "next" dirty room.
    """

    def __init__(self, env, searchtype):
        """ Define goal state and initialize a problem
            initial is a pair (i, j) of where the agent is
            goal is next pair(k, l) where map[k][l] is dirty
        """
        self.solution = None
        self.env = env
        self.state = env.agent.location
        super().__init__(self.state)
        self.map = env.things
        self.searchType = searchtype
        env.agent.direction = 'UP'  # initial direction of the agent.
        self.agent = env.agent

    def generateSolution(self):
        """ generate full path and explored nodes from current node to the next goal node based on type of the search chosen"""
        if self.searchType == 'None':
            print("generateSolution: searchType not set or running not clicked!")
            return

        self.env.read_env()
        self.state = self.env.agent.location
        super().__init__(self.state)

        if self.searchType == 'BFS':
            path, explored = breadth_first_graph_search(self)
        elif self.searchType == 'DFS':
            path, explored = depth_first_graph_search(self)
        elif self.searchType == 'UCS':
            path, explored = uniform_cost_search(self)
        elif self.searchType == 'Greedy':
            path, explored = best_first_graph_search(self, None)
        elif self.searchType == 'A*':
            path, explored = astar_search(self, None)
        elif self.searchType == 'Reflex':
            path, explored = reflexAgentSearch(self)
        else:
            raise 'NameError'

        if (path != None):
            self.env.set_solution(path)
        else:
            print("There is no solution!\n")

        if (explored != None):
            self.env.display_explored(explored)
            self.env.exploredCount += len(explored)
            self.env.pathCount += len(self.env.path)
            self.env.ExploredCount_label.config(text=str(self.env.exploredCount))
            self.env.PathCount_label.config(text=str(self.env.pathCount))
        else:
            print("There is not explored list!\n")

    def generateNextSolution(self):
        self.generateSolution()

    def actions(self, state):
        """ Return the actions that can be executed in the given state.
        The result would be a list, since there are only four possible actions
        in any given state of the environment """

        possible_neighbors = self.env.things_near(state)
        possible_actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        for slot in possible_neighbors:
            if isinstance(slot[0], Wall):
                x, y = slot[0].location
                if x == state[0] and y == state[1] + 1:
                    possible_actions.remove('UP')
                if x == state[0] and y == state[1] - 1:
                    possible_actions.remove('DOWN')
                if x == state[0] + 1 and y == state[1]:
                    possible_actions.remove('RIGHT')
                if x == state[0] - 1 and y == state[1]:
                    possible_actions.remove('LEFT')

        return possible_actions

    def result(self, state, action):
        """ Given state and action, return a new state that is the result of the action.
        Action is assumed to be a valid action for the state """
        self.agent.direction = action
        new_state = list(state)
        if action == 'RIGHT':
            new_state[0] += 1
        elif action == 'LEFT':
            new_state[0] -= 1
        elif action == 'UP':
            new_state[1] += 1
        elif action == 'DOWN':
            new_state[1] -= 1

        return new_state

    def goal_test(self, state):
        """ Given a state, return True if state is a goal state or False, otherwise """
        return self.env.some_things_at(state, Dirt)

    def path_cost(self, curNode, state1, action, state2):
        beg = 0
        beside = 1
        cost = curNode.path_cost

        if self.env.costFunc == 'Step':
            cost = cost +1

        elif self.env.costFunc == 'StepTurn':
            turnc = self.computeTurnCost(curNode.action, action)
            cost1 = cost +1
            cost = cost1 + turnc

        elif self.env.costFunc == 'StayLeft':
            cost = cost + state2[beg]

        elif self.env.costFunc == 'StayUp':
            newc = cost + 1
            cost = newc + (state2[beside] / len(self.map))


            if self.env.searchType == 'UCS' and action == 'DOWN':
                cost  = cost + 5

        return cost

    def computeTurnCost(self, action1, action):

        directions = ['UP', 'RIGHT', 'DOWN', 'LEFT']

        if action1 not in directions or action not in directions:
            return 0

        index1 = directions.index(action1)
        index2 = directions.index(action)


        tc = abs(index2 - index1)

        val1 = min(tc, 4 - tc) * 3

        return val1

    def distance_manhattan(pos1, pos2):

        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def best_first_graph_search(problem, f=None):

        # Memoize the evaluation function f (if provided) to avoid repeated computations
        f = memoize(f or problem.h, 'f')
        # Initialize the root node
        node = Node(problem.initial)
        # Priority queue (min-heap) for the frontier, sorted by f(n)
        frontier = PriorityQueue('min', f)
        frontier.append(node)
        # Dictionary to track explored states and their best path costs
        explored = {}

        while frontier:
            # Pop the node with the smallest f(n) value
            node = frontier.pop()

            # Debug: Print the current node being expanded
            print(f"Expanding: {node.state}, Path cost (g): {node.path_cost}, "
                  f"Total cost (f): {f(node)}")

            # Check if the current node satisfies the goal condition
            if problem.goal_test(node.state):
                # Return the solution node and all explored states
                return node, list(explored.keys())

            # Add the current node to the explored dictionary with its path cost
            explored[tuple(node.state)] = node.path_cost

            # Expand the current node
            for child in sorted(node.expand(problem), key=lambda c: 0 if c.action == 'LEFT' else 1):
                child_state = tuple(child.state)
                child_cost = child.path_cost

                # Debug: Print child node being added
                print(f"Adding Child: {child.state}, Action: {child.action}, Path Cost: {child_cost}")

                # If the child is unexplored or has a lower path cost than previously found
                if child_state not in explored or child_cost < explored[child_state]:
                    # Add or update the child in the priority queue
                    frontier.append(child)
                    explored[child_state] = child_cost

        # If no solution is found, return None and the list of explored states
        return None, list(explored.keys())

    class VacuumPlanning:
        def __init__(self, env):
            self.env = env

    def findMinManhattanDist(self, pos):
        dirty_rooms = [thing.location for thing in self.env.things if isinstance(thing, Dirt)]

        if not dirty_rooms:
            return 0

        min_distance = float('inf')
        startpow = 0
        beg = 0
        beside = 1

        while startpow < len(dirty_rooms):
            room = dirty_rooms[startpow]
            d1 = abs(pos[beg] - room[beg])
            d2 = abs(pos[beside] - room[beside])
            td = d1 +d2
            if td < min_distance:
                min_distance = td
            startpow += 1

        return min_distance



    def findMinEuclidDist(self, pos):

        dirty_rooms = [thing.location for thing in self.env.things if isinstance(thing, Dirt)]

        if not dirty_rooms:
            return 0

        mind = float('inf')
        index = 0
        start = 0
        beside =1

        while index < len(dirty_rooms):
            room = dirty_rooms[index]
            d1 = (pos[start] - room[start]) ** 2
            d2 = (pos[beside] - room[beside]) ** 2
            d3 = d1 +d2
            if d3 < mind:
                mind = d3
            index += 1

        return mind

    def h(self, node):
        """ Return the heuristic value for a given state. For this problem use minimum Manhattan or Euclid
        distance to a dirty room, among all the dirty rooms.
        """
        if self.env.args['heuristic'] == 'Manhattan':
            heur = self.findMinManhattanDist(node.state)
        else:  ## means Euclid distance
            heur = self.findMinEuclidDist(node.state)

        return heur

# ______________________________________________________________________________


# ______________________________________________________________________________
# Uninformed Search algorithms






#as implemented in notes with deque
def breadth_first_graph_search(problem):

    node = Node(problem.initial)

    #if goals state we shall return it
    if problem.goal_test(node.state):
        return node, [tuple(node.state)]

    #define our frontier and explored as did in slides
    explore = set()

    front = deque([node])
    #while not empty
    while len(front) > 0:
        #remove node
        node = front.popleft()

        explore.add(tuple(node.state))

        actions = problem.actions(node.state)
        for act in actions:

            c = node.child_node(problem, act)

            if not (tuple(c.state) in explore or c in front):
            # if its passes the goal test then return it
                if problem.goal_test(c.state):

                    return c, list(explore)
                #if not then append the child
                front.append(c)

    return None, list(explore)





def depth_first_graph_search(problem):

    node = Node(problem.initial)
    if problem.goal_test(node.state):
        return node, [tuple(node.state)]

    #definitions
    front = [node]
    explore = set()
    #while not empty
    while len(front) > 0:
        node = front.pop()
        explore.add(tuple(node.state))

        actions = problem.actions(node.state)
        for act in actions:
            c = node.child_node(problem, act)

            if not (tuple(c.state) in explore or c in front):
                if problem.goal_test(c.state):
                    return c, list(explore)

                front.append(c)

    return None, list(explore)



#memoize function
def memoize(inp, pos=None):
    if not (pos is None):
        def memoized_fn(obj):
            if pos in dir(obj):
                return getattr(obj, pos)

            v = inp(obj)

            setattr(obj, pos, v)
            return v
    else:
        def memoized_fn(*args):
            if memoized_fn.cache.get(args) is None:

                memoized_fn.cache[args] = inp(*args)

            return memoized_fn.cache[args]

        memoized_fn.cache = {}
    return memoized_fn







def best_first_graph_search(problem, f=None):
    f = memoize(f or problem.h, 'f')
    node = Node(problem.initial)

    front = PriorityQueue('min', f)

    front.append(node)

    explore = set()

    while len(front) > 0:

        node = front.pop()

        if problem.goal_test(node.state):

            return node, explore

        explore.add(tuple(node.state))

        expanded_nodes = node.expand(problem)

        for c in expanded_nodes:

            c_state = tuple(c.state)

            if not (c_state in explore or c in front):

                front.append(c)

            elif c in front and not f(c) >= front[c]:

                del front[c]

                front.append(c)

    return None, explore










def reflexAgentSearch(problem):
    """returns a path to next cell neighboring current location based on a typical reflex agent.
    A reflex agent senses the immediate neighboring cells and it finds a dirty one, move there, otherwise
    move randomly to one of the available left, right, and forward cells."""
    node = Node(problem.state)
    neighbors = node.expand(problem)
    for neigh in neighbors:
        if(problem.goal_test(neigh.state)):
            return neigh, None
    randPic = random.choice(neighbors)
    return randPic, None


def uniform_cost_search(problem):
    """[Figure 3.14]"""
    return best_first_graph_search(problem, lambda node: node.path_cost)


# ______________________________________________________________________________
# Informed (Heuristic) Search


greedy_best_first_graph_search = best_first_graph_search


# Greedy best-first search is accomplished by specifying f(n) = h(n).


def astar_search(problem, h=None):
    """A* search is best-first graph search with f(n) = g(n)+h(n).
    You need to specify the h function when you call astar_search, or
    else in your Problem subclass."""
    h = memoize(h or problem.h, 'h')
    return best_first_graph_search(problem, lambda n: n.path_cost + h(n))

# ______________________________________________________________________________
# ______________________________________________________________________________





