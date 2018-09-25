import random
import sys
import time
import unittest
import math
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

DEPTH_LIMIT = 3

##
#AIPlayer
#Andrew Ripple and Chris Sebrechts
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##

class nodeOfTree: #Defines a node for the recursion algoithm (One node of the bigger tree)
    def __init__(self, gameState, currentDepth, move):
        self.move = move #The move it took to get to this node.
        self.state = gameState # The gamestate of the node.
        self.score = -1.0 #Its score
        self.parent = None #A reference to its parent.
        self.depth = currentDepth #Its depth

class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "HybridDepthBreadth")
    
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
        root = nodeOfTree(currentState, 0, None)
        root.score = self.analyzeGameState(currentState)
        move = self.recursion(currentState, 0, root)
        return move
    
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


#METHOD
#ANALYZES GAMESTATE OF CURRENT STATE.
#RETURNS A VALUE BETWEEN -1.0 and 1.0 depending on how good the state is
    def analyzeGameState(self, gameState):
        me = gameState.whoseTurn #My turn
        enemy = 1-me #Enemy ID
        #Get a whole lot of information about the current game state...ie
        #Where my anthill, tunnel are at
        #Num of workers.
        #Enemy ants, etc
        myInv = getCurrPlayerInventory(gameState)
        myWorkers = getAntList(gameState,me,(WORKER,))
        thisSoldier= getAntList(gameState,me,(SOLDIER,))
        myAnthill= getConstrList(gameState,me,(ANTHILL,))[0].coords
        myTunnel = getConstrList(gameState,me,(TUNNEL,))[0].coords
        numFood = len(getCurrPlayerFood(self, gameState))
        foodCoord1 = getCurrPlayerFood(self, gameState)[0].coords
        foodCoord2 = getCurrPlayerFood(self, gameState)[1].coords
        rating = 0
        numWorkers = len(getAntList(gameState,me, (WORKER,)))
        Queenlocation = getAntList(gameState,me,(QUEEN,))[0].coords
        enemyAnts = getAntList(gameState,enemy,(DRONE,SOLDIER,WORKER))



         #all based on food
        #If num food is 11, we have won. so return 1.0
        if (numFood == 11):
            return 1.0
        #If numWorkers is less than 1, then if we have 0 food, we have lost. Return -1.0
        if(numWorkers < 1):
            if(numFood == 0):
               return -1.0
        #If we have 1 workers, thats good, add 5.
        if(numWorkers == 1):
            rating += 5
        #If we have 2 workers, thats better...add 10.
        elif(numWorkers==2 and approxDist(foodCoord1,foodCoord2) > 2 and approxDist(myTunnel,myAnthill) > 2):
            rating += 10
        #If we have 3 workers...bad...subract 5
        elif(numWorkers >= 3):
            rating += -5


        # routes to worker
        #If we have one soldier...thats good.
        if (len(thisSoldier) == 1):
            rating += 5
            #How many enemies are out.
            enemyUnitsLength = len(getAntList(gameState, enemy, (DRONE, WORKER,)))
            #What is next to our Soldier.
            soldierAdjacent = listAdjacent(thisSoldier[0].coords)
            blocking = False
            for adj in soldierAdjacent:
                #If the queen is adjacent to our Soldier...or is making an illegal move..or blocking stuff..(BAD)
                if Queenlocation != adj and Queenlocation[1] <= 3 and Queenlocation != myAnthill and Queenlocation != myTunnel \
                            and Queenlocation != foodCoord1 and Queenlocation != foodCoord2:
                    continue
                else:
                    blocking = True #if its blocking...bad
                    rating -= 4
            if not blocking:
                rating += 4 #We want a queen that is not blocking anything
            if (enemyUnitsLength > 0): #If they have some workers or drones.
                enemyworkerdistance = approxDist(thisSoldier[0].coords,
                                                     getAntList(gameState, enemy, (DRONE, WORKER,))[0].coords)

                #this makes sure the soldier keeps moving forward if it can.
                if (thisSoldier[0].coords[1] > myAnthill[1]):
                    rating += 5 #Make the soldier move forward.

                rating += 6 - (enemyworkerdistance + 1) / 10 #Add a rating based off of the distance away it is from enemies.
                #The closer it is, the better the rating.

            elif len(getAntList(gameState, enemy, (QUEEN,))) == 1: #If Its just the queen left.
                enemyqueendistance = approxDist(thisSoldier[0].coords,
                                                    getAntList(gameState, enemy, (QUEEN,))[0].coords)
                #If our soldier can get adjacent and attack..DO IT.
                queenAdj = listAdjacent(getAntList(gameState, enemy, (QUEEN,))[0].coords)
                attack = False
                for adj in queenAdj: #Check adjacent squares
                    if thisSoldier[0].coords == adj: #If our soldier is there..good.
                        attack = True
                if attack: #If it can attack, good.
                    rating += 10
                else: #if it cant, just get closer.
                    rating += 5 - (enemyqueendistance + 1) / 10
            else: #if they have no queen...we win.
                return 1.0

        #IF WE HAVE 2 WORKERS...We want them to go for different food and for different structures if possible.
        if len(myWorkers) == 2:
            #So, if our workers are going for the same food...thats bad.
            if approxDist(myWorkers[0].coords, foodCoord1) < approxDist(myWorkers[0].coords, foodCoord2) \
                        and approxDist(myWorkers[1].coords, foodCoord1) < approxDist(myWorkers[1].coords, foodCoord2):
                rating -= 4
            #Going for same food...
            elif approxDist(myWorkers[0].coords, foodCoord1) > approxDist(myWorkers[0].coords, foodCoord2) \
                        and approxDist(myWorkers[1].coords, foodCoord1) > approxDist(myWorkers[1].coords, foodCoord2):
                rating -= 4
            #We also want them going for different tunnel/anthills so they dont get stuck.
            if approxDist(myWorkers[0].coords, myTunnel) < approxDist(myWorkers[0].coords, myTunnel) \
                        and approxDist(myWorkers[1].coords, myTunnel) < approxDist(myWorkers[1].coords, myTunnel):
                rating -= 4
            elif approxDist(myWorkers[0].coords, myAnthill) > approxDist(myWorkers[0].coords, myAnthill) \
                        and approxDist(myWorkers[1].coords, myAnthill) > approxDist(myWorkers[1].coords, myAnthill):
                rating -= 4

        #Go through every worker in our inventory.
        for worker in myWorkers:
            if (worker.carrying): #If they are carrying food...Compute distance to anthill verse tunnel
                anthilldistance = approxDist(worker.coords, getConstrList(gameState, me, (ANTHILL,))[0].coords)
                tunnelDistance = approxDist(worker.coords, getConstrList(gameState, me, (TUNNEL,))[0].coords)
                #If the anthill is closer, then skew it so we move towards it.
                if (anthilldistance < tunnelDistance):
                    rating += 5 - ((anthilldistance) + 1) / 100
                    #Skew it the other way if its the tunnel
                elif (tunnelDistance < anthilldistance):
                    rating += 5 - ((tunnelDistance) + 1) / 100
                else:
                    #If they are the same, default to the tunnel.
                    rating += ((tunnelDistance) + 1) / 100
                #If our move while carrying puts us on the anthill or tunnel, prioritize that.
                if (myAnthill == worker.coords):
                    rating += 10
                elif (myTunnel == worker.coords):
                    rating += 10
            else:
                #calculate closest food. (Same logic as closest tunnel or anthill)

                fooddistance = approxDist(worker.coords, foodCoord1) #First food
                fooddistance2 = approxDist(worker.coords, foodCoord2) #Second food
                if (fooddistance < fooddistance2):
                    rating += 5 - (fooddistance+1) / 5 #The closer the food, the better
                elif fooddistance >= fooddistance2:
                    rating += 5 - (fooddistance2+1) / 5
                elif fooddistance == 0 or fooddistance2 == 0:
                    rating += 15 #If we end up on food...thats good.

        # checking to the food count
        rating += 2.5 * myInv.foodCount #As our food count increases, increase the rating.

        health = 0
        for enemyAnt in enemyAnts:
            health += enemyAnt.health
        rating += 10 / (health + 1) #Less enemy health means a higher rating.

        #If our queen is on the anthill..or its moving illegally..make that move bad.
        if (Queenlocation[1] > 3 or Queenlocation == myAnthill):
            return -.8 + numWorkers/100
        #Make sure queen is not sitting on food.
        elif foodCoord2 == Queenlocation or foodCoord1 == Queenlocation:
            return -.8
        #Rating between -1.0 and 1.0.
        return rating / 100

