#!/usr/bin/python -u

import sys, json

shortCommands = {
    "n" : "north",
    "e" : "east",
    "s" : "south",
    "w" : "west"
}

class StevePlayer:
    def __init__(self, room):
        self.room = room
        self.dead = False
        self.won = False
        self.state = {}
        self.inv = []

class SteveWorld:
    def getStartRoom(self):
        return "start"
    
    def getDescription(self, room):
        pass
    
    def getActions(self, room):
        pass
        
    def isRoom(self, room):
        pass

class SteveInterface:
    def printLines(self, lines):
        pass
    
    def printDebug(self, message):
        pass

class SteveEngine:
    def __init__(self, world):
        self.world = world
    
    def evaluateConditions(self, interface, player, conditions, extra):
        for cond in conditions:
            if cond["type"] == "extra":
                foundMatch = True
                for required in cond["extra"]:
                    if len(required) == len(extra):
                        foundMatch = True
                        for i in range(len(extra)):
                            if required[i] != extra[i]:
                                foundMatch = False
                                break
                if not foundMatch:
                    interface.printDebug("DEBUG: CONDFAIL: Failed to match " + str(extra) + " to any of " + str(required))
                    return False
                    
            elif cond["type"] == "state":
                var = cond["var"]
                op = cond["op"]
                if var in player.state:
                    if op == "unset":
                        interface.printDebug("DEBUG: CONDFAIL: wanted unset for var " + var)
                        return False
                    if op != "set":
                        val = cond["val"]
                        if op == "=" or op == "eq":
                            if val != player.state[var]:
                                return False
                        elif op == "!=" or op == "ne":
                            if val == player.state[var]:
                                return False
                elif op != "unset":
                    interface.printDebug("DEBUG: CONDFAIL: var " + var + " was not set")
                    return False                        
                    
        return True
    
    def processAction(self, interface, player, action, extra):
        if "conditions" in action:
            if not self.evaluateConditions(interface, player, action["conditions"], extra):
                return False
        
        if "actions" in action:
            for subaction in action["actions"]:
                if not self.processAction(interface, player, subaction, extra):
                    return False
            return True
        elif "choice" in action:
            for subaction in action["choice"]:
                if self.processAction(interface, player, subaction, extra):
                    return True
        elif "action" in action:
            if action["action"] == "move":
                player.room = action["room"]
                if not self.world.isRoom(player.room):
                    interface.printLines("You find yourself in a room the developer was too lazy to create.\n"+
                                         "You have contracted dysentery.")
                    player.dead = True
            elif action["action"] == "die":
                player.dead = True
                if "message" in action:
                    interface.printLines(action["message"])
            elif action["action"] == "win":
                player.won = True
                if "message" in action:
                    interface.printLines(action["message"])
            elif action["action"] == "message":
                interface.printLines(action["message"])
            elif action["action"] == "state_set":
                var = action["var"]
                val = True
                if "val" in action:
                    val = action["val"]
                player.state[var] = val
            elif action["action"] == "state_unset":
                var = action["var"]
                player.state.pop(var, None)
            else:
                print "WARN: Cannot understand action " + action["action"]
                return False
            return True
        else:
            print "WARN: Cannot find property 'action', 'actions' or 'choice' in room " + player.room
                
        
        return False
    
    def process(self, interface, player, commandLine):
        cmdLine = commandLine.lower().strip()
        cmdArr = cmdLine.split(' ')
        cmd = cmdArr[0]
        extra = []
        if len(cmdArr) > 1:
            extra = cmdArr[1:]
        
        actions = self.world.getActions(player.room)
        
        if cmd in shortCommands:
            cmd = shortCommands[cmd]
        
        if cmd in actions:
            if self.processAction(interface, player, actions[cmd], extra):
                return True
        elif cmd in ["north", "east", "south", "west"]:
            interface.printLines("I can't go that way.")
            return False
        
        interface.printLines("I don't know how to " + commandLine + ".")
        return False

class JsonWorld(SteveWorld):
    def __init__(self, jsonFile):
        with open(jsonFile, "r") as fp:
            self.__world = json.load(fp)

    def getDescription(self, room):
        if not room in self.__world["rooms"]:
            return ""
        if not "desc" in self.__world["rooms"][room]:
            return ""
        return self.__world["rooms"][room]["desc"]

    def getActions(self, room):
        if not room in self.__world["rooms"]:
            return {}
        if not "actions" in self.__world["rooms"][room]:
            return {}
        return self.__world["rooms"][room]["actions"]

    def isRoom(self, room):
        return room in self.__world["rooms"]

