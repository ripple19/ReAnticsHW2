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
        super(AIPlayer,self).__init__(inputPlayerId, "Hybrid AI")
        ## Initialize class variables on start of program ##

        self.foodCoords = []
        self.buildingCoords = []

        # Init depth limit for recursion
        self.depthLimit = 2
        self.bestMove = None
        self.prune = False

################################################################################
    def analyzeGameState(self, gameState):
        me = gameState.whoseTurn  # My turn
        enemy = 1 - me  # Enemy ID
        # Get a whole lot of information about the current game state...ie
        # Where my anthill, tunnel are at
        # Num of workers.
        # Enemy ants, etc
        myInv = getCurrPlayerInventory(gameState)
        myWorkers = getAntList(gameState, me, (WORKER,))
        thisSoldier = getAntList(gameState, me, (SOLDIER,))
        myAnthill = getConstrList(gameState, me, (ANTHILL,))[0].coords
        myTunnel = getConstrList(gameState, me, (TUNNEL,))[0].coords
        numFood = len(getCurrPlayerFood(self, gameState))
        foodCoord1 = getCurrPlayerFood(self, gameState)[0].coords
        foodCoord2 = getCurrPlayerFood(self, gameState)[1].coords
        rating = 0
        numWorkers = len(getAntList(gameState, me, (WORKER,)))
        Queenlocation = getAntList(gameState, me, (QUEEN,))[0].coords
        enemyAnts = getAntList(gameState, enemy, (DRONE, SOLDIER, WORKER))

        # all based on food
        # If num food is 11, we have won. so return 1.0
        if (numFood == 11):
            return 1.0
        # If numWorkers is less than 1, then if we have 0 food, we have lost. Return -1.0
        if (numWorkers < 1):
            if (numFood == 0):
                return -1.0
        # If we have 1 workers, thats good, add 5.
        if (numWorkers == 1):
            rating += 5
        # If we have 2 workers, thats better...add 10.
        elif (numWorkers == 2 and approxDist(foodCoord1, foodCoord2) > 2 and approxDist(myTunnel, myAnthill) > 2):
            rating += 10
        # If we have 3 workers...bad...subract 5
        elif (numWorkers >= 3):
            rating += -5

        # routes to worker
        # If we have one soldier...thats good.
        if (len(thisSoldier) == 1):
            rating += 5
            # How many enemies are out.
            enemyUnitsLength = len(getAntList(gameState, enemy, (DRONE, WORKER,)))
            # What is next to our Soldier.
            soldierAdjacent = listAdjacent(thisSoldier[0].coords)
            blocking = False
            for adj in soldierAdjacent:
                # If the queen is adjacent to our Soldier...or is making an illegal move..or blocking stuff..(BAD)
                if Queenlocation != adj and Queenlocation[
                    1] <= 3 and Queenlocation != myAnthill and Queenlocation != myTunnel \
                        and Queenlocation != foodCoord1 and Queenlocation != foodCoord2:
                    continue
                else:
                    blocking = True  # if its blocking...bad
                    rating -= 4
            if not blocking:
                rating += 4  # We want a queen that is not blocking anything
            if (enemyUnitsLength > 0):  # If they have some workers or drones.
                enemyworkerdistance = approxDist(thisSoldier[0].coords,
                                                 getAntList(gameState, enemy, (DRONE, WORKER,))[0].coords)

                # this makes sure the soldier keeps moving forward if it can.
                if (thisSoldier[0].coords[1] > myAnthill[1]):
                    rating += 5  # Make the soldier move forward.

                rating += 6 - (
                              enemyworkerdistance + 1) / 10  # Add a rating based off of the distance away it is from enemies.
                # The closer it is, the better the rating.

            elif len(getAntList(gameState, enemy, (QUEEN,))) == 1:  # If Its just the queen left.
                enemyqueendistance = approxDist(thisSoldier[0].coords,
                                                getAntList(gameState, enemy, (QUEEN,))[0].coords)
                # If our soldier can get adjacent and attack..DO IT.
                queenAdj = listAdjacent(getAntList(gameState, enemy, (QUEEN,))[0].coords)
                attack = False
                for adj in queenAdj:  # Check adjacent squares
                    if thisSoldier[0].coords == adj:  # If our soldier is there..good.
                        attack = True
                if attack:  # If it can attack, good.
                    rating += 10
                else:  # if it cant, just get closer.
                    rating += 5 - (enemyqueendistance + 1) / 10
            else:  # if they have no queen...we win.
                return 1.0

        # IF WE HAVE 2 WORKERS...We want them to go for different food and for different structures if possible.
        if len(myWorkers) == 2:
            # So, if our workers are going for the same food...thats bad.
            if approxDist(myWorkers[0].coords, foodCoord1) < approxDist(myWorkers[0].coords, foodCoord2) \
                    and approxDist(myWorkers[1].coords, foodCoord1) < approxDist(myWorkers[1].coords, foodCoord2):
                rating -= 4
            # Going for same food...
            elif approxDist(myWorkers[0].coords, foodCoord1) > approxDist(myWorkers[0].coords, foodCoord2) \
                    and approxDist(myWorkers[1].coords, foodCoord1) > approxDist(myWorkers[1].coords, foodCoord2):
                rating -= 4
            # We also want them going for different tunnel/anthills so they dont get stuck.
            if approxDist(myWorkers[0].coords, myTunnel) < approxDist(myWorkers[0].coords, myTunnel) \
                    and approxDist(myWorkers[1].coords, myTunnel) < approxDist(myWorkers[1].coords, myTunnel):
                rating -= 4
            elif approxDist(myWorkers[0].coords, myAnthill) > approxDist(myWorkers[0].coords, myAnthill) \
                    and approxDist(myWorkers[1].coords, myAnthill) > approxDist(myWorkers[1].coords, myAnthill):
                rating -= 4

        # Go through every worker in our inventory.
        for worker in myWorkers:
            if (worker.carrying):  # If they are carrying food...Compute distance to anthill verse tunnel
                anthilldistance = approxDist(worker.coords, getConstrList(gameState, me, (ANTHILL,))[0].coords)
                tunnelDistance = approxDist(worker.coords, getConstrList(gameState, me, (TUNNEL,))[0].coords)
                # If the anthill is closer, then skew it so we move towards it.
                if (anthilldistance < tunnelDistance):
                    rating += 5 - ((anthilldistance) + 1) / 100
                    # Skew it the other way if its the tunnel
                elif (tunnelDistance < anthilldistance):
                    rating += 5 - ((tunnelDistance) + 1) / 100
                else:
                    # If they are the same, default to the tunnel.
                    rating += ((tunnelDistance) + 1) / 100
                # If our move while carrying puts us on the anthill or tunnel, prioritize that.
                if (myAnthill == worker.coords):
                    rating += 10
                elif (myTunnel == worker.coords):
                    rating += 10
            else:
                # calculate closest food. (Same logic as closest tunnel or anthill)

                fooddistance = approxDist(worker.coords, foodCoord1)  # First food
                fooddistance2 = approxDist(worker.coords, foodCoord2)  # Second food
                if (fooddistance < fooddistance2):
                    rating += 5 - (fooddistance + 1) / 5  # The closer the food, the better
                elif fooddistance >= fooddistance2:
                    rating += 5 - (fooddistance2 + 1) / 5
                elif fooddistance == 0 or fooddistance2 == 0:
                    rating += 15  # If we end up on food...thats good.

        # checking to the food count
        rating += 2.5 * myInv.foodCount  # As our food count increases, increase the rating.

        health = 0
        for enemyAnt in enemyAnts:
            health += enemyAnt.health
        rating += 10 / (health + 1)  # Less enemy health means a higher rating.

        # If our queen is on the anthill..or its moving illegally..make that move bad.
        if (Queenlocation[1] > 3 or Queenlocation == myAnthill):
            return -.8 + numWorkers / 100
        # Make sure queen is not sitting on food.
        elif foodCoord2 == Queenlocation or foodCoord1 == Queenlocation:
            return -.8
        # Rating between -1.0 and 1.0.
        return rating / 100

    # Evaluation function for the number of workers that the AI controls
    def evalWorkerCount(self, currentState, test = False, testvar = None):
        if test:
            workerCount = testvar
        else:
            workerCount = len(getAntList(currentState, currentState.whoseTurn, (WORKER,)))
        # Reward the AI for having only one worker
        if (workerCount > 1):
            return -1.0
        else:
            return workerCount

    # Evaluation function for the number of soldier that the AI controls
    def evalSoldierCount(self, currentState, test = False, testvar = None):
        if test:
            soldierCount = testvar
        else:
            soldierCount = len(getAntList(currentState, currentState.whoseTurn, (SOLDIER,)))
        # Reward for having more than 10 soldiers
        if (soldierCount > 3):
            return -1.0
        else:
            return 0.33 * soldierCount

    # Evaluation function for the difference in ants between AIs
    def evalAntDifference(self, currentState, test = False, testMyAnts = None, testEnemyAnts = None):
        if test:
            myAntCount = testMyAnts
            enemyAntCount = testEnemyAnts
        else:
            me = currentState.whoseTurn
            myAntCount = len(getAntList(currentState, me))
            enemyAntCount = len(getAntList(currentState, 1-me))
        # Evaluation score is the ratio of our AI's ants vs the total number of ants on the board
        return (myAntCount-enemyAntCount) / (myAntCount+enemyAntCount)

    def evalEnemyQueenHealthDifference(self, currentState, test=False, testMyAnts = None, testEnemyAnts = None):
        enemyQueenHealth = getEnemyInv(None,currentState).getQueen().health
        return 1- ((enemyQueenHealth)/(10))

    # Evaluation function for the difference in health of the ants between AIs
    def evalHealthDifference(self, currentState, test = False, testMyAntList = None, testEnemyAntList = None):
        if test:
            myAnts = testMyAntList
            enemyAnts = testEnemyAntList
        else:
            me = currentState.whoseTurn
            myAnts = getAntList(currentState, me)
            enemyAnts = getAntList(currentState, 1-me)

        myTotalHealth = 0
        enemyTotalHealth = 0
        for ant in myAnts:
            myTotalHealth += ant.health
        for ant in enemyAnts:
            enemyTotalHealth += ant.health
        return (myTotalHealth-enemyTotalHealth) / (myTotalHealth+enemyTotalHealth)

    # Evaluation function for the position of the worker
        # Rewards AI for collection food and bring the food back to the anthill/tunnel
    def evalWorkerPositions(self, currentState):
        me = currentState.whoseTurn
        workerList = getAntList(currentState, me, (WORKER,))
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

        myInv = getCurrPlayerInventory(currentState)
        totalStepsToDestination += (11-myInv.foodCount) * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        scoreCeiling = 12 * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        evalScore = scoreCeiling - totalStepsToDestination
        # Max possible score is 1.0, where all workers are at their destination.
        return (evalScore/scoreCeiling)

    # Evaluation function for the position of the soldier
        # Rewards for being closer to enemy ants resulting in attack
    def evalSoldierPositions(self, currentState):
        me = currentState.whoseTurn
        soldierList = getAntList(currentState, me, (SOLDIER,))
        if (len(soldierList) == 0):
            return 0.0
        # Save the coordinates of all the enemy's ants.
        enemyAntCoords = self.getCoordsOfListElements(getAntList(currentState, 1-me))

        totalStepsToEnemy = 0
        for soldier in soldierList:
            totalStepsToEnemy += self.getMinStepsToTarget(soldier.coords, enemyAntCoords)

        # 30 steps is around the furthest distance one soldier could theoretically be
        # from an enemy ant. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_ENEMY = 30
        scoreCeiling = MAX_STEPS_FROM_ENEMY * len(soldierList)
        evalScore = scoreCeiling - totalStepsToEnemy
        # Max possible score is 1.0, where all soldiers are at their destination.
        return (evalScore/scoreCeiling)

    # Evaluation function for the position of the queen
        # Rewards AI for moving away from the closest enemy and not on the anthill/tunnel
    def evalQueenPosition(self, currentState):
        me = currentState.whoseTurn
        queen = getCurrPlayerQueen(currentState)
        enemyAnts = getAntList(currentState, 1-me, (DRONE, SOLDIER, R_SOLDIER))
        enemyAntCoords = self.getCoordsOfListElements(enemyAnts)
        totalDistance = 0
        for enemyCoords in enemyAntCoords:
            totalDistance += approxDist(queen.coords, enemyCoords)

        if (len(enemyAntCoords) > 0):
            MAX_STEPS_FROM_ENEMY = 30
            scoreCeiling = MAX_STEPS_FROM_ENEMY * len(enemyAntCoords)
            buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return totalDistance/scoreCeiling
        else:
            buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return 1.0

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
    def evalOverall(self, currentState, move):
        # Determine if the game has ended and who won
        winResult = getWinner(currentState)
        if winResult == 1:
            return 1.0
        elif winResult == 0:
            return -1.0
        # else neither player has won this state.
        if move.buildType in [R_SOLDIER, DRONE, WORKER]:
            return -0.99

        # Initialize the totalScore
        totalScore = 0

        # Initialize the weights for the specific evaluation functions
        workerCountWeight = 1
        soldierCountWeight = 1
        antDifferenceWeight = 0
        healthDifferenceWeight = 1
        workerPositionWeight = 1
        soldierPositionWeight = 1
        queenPositionWeight = 1
        enemyQueenHealthWeight = 0
        totalWeight = workerCountWeight+soldierCountWeight+antDifferenceWeight+\
                                        healthDifferenceWeight+ workerPositionWeight+\
                                        soldierPositionWeight+queenPositionWeight+enemyQueenHealthWeight

        # Determine evaluation scores multiplied by it weights
        totalScore += self.evalWorkerCount(currentState) * workerCountWeight
        totalScore += self.evalSoldierCount(currentState) * soldierCountWeight
        totalScore += self.evalAntDifference(currentState) * antDifferenceWeight
        totalScore += self.evalHealthDifference(currentState) * healthDifferenceWeight
        totalScore += self.evalWorkerPositions(currentState) * workerPositionWeight
        totalScore += self.evalSoldierPositions(currentState) * soldierPositionWeight
        totalScore += self.evalQueenPosition(currentState) * queenPositionWeight
        totalScore += self.evalEnemyQueenHealthDifference(currentState) * enemyQueenHealthWeight


        ### OVERALL WEIGHTED AVERAGE ###
        # Takes the weighted average of all of the scores
        # Only the game ending scores should be 1 or -1.
        overallScore = 0.99 * totalScore / totalWeight

        return overallScore

    # Recursion function to search for the best move per depth
    def greedyGetBestMove(self, currentState, currentDepth, currentNode):
        moves = []
        moves.extend(listAllMovementMoves(currentState))
        moves.append(Move(END, None, None))
        moves.extend(listAllBuildMoves(currentState))
        print(len(moves))


        localNum = 0
        for child_move in moves:
            if self.prune:
                break

            if currentDepth >= self.depthLimit:
                stateScore = self.analyzeGameState(currentNode.state)

                if not currentNode.parent.turn and (-1*stateScore < currentNode.parent.beta):
                    currentNode.parent.beta = stateScore*-1
                    if currentNode.parent.alpha >= currentNode.parent.beta:
                        #print("Pruning Tree:")
                       # print("The Alpha Val is: " + str(currentNode.parent.alpha))
                        #print("The Beta Val is: " + str(currentNode.parent.beta))
                        self.prune = True
                    return
                if currentNode.parent.turn and stateScore > currentNode.parent.alpha:
                    currentNode.parent.alpha = stateScore
                    if currentNode.parent.alpha >= currentNode.parent.beta:
                        #print("Pruning Tree:")
                        #print("The Alpha Val is: " + str(currentNode.parent.alpha))
                        #print("The Beta Val is: " + str(currentNode.parent.beta))
                        self.prune = True
                    return

                return
            else:
                resultState = getNextStateAdversarial(currentState, child_move)

                if not currentNode.turn:
                    if child_move.moveType == END:
                        resultNode = Node(resultState, child_move, 1000, currentNode, not currentNode.turn, currentNode.alpha, currentNode.beta)
                    else:
                        resultNode = Node(resultState, child_move, 1000, currentNode, currentNode.turn, currentNode.alpha,
                                          currentNode.beta)
                else:
                    if child_move.moveType == END:
                        resultNode = Node(resultState, child_move, -1000, currentNode, not currentNode.turn, currentNode.alpha, currentNode.beta)
                    else:
                        resultNode = Node(resultState, child_move, -1000, currentNode, currentNode.turn, currentNode.alpha,
                                          currentNode.beta)

                self.greedyGetBestMove(resultNode.state, currentDepth + 1, resultNode)

        if not self.prune:
            if currentNode.turn:
                currentNode.score = currentNode.alpha
            else:
                currentNode.score = currentNode.beta
        else:
            self.prune = False
            return


        if currentDepth > 0:
            #print("currentNode.parent.turn: " + str(currentNode.parent.turn))
           # print("currentNode.score: " + str(currentNode.score))
            #print("currentNode.parent.alpha: " + str(currentNode.alpha))
            #print("currentNode.parent.beta: " + str(currentNode.beta))
            if not currentNode.parent.turn and (currentNode.score < currentNode.parent.beta):
                #print("Passing up beta")
                currentNode.parent.beta = currentNode.score
                if currentDepth == 1:
                    self.bestMove = currentNode.move
                    #print(self.bestMove)
            elif currentNode.parent.turn and (currentNode.score > currentNode.parent.alpha):
                #print("Passing up alpha")
                currentNode.parent.alpha = currentNode.score
                if currentDepth == 1:
                    self.bestMove = currentNode.move
                    #print(self.bestMove)
        return


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
        print("MOVE: " + str(self.bestMove))
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

# Node class that creates a new instance of a game state
# Takes in the game state, the move that was made to reach the state, the evaluation score of the state
# and the parent game state
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
if testAI.evalSoldierCount(None,True,5) != -1:
    print("ERROR: Soldier Count Evaluation2")
if testAI.evalSoldierCount(None,True,3) != .99:
    print("ERROR: Soldier Count Evaluation3")
if testAI.evalSoldierCount(None,True,12) != -1:
    print("ERROR: Soldier Count Evaluation4")

# evalAntDifference
if testAI.evalAntDifference(None,True,1,1) != 0:
    print("ERROR: Ant Difference Evaluation1")
if testAI.evalAntDifference(None,True,1,2) != -1/3:
    print("ERROR: Ant Difference Evaluation2")
if testAI.evalAntDifference(None,True,2,1) != 1/3:
    print("ERROR: Ant Difference Evaluation3")
if testAI.evalAntDifference(None,True,3,2) != .2:
    print("ERROR: Ant Difference Evaluation4")
if testAI.evalAntDifference(None,True,2,3) != -.2:
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
