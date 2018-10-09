import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

from functools import lru_cache

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "IveGotThePrunes AI")
        ## Initialize class variables on start of program ##

        self.foodCoords = [] #Our food corrds
        self.buildingCoords = [] #Our building coords

        # Init depth limit for recursion
        self.depthLimit = 3
        self.bestMove = None #Best move..to return to getMove.
        self.prune = False #Lets us know whether we are pruning or not.

################################################################################

    # Evaluation function for the number of workers that the AI controls
    @lru_cache(maxsize = None) #ALWAYS CACHING
    def evalWorkerCount(self, workerCount, test = False, testvar = None):
        if test:
            workerCount = testvar
        # Reward the AI for having only one worker
        if (workerCount > 1):
            return -1.0
        else:
            return workerCount

    # Evaluation function for the number of soldier that the AI controls
    @lru_cache(maxsize = None)
    def evalSoldierCount(self, soldierCount, test = False, testvar = None):
        if test:
            soldierCount = testvar
        # Reward for having more than 3 soldiers
        if (soldierCount > 1):
            return -1.0
        else:
            return 0.5 * soldierCount

    # Evaluation function for the difference in ants between AIs
    @lru_cache(maxsize = None) #CACHING FOR EFFICIENCY
    def evalAntDifference(self, myAntCount, enemyAntCount, test = False, testMyAnts = None, testEnemyAnts = None):
        if test:
            myAntCount = testMyAnts
            enemyAntCount = testEnemyAnts
        # Evaluation score is the ratio of our AI's ants vs the total number of ants on the board
        return (myAntCount-enemyAntCount) / (myAntCount+enemyAntCount)

    @lru_cache(maxsize = None)
    def evalEnemyQueenHealth(self, enemyQueenHealth, test=False, testMyAnts = None, testEnemyAnts = None):
        return 1- ((enemyQueenHealth)/(10))


    # Evaluation function for the difference in health of the ants between AIs
    def evalHealthDifference(self, currentState, test = False, testMyAntList = None, testEnemyAntList = None):
        #Used for testing the function.
        if test:
            myAnts = testMyAntList
            enemyAnts = testEnemyAntList
        else:
            me = currentState.whoseTurn
            myAnts = getAntList(currentState, me)
            enemyAnts = getAntList(currentState, 1-me)

        #Go through my health and enemy health of ants and see if they went down.
        myTotalHealth = 0
        enemyTotalHealth = 0
        for ant in myAnts:
            myTotalHealth += ant.health
        for ant in enemyAnts:
            enemyTotalHealth += ant.health
        return (myTotalHealth-enemyTotalHealth) / (myTotalHealth+enemyTotalHealth)

    # Evaluation function for the position of the worker
    # Rewards AI for collection food and bring the food back to the anthill/tunnel
    def evalWorkerPositions(self, workerList, myInv):
        if (len(workerList) == 0):
            return -1.0

        # 16 steps is around the furthest distance one worker could theoretically be
        # from a food source. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_FOOD = 16

        # Calculate the total steps each worker is from its nearest destination.
        totalStepsToDestination = 0
        for worker in workerList:
            if worker.carrying:
                totalStepsToDestination += self.getMinStepsToTarget(worker.coords, self.buildingCoords)
            else:
                steps = self.getMinStepsToTarget(worker.coords, self.foodCoords)
                totalStepsToDestination += steps + MAX_STEPS_FROM_FOOD

        totalStepsToDestination += (11-myInv.foodCount) * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        scoreCeiling = 12 * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        evalScore = scoreCeiling - totalStepsToDestination
        # Max possible score is 1.0, where all workers are at their destination.
        return (evalScore/scoreCeiling)

    # Evaluation function for the position of the soldier
    # Rewards for being closer to enemy ants resulting in attack
    def evalSoldierPositions(self, soldierList, enemyAntCoords, currentState, parentState):
        if (len(soldierList) == 0):
            return 0.0
        # Save the coordinates of all the enemy's ants.
        good = 0.0 #Looks at whether or not a soldier is moving forwards toward the enemy
        parentSoldierList = getAntList(parentState, parentState.whoseTurn,[SOLDIER])
        if parentState.whoseTurn == currentState.whoseTurn and len(parentSoldierList) != 0 and len(soldierList) != 0:
            if parentSoldierList[0].coords[1] - soldierList[0].coords[1] >= 1: #Check if moving up!
                good = .8 #If Soldier is moving towards the enemy...Then add to our eval


        totalStepsToEnemy = 0
        for soldier in soldierList:
            totalStepsToEnemy += self.getMinStepsToTarget(soldier.coords, enemyAntCoords)

        # 30 steps is around the furthest distance one soldier could theoretically be
        # from an enemy ant. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_ENEMY = 30
        scoreCeiling = MAX_STEPS_FROM_ENEMY * len(soldierList)
        evalScore = scoreCeiling - totalStepsToEnemy
        # Max possible score is 1.0, where all soldiers are at their destination.
        return ((evalScore + good -.8)/scoreCeiling)


    # Evaluation function for the position of the queen
    # Rewards AI for moving away from the closest enemy and not on the anthill/tunnel
    def evalQueenPosition(self, queen, enemyAnts, enemyAntCoords, buildings):
        totalDistance = 0
        for enemyCoords in enemyAntCoords:
            totalDistance += approxDist(queen.coords, enemyCoords)

        if (len(enemyAntCoords) > 0):
            MAX_STEPS_FROM_ENEMY = 30
            scoreCeiling = MAX_STEPS_FROM_ENEMY * len(enemyAntCoords)
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return totalDistance/scoreCeiling
        else:
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return 1.0

    @lru_cache(maxsize = None)
    def evalFoodCount(self, foodCount):
        return foodCount/11



