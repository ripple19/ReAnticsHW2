from AIPlayerUtils import *
from GameState import *
from Player import *

import sys
from typing import List, Tuple


class Gene:
    """
    Gene
    A gene for the genetic algorithm.
    NOTE: 24 hour extension was granted by Dr. Nuxoll (Due Saturday at 11:55 PM)!

    Authors: Alex Hadi and Andrew Ripple
    Date: November 9, 2018
    """

    def __init__(self, my_placements: List[Tuple[int, int]]=None,
                 enemy_placements: List[Tuple[int, int]]=None):
        """
        __init__
        Creates a gene.

        :param my_placements: List of coordinates for placements of anthill, tunnel, and grass.
        :param enemy_placements: List of coordinates for placements of enemy food.
        """

        # Constants pertaining to a gene.
        self.NUM_MY_PLACEMENTS = 11
        self.NUM_ENEMY_PLACEMENTS = 2
        self.MUTATION_CHANCE = 0.10

        # Useful variables for the fitness_test calculation.
        self.ending_state: GameState = None
        self.total_moves_across_games = 0
        self.games_played = 0
        self.fitness_score = 0  # Equal to the number of games the agent has won.

        # Initialize the placements for the the anthill, tunnel, and grass.
        self.my_placements = []
        if my_placements:
            # To remove duplicate coordinates (if passing a parent list).
            self.my_placements = list(set(my_placements))

        # Initialize the placements for the enemy food.
        self.enemy_placements = []
        if enemy_placements:
            # To remove duplicate coordinates
            self.enemy_placements = list(set(enemy_placements))

        # Initialize the unused coordinates.
        self.unused_my_coords = []
        self.unused_enemy_coords = []
        self.init_unused_coords()

        # Add coordinates to the lists if needed
        # (only happens when duplicates were passed in as input).
        self.init_my_placements()
        self.init_enemy_placements()

    def mutate_gene(self) -> None:
        """
        Generates a random number.
        If it matches the given set probability (MUTATION_CHANCE), mutate the gene.
        """

        if random.random() <= self.MUTATION_CHANCE:
            # Selects any placement with equal probability.
            placement_to_change = random.choice(self.my_placements + self.enemy_placements)

            # Checks which list the placement coordinate was in.
            if placement_to_change in self.my_placements:
                self.my_placements.remove(placement_to_change)
                self.init_my_placements()
            else:
                self.enemy_placements.remove(placement_to_change)
                self.init_enemy_placements()

    def init_unused_coords(self) -> None:
        """
        init_unused_coords
        Initializes the lists of unused coordinates.
        """

        # Both players have the same x coordinates.
        for x in range(9):
            # y coordinates on my side of the board.
            for y in range(3):
                if (x, y) not in self.my_placements:
                    self.unused_my_coords.append((x, y))
            # y coordinates on the opponent's side of the board.
            for y in range(6, 9):
                if (x, y) not in self.enemy_placements:
                    self.unused_enemy_coords.append((x, y))

    def init_my_placements(self) -> None:
        """
        init_my_placements
        Appends enough unused coordinates to the list until the list is of proper size.
        """
        while len(self.my_placements) != self.NUM_MY_PLACEMENTS:
            self.my_placements.append(self.get_random_unused_my_coord())

    def init_enemy_placements(self) -> None:
        """
        init_enemy_placements
        Appends enough unused coordinates to the list until the list is of proper size.
        """
        while len(self.enemy_placements) != self.NUM_ENEMY_PLACEMENTS:
            self.enemy_placements.append(self.get_random_unused_enemy_coord())

    def get_random_unused_my_coord(self) -> Tuple[int, int]:
        """
        get_random_unused_my_coord
        Helper method to select an unused coordinate at random.

        :return: The unused coordinate.
        """
        return self.unused_my_coords.pop(random.randrange(len(self.unused_my_coords)))

    def get_random_unused_enemy_coord(self) -> Tuple[int, int]:
        """
        get_random_unused_enemy_coord
        Helper method to select an unused coordinate at random.

        :return: The unused coordinate.
        """
        return self.unused_enemy_coords.pop(random.randrange(len(self.unused_enemy_coords)))


class AIPlayer(Player):
    """
    AIPlayer
    The genetic algorithm agent for CS 421.
    NOTE: 24 hour extension was granted by Dr. Nuxoll (Due Saturday at 11:55 PM)!

    Authors: Alex Hadi and Andrew Ripple
    Date: November 9, 2018
    """

    def __init__(self, input_player_id):
        """
        __init__
        Creates the player for the genetic algorithm agent.

        :param input_player_id: The id to give the new player (int).
        """

        super(AIPlayer, self).__init__(input_player_id, "GeneMaster")

        # Constants relating to the amounts of genes.
        self.POPULATION_SIZE = 30
        self.GAMES_PER_GENE = 50
        self.NUMBER_OF_GENERATIONS = 30

        # Create the initial gene list and set the current gene & its index.
        self.gene_list: List[Gene] = []
        self.init_gene_list()
        self.current_gene_index = 0
        self.current_gene = self.gene_list[self.current_gene_index]

        # Set the current generation and instance variable to keep track of the GameState.
        self.current_generation = 0
        self.setup_state: GameState = None

    def init_gene_list(self) -> None:
        """
        init_gene_list
        Initializes the gene list to the proper population size.
        """

        self.gene_list = []
        while len(self.gene_list) != self.POPULATION_SIZE:
            self.gene_list.append(Gene())

    def coord_with_construction(self, current_state: GameState,
                                coordinate_list: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        coord_with_construction
        Helper function that finds a coordinate that has a Construction in it (or returns None).

        :param current_state: The current state of the game (GameState).
        :param coordinate_list: The list of coordinates to check.
        :return: The coordinate that has a Construction on it (or nothing).
        """

        for coordinate in coordinate_list:
            if current_state.board[coordinate[0]][coordinate[1]].constr is not None:
                return coordinate

    def check_enemy_placements(self, current_state: GameState) -> None:
        """
        check_enemy_placements
        Helper method that checks the enemy food placements & replaces some coordinates if needed.

        :param current_state: The current state of the game (GameState).
        """

        # Check coordinates with helper function.
        coord = self.coord_with_construction(current_state, self.current_gene.enemy_placements)
        while coord:
            # Remove the given coordinate and replace it.
            self.current_gene.enemy_placements.remove(coord)
            self.current_gene.init_enemy_placements()

            # Reset coordinate to check if all placements are now good.
            coord = self.coord_with_construction(current_state, self.current_gene.enemy_placements)

    def getPlacement(self, current_state: GameState) -> List[Tuple[int, int]]:
        """
        getPlacement
        Called during the setup phase for each Construction that must be placed by the player.
        These items are: 1 Anthill on the player's side, 1 tunnel on player's side,
        9 grass on the player's side, and 2 food on the enemy's side.

        :param current_state: The current state of the game (GameState).
        :return: The coordinates of where the construction is to be placed.
        """

        if current_state.phase == SETUP_PHASE_1:
            return self.current_gene.my_placements
        elif current_state.phase == SETUP_PHASE_2:
            # Checks to make sure enemy food placements are valid.
            self.check_enemy_placements(current_state)
            return self.current_gene.enemy_placements

    def getMove(self, current_state: GameState) -> Move:
        """
        getMove
        Gets the next move from the Player.

        :param current_state: The state of the current game waiting for the Player's move.
        :return: The Move to be made.
        """

        # Increment the amount of moves.
        self.current_gene.total_moves_across_games += 1

        # Randomly select a move.
        moves = listAllLegalMoves(current_state)
        selected_move = moves[random.randint(0, len(moves) - 1)]

        # Don't do a build move if there are already 3+ ants
        num_ants = len(current_state.inventories[current_state.whoseTurn].ants)
        while selected_move.moveType == BUILD and num_ants >= 3:
            selected_move = moves[random.randint(0, len(moves) - 1)]

        # Set the current state to an instance variable (if currently playing a game).
        if current_state.phase == PLAY_PHASE:
            self.setup_state = current_state

        return selected_move

    def mate_genes(self, first_parent: Gene, second_parent: Gene) -> List[Gene]:
        """
        mate_genes
        Mates two parent genes and creates two children genes.

        :param first_parent: The first parent Gene.
        :param second_parent: The second parent Gene.
        :return: The two children as a list of genes.
        """

        # Gets a random crossover point for the placements of the anthill, tunnel, and grass.
        my_placements_crossover = int(random.randrange(first_parent.NUM_MY_PLACEMENTS))

        # Get the parent lists for the placements of the anthill, tunnel, and grass.
        first_parent_my_placements = first_parent.my_placements
        second_parent_my_placements = second_parent.my_placements

        # Creates the children lists for the placements of the anthill, tunnel, and grass.
        first_child_my_placements = first_parent_my_placements[:my_placements_crossover]
        first_child_my_placements += second_parent_my_placements[my_placements_crossover:]
        second_child_my_placements = first_parent_my_placements[my_placements_crossover:]
        second_child_my_placements += second_parent_my_placements[:my_placements_crossover]

        # Sets the crossover point to the midpoint for the placements of the food.
        enemy_placements_crossover = int(first_parent.NUM_ENEMY_PLACEMENTS / 2)
        first_parent_enemy_placements = first_parent.enemy_placements
        second_parent_enemy_placements = second_parent.enemy_placements

        # Creates the children lists for the placements of the food.
        first_child_enemy_placements = first_parent_enemy_placements[:enemy_placements_crossover]
        first_child_enemy_placements += second_parent_enemy_placements[enemy_placements_crossover:]
        second_child_enemy_placements = first_parent_enemy_placements[enemy_placements_crossover:]
        second_child_enemy_placements += second_parent_enemy_placements[:enemy_placements_crossover]

        # Create and mutate (if the proper random number was generated) the first child.
        first_child = Gene(first_child_my_placements, first_child_enemy_placements)
        first_child.mutate_gene()

        # Create and mutate (if the proper random number was generated) the second child.
        second_child = Gene(second_child_my_placements, second_child_enemy_placements)
        second_child.mutate_gene()

        return [first_child, second_child]

    def getAttack(self, current_state, attacking_ant, enemy_locations):
        """
        getAttack
        Gets the attack to be made from the Player.

        :param current_state: The current state (GameState).
        :param attacking_ant: The ant currently making the attack (Ant).
        :param enemy_locations: The Locations of the enemies that can be attacked (Location[])
        :return: The attack to perform.
        """

        # Attack a random enemy.
        return enemy_locations[random.randint(0, len(enemy_locations) - 1)]

    def registerWin(self, has_won: bool) -> None:
        """
        registerWin
        Called when the agent wins or loses.

        :param has_won: True if the agent won (otherwise False).
        """

        # Sets the GameState and evaluates its fitness score.
        current_state = self.setup_state
        self.current_gene.ending_state = current_state
        self.fitness_test(self.current_gene, current_state, has_won)  # Set the fitness of the gene.
        self.current_gene.games_played += 1

        # Once the amount of games played has been reached, change the gene being evaluated.
        if self.current_gene.games_played == self.GAMES_PER_GENE:
            self.current_gene.fitness_score = self.current_gene.fitness_score / self.GAMES_PER_GENE

            # Then, we need to create the next generation.
            if self.current_gene_index == self.POPULATION_SIZE - 1:
                self.print_ascii(self.gene_list)
                self.gene_list = self.get_next_generation(self.gene_list)

                self.current_gene_index = 0
                self.current_gene = self.gene_list[self.current_gene_index]
                self.current_generation += 1
            # Otherwise, need to just change the gene in the current generation.
            else:
                self.current_gene_index += 1
                self.current_gene = self.gene_list[self.current_gene_index]

    def get_next_generation(self, gene_list: List[Gene]) -> List[Gene]:
        """
        get_next_generation
        Gets the next generation of genes.

        :param gene_list: The list of genes to use as parent genes.
        :return: The next generation as a list of genes.
        """

        # Sorts the input gene list in descending order by fitness score.
        gene_list.sort(key=lambda gene: gene.fitness_score, reverse=True)

        # Gets the best genes and copies them throughout the list.
        best_gene_list = gene_list[:int(self.POPULATION_SIZE / 3)]
        best_gene_list *= int(self.POPULATION_SIZE / len(best_gene_list))

        new_generation = []
        # Continue adding to the new generation until it reaches the proper size.
        while len(new_generation) != self.POPULATION_SIZE:
            # Call gene function that mates two parents.
            # Return list of two new child genes. Add them to the new gene list.
            new_generation += self.mate_genes(best_gene_list.pop(0), best_gene_list.pop(0))
        return new_generation

    def fitness_test(self, gene: Gene, current_state: GameState, has_won: bool) -> None:
        """
        fitness_test
        Sets the fitness score for a gene with a given state.

        :param gene: The gene to evaluate.
        :param current_state: The GameState to evaluate.
        :param has_won: True if agent won, otherwise False.
        """

        # Gets the agent's food count.
        my_food_count = getCurrPlayerInventory(current_state).foodCount
        gene.fitness_score += my_food_count

        # Gets the move weight.
        move_weight = gene.total_moves_across_games / 100
        gene.fitness_score += move_weight

        # Reward the agent significantly for winning.
        if has_won:
            gene.fitness_score += 30

    def print_ascii(self, gene_list: List[Gene]) -> None:
        """
        print_ascii
        Prints the ending state from the best gene (by fitness score) using asciiPrintState.

        :param gene_list: The list of genes.
        """

        # Gets the maximum scoring gene.
        best_gene = max(gene_list, key=lambda gene: gene.fitness_score)
        with open("evidence_file.txt", "a") as file:
            sys.stdout = file
            asciiPrintState(best_gene.ending_state)
            print("\n")
        # Reset sys.stdout to default value.
        sys.stdout = sys.__stdout__
