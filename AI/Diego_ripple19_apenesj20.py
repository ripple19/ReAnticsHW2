import random
import math
import sys
import time
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
    NODES = 25
    FINAL = 1  # 0: Set random weights and use back propagation. 1: Use final weights and exclude back propagation

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Diego")
        self.depth_limit = 3
        self.me = 0
        self.move = None
        self.nextMove = None
        self.prunedMoves = 0
        self.alpha = 0.7
        self.currentNeuralOutput = 0
        self.currentEvalOutput = 0
        self.currentError = self.currentEvalOutput - self.currentNeuralOutput
        self.inputBiasWeights = [0] * self.NODES
        self.outputBiasWeight = 0
        self.inputWeights = []  # 2D array
        self.outputWeights = []  # 1D array
        self.hiddenValues = [0] * self.NODES
        self.inputValues = [0] * self.INPUTS
        self.gamesPlayed = 0
        self.moveCounter = 0
        self.moveSum = 0
        if self.FINAL == 0:
            self.initializeNetwork()
            self.useNetwork = False
            self.notReady = True
        else:
            self.initializeFinalNetwork()
            self.useNetwork = True
            self.notReady = False


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
        # for neural network use
        self.gamesPlayed += 1
        # print average error
        # if still testing, print error and network weights
        if self.FINAL == 0:
            print("AVERAGE ERROR %.4f" % (self.moveSum / self.moveCounter))
            self.moveSum = 0
            self.moveCounter = 0
            # print network weights
            print("PRINTING NETWORK WEIGHTS")
            self.printWeights()
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
                    rSoldierDistance = abs(approxDist(rSoldiers[0].coords, enemyQueenCoords)-2)  # there is an error when it's -3 so I'm changing it to see if it's fixed
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
                    if self.FINAL == 0:
                        self.backPropagate(n["state"])
                        node["min"] = max(self.evaluateState(n["state"]), node["min"])
                    else:
                        node["min"] = max(self.getOutputValue(n["state"]), node["min"])
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
                    if self.FINAL == 0:
                        self.backPropagate(n["state"])
                        node["max"] = min(self.evaluateState(n["state"]), node["max"])
                    else:
                        node["max"] = min(self.getOutputValue(n["state"]), node["max"])
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
        else:
            inputs.append(1)
        # Do we have 4 ants?
        ourAnts = getAntList(currentState, me, types=(QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER))
        if len(ourAnts) == 4:
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
                    rSoldierDistance = abs(approxDist(rSoldiers[0].coords, enemyQueenCoords) - 2) # there is an error when it's -3 so I'm changing it to see if it's fixed
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
        inputs.append(((2*ourFoodNumber+carrying)-(3*enemyFoodNumber))/(max((2*ourFoodNumber+carrying)
                                                                            + (3*enemyFoodNumber), 1)))
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
        random.seed(time.clock())
        # reset weights (if necessary)
        self.inputWeights = [0] * (self.NODES * self.INPUTS)
        self.outputWeights = [0] * self.NODES
        self.outputBiasWeight = random.uniform(-1,1)
        for i in range(0, self.NODES):
            # get random values for a set of weights that attach to a single hidden node
            for j in range(0, self.INPUTS):
                self.inputWeights[(i*self.INPUTS)+j] = random.uniform(-1, 1)
            # get weight for hidden node to output node
            self.outputWeights[i] = random.uniform(-1, 1)
            self.inputBiasWeights[i] = random.uniform(-1, 1)

    ##
    # initializeFinalNetwork()
    # FOR NEURAL NETWORKS
    # Sets initial weights values learned from neural network testing
    ##

    def initializeFinalNetwork(self):
        self.inputWeights = [-0.2781678553056542, 0.29665497642667465, 0.42787119011983243, 0.8270532309127439, 0.6254641885232817, -0.5166575827637829, 0.7425280317029119, -0.11299387439879607, 0.7931291182081868, -0.17764701164268212, -0.5327301102214645, 0.19487191880186033, -1.0740971250539095, 0.6051578467782516, 0.6981160590173097, 0.7962289863591607, 0.7167200915156313, -0.03569936849848813, -0.571721544777044, -0.5323764519711219, -0.12391073852356785, 0.7145884565338465, -0.7435615069017898, 0.026932894297235787, 0.22750281358500338, -0.5961221393708238, -1.006233929065173, -0.26137057816005105, -0.490498618588832, -0.5369042684280148, -0.23153458977614721, -0.3993304882818629, -1.3088779943320354, 0.21016461410183798, 0.6370623112044109, -0.534060456791071, 0.1811224251756425, -0.7790452334948254, 0.08360233258734873, -0.5816613782566042, -0.365580056603378, -0.6166779538061542, 1.8905996690605837, -0.19120379810798335, 0.17547476658368855, 0.5397733860088795, -0.21661472753256, 0.016027261366507714, -0.19029479480670974, -0.06961408960731387, 0.5051210373992279, 0.20015265200080173, -0.6575537890911226, -0.6652682525862432, -0.11839857614762953, -0.553276035154666, 0.4401451057408008, -0.792535103113869, 0.6099945301189794, -0.012089301926623865, 0.31601921792015425, 0.6157349047181129, -1.8565248921186408, 0.9445405691815555, -0.35331957720529295, 0.0700474549897477, -0.2289032770905645, 0.21534535909582875, 0.197065565411537, -0.35466327923164076, -0.7228058469573685, -0.20291375191554403, 1.1200601482317374, -0.3738689871898857, -0.7028100752288401, -0.5993318233907579, -0.2505262098504256, 0.8819849164409892, 0.21440893125387855, 0.7707864316023809, -0.6312491460311573, 0.08682192283758518, 1.5362460273515544, -0.7212755763473963, -0.5451122110085475, 0.1305865849049965, 0.05106415668713476, -0.128530933576501, -1.8787394204799555, -0.9817378916077305, -0.5278624350047482, -0.46343092423960497, -1.5442672661207482, -0.2027204839988108, -0.4117983283951422, 0.30811331387008734, -0.12939630479914274, 0.44019923773104175, 0.4535601419381985, 1.0426909253869667, -0.41939425617315496, -0.8863841840747053, 0.15884647363937968, -0.01267942137560592, 0.019681044562838826, -0.7362636691956822, -0.5698375754218087, -0.9325561355455106, -0.2734388763565631, -0.7265885871527975, 0.35336956712506823, 0.28627111239849523, 0.7072523657294083, -0.27755222856077827, -0.6693995832515731, 0.3482938703251111, 0.06858491343647595, -0.7079507367597698, -0.14681876942765126, 0.1460275422090924, -0.03201895220498965, -0.266892937073763, -1.6515134316714348, -0.5469401984164409, 0.5908528462335083, 0.46259997538285186, -0.5905130421868673, -0.690294167076429, 0.7065093513050781, -0.3148017372733469, -0.5252331562489756, -0.7951657703663447, -0.22744407528417004, 1.2084978883030935, -0.9261519881136577, -0.5311675058944989, -0.2826717364234586, -0.11953477730754478, -0.4022420848657305, -0.7269178411437218, -0.7317865048688322, -0.03465499686537327, 0.43490227830696027, -0.1141362114136772, 0.1004945950074199, -0.41037925943588316, -0.3940107751781822, 0.24374377702070224, -0.33727414732834954, -0.40931540012614837, 0.5782119992308317, -0.2691054640768666, 0.679835677991694, -0.4618841057048102, -0.34575513209936926, 0.4624579311227241, 0.3763094354457867, -0.41030085483843814, -1.1010250974972484, -0.9465901551922665, 1.0251559350307022, 0.8211071891841237, -0.34325362484138516, -0.2637436428180884, -0.3047374327426449, 0.36741132304349916, 0.6103744657945552, 0.06381489007783533, 0.8827383730281587, 0.7238153963788674, 0.784970461740233, -0.9188526096741978, 1.4211657541538005, -1.1800687606896458, -0.4184815377462033, 0.4060125554222894, -0.3927500389864438, -0.18736515291517802, -0.24249127891196207, -0.14398055670566778, -0.6543070672611677, 0.891637110066642, 0.198511465819935, 0.5849356015072301, 0.47100610839513346, -0.6909227823858162, 0.5892939829444852, -0.17211787472261053, -0.4161167920297748, 0.621194731930679, 0.6996550871288816, -0.8747843846537493, 0.9259161309714766, 0.6024433268171151, -0.18357764771341403, -0.5863399425873853, -0.7256970454958355, 0.6936464411196341, 0.7625975675580963, -0.45546977114031995, -0.5575406368049476, -0.17488820288574103, 0.022294087793096055, 0.32150856813716305, 0.3125022527528067, 0.6168390351975322, 0.8737652316979759, -0.43080655138283924, 1.199190344188106, 0.11381110531810446, 0.2678106646133407, 0.2775598022174424, 1.1100216617110603, 0.8544170616837538, -0.5485815769435624, -0.02314166433365337, -0.04854810254816493, 0.3456233436004858, 0.7356548013011063, 0.7648576458395717, -0.702746728691288, -0.5663421908944241, 1.0554493655758397, 0.04315624248028066, -0.7954435643003797, -0.4978457925256438, -0.036559714878072476, -0.6922095835939972, 0.4877739123745504, -0.5746067831721068, -0.999949676477011, 0.7525048183824024, 2.082602340557908, -0.04834652380880529, 0.3579214023606864, -0.5912929486001784, -0.15362329474660427, 0.6056744356233638, 0.6725946777692976, 0.20532572928779996, 0.4098706047556628, 0.1373136512979228, 0.29225931677563216, 0.35881814765026504, -0.3924398583578563, 0.0032370507983459965, 0.8239435006338915, -0.05645708025891507, -0.8818176307263844, 0.4888989021417712]
        self.outputWeights = [0.006390390223166474, 0.4668115313258867, 0.3034559305352658, 1.4302135344186073, -1.9305201861107868, 1.0084365051418716, 2.007596645171674, -1.2889493986322627, -1.9462459836736474, 1.5455690821369514, -0.8392348709612163, -0.8637195943371151, 2.0605009506829473, 1.2458338161703808, -0.5303781998981747, -0.32163423873653324, 0.8192162922110997, -1.532750853410977, -0.2362735420212691, -0.3968212590994018, -0.48917449853309947, -1.3057151861364635, -0.6206218157086754, -2.198031274058388, -0.05960103381477103]
        self.inputBiasWeights = [1.0129722842338729, -0.02450900417919737, 0.4071666531886748, 0.934964628484609, -0.6264231745909831, 0.5570752239093206, 0.5625550452675864, -0.7996692754254171, -0.8484259510443861, -0.25329472710729967, -0.8743218141783536, 0.8518390535874437, 0.620544457726544, -0.912541948841004, 0.48243219043678837, -0.08286593090556285, 0.09046763907154218, 0.3132660761677234, 0.8490885421148814, -0.25235191863845285, -0.5322048248728336, -0.5986447436643908, -0.24470227771032416, -0.7137035378557804, -0.3818914417583937]
        self.outputBiasWeight = -0.6695046131047603

    ##
    # getOutputValue()
    # Takes GameState inputs [converted using getStateInputs()]
    # to find the output value of the neural network.
    # Output will be between 0 and 1
    ##

    def getOutputValue(self, currentState):
        # get inputs
        self.inputValues = self.getStateInputs(currentState)
        # get hidden node values
        for i in range(0, self.NODES):
            sum = 0
            # input weights
            for j in range(0, self.INPUTS):
                sum += self.inputWeights[(i*self.INPUTS)+j]*self.inputValues[j]
            # bias weight
            sum += self.inputBiasWeights[i]
            # print(sum)
            self.hiddenValues[i] = 1/(1+math.pow(math.e, -sum))

        # get final values
        sum = 0
        for i in range(0, self.NODES):
            # output weights
            sum += self.outputWeights[i]*self.hiddenValues[i]
        # bias weight
        sum += self.outputBiasWeight
        output = 1/(1+math.pow(math.e, -sum))
        return output

    ##
    # backPropagate()
    # This function updates every weight using the method below
    #
    # get output error
    # get delta of output node
    # get error value of each hidden node (weight)*(delta of output node)
    # get delta of each hidden node (hiddenValues = b) (b)(1-b)(err)
    # update every weight
    #   - (old weight) + (alpha)*(delta of output node)*(input)
    ##
    def backPropagate(self, currentState):
        # get output error
        self.calculateError(currentState)
        # get delta of output node
        delta = self.outputValue*(1-self.outputValue)*self.currentError

        outputWeightErrors = []
        hiddenNodeDeltas = []
        for x in range(0, len(self.outputWeights)):
            # get error value of each hidden node (weight)*(delta of output node)
            outputWeightErrors.append(self.outputWeights[x]*delta)
            # get delta of each hidden node (hiddenValues = b) (b)(1-b)(err)
            hiddenNodeDeltas.append(self.hiddenValues[x]*(1-self.hiddenValues[x])*outputWeightErrors[x])

        # update input weights
        for x in range(0, len(self.hiddenValues)):
            for y in range(0, len(self.inputValues)):
                #   - (old weight) + (alpha)*(delta of output node)*(input)
                self.inputWeights[(x*self.INPUTS)+y] = self.inputWeights[(x*self.INPUTS)+y] \
                    + self.alpha*hiddenNodeDeltas[x]*self.inputValues[y]
                # print("New Weight %d: %.2f" % (((x*self.INPUTS)+y), self.inputWeights[(x*self.INPUTS)+y]))

        # update hidden node bias weights
        for x in range(0, self.NODES):
            self.inputBiasWeights[x] = self.inputBiasWeights[x] + self.alpha*hiddenNodeDeltas[x]

        # update output weights
        for x in range(0, len(self.outputWeights)):
            self.outputWeights[x] = self.outputWeights[x] + self.alpha*delta*self.hiddenValues[x]

        # update output node bias weight
        self.outputBiasWeight = self.outputBiasWeight + self.alpha*delta



    def calculateError(self, currentState):
        self.outputValue = self.getOutputValue(currentState)
        # Since self.evaluateState() outputs a range between -1 and 1, fix range to be between 0 and 1
        expectedValue = (self.evaluateState(currentState)+1)/2
        self.currentError = expectedValue-self.outputValue
        # since this is used for every move/state, update moveCounter and moveSum
        self.moveCounter += 1
        self.moveSum += self.currentError
        # if not self.notReady and abs(self.currentError) > 0.03:
        #     self.notReady = True
        # if abs(self.currentError) > 0.03:
        # print(self.currentError)

    def printWeights(self):
        print("Input Weights:")
        print(*self.inputWeights, sep=", ")
        print("Output Weights:")
        print(*self.outputWeights, sep=", ")
        print("Input Bias Weights:")
        print(*self.inputBiasWeights, sep=", ")
        print("Output Bias Weight:")
        print(self.outputBiasWeight)

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