#DEFINITION: THIS METHOD CHECKS TO SEE IF THERE ARE ANY ANTS TO KILL IN REACHABLE AREAS:
#IT PRIORITIZES WORKERS, DRONES, and then THE QUEEN.
    def evalAttackEnemyAnts(self, currentState, soldierList):
        totalScore = 0

        #If emepty list...doesnt matter.
        if len(soldierList) == 0:
            return 0

        for soldier in soldierList:
            #Get attackable list coordinates, and see if enemy ants are on them.
            attackList = listAttackable(soldier.coords)
            if attackList == []:
                totalScore += -1.0
            else:
                #Depending on type of ant..we want to make that move more or less.
                for coords in attackList:
                    ant = getAntAt(currentState, coords)
                    if ant == WORKER:
                        totalScore += 1.0
                    elif ant == DRONE:
                        totalScore += 0.8
                    elif ant == QUEEN:
                        totalScore += 0.7
                    else:
                        totalScore += 0.3

        return totalScore/len(soldierList)

    # Helper function to get the minimum steps to the given target
    def getMinStepsToTarget(self, targetCoords, coordsList):
        minSteps = 10000 # infinity
        for coords in coordsList:
            stepsToTarget = approxDist(targetCoords, coords)
            if stepsToTarget < minSteps:
                minSteps = stepsToTarget
        return minSteps

    # Helper function to get the coordinate list of the given list
    def getCoordsOfListElements(self, elementList):
        coordList = []
        for element in elementList:
            coordList.append(element.coords)
        return coordList

    ##
    # evalOverall
    # Description: Calls all of the evaluation scores and multiplies them by a
    #   weight. This allows the AI to fine tune the evaluation scores to better
    #   suit favorable moves and strategies.
    #
    # Parameters:
    #   currentState - A clone of the current game state that will be evaluated
    #
    # Return:
    # A score between [-1.0, 1.0] such that + is good and - is bad for the
    #   player in question (me parameter)
    ##
    def evalOverall(self, currentState, parentState):
        # Determine if the game has ended and who won
        winResult = getWinner(currentState)
        if winResult == 1:
            return 1.0
        elif winResult == 0:
            return -1.0
        # else neither player has won this state.

        # Initialize the totalScore
        totalScore = 0

        # Initialize the weights for the specific evaluation functions
        workerCountWeight = 1
        soldierCountWeight = 1
        antDifferenceWeight = 1
        healthDifferenceWeight = 0
        workerPositionWeight = 1
        soldierPositionWeight = 1
        queenPositionWeight = 0
        enemyQueenHealthWeight = 1000 # WE REALLY WANT THE QUEEN DEAD
        foodCountWeight = 100 # WE REALLY WANT FOOD
        attackEnemyAntsWeight = 1000 #WE REALLY WANT TO KILL ANTS! ARGH!!
        totalWeight = workerCountWeight + soldierCountWeight + antDifferenceWeight + \
                      healthDifferenceWeight + workerPositionWeight + \
                      soldierPositionWeight + queenPositionWeight + \
                      enemyQueenHealthWeight + foodCountWeight + \
                      attackEnemyAntsWeight

        # Create parameters for eval functions
        workerList = getAntList(currentState, currentState.whoseTurn, (WORKER,))
        soldierList = getAntList(currentState, currentState.whoseTurn, (SOLDIER,))
        me = currentState.whoseTurn
        myAnts = getAntList(currentState, me)
        enemyAnts = getAntList(currentState, 1-me)
        enemyQueenHealth = getEnemyInv(None,currentState).getQueen().health
        myInv = getCurrPlayerInventory(currentState)
        enemyAntCoords = self.getCoordsOfListElements(getAntList(currentState, 1-me))
        queen = getCurrPlayerQueen(currentState)
        buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
        foodCount = myInv.foodCount

        # Determine evaluation scores multiplied by it weights
        totalScore += self.evalWorkerCount(len(workerList)) * workerCountWeight
        totalScore += self.evalSoldierCount(len(soldierList)) * soldierCountWeight
        totalScore += self.evalAntDifference(len(myAnts),len(enemyAnts)) * antDifferenceWeight
        totalScore += self.evalEnemyQueenHealth(enemyQueenHealth) * enemyQueenHealthWeight
        totalScore += self.evalHealthDifference(currentState) * healthDifferenceWeight
        totalScore += self.evalWorkerPositions(workerList, myInv) * workerPositionWeight
        totalScore += self.evalSoldierPositions(soldierList, enemyAntCoords, currentState, parentState) * soldierPositionWeight
        totalScore += self.evalQueenPosition(queen, enemyAnts, enemyAntCoords, buildings) * queenPositionWeight
        totalScore += self.evalFoodCount(foodCount)
        totalScore += self.evalAttackEnemyAnts(currentState, soldierList) * attackEnemyAntsWeight

        ### OVERALL WEIGHTED AVERAGE ###
        # Takes the weighted average of all of the scores
        # Only the game ending scores should be 1 or -1.
        overallScore = 0.99 * totalScore / totalWeight

        return overallScore

    # Recursion function to search for the best move per depth
    ##
    # greedyGetBestMove
    # Description: Recursively goes and creates a tree of nodes and evaluates their values, alpha, and beta scores
    # to figure out which move should be passed to getMove.
    # Parameters:
    #   currentState - A clone of the current game state that will be evaluated
    #   currentDepth- The depth of the current recursive call.
    #   currentNode- The Node we are currently looking at
    # Return:
    # A recursive call for evaluating more nodes
    # or we just return out of the function...since it sets self.bestMove inside of it. No need to return the move.
    def greedyGetBestMove(self, currentState, currentDepth, currentNode):
        # Initiate moves to an empty list
        moves = []
        #Put the movement moves first, then end move, then the build moves...might cut down
        #Computation time.
        moves.extend(listAllMovementMoves(currentState))
        moves.append(Move(END, None, None))
        moves.extend(listAllBuildMoves(currentState))

        #For each move in the move list
        for child_move in moves:

            #If we are building a new Range Soldier or Drone...we don't want that...so prune it.
            if child_move.buildType in [R_SOLDIER, DRONE]:
                continue
            #Don't create soldiers if we have one.
            if len(getAntList(currentState, currentState.whoseTurn, [SOLDIER])) >= 1 and child_move.buildType in [SOLDIER]:
                continue
            # Only create workers if we have 0.
            if len(getAntList(currentState, currentState.whoseTurn, [WORKER])) >= 1 and child_move.buildType in [WORKER]:
                continue
            # If we are pruning..break out and skip other nodes.
            if self.prune:
                break

            #CASE 1: If we are at the depth limit.
            if currentDepth >= self.depthLimit:

                #Current node's score.
                stateScore = self.evalOverall(currentNode.state, currentNode.parent.state)

                #Enemy Turn
                if not currentNode.turn and (-1*stateScore < currentNode.beta):
                    currentNode.beta = stateScore*-1 #Set beta to negative of statescore
                    if currentNode.alpha >= currentNode.beta: #Check to see if pruning is necessary
                        self.prune = True
                #Our turn
                if currentNode.turn and stateScore > currentNode.alpha:
                    currentNode.alpha = stateScore
                    if currentNode.alpha >= currentNode.beta: #Check to see if pruning is necessary
                        self.prune = True
            else: #CASE 2: We are in nodes not at depth limit.
                #Get the next state
                resultState = getNextStateAdversarial(currentState, child_move)

                #If not our turn.
                if not currentNode.turn:
                    if child_move.moveType == END: #Check if we swap turns...change turn value if so.
                        resultNode = Node(resultState, child_move, 1000, currentNode, not currentNode.turn, currentNode.alpha, currentNode.beta)
                    else: #If we dont, then node is same as its parent.
                        resultNode = Node(resultState, child_move, 1000, currentNode, currentNode.turn, currentNode.alpha,
                                          currentNode.beta)
                else: #If it is our turn...same logic as above but different alpha beta values.
                    if child_move.moveType == END:
                        resultNode = Node(resultState, child_move, -1000, currentNode, not currentNode.turn, currentNode.alpha, currentNode.beta)
                    else:
                        resultNode = Node(resultState, child_move, -1000, currentNode, currentNode.turn, currentNode.alpha,
                                          currentNode.beta)
                #Recursive Call
                self.greedyGetBestMove(resultNode.state, currentDepth + 1, resultNode)

        #OUTSIDE OF FOR LOOP
        #If we aren't pruning.
        if not self.prune:
            if currentNode.turn: #If is our turn...
                currentNode.score = currentNode.alpha #Then we want to pass our alpha to our score.
            else:
                currentNode.score = currentNode.beta #Enemy turn...beta value instead.
        else: #If we did prune...we want to set it to false now. RESET
            self.prune = False
            return #Return out because we dont want to pass up values to parents.

        #If we have not gotten to our root node.
        if currentDepth > 0:
            #We basically check whose turn it is and figure out whether or not to change the alpha
            #beta values of the parent node based on our current nodes evaluation score.
            #If its a max node...we pass up to the alpha.
            #If its a min node..we pass up the beta.
            if not currentNode.parent.turn and (currentNode.score < currentNode.parent.beta):
                currentNode.parent.beta = currentNode.score
                # If we are at depth 1...we want to make our best move the node we are currently on.
                if currentDepth == 1:
                    self.bestMove = currentNode.move
            elif currentNode.parent.turn and (currentNode.score > currentNode.parent.alpha):
                currentNode.parent.alpha = currentNode.score
                if currentDepth == 1:
                    self.bestMove = currentNode.move
        return #Return back to recursion.