#METHOD THAT ANALYZES A LIST OF NODES AND RETURNS THE ONE WITH THE HIGHEST SCORE.
    def analyzeNodes(self, listNodes):
        bestNode = None #Set to none
        bigNum = -1.0 #Default value to beat.

        if len(listNodes) == 0:
            return None #If there is nothing in our list..return None
        for node in listNodes: #Go through each node, and analyze its game state
            node.score = self.analyzeGameState(node.state)
            if node.score > bigNum: #Compare to best score yet.
                bestNode = node #If the score is better, the best node is updated to that node.
                bigNum = node.score #Best score updated
        return bestNode #return best Node found






#RECURSIVE METHOD THAT ANALYZES 3 LAYERS OF NODES TO FIND THE BEST MOVE
#Hybrid of Depth/Breadth first search.
#Takes the best Node + some of the other better ones and expands them.
    def recursion(self, gameState, currentDepth, parent):
        moveList = listAllLegalMoves(gameState) #List of all possible moves.
        nodeList = [] #List of nodes to analyze
        iter = 0 #Keep track of where we are in loop
        for move in moveList: #Each move
            newNode = nodeOfTree(gameState, currentDepth, move) #Create a node for each move.
            if move.moveType == "END": #If the move type is end, just delete it.
                del iter
            nodeList.append(newNode)#Append node to our list
            nodeList[iter].parent = parent #set its parent
            nodeList[iter].state = getNextState(gameState, move) #Get its actual state.
            nodeList[iter].depth = currentDepth #set its current depth
            nodeList[iter].move = move #Set its move it took to get there.
            iter += 1 #Increase iter
        highestScoreNode = self.analyzeNodes(nodeList)  # analyze the nodes we just created...see which one is the best
        if currentDepth < DEPTH_LIMIT: #if our depth has not been reached yet.
            currentDepth += 1 #Iterate our depth
            bestScore = parent.score #Our best score right now is the parent above us technically.
            bestList = [] #Holds best nodes to try.
            for node in nodeList: #Each node
                if node.score > bestScore: #Add best nodes to the best list.
                    bestList.append(node)
                    bestScore = node.score
            for node in bestList: #Do recursion on the best nodes.
                node.score = self.recursion(node.state, currentDepth, node)

        #if our highest node is not none.
        if highestScoreNode is not None:
            if highestScoreNode.depth > 0: #Make sure of its depth.
                return highestScoreNode.score #if its not zero, we pass up the score.
            else:
                #otherwise, we pass the move at the top level
                return highestScoreNode.move
        else:
            #If our best scorenode is zero...return -1.0. (Edge case if bottom level has bad nodes)
            return -1.0