class ConsoleInterface(SteveInterface):
    def __init__(self):
        self.debug = False
    
    def printLines(self, lines):
        print lines

    def printDebug(self, lines):
        if self.debug:
            print "DEBUG : " + lines

    def run(self, engine):
        playing = True
        try:
            while playing:
                player = StevePlayer(engine.world.getStartRoom())
        
                showDescription = True
                while not (player.won or player.dead):
                    self.printLines("")
                    if showDescription:
                        desc = engine.world.getDescription(player.room)
                        if desc != "":
                            self.printLines(desc)
                    input = raw_input('> ').strip()
                    if input == "quit":
                        playing = False
                        break
                    showDescription = engine.process(self, player, input)
            
                if not playing:
                    break
            
                if player.won:
                    input = ""
                    while input not in ["y", "n"]:
                        print "You won! Play again? (Y/N)"
                        input = raw_input("> ").strip().lower()
                    playing = input == "y"
                elif player.dead:
                    input = ""
                    while input not in ["y", "n"]:
                        print "You have died! Try again? (Y/N)"
                        input = raw_input("> ").strip().lower()
                    playing = input == "y"
        except (EOFError, KeyboardInterrupt):
            print ""

class DevToolBaseRoomVisitor:
    def __init__(self, world):
        self.world = world
        
    def getAllDestinations(self, action):
        if "action" in action:
            if action["action"] == "move":
                return [action["room"]]
        elif "actions" in action:
            retVal = []
            for subaction in action["actions"]:
                retVal += self.getAllDestinations(subaction)
            return retVal
        elif "choice" in action:
            retVal = []
            for subaction in action["choice"]:
                retVal += self.getAllDestinations(subaction)
            return retVal
                
        return []
        
    def visitRooms(self):
        visitedRooms = []
        toVisit = [self.world.getStartRoom()]

        while len(toVisit) > 0:
            room = toVisit.pop()
            visitedRooms.append(room)
            
            actions = self.world.getActions(room)
            self.onRoom(room, actions)
            
            for actionId, action in actions.iteritems():
                for adjRoom in self.getAllDestinations(action):
                    if adjRoom not in visitedRooms and adjRoom not in toVisit:
                        toVisit.append(adjRoom)

    def onRoom(self, room, actions):
        pass

class DevToolDotPrinter(DevToolBaseRoomVisitor):
    def __init__(self, world):
        DevToolBaseRoomVisitor.__init__(self, world)
    
    def getDotRepresentation(self):
        self.retVal = "digraph {\n"
        self.retVal += "  " + self.world.getStartRoom() + " [ shape=\"doublecircle\" ]\n"
        self.visitRooms()
        self.retVal += "}\n"
        return self.retVal
    
    def onRoom(self, room, actions):
        if not self.world.isRoom(room):
            self.retVal += "  " + room + " [ style=\"filled\", fillcolor=\"red\"]\n"
        for actionId, action in actions.iteritems():
            edges = []
            for adjRoom in self.getAllDestinations(action):
                if adjRoom not in edges:
                    edges.append(adjRoom)
                    self.retVal += "  " + room + " -> " + adjRoom + " [ label=\"" + actionId + "\" ]\n"

class DevToolStatistics(DevToolBaseRoomVisitor):
    def __init__(self, world):
        self.world = world
    
    def getCounts(self):
        self.counts = { "Room Count" : 0 }
        self.visitRooms()
        return self.counts

    def onRoom(self, room, actions):
        self.counts["Room Count"] += 1
        for actionId, action in actions.iteritems():
            cmdKey = "Command " + actionId
            if cmdKey not in self.counts:
                self.counts[cmdKey] = 1
            else:
                self.counts[cmdKey] += 1
            self.onAction(action)
    
    def onAction(self, action):
        actionKey = None
        if "action" in action:
            actionKey = "Action " + action["action"]
        elif "actions" in action:
            actionKey = "Action actions"
            for subaction in action["actions"]:
                self.onAction(subaction)
        elif "choice" in action:
            actionKey = "Action choice"
            for subaction in action["choice"]:
                self.onAction(subaction)
        else:
            return
                
        if actionKey not in self.counts:
            self.counts[actionKey] = 1
        else:
            self.counts[actionKey] += 1


