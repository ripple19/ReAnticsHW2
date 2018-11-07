import random
from Player import *
from GameState import *
from AIPlayerUtils import *
from typing import List, Tuple


class Gene:
    def __init__(self, my_placements: List[Tuple[int, int]]=None,
                 enemy_placements: List[Tuple[int, int]]=None):
        self.NUM_MY_PLACEMENTS = 11
        self.NUM_ENEMY_PLACEMENTS = 2

        self._init_unused_coords()

        self.my_placements: List[Tuple[int, int]] = []
        if my_placements:
            # To remove duplicate coordinates
            self.my_placements = list(set(my_placements))
        self._init_my_placements()

        self.enemy_placements: List[Tuple[int, int]] = []
        if enemy_placements:
            # To remove duplicate coordinates
            self.enemy_placements = list(set(enemy_placements))
        self.init_enemy_placements()

    def mutate_gene(self) -> None:
        MUTATION_CHANCE = 0.02
        if random.random() <= MUTATION_CHANCE:
            placement_to_change = random.choice(self.my_placements + self.enemy_placements)
            if placement_to_change in self.my_placements:
                self.my_placements.remove(placement_to_change)
                self._init_my_placements()
            else:
                self.enemy_placements.remove(placement_to_change)
                self.init_enemy_placements()

    def _init_unused_coords(self) -> None:
        self.unused_my_coords: List[Tuple[int, int]] = []
        self.unused_enemy_coords: List[Tuple[int, int]] = []
        for x in range(9):
            for y in range(3):
                self.unused_my_coords.append((x, y))
            for y in range(6, 9):
                self.unused_enemy_coords.append((x, y))

    def _init_my_placements(self) -> None:
        while len(self.my_placements) != self.NUM_MY_PLACEMENTS:
            self.my_placements.append(self._get_random_unused_my_coord())

    def init_enemy_placements(self) -> None:
        while len(self.enemy_placements) != self.NUM_ENEMY_PLACEMENTS:
            self.enemy_placements.append(self._get_random_unused_enemy_coord())

    def _get_random_unused_my_coord(self) -> Tuple[int, int]:
        return self.unused_my_coords.pop(random.randrange(len(self.unused_my_coords)))

    def _get_random_unused_enemy_coord(self) -> Tuple[int, int]:
        return self.unused_enemy_coords.pop(random.randrange(len(self.unused_enemy_coords)))


##
# AIPlayer
# Description: The responsibility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course.
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):
    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, input_player_id):
        super(AIPlayer, self).__init__(input_player_id, "GeneMaster")
        self.POPULATION_SIZE = 30
        self.GAMES_PER_GENE = 50
        self.NUMBER_OF_GENERATIONS = 20

        self.gene_list: List[Gene] = []
        self.gene_index: int = 0

        self._init_gene_list()

    def _init_gene_list(self) -> None:
        self.gene_list = []
        while len(self.gene_list) != self.POPULATION_SIZE:
            self.gene_list.append(Gene())

    def _index_with_construction(self, current_state: GameState,
                                 coordinate_list: List[Tuple[int, int]]) -> int:
        for index, coordinate in enumerate(coordinate_list):
            if current_state.board[coordinate[0]][coordinate[1]].constr is not None:
                return index
        return -1

    def _check_enemy_placements(self, current_state: GameState) -> None:
        current_gene = self.gene_list[self.gene_index]

        index = self._index_with_construction(current_state, current_gene.enemy_placements)
        while index != -1:
            current_gene.enemy_placements.pop(index)
            current_gene.init_enemy_placements()

            # Reset index to check if all placements are now good.
            index = self._index_with_construction(current_state, current_gene.enemy_placements)

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
        current_gene = self.gene_list[self.gene_index]
        if current_state.phase == SETUP_PHASE_1:
            return current_gene.my_placements
        elif current_state.phase == SETUP_PHASE_2:
            self._check_enemy_placements(current_state)
            return current_gene.enemy_placements

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
        moves = listAllLegalMoves(current_state)
        selected_move = moves[random.randint(0, len(moves) - 1)]

        # don't do a build move if there are already 3+ ants
        num_ants = len(current_state.inventories[current_state.whoseTurn].ants)
        while selected_move.moveType == BUILD and num_ants >= 3:
            selected_move = moves[random.randint(0, len(moves) - 1)]

        return selected_move

    def mate_genes(self, first_parent: Gene, second_parent: Gene) -> List[Gene]:
        crossover = random.randint(0, len(first_parent.coordinate_scores))

        first_parent_item_list = list(first_parent.coordinate_scores.items())
        second_parent_item_list = list(second_parent.coordinate_scores.items())

        first_child_coord_scores_dict = dict(first_parent_item_list[:crossover])
        first_child_coord_scores_dict.update(dict(second_parent_item_list[crossover:]))

        second_child_coord_scores_dict = dict(first_parent_item_list[crossover:])
        second_child_coord_scores_dict.update(dict(second_parent_item_list[:crossover]))

        children = [Gene(first_child_coord_scores_dict), Gene(second_child_coord_scores_dict)]
        children[0] = self.mutate_gene(children[0])
        children[1] = self.mutate_gene(children[1])

        return children

    ##
    # getAttack
    # Description: Gets the attack to be made from the Player
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        # Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    # registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        # method templaste, not implemented
        pass

    def registerWin(self, hasWon):
        # self.currentGene.fitness = fitnesstest(self.currentGene.dna)
        # Add current fitness score to the average fitness score. (Divide by number of games after done)
        # if number of games is past a current number, then were good.
        # Check to see if there are more genees. If so, advance to next gene.
        # If we are out of genes in this pop, then create a new population. Reset our index to start.
        # Update our list of genes to the new one, start playing again.
        # Else, we want to keep testing this gene, play again.
        pass

    # Method to take two parents from the gene population and
    # create two children. Will call the fitness function to figure out which is best.
    def createNewPopulation(self, firstGene, secondGene):
        pass

    def nextGeneration(self, listOfGenes):
        lowFitness = 0
        fitGenes = None
        for gene in listOfGenes:
            if gene.fitness > lowFitness:
                fitGenes.add(gene)

                # Need to flush out the original gene list
                # Call gene function that mates two parents. mate(gene1, gene2)
                # Return two new child genes. Add them to the new gene list.
                # Set new generation to be the actual gene list.

    def fitnessTest(self, gene):
        pass
