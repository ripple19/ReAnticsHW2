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
    FINAL = 0  # 0: Set random weights and use back propagation. 1: Use final weights and exclude back propagation

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
        self.outputWeights = [] # 1D array
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
        self.inputWeights = [0.8067856231477833, 0.41738792457124374, -0.19887300589083237, -0.05271362198458734, -0.7543744482287789, 0.006899232347048946, -1.230477929904425, -1.0619954483507277, -0.01520748404038509, 0.11081685778197316, 0.3336644685744748, 0.019450436507159833, -0.4508165293936773, -1.002653837497236, -0.4548918976081499, -0.1209228894160165, -0.6027458906707103, -0.8506502029153862, -4.957803377844669, -0.7256239450342228, -0.486028581943061, -0.5846312658493289, -1.2153198662149218, -0.6433091755773785, 1.2107551578685998, 0.08199264712945183, -0.09464656057707628, -0.16845480792153003, 1.381052433738868, 1.0325909090328105, -0.6855830777546078, -0.32853428940251134, 0.458780065533836, 0.70026643817939, 0.9530675945301187, 0.27517859459302757, -0.2938484696456349, 0.7325451980111783, -0.6433125551086087, -0.5819069136536735, 0.4026779962261581, -1.1153697207764388, -0.41560709597017426, 0.13414833492568412, -0.05066529315212854, -0.0497875554280486, -0.5428832630446792, 0.2441587004935594, -0.6997655776923016, -0.3281603015694086, 0.1696545467334449, 0.5205323687034132, -0.9261689117648114, 0.08368717960756147, -0.5366379465682152, -0.38548020841159764, -0.46908885375931975, -0.41527946587236114, -0.28235158692928486, -0.13850819842076892, -0.8741716861701204, -0.2205384030567835, 0.22366324652467823, -0.5530735302662925, 0.04505300159528369, 0.5122642635231173, -0.518192028179579, 0.6164914424377584, 1.26659866303241, 0.8554535187295188, 0.6060419079195113, -0.4274348587898449, -3.3350747126560196, -1.1745769610692007, 1.5769714817279568, 1.070492829316899, -0.18100944210461695, -0.0931928097704034, -0.6793680787373912, 0.4849283984197579, -0.8156898240298348, -0.3400785070525615, -0.29040828749552516, 0.07835438703553456, -0.03741218561818965, -0.8190960619454708, -0.21410191807296453, -0.054419167686085984, -0.5853877036161055, -0.3940634611586746, -0.1456388573067664, 0.035104035524662236, -0.019595241969823162, -0.556347027728655, -0.12285320227175943, 0.34271222011179236, 0.8204961023538545, -0.3293435913007173, -0.8465676862561462, 0.2821094852862159, -0.6369001797579064, -0.059522936852081425, -0.29427716580268953, -0.03476557786914222, 0.20096407218524315, -0.396403013209437, -0.7636318500448261, 0.800926203517044, -1.7882419518231145, -0.4811295548376988, -0.24484117775531317, -0.5344503912092723, 0.8609116278574517, 0.14035284675013843, -0.2404035118508337, 0.1857179917740922, -0.43398722696717684, -1.9352827526718528, 0.3810445220862126, -1.4861133591423354, -0.4784756075016206, -0.8477598244026642, -0.2944855841839375, -1.3708662464594896, -1.2941610120079299, 0.36489637642190437, -0.550473088492006, 0.10957643318578532, 0.0531536740173448, 0.38375853289485956, -0.13675201697313036, -0.6962325740664483, 0.2452029438966204, -0.6476354100899703, -1.362424304294363, 0.2024899439855339, 0.4241789354945173, -0.5606517984409004, -0.7328347347861229, 0.19728261711200276, -0.12517430134419444, 0.6027565632646966, -2.094756482979378, -1.8721436191101082, 0.3419961205759069, 0.4558958206790008, -0.15199529485090169, 0.45722321857831916, -1.0212871135527741, 0.45728299706328107, -0.568278158195393, 0.22580036407208814, 0.4109066895167868, 0.05846358265138499, -0.758550601268024, -0.7521098248148358, -0.4029100643134351, -1.0330457546344158, -0.21248874359211695, -0.8818177620493094, 0.39586935184527405, -0.49488876009807586, -1.825854504711797, -1.4959516102483825, -0.7221520100133975, -0.5858647661628508, -0.30977425578830237, 0.9282967221954653, 0.3040877501432744, -0.1167101268849202, -0.9309599997703408, 0.1616441304389718, 1.7165944913241018, -0.6957138012502116, 0.6806088457778549, -0.4003191651196082, 0.1588628658615189, -0.7014369413094652, -3.333676429138467, 0.8753822959356765, 0.9458792238946614, -0.6200709563036336, 0.5907412629705772, -0.2640290283696703, -0.9089782503694956, 0.2805405483684404, 0.11672460136427568, -0.14722851375079501, -0.6449082365403674, 0.2964070811212209, -0.3415139947608611, 0.1221861175282159, -0.31786324824546086, 0.25544044684970635, -1.2793173359818004, -0.44160247956259985, -0.06100857335401386, -1.5688852784346488, 1.4321173499825395, -1.257839756580869, -1.0224374902122697, -0.6267234471058017, -0.9147513044951421, -0.42034330170123574, 0.49066663496117846, -0.1221982859771217, -0.7509575733375148, 0.1263397677759735, 0.6159567941468997, -0.3060780497489341, 0.0006681898631190887, 0.14120901576616543, -0.1066563402474547, -0.5960484360662748, -0.9101085796035837, -0.1075860503689926, -0.5714374298207229, -0.7108075327201452, -0.27669247809591746, -0.7727723200889187, 0.6181729196685014, -0.6382864584845175, -2.206145707981424, -1.6708696468923143, 1.5331005382857732, 0.06508676747003626, -0.15695936611048075, -0.4425148480186565, -3.3000489421908465, 0.6219801856897533, 0.90140011027964, -0.5915657439321349, -0.5728474970533164, -0.30906081751862635, -0.26014942195250784, 0.5983541516182563, -0.874714476123024, 0.4033484852906749, 1.4464764510824213, -0.602765692812333, 0.784330734049022, -0.20886164342762395, 0.6017374741404735, -0.2913016529211878, 1.4659013216266705, 0.5324325963413791, -0.48134974160201166, -1.664452051018378, -1.0086016646380573, 0.37548868451653666]
        self.outputWeights = [-0.25135448084032314, -3.266992519776581, -1.2787895396079771, 0.6147285374354081, 0.49573764695087563, -0.2100573219092263, -0.9319153233725589, -2.8187155810856455, 0.42751463774045334, 1.1036920440514912, 0.8679845076645002, 2.808807242852582, -1.1815742331097614, -0.0018670392527625722, -1.9075516329453426, -0.060883645380317354, -1.5369413008975379, -1.85417596610327, 0.36991611352863846, 1.5794235832039256, -0.5203228986444965, -0.30902820889852856, -1.7799767978983243, 1.0718914355668487, 2.23623991175124]
        self.inputBiasWeights = [0.246283064590179, -1.0717264875019583, 0.11670599136507376, 0.6956991310221053, 0.4470279182723319, -0.73687536937471, -0.08520133689393414, -0.3003635207642156, -0.45844754461699816, 0.15567023984428893, -0.06061654082316659, -1.4125737265762615, 0.47600893809266687, 0.21630336061121908, -0.2803404063848437, -0.11743619426911535, 1.1983285333266753, -0.6653520197059809, -0.5443001192433214, -0.8187933757579712, -0.15675164485359927, -0.10204544597089535, 1.283029037915817, -0.32685373962298053, -1.2690466664030071]
        self.outputBiasWeight = 0.5182174798418924

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
            #print(sum)
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
        for x in range(0,len(self.outputWeights)):
            # get error value of each hidden node (weight)*(delta of output node)
            outputWeightErrors.append(self.outputWeights[x]*delta)
            # get delta of each hidden node (hiddenValues = b) (b)(1-b)(err)
            hiddenNodeDeltas.append(self.hiddenValues[x]*(1-self.hiddenValues[x])*outputWeightErrors[x])

        # update input weights
        for x in range(0, len(self.hiddenValues)):
            for y in range(0,len(self.inputValues)):
                #   - (old weight) + (alpha)*(delta of output node)*(input)
                self.inputWeights[(x*self.INPUTS)+y] = self.inputWeights[(x*self.INPUTS)+y] \
                    + self.alpha*hiddenNodeDeltas[x]*self.inputValues[y]
                # print("New Weight %d: %.2f" % (((x*self.INPUTS)+y), self.inputWeights[(x*self.INPUTS)+y]))

        # update hidden node bias weights
        for x in range(0, self.NODES):
            self.inputBiasWeights[x] = self.inputBiasWeights[x] + self.alpha*hiddenNodeDeltas[x]

        # update output weights
        for x in range(0,len(self.outputWeights)):
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