################################################################################

    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        # Initialize class variables on start of game
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        # Acquire the location of the food and the buildings for the worker
        # position eval function
        self.foodCoords = self.getCoordsOfListElements(getConstrList(currentState, None, (FOOD,)))
        self.buildingCoords = self.getCoordsOfListElements(getConstrList(currentState, currentState.whoseTurn, (ANTHILL, TUNNEL)))

        # Run the recursive MinMax evaluation to determine the best move
        self.bestMove = None
        dummyNode = Node(currentState,None,-1000,None,True, -1000, 1000)
        self.greedyGetBestMove(currentState, 0, dummyNode)
        return self.bestMove

    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

# DESCRIPTION: Node class that creates a new instance of a game state
# PARAMETER: Takes in the game state, the move that was made to reach the state, the evaluation score of the state
# and the parent game state, and the alpha and beta values associated with the node.
# ALLOWS US TO STORE NODES IN THE TREE IN THIS STRUCTURE.
class Node:

    def __init__(self, state, move, score, parent, turn, alphaVal, betaVal):
        self.state = state
        self.move = move
        self.score = score
        self.parent = parent
        self.turn = turn
        self.alpha = alphaVal
        self.beta = betaVal


###########################################################################################################
##
# UNIT TESTS Cases
##

testAI = AIPlayer(0)
# evalWorkerCount
if testAI.evalWorkerCount(None,True,0) != 0:
    print("ERROR: Worker Count Evaluation1")