class DevToolWorldChecker(DevToolBaseRoomVisitor):
    def __init__(self, world):
        self.world = world
        
    def check(self, printErrors=True):
        self.errors = []
        self.visitRooms()
        if printErrors:
            if len(self.errors) > 0:
                self.printErrors(self.errors)
            else:
                print "OK!"
        return self.errors
    
    def printErrors(self, errors):
        for err in errors:
            print err["type"].upper() + " " + err["room"] + "{" + err["actionId"] + "} - " + err["message"]

    def warn(self, room, actionId, action, message):
        self.errors.append({'type' : 'warn', 'room' : room, 'actionId' : actionId, 'action' : action, 'message' : message})

    def error(self, room, actionId, action, message):
        self.errors.append({'type' : 'error', 'room' : room, 'actionId' : actionId, 'action' : action, 'message' : message})

    def onRoom(self, room, actions):
        for actionId, action in actions.iteritems():
            self.onAction(room, actionId, action)
        
    def onAction(self, room, actionId, action):
        if "action" in action:
            if "actions" in action:
                self.warn(room, actionId, action, "Found 'actions' and 'action' in same block")
            if "choice" in action:
                self.warn(room, actionId, action, "Found 'choice' and 'action' in same block")
            self.checkAction(room, actionId, action)
            
        elif "actions" in action:
            if "choice" in action:
                self.warn(room, actionId, action, "Found 'choice' and 'actions' in same block")
            if len(action["actions"]) == 0:
                self.warn(room, actionId, action, "Empty 'actions' block")
            for key in action.keys():
                if key not in ["actions", "conditions"]:
                    self.warn(room, actionId, action, "Unexpected key '" + key + "' for actions block")
                elif key == "conditions":
                    conditions = action["conditions"]
                    if len(conditions) == 0:
                        self.warn(room, actionId, action, "Empty 'conditions' block in actions block")
                    for condition in conditions:
                        self.checkCondition(room, actionId, action, condition)
            for subaction in action["actions"]:
                self.onAction(room, actionId, subaction)
                
        elif "choice" in action:
            if len(action["choice"]) == 0:
                self.warn(room, actionId, action, "Empty 'choice' block")
            for key in action.keys():
                if key not in ["choice", "conditions"]:
                    self.warn(room, actionId, action, "Unexpected key '" + key + "' for choice block")
                elif key == "conditions":
                    conditions = action["conditions"]
                    if len(conditions) == 0:
                        self.warn(room, actionId, action, "Empty 'conditions' block in choice block")
                    for condition in conditions:
                        self.checkCondition(room, actionId, action, condition)
            for subaction in action["choice"]:
                self.onAction(room, actionId, subaction)
        else:
            
            self.error(room, actionId, action, "Could not find 'action', 'actions' or 'choice' blocks, found: " + str(action.keys()))

    def checkAction(self, room, actionId, action):
        actionType = action["action"]
    
        if actionType not in ['die', 'win', 'message', 'move', 'state_set', 'state_unset']:
            self.error(room, actionId, action, "Found unknown action type: " + actionType)
    
        validKeys = ['action', 'conditions']
        requiredKeys = []
        if actionType in ['die', 'win', 'message']:
            validKeys += ['message']
            requiredKeys += ['message']

        if actionType in ['move']:
            validKeys += ['room']
            requiredKeys += ['room']

        if actionType in ['state_set', 'state_unset']:
            validKeys += ['var']
            requiredKeys += ['var']
        
        if actionType in ['state_set']:
            validKeys += ['val']
    
        for key in action.keys():
            if key not in validKeys:
                self.warn(room, actionId, action, "Unexpected key '" + key + "' for action " + actionType)
            if key in requiredKeys:
                requiredKeys.remove(key)
        
        if len(requiredKeys) > 0:
            self.error(room, actionId, action, "One or more missing required keys for action " + actionType + ": " + str(requiredKeys))
        
        if "conditions" in action:
            conditions = action["conditions"]
            if len(conditions) == 0:
                self.warn(room, actionId, action, "Empty 'conditions' block")
            for condition in conditions:
                self.checkCondition(room, actionId, action, condition)

    def checkCondition(self, room, actionId, action, condition):
        if "type" not in condition:
            self.error(room, actionId, action, "Type not found for condition!")
            return
            
        conditionType = condition["type"]
        
        if conditionType not in ["extra", "state"]:
            self.error(room, actionId, action, "Found unknown condition type: " + conditionType)
        
        validKeys = ["type"]
        requiredKeys = []
        if conditionType in ["extra"]:
            validKeys += ["extra"]
            requiredKeys += ["extra"]
        
        if conditionType in ["state"]:
            validKeys += ["var", "op"]
            requiredKeys += ["var", "op"]
            if "op" in condition:
                if condition["op"] not in ["set", "unset", "=", "eq", "!=", "ne"]:
                    self.error(room, actionId, action, "Unknown op '" + condition["op"] + "' for condition " + conditionType)
                elif condition["op"] not in ["set", "unset"]:
                    validKeys += ["val"]
                    requiredKeys += ["val"]
    
        for key in condition.keys():
            if key not in validKeys:
                self.warn(room, actionId, action, "Unexpected key '" + key + "' for condition " + conditionType)
            if key in requiredKeys:
                requiredKeys.remove(key)
        
        if len(requiredKeys) > 0:
            self.error(room, actionId, action, "One or more missing required keys for condition type " + conditionType + ": " + str(requiredKeys))
            
def main(args=sys.argv):
    args = args[1:]
    
    worldName = "default"
    devMode = ""
    
    if len(args) > 0:
        if args[0][0] != '-':
            worldName = args[0]
            args = args[1:]
        if len(args) > 0:
            if args[0] == '--dev':
                if len(args) > 1:
                    devMode = args[1]
                else:
                    print "--dev option requires mode argument"
                    return 1
    
    world = JsonWorld(worldName + ".world.json")
    if devMode == "graphviz":
        print DevToolDotPrinter(world).getDotRepresentation()
    elif devMode == "stats":
        counts = DevToolStatistics(world).getCounts()
        for key in sorted(counts):
            value = str(counts[key])
            spacer = '.' * (30 - (len(key) + len(value)))
            print key + " " + spacer + " " + value
    elif devMode == "check":
        DevToolWorldChecker(world).check()
    elif devMode == "":
        engine = SteveEngine(world)
        interface = ConsoleInterface()
        interface.run(engine)
    return 0

if __name__ == "__main__":
    sys.exit(main())