class test_calc(unittest.TestCase):

    def testRecursion(self):
        AIplayer = AIPlayer(PLAYER_ONE) #AI Player...to call methods.
        gameState = GameState.getBasicState()
        #Add food to the basic gamestate
        constr = Building((0, 5), FOOD, PLAYER_ONE)
        constr1 = Building((1, 4), FOOD, PLAYER_ONE)
        constr2 = Building((4, 2), FOOD, PLAYER_TWO)
        constr3 = Building((3, 3), FOOD, PLAYER_TWO)
        #Add food to players inventories.
        gameState.inventories[NEUTRAL].constrs.append(constr)
        gameState.inventories[NEUTRAL].constrs.append(constr1)
        gameState.inventories[NEUTRAL].constrs.append(constr2)
        gameState.inventories[NEUTRAL].constrs.append(constr3)
        #Create a node with the game state at depth 3.
        nodeOne = nodeOfTree(gameState, 3, None)
        nodeOne.score = 0 #its score is 0.
        nodeOne.parent = None
        nodeList = []
        nodeList.append(nodeOne)
        #There should be a move better than a score of 0 if we use recursion on this...see if that is the case.
        #First test makes sure that the score returned by a depth 3 call is not nodeOnes score.
        # Second Test makes sure the move of nodeOne is not the move that is returned if it was the depth 0 node.
        # Third test makes sure that the node returned has a higher score than nodeOne's score.
        self.assertNotEqual(AIplayer.recursion(gameState,3,nodeOne), nodeOne.score, "Better score not found..Error")
        self.assertNotEqual(AIplayer.recursion(gameState, 0, nodeOne), nodeOne.move, "Same node is the best...error")
        self.assertGreater(AIplayer.recursion(gameState, 3, nodeOne), nodeOne.score, "Worse node found, error")


    def testAnalyzeNodes(self):
        #Tests to make sure that nodes with higher scores are returned.
        AIplayer = AIPlayer(PLAYER_ONE) #the Player
        gameState = GameState.getBasicState() #The first game state
        gameState2 = GameState.getBasicState() #The second game state.
        currentDepth = 0 #Our current depth is 0.
        #Create 4 foods.
        constr = Building((0,5), FOOD, PLAYER_ONE)
        constr1 = Building((1, 4), FOOD, PLAYER_ONE)
        constr2 = Building((4, 2), FOOD, PLAYER_TWO)
        constr3 = Building((3, 3), FOOD, PLAYER_TWO)
        #Add the foods to both states.
        gameState.inventories[NEUTRAL].constrs.append(constr)
        gameState.inventories[NEUTRAL].constrs.append(constr1)
        gameState.inventories[NEUTRAL].constrs.append(constr2)
        gameState.inventories[NEUTRAL].constrs.append(constr3)
        gameState2.inventories[NEUTRAL].constrs.append(constr)
        gameState2.inventories[NEUTRAL].constrs.append(constr1)
        gameState2.inventories[NEUTRAL].constrs.append(constr2)
        gameState2.inventories[NEUTRAL].constrs.append(constr3)
        #create our first node...holds the first game state.
        nodeOne = nodeOfTree(gameState, currentDepth, None)
        #Create a worker ant for player one.
        ant = Ant((2, 2), WORKER, PLAYER_ONE)
        gameState2.board[2][2].ant = ant
        gameState2.inventories[PLAYER_ONE].ants.append(ant)
        #Node Two has second game state (A better gamestate)
        nodeTwo = nodeOfTree(gameState2, currentDepth, None)
        listNodes = []
        listNodes.append(nodeOne)
        listNodes.append(nodeTwo)
        #Game state 2 is better than 1, so nodeTwo should be returned.
        self.assertEqual(AIplayer.analyzeNodes(listNodes), nodeTwo, "Failed to Anaylize Nodes Properly")


    def testHeuristic(self):
        #Same set up as above unit test...but only one gamestate.
        AIplayer = AIPlayer(PLAYER_ONE)
        gameState = GameState.getBasicState()
        #Set up the food.
        constr = Building((0, 5), FOOD, PLAYER_ONE)
        constr1 = Building((1, 4), FOOD, PLAYER_ONE)
        constr2 = Building((4, 2), FOOD, PLAYER_TWO)
        constr3 = Building((3, 3), FOOD, PLAYER_TWO)
        #add it to everyones inventory.
        gameState.inventories[NEUTRAL].constrs.append(constr)
        gameState.inventories[NEUTRAL].constrs.append(constr1)
        gameState.inventories[NEUTRAL].constrs.append(constr2)
        gameState.inventories[NEUTRAL].constrs.append(constr3)
        #Make sure that when we analyze game state 1, we get -0.8, since the queen is on the anthill.
        self.assertEqual(AIplayer.analyzeGameState(gameState), -0.8, "Failed to Anaylize GameState Properly")
        ant = Ant((2, 2), WORKER, PLAYER_ONE)
        gameState.board[2][2].ant = ant
        gameState.inventories[PLAYER_ONE].ants.append(ant)
        #Gamestate 1 now has an ant on the board, so this means the rating should increase .01.
        self.assertEqual(AIplayer.analyzeGameState(gameState), -0.79, "Failed to Anaylize GameState Properly")


if __name__ == '__main__':
    unittest.main()