if testAI.evalWorkerCount(None,True,1) != 1:
    print("ERROR: Worker Count Evaluation2")
if testAI.evalWorkerCount(None,True,2) != -1:
    print("ERROR: Worker Count Evaluation3")

# evalSoldierCount
if testAI.evalSoldierCount(None,True,0) != 0:
    print("ERROR: Soldier Count Evaluation1")
if testAI.evalSoldierCount(None,True,1) != .5:
    print("ERROR: Soldier Count Evaluation2")
if testAI.evalSoldierCount(None,True,3) != -1:
    print("ERROR: Soldier Count Evaluation3")
if testAI.evalSoldierCount(None,True,12) != -1:
    print("ERROR: Soldier Count Evaluation4")

# evalAntDifference
if testAI.evalAntDifference(None,None,True,1,1) != 0:
    print("ERROR: Ant Difference Evaluation1")
if testAI.evalAntDifference(None,None,True,1,2) != -1/3:
    print("ERROR: Ant Difference Evaluation2")
if testAI.evalAntDifference(None,None,True,2,1) != 1/3:
    print("ERROR: Ant Difference Evaluation3")
if testAI.evalAntDifference(None,None,True,3,2) != .2:
    print("ERROR: Ant Difference Evaluation4")
if testAI.evalAntDifference(None,None,True,2,3) != -.2:
    print("ERROR: Ant Difference Evaluation5")

# evalHealthDifference
myAnts = [Ant((0,0), WORKER, 0), Ant((1,1), QUEEN, 0), Ant((2,2), DRONE, 0)]
enemyAnts = [Ant((9,9), WORKER, 1), Ant((8,8), SOLDIER, 1), Ant((7,7), R_SOLDIER, 1)]
if testAI.evalHealthDifference(None, True, myAnts, enemyAnts) != 4/28:
    print("ERROR: evalHealthDifference result")

# getMinStepsToTarget
if testAI.getMinStepsToTarget((0,0), [(2,2), (1,1), (3,3)]) != 2:
    print("ERROR: MinStepsToTarget result")

# getCoordsOfListElements
class testCoords:
    def __init__(self, c):
        self.coords = c

testCoordsList = [testCoords((0,1)), testCoords((1,2)), testCoords((45,2))]
if testAI.getCoordsOfListElements(testCoordsList) != [(0,1), (1,2), (45,2)]:
    print("ERROR: getCoordsOfListElements result")