from AIPlayerUtils import *
from GameState import *
from Player import *

import sys
from typing import List, Tuple


class Gene:
    def __init__(self, my_placements: List[Tuple[int, int]]=None,
                 enemy_placements: List[Tuple[int, int]]=None):
        self.NUM_MY_PLACEMENTS = 11
        self.NUM_ENEMY_PLACEMENTS = 2
        self.MUTATION_CHANCE = 0.10

        self.ending_state: GameState = None
        self.total_moves_across_games = 0
        self.games_played = 0
        self.fitness_score = 0  # Equal to the number of games the agent has won.

        self.my_placements = []
        if my_placements:
            # To remove duplicate coordinates
            self.my_placements = list(set(my_placements))
        self.enemy_placements = []
        if enemy_placements:
            # To remove duplicate coordinates
            self.enemy_placements = list(set(enemy_placements))

        self.unused_my_coords = []
        self.unused_enemy_coords = []
        self.init_unused_coords()
        
        self.init_my_placements()
        self.init_enemy_placements()

    def mutate_gene(self) -> None:
        if random.random() <= self.MUTATION_CHANCE:
            placement_to_change = random.choice(self.my_placements + self.enemy_placements)
            if placement_to_change in self.my_placements:
                self.my_placements.remove(placement_to_change)
                self.init_my_placements()
            else:
                self.enemy_placements.remove(placement_to_change)
                self.init_enemy_placements()

    def init_unused_coords(self) -> None:
        for x in range(9):
            for y in range(3):
                if (x, y) not in self.my_placements:
                    self.unused_my_coords.append((x, y))
            for y in range(6, 9):
                if (x, y) not in self.enemy_placements:
                    self.unused_enemy_coords.append((x, y))

    def init_my_placements(self) -> None:
        while len(self.my_placements) != self.NUM_MY_PLACEMENTS:
            self.my_placements.append(self.get_random_unused_my_coord())

    def init_enemy_placements(self) -> None:
        while len(self.enemy_placements) != self.NUM_ENEMY_PLACEMENTS:
            self.enemy_placements.append(self.get_random_unused_enemy_coord())

    def get_random_unused_my_coord(self) -> Tuple[int, int]:
        return self.unused_my_coords.pop(random.randrange(len(self.unused_my_coords)))

    def get_random_unused_enemy_coord(self) -> Tuple[int, int]:
        return self.unused_enemy_coords.pop(random.randrange(len(self.unused_enemy_coords)))


class AIPlayer(Player):
    """
    AIPlayer
    The genetic algorithm agent for CS 421.
    NOTE: 24 hour extension was granted by Dr. Nuxoll (Due Saturday at 11:55 PM)!

    Authors: Alex Hadi and Andrew Ripple
    Date: November 7, 2018
    """

    def __init__(self, input_player_id):
        """
        __init__
        Creates the player for the genetic algorithm agent.

        :param input_player_id: The id to give the new player (int).
        """
        super(AIPlayer, self).__init__(input_player_id, "GeneMaster")

        self.POPULATION_SIZE = 30
        self.GAMES_PER_GENE = 50
        self.NUMBER_OF_GENERATIONS = 30

        self.gene_list: List[Gene] = []
        self.init_gene_list()
        self.current_gene_index = 0
        self.current_gene = self.gene_list[self.current_gene_index]

        self.current_generation = 0
        self.setup_state: GameState = None

    def init_gene_list(self) -> None:
        self.gene_list = []
        while len(self.gene_list) != self.POPULATION_SIZE:
            self.gene_list.append(Gene())

    def coord_with_construction(self, current_state: GameState,
                                coordinate_list: List[Tuple[int, int]]) -> Tuple[int, int]:
        for coordinate in coordinate_list:
            if current_state.board[coordinate[0]][coordinate[1]].constr is not None:
                return coordinate

    def check_enemy_placements(self, current_state: GameState) -> None:
        coord = self.coord_with_construction(current_state, self.current_gene.enemy_placements)
        while coord:
            self.current_gene.enemy_placements.remove(coord)
            self.current_gene.init_enemy_placements()

            # Reset coordinate to check if all placements are now good.
            coord = self.coord_with_construction(current_state, self.current_gene.enemy_placements)

    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    # Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    # Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, current_state: GameState) -> List[Tuple[int, int]]:
        if current_state.phase == SETUP_PHASE_1:
            return self.current_gene.my_placements
        elif current_state.phase == SETUP_PHASE_2:
            self.check_enemy_placements(current_state)
            return self.current_gene.enemy_placements

    ##
    # getMove
    # Description: Gets the next move from the Player.
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: The Move to be made
    ##
    def getMove(self, current_state: GameState) -> Move:
        self.current_gene.total_moves_across_games += 1
        moves = listAllLegalMoves(current_state)
        selected_move = moves[random.randint(0, len(moves) - 1)]

        # don't do a build move if there are already 3+ ants
        num_ants = len(current_state.inventories[current_state.whoseTurn].ants)
        while selected_move.moveType == BUILD and num_ants >= 3:
            selected_move = moves[random.randint(0, len(moves) - 1)]

        if current_state.phase == PLAY_PHASE:
            self.setup_state = current_state

        return selected_move

    def mate_genes(self, first_parent: Gene, second_parent: Gene) -> List[Gene]:
        my_placements_crossover = int(random.randrange(first_parent.NUM_MY_PLACEMENTS))
        first_parent_my_placements = first_parent.my_placements
        second_parent_my_placements = second_parent.my_placements

        first_child_my_placements = first_parent_my_placements[:my_placements_crossover]
        first_child_my_placements += second_parent_my_placements[my_placements_crossover:]
        second_child_my_placements = first_parent_my_placements[my_placements_crossover:]
        second_child_my_placements += second_parent_my_placements[:my_placements_crossover]

        enemy_placements_crossover = int(first_parent.NUM_ENEMY_PLACEMENTS / 2)
        first_parent_enemy_placements = first_parent.enemy_placements
        second_parent_enemy_placements = second_parent.enemy_placements

        first_child_enemy_placements = first_parent_enemy_placements[:enemy_placements_crossover]
        first_child_enemy_placements += second_parent_enemy_placements[enemy_placements_crossover:]
        second_child_enemy_placements = first_parent_enemy_placements[enemy_placements_crossover:]
        second_child_enemy_placements += second_parent_enemy_placements[:enemy_placements_crossover]

        first_child = Gene(first_child_my_placements, first_child_enemy_placements)
        first_child.mutate_gene()

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
