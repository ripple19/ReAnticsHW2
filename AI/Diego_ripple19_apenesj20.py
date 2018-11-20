import random
import math
import sys
sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
from random import shuffle

##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course. 
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):
    INPUTS = 10
    NODES = 20

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Max")
        self.depth_limit = 3
        self.me = 0
        self.move = None
        self.nextMove = None
        self.prunedMoves = 0
        self.alpha = 0.7
        self.currentNeuralOutput = 0
        self.currentEvalOutput = 0
        self.currentError = self.currentEvalOutput - self.currentNeuralOutput
        self.biases = [] #Needed to incorporate this in.
        self.inputWeights = []  # 2D array
        self.outputWeights = [] # 1D array
        self.hiddenValues = [0] * self.NODES
        self.initializeNetwork()


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
    def getPlacement(self, currentState):
        numToPlace = 0
        # implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    # stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   # stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    # getMove
    # Description: Gets the next move from the Player.
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: The Move to be made
    ##
    def getMove(self, currentState):
        self.me = currentState.whoseTurn
        # rotate to the next move
        self.move = self.nextMove
        # set number of pruned nodes to zero
        self.prunedMoves = 0
        # if the list of moves is empty or move holds an enemy move, do minimax()
        if self.move is None or self.move["minmax"] == -1:
            root = {"move": None, "state": currentState, "value": 0, "min": -1000, "max": 1000, "parent": None, "depth": 0,
                    "minmax": 1, "next-move": None}
            # root has no move associated with it so automatically update self.move to minimax["next-move"]
            self.move = self.minimax(root, 0)["next-move"]
            # if minimax returns no moves, do an end move
            if self.move is None:
                self.nextMove = None  # done so the code at the start of getMove work
                return Move(END, None, None)
            else:
                self.nextMove = self.move["next-move"]
        else:
            # so move is not None AND move is our move
            self.nextMove = self.move["next-move"]
        # if you want the number of pruned moves to be printed, use the two lines below
        # if self.prunedMoves != 0:
        #    print("Pruned ", self.prunedMoves, " moves")
        return self.move["move"]

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
    # however we need to reset global variables
    #
    def registerWin(self, hasWon):
        # reset these variables so it does not interfere with the next game
        self.move = None
        self.nextMove = None 
        pass

    ##
    # evaluateState
    #
    # This agent evaluates the state and returns a double between -1.0 and 1.0
    #
    def evaluateState(self, currentState):
        me = self.me
        # If we win or lose, just return the right value straight away
        if getWinner(currentState) == 1:
            return 1
        elif getWinner(currentState) == 0:
            return -1
        # Get the different inventories
        myInventory = currentState.inventories[me]
        enemyInventory = currentState.inventories[1-me]
        neutralInventory = currentState.inventories[2] 
        # Queen should stay around the anthill
        ourQueen = getAntList(currentState, me, types=(QUEEN,))
        queenAroundAnthill = 20
        if len(ourQueen) == 1:
            ourAnthillCoords = myInventory.getAnthill().coords
            queenAroundAnthill = max(approxDist(ourQueen[0].coords, ourAnthillCoords),2)
        # Never get more than 3 ants
        ourAnts = getAntList(currentState, me, types=(QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER))
        if len(ourAnts) == 4:
            return -1
        # One worker is more than enough. Highest priority ant.
        workers = getAntList(currentState, me, types=(WORKER, WORKER))
        if len(workers) == 1:
            worker = 1
        else:
            worker = 0
        # One ranged soldier is more than enough. Priority one below the worker.
        rSoldiers = getAntList(currentState, me, types=(R_SOLDIER, R_SOLDIER))
        if len(rSoldiers) == 1:
            rSoldier = 1
        else:
            rSoldier = 0
        # If we have an r soldier make sure it attacks a worker or goes to the opponent's queen
        rSoldierDistance = 20
        enemyQueen = getAntList(currentState, 1-me, types=(QUEEN,))
        if rSoldier:
            enemyWorkers = getAntList(currentState, 1-me, types=(WORKER, WORKER))
            if enemyWorkers:
                rSoldierDistance = approxDist(rSoldiers[0].coords, enemyWorkers[0].coords)
            else: 
                if len(enemyQueen) == 1: # Just to double check we actually have a queen
                    enemyQueenCoords = enemyQueen[0].coords
                    rSoldierDistance = abs(approxDist(rSoldiers[0].coords, enemyQueenCoords)-3)
                else:
                    return 1
        # Make sure the worker goes to get food and gets it back to the tunnel
        foodDistance = 20
        # Incentivize carrying food
        carrying = 0
        if worker:
            if workers[0].carrying:
                carrying = 1
            constrs = neutralInventory.constrs
            foodCoords = (0,0)
            if carrying == 0: # Compute distance to food if not carrying
                for construction in constrs:
                    if construction.type == FOOD:
                        foodCoords = construction.coords
                        newDistance = approxDist(workers[0].coords, foodCoords)
                        if newDistance <= foodDistance:
                            foodDistance = newDistance
            else:  # Compute distance to tunnel if carrying
                myTunnelCoords = myInventory.getTunnels()[0].coords
                foodDistance = approxDist(workers[0].coords, myTunnelCoords)
        # Enemy queen health is also important
        enemyQueenHealth = 0
        if len(enemyQueen) == 1:
            enemyQueenHealth = enemyQueen[0].health
        # Get food and enemy ant number
        ourFoodNumber = myInventory.foodCount
        enemyAntNumber = len(enemyInventory.ants)
        enemyFoodNumber = enemyInventory.foodCount
        ourPoints = 5*worker + 4*rSoldier + 2*ourFoodNumber + carrying \
            + 1/(rSoldierDistance+1) + 0.5/(foodDistance+1) + 0.25/(queenAroundAnthill)
        enemyPoints = 3*enemyFoodNumber + 2*enemyAntNumber + enemyQueenHealth
        # This makes sure the value is always between -1 and 1
        value = (ourPoints - enemyPoints) / (ourPoints + enemyPoints) 
        return value

    ##
    # expandNode
    #
    # This function takes a node (dictionary) as input finds all the legal moves from that state
    # and creates a list of new node with states resulting from each of those nodes and returns that list
    #
    def expandNode(self, node):
        moves = listAllLegalMoves(node["state"])
        states = []
        for move in moves:
            newNode = {"move":move}
            newNode["state"] = self.getNextStateAdversarial(node["state"], newNode["move"])
            newNode["value"] = 0
            newNode["min"] = node["min"]
            newNode["max"] = node["max"]
            newNode["parent"] = node
            newNode["depth"] = node["depth"]+1
            if move.moveType == END:
                newNode["minmax"] = -1 * node["minmax"]
            else:
                newNode["minmax"] = node["minmax"]
            newNode["next-move"] = None
            states.append(newNode)
        return states

    ##
    # evalListNodes
    #
    # This function takes a list of nodes and takes the best node dependent on 
    # the move being a min or max move. If a node has a "minmax" of 1 it is a max move,
    # if a node has a "minmax" of -1 it is a min move.
    #
    def evalListNodes(self, nodes):
        if nodes and len(nodes) > 1:
            randomNode = nodes[0]
            if randomNode["minmax"] == 1: 
                bestNodeValue = -1
                for node in nodes:
                    if node["value"] >= bestNodeValue:
                        bestNodeValue = node["value"]
            elif randomNode["minmax"] == -1: 
                bestNodeValue = 1
                for node in nodes:
                    if node["value"] <= bestNodeValue:
                        bestNodeValue = node["value"]
            return bestNodeValue
        elif nodes:
            return nodes[0]["value"]
        else:
            return -1


    ##
    # minimax
    #
    # This function preforms minimax search
    # It takes a node and the depth
    # The nodes are expanded until the depth limit is reached
    # Then the values of the nodes are propagated up based on being the best min or max move
    # The method returns a node that contains a sequence of moves (when depth == 0)
    # This assumes both players are rational
    # Alpha-beta pruning is used to make this process faster by pruning nodes that for certain
    # do not hold better outcomes
    #
    def minimax(self, node, depth):
        newNodes = self.expandNode(node)
        shuffle(newNodes)
        # create pruning counter to see how many nodes get pruned
        counter = 0
        # it is depth + 1 since we just expanded the node and are
        # now evaluating nodes at depth + 1
        if depth+1 < self.depth_limit:
            # if the next set of nodes are inside the depth limit,
            for n in newNodes:
                # !!! update neural network heruistic !!!
                # increment pruning counter
                counter += 1
                # update the bounds of each newNode since a previous newNode could have updated node's bounds
                n["min"] = node["min"]
                n["max"] = node["max"]
                # minimax updates the min and max bounds of the parent node, not the children
                if node["minmax"] == 1:                   
                    temp = node["min"]  # used so we don't do minimax() twice
                    node["min"] = max(self.minimax(n, depth+1), node["min"])
                    # if the value was updated, update the next-move value to n
                    if temp != node["min"]:
                        node["next-move"] = n
                    # if the bounds cross each other, prune remaining nodes
                    # if min bound equals 1, just return it
                    if node["min"] > node["max"] or node["min"] == 1: 
                        # updated global variable
                        self.prunedMoves += len(newNodes) - counter
                        if depth == 0:
                            return node
                        else: 
                            return node["min"]
                else: # here the same happens for "minmax" == -1
                    temp = node["max"]
                    node["max"] = min(self.minimax(n, depth+1), node["max"])
                    if temp != node["max"]:
                        node["next-move"] = n
                    if node["min"] > node["max"]:
                        self.prunedMoves += len(newNodes) - counter
                        if depth == 0:
                            return node
                        else:
                            return node["max"]
        else:
            # else find the best value for min/max
            for n in newNodes:
                # !!! update neural network heuristic !!!
                # increment pruning counter
                counter += 1
                if node["minmax"] == 1:
                    temp = node["min"]
                    node["min"] = max(self.evaluateState(n["state"]), node["min"])
                    # if the bounds cross each other, prune remaining nodes
                    if node["min"] > node["max"]:
                        self.prunedMoves += len(newNodes) - counter
                        return node["min"]
                    # if the value was updated, update the next-move value to n
                    if temp != node["min"]:
                        node["next-move"] = n
                    if node["min"] == 1:
                        return node["min"]
                else: # here the same happens for "minmax" == -1
                    temp = node["max"]
                    node["max"] = min(self.evaluateState(n["state"]), node["max"])
                    if node["min"] > node["max"]:
                        self.prunedMoves += len(newNodes) - counter
                        return node["max"]
                    # if the value was updated, update the next-move value to n
                    if temp != node["max"]:
                        node["next-move"] = n
        # if we are not at depth 0 we return a value, otherwise we return a node
        if depth > 0:
            if node["minmax"] == 1:
                return node["min"]
            else:
                return node["max"]
        else:
            # when we've finished minimax, return the root node with all the updated values
            return node

    ##
    # getStateInputs
    # FOR NEURAL NETWORKS
    # takes in a GameState and outputs an array of values that are related to the minimax fitness function
    # all values in the array range from -1 to 1
    ##

    def getStateInputs(self, currentState):
        inputs = []
        me = self.me
        # If we win or lose, just return the right value straight away
        if getWinner(currentState) == 1:
            inputs.append(1)
        elif getWinner(currentState) == 0:
            inputs.append(-1)
        else:
            inputs.append(0)
        # Get the different inventories
        myInventory = currentState.inventories[me]
        enemyInventory = currentState.inventories[1 - me]
        neutralInventory = currentState.inventories[2]
        # Queen distance from anthill
        ourQueen = getAntList(currentState, me, types=(QUEEN,))
        queenAroundAnthill = 20
        if len(ourQueen) == 1:
            ourAnthillCoords = myInventory.getAnthill().coords
            queenAroundAnthill = max(approxDist(ourQueen[0].coords, ourAnthillCoords), 2)
            inputs.append(1/queenAroundAnthill)
        # Do we have 3 ants?
        ourAnts = getAntList(currentState, me, types=(QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER))
        if len(ourAnts) == 3:
            inputs.append(1)
        else:
            inputs.append(0)
        # Do we have only one worker?
        workers = getAntList(currentState, me, types=(WORKER, WORKER))
        if len(workers) == 1:
            inputs.append(1)
            worker = 1
        else:
            inputs.append(0)
            worker = 0
        # Do we only have one ranged soldier?
        rSoldiers = getAntList(currentState, me, types=(R_SOLDIER, R_SOLDIER))
        if len(rSoldiers) == 1:
            inputs.append(1)
            rSoldier = 1
        else:
            inputs.append(0)
            rSoldier = 0
        # How close is the ranged soldier to the enemy ants (workers, then queen)
        rSoldierDistance = 20
        enemyQueen = getAntList(currentState, 1 - me, types=(QUEEN,))
        if rSoldier:
            enemyWorkers = getAntList(currentState, 1 - me, types=(WORKER, WORKER))
            if enemyWorkers:
                rSoldierDistance = approxDist(rSoldiers[0].coords, enemyWorkers[0].coords)
            else:
                if len(enemyQueen) == 1:  # Just to double check we actually have a queen
                    enemyQueenCoords = enemyQueen[0].coords
                    rSoldierDistance = abs(approxDist(rSoldiers[0].coords, enemyQueenCoords) - 3)
                else:
                    rSoldierDistance = 0
        inputs.append(1/(rSoldierDistance+1))
        # How close is the worker to the food/tunnel
        foodDistance = 20
        # Incentivize carrying food
        carrying = 0
        if worker:
            if workers[0].carrying:
                carrying = 1
            constrs = neutralInventory.constrs
            foodCoords = (0, 0)
            if carrying == 0:  # Compute distance to food if not carrying
                for construction in constrs:
                    if construction.type == FOOD:
                        foodCoords = construction.coords
                        newDistance = approxDist(workers[0].coords, foodCoords)
                        if newDistance <= foodDistance:
                            foodDistance = newDistance
            else:  # Compute distance to tunnel if carrying
                myTunnelCoords = myInventory.getTunnels()[0].coords
                foodDistance = approxDist(workers[0].coords, myTunnelCoords)
        inputs.append(1/(foodDistance+1))
        # Enemy queen health is also important
        if len(enemyQueen) == 1:
            inputs.append(enemyQueen[0].health/10)
        else:
            inputs.append(0)
        # Get food difference
        ourFoodNumber = myInventory.foodCount
        enemyFoodNumber = enemyInventory.foodCount
        inputs.append(((2*ourFoodNumber+carrying)-(3*enemyFoodNumber))/((2*ourFoodNumber+carrying)+(3*enemyFoodNumber)))
        # Get enemy ant count (for some unknown reason)
        inputs.append(min(len(enemyInventory.ants), 4)/4)
        return inputs

    ##
    # initializeNetwork()
    # FOR NEURAL NETWORKS
    # Sets initial weights to random values between -1 and 1
    # -1 and 1 is a random range. It may have a wider range in the future
    ##

    def initializeNetwork(self):
        # reset weights (if necessary)
        self.inputWeights = []
        self.outputWeights = [0] * self.NODES
        weights = [0] * self.INPUTS
        for i in range(0, self.NODES):
            # get random values for a set of weights that attach to a single hidden node
            for j in range(0, self.INPUTS):
                weights[j] = random.uniform(-1, 1)
            self.inputWeights.append(weights)
            # get weight for hidden node to output node
            self.outputWeights[i] = random.uniform(-1, 1)

    ##
    # getOutputValue()
    # Takes GameState inputs [converted using getStateInputs()]
    # to find the output value of the neural network
    ##

    def getOutputValue(self, inputs):
        # get hidden node values
        for i in range(0, self.NODES):
            sum = 0
            for j in range(0, self.INPUTS):
                sum += self.inputWeights[i][j]*inputs[j]
            self.hiddenValues[i] = 1/(1+math.pow(math.e, -sum))

        # get final values
        sum = 0
        for i in range(0, self.NODES):
            sum += self.outputWeights[i]*self.hiddenValues[i]
        output = 1/(1+math.pow(math.e, -sum))
        return output



    def backPropogate(self, totalError):

        for input in self.inputWeights:
            for x in range(0,len(self.hiddenValues)):
                errorTerm = self.outputWeights[x]*totalError*((1/(1+math.pow(math.e, -self.hiddenValues[x])))
                                                              *(1-(1/(1+math.pow(math.e, -self.hiddenValues[x])))))
                newWeight = input[x] + self.alpha * errorTerm
                input[x] = newWeight

        for output in self.outputWeights:
            errorTerm = self.outputWeights[x] * totalError * ((1 / (1 + math.pow(math.e, -self.hiddenValues[x])))
                                                            * (1 - (1 / (1 + math.pow(math.e, -self.hiddenValues[x])))))
            newWeight = output + self.alpha * errorTerm
            output = newWeight
            print(output)


    ##
    # getNextState
    #
    # Author:  Jordan Goldey (Class of 2017)
    #
    # Description: Creates a copy of the given state and modifies the inventories in
    # it to reflect what they would look like after a given move.  For efficiency,
    # only the inventories are modified and the board is set to None.  The original
    # (given) state is not modified. It NOW correctly reflects how to food is picked
    # up in the game
    #
    # CAVEAT: To facilitate longer term analysis without having to take enemy moves
    # into consideration, MOVE_ANT commands do not cause the hasMoved property of
    # the ant to change to True.  Furthermore the END move type is ignored.
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   move - The move that the agent would take (Move)
    #
    # Return: A clone of what the state would look like if the move was made
    ##
    def getNextState(self, currentState, move):
        # variables I will need
        myGameState = currentState.fastclone()
        myInv = getCurrPlayerInventory(myGameState)
        me = myGameState.whoseTurn
        myAnts = myInv.ants
        myTunnels = myInv.getTunnels()
        myAntHill = myInv.getAnthill()

        # If enemy ant is on my anthill or tunnel update capture health
        ant = getAntAt(myGameState, myAntHill.coords)
        if ant is not None:
            if ant.player != me:
                myAntHill.captureHealth -= 1

        # If an ant is built update list of ants
        antTypes = [WORKER, DRONE, SOLDIER, R_SOLDIER]
        if move.moveType == BUILD:
            if move.buildType in antTypes:
                ant = Ant(myInv.getAnthill().coords, move.buildType, me)
                myInv.ants.append(ant)
                # Update food count depending on ant built
                if move.buildType == WORKER:
                    myInv.foodCount -= 1
                elif move.buildType == DRONE or move.buildType == R_SOLDIER:
                    myInv.foodCount -= 2
                elif move.buildType == SOLDIER:
                    myInv.foodCount -= 3
            # ants are no longer allowed to build tunnels, so this is an error
            elif move.buildType == TUNNEL:
                print("Attempted tunnel build in getNextState()")
                return currentState

        # If an ant is moved update their coordinates and has moved
        elif move.moveType == MOVE_ANT:
            newCoord = move.coordList[-1]
            startingCoord = move.coordList[0]
            for ant in myAnts:
                if ant.coords == startingCoord:
                    ant.coords = newCoord
                    ant.hasMoved = False
                    # If an ant is carrying food and ends on the anthill or tunnel drop the food
                    # THIS CODE IS NOT WHAT GAME.PY DOES
                    # if ant.carrying and ant.coords == myInv.getAnthill().coords:
                    #     myInv.foodCount += 1
                    #     ant.carrying = False
                    # for tunnels in myTunnels:
                    #     if ant.carrying and (ant.coords == tunnels.coords):
                    #         myInv.foodCount += 1
                    #         ant.carrying = False
                    # # If an ant doesn't have food and ends on the food grab food
                    # if not ant.carrying and ant.type == WORKER:
                    #     foods = getConstrList(myGameState, 2, [FOOD])
                    #     for food in foods:
                    #         if food.coords == ant.coords:
                    #             ant.carrying = True
                    # If my ant is close to an enemy ant attack it
                    attackable = listAttackable(ant.coords, UNIT_STATS[ant.type][RANGE])
                    for coord in attackable:
                        foundAnt = getAntAt(myGameState, coord)
                        if foundAnt is not None:  # If ant is adjacent my ant
                            if foundAnt.player != me:  # if the ant is not me
                                foundAnt.health = foundAnt.health - UNIT_STATS[ant.type][ATTACK]  # attack
                                # If an enemy is attacked and looses all its health remove it from the other players
                                # inventory
                                if foundAnt.health <= 0:
                                    myGameState.inventories[1 - me].ants.remove(foundAnt)
                                # If attacked an ant already don't attack any more
                                break
        return myGameState

    ##
    # getNextStateAdversarial
    #
    # Description: This is the same as getNextState (above) except that it properly
    # updates the hasMoved property on ants and the END move is processed correctly.
    # It has been updated to reflect this description.
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   move - The move that the agent would take (Move)
    #
    # Return: A clone of what the state would look like if the move was made
    ##
    def getNextStateAdversarial(self, currentState, move):
        # variables I will need
        nextState = self.getNextState(currentState, move)
        myInv = getCurrPlayerInventory(nextState)
        myAnts = myInv.ants

        # If an ant is moved update their coordinates and has moved
        if move.moveType == MOVE_ANT:
            # startingCoord = move.coordList[0]
            startingCoord = move.coordList[len(move.coordList) - 1]
            for ant in myAnts:
                if ant.coords == startingCoord:
                    ant.hasMoved = True
        elif move.moveType == END:
            for ant in myAnts:
                ant.hasMoved = False
            nextState.whoseTurn = 1 - currentState.whoseTurn
        ## NEW STUFF
        elif move.moveType == BUILD:
            for ant in myAnts:
                if ant.coords == myInv.getAnthill().coords:
                    ant.hasMoved = True
        return nextState
