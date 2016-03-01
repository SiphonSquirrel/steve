#!/usr/bin/python -u

import sys, json
import os, os.path

defaultShortCommands = {
    "n" : "north",
    "e" : "east",
    "s" : "south",
    "w" : "west"
}

class StevePlayer:
    def __init__(self):
        self.room = ""
        self.dead = False
        self.won = False
        self.state = {}
        self.inv = {}

    def save(self, world, slot):
        pass

    def load(self, world, slot):
        pass

class SteveWorld:
    def getWorldName(self):
        return ""

    def getMotd(self):
        return []

    def getShortCommands(self):
        return defaultShortCommands

    def getStartRoom(self):
        return "start"

    def getDescription(self, room):
        return ""

    def getActions(self, room):
        return {}

    def getRoomActions(self, room):
        return {}

    def getLibraryAction(self, actionId):
        return {}

    def getLibraryCondition(self, conditionId):
        return {}

    def isRoom(self, room):
        return False

    def getItem(self, itemId):
        return { "name" : "", "desc" : "" }

    def isItem(self, itemId):
        return False

class SteveInterface:
    def printLines(self, lines):
        pass

    def printDebug(self, message):
        pass

class SteveEngine:
    def __init__(self, world):
        self.world = world
        self.shortCommands = world.getShortCommands()

    def initPlayer(self, interface, player):
        player.room = self.world.getStartRoom()
        interface.printLines("\n".join(self.world.getMotd()))
        self.enterRoom(interface, player, player.room)

    def enterRoom(self, interface, player, room):
        roomActions = self.world.getRoomActions(player.room)

        if "pre" in roomActions:
            self.processAction(interface, player, roomActions["pre"], [])

        if not player.dead:
            desc = self.world.getDescription(room)
            if desc != "":
                interface.printLines(desc)

            if "post" in roomActions:
                self.processAction(interface, player, roomActions["post"], [])

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
                        if foundMatch:
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
                        elif op == "<=" or op == "le":
                            if val <= player.state[var]:
                                return False
                        elif op == "<" or op == "lt":
                            if val < player.state[var]:
                                return False
                        elif op == ">=" or op == "ge":
                            if val >= player.state[var]:
                                return False
                        elif op == ">" or op == "gt":
                            if val > player.state[var]:
                                return False
                elif op != "unset":
                    interface.printDebug("DEBUG: CONDFAIL: var " + var + " was not set")
                    return False

            elif cond["type"] == "item":
                itemId = cond["item"]

                maxCount = None
                if "max" in cond:
                    maxCount = cond["max"]

                if "min" in cond:
                    minCount = cond["min"]
                elif maxCount != None:
                    minCount = min(1, maxCount)
                else:
                    minCount = 1

                count = 0
                if itemId in player.inv:
                    count = player.inv[itemId]["count"]

                if maxCount != None and count > maxCount:
                    return False

                if count < minCount:
                    return False

            elif cond["type"] == "compound":
                subConditions = cond["conditions"]
                if not self.self.evaluateConditions(interface, player,
                        subConditions, extra):
                    return False

            elif cond["type"] == "library":
                conditionId = cond["ref"]
                if not self.self.evaluateConditions(interface, player,
                        world.getLibraryCondition(conditionId), extra):
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
        elif "library" in action:
            subaction = self.world.getLibraryAction(action["library"])
            return self.processAction(interface, player, subaction, extra)
        elif "action" in action:
            if action["action"] == "move":
                player.room = action["room"]
                if not self.world.isRoom(player.room):
                    interface.printLines("You find yourself in a room the developer was too lazy to create.\n"+
                                         "You have contracted dysentery.")
                    player.dead = True
                else:
                    self.enterRoom(interface, player, player.room)
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
            elif action["action"] == "state_inc":
                var = action["var"]
                val = 1
                if "val" in action:
                    val = action["val"]
                if var in player.state:
                    player.state[var] += val
                else:
                    player.state[var] = val
            elif action["action"] == "state_dec":
                var = action["var"]
                val = 1
                if "val" in action:
                    val = action["val"]
                if var in player.state:
                    player.state[var] -= val
                else:
                    player.state[var] = -val
            elif action["action"] == "item_take":
                itemId = action["item"]
                count = 1
                if "count" in action:
                    count = action["count"]
                if itemId not in player.inv:
                    player.inv[itemId] = { "count" : count }
                else:
                    player.inv[itemId]["count"] += count
                itemName = itemId
                if self.world.isItem(itemId):
                    itemName = self.world.getItem(itemId)["name"]
                interface.printLines("Got item: " + itemName)
            elif action["action"] == "item_drop":
                itemId = action["item"]
                count = 1
                if "count" in action:
                    count = action["count"]
                if itemId in player.inv:
                    player.inv[itemId]["count"] -= count
                    if player.inv[itemId]["count"] <= 0:
                        del player.inv[itemId]
                    itemName = itemId
                    if self.world.isItem(itemId):
                        itemName = self.world.getItem(itemId)["name"]
                    interface.printLines("Lost item: " + itemName)
                else:
                    print "WARN: No item " + itemId + " to drop."
                    return False
            else:
                print "WARN: Cannot understand action " + action["action"]
                return False
            return True
        else:
            print "WARN: Cannot find property 'action', 'actions', 'choice' or 'library' in room " + player.room

        return False

    def process(self, interface, player, commandLine):
        cmdLine = commandLine.lower().strip()
        cmdArr = cmdLine.split(' ')
        cmd = cmdArr[0]
        extra = []
        if len(cmdArr) > 1:
            extra = cmdArr[1:]

        actions = self.world.getActions(player.room)

        if cmd in self.shortCommands:
            cmd = self.shortCommands[cmd]

        if cmd in actions:
            if self.processAction(interface, player, actions[cmd], extra):
                return True
        elif cmd in ["north", "east", "south", "west"]:
            interface.printLines("I can't go that way.")
            return False

        interface.printLines("I don't know how to " + commandLine + ".")
        return False

class JsonPlayer(StevePlayer):
    def __init__(self):
        StevePlayer.__init__(self)

    def save(self, world, slot):
        playerData = {
            "room" : self.room,
            "dead" : self.dead,
            "won" : self.won,
            "state" : self.state,
            "inv" : self.inv
        }

        saveDir = os.path.join(os.path.expanduser("~"), ".steve")
        if not os.path.isdir(saveDir):
            os.makedirs(saveDir)

        saveName = os.path.join(saveDir, world.getWorldName() + ".save." + str(slot) + ".json")
        with open(saveName, "w") as fp:
            json.dump(playerData, fp)

    def load(self, world, slot):
        saveDir = os.path.join(os.path.expanduser("~"), ".steve")
        if not os.path.isdir(saveDir):
            os.makedirs(saveDir)

        saveName = os.path.join(saveDir, world.getWorldName() + ".save." + str(slot) + ".json")
        if not os.path.isfile(saveName):
            return False

        with open(saveName, "r") as fp:
            playerData = json.load(fp)

            self.room = playerData["room"]
            self.dead = playerData["dead"]
            self.won = playerData["won"]
            self.state = playerData["state"]
            self.inv = playerData["inv"]

        return True

class JsonWorld(SteveWorld):
    def __init__(self, jsonFile):
        import os.path
        with open(jsonFile, "r") as fp:
            self.__world = json.load(fp)

        name = os.path.basename(jsonFile)
        self.worldName = name[:name.find(".world.json")]

    def getWorldName(self):
        return self.worldName

    def getMotd(self):
        if "motd" in self.__world:
            return self.__world["motd"]
        return []

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

    def getRoomActions(self, room):
        retVal = {}

        if not room in self.__world["rooms"]:
            return {}

        if "pre" in self.__world["rooms"][room]:
            retVal["pre"] = self.__world["rooms"][room]["pre"]
        if "post" in self.__world["rooms"][room]:
            retVal["post"] = self.__world["rooms"][room]["post"]
        return retVal

    def getLibraryAction(self, actionId):
        if not "library" in self.__world:
            return {}
        if not "actions" in self.__world["library"]:
            return {}
        if not actionId in self.__world["library"]["actions"]:
            return {}
        return self.__world["library"]["actions"][actionId]

    def getLibraryCondition(self, conditionId):
        if not "library" in self.__world:
            return {}
        if not "conditions" in self.__world["library"]:
            return {}
        if not conditionId in self.__world["library"]["conditions"]:
            return {}
        return self.__world["library"]["conditions"][conditionId]

    def isRoom(self, room):
        return room in self.__world["rooms"]

    def getItem(self, itemId):
        if "items" not in self.__world:
            return { "name" : "", "desc" : "" }
        if itemId not in self.__world["items"]:
            return { "name" : "", "desc" : "" }
        return self.__world["items"][itemId]

    def isItem(self, itemId):
        if "items" not in self.__world:
            return False
        if itemId not in self.__world["items"]:
            return False
        return True

class TextBasedInterface(SteveInterface):

    INPUT_RESULT_NO_CHANGE = 0
    INPUT_RESULT_ROOM_CHANGED = 1
    INPUT_RESULT_QUIT = 2

    def __init__(self):
        self.saveEnabled = False

    def showHelp(self):
        helpText  = "Command Help\n"
        helpText += "------------\n"
        helpText += "?,!help      - This help text\n"
        helpText += "!quit        - Exits the game\n"
        helpText += "!inv         - Displays your current inventory\n"
        if self.saveEnabled:
            helpText += "!save [slot] - Saves the game to the specified slot, default: 0\n"
            helpText += "!load [slot] - Loads the game from the specified slot, default: 0\n"
        self.printLines(helpText)

    def handleInput(self, engine, player, input):
        result = TextBasedInterface.INPUT_RESULT_NO_CHANGE
        if input.startswith("!"):
            cmdArr = input[1:].split(" ")
            if cmdArr[0] == "quit":
                return TextBasedInterface.INPUT_RESULT_QUIT
            elif cmdArr[0] == "help":
                self.showHelp()
            elif cmdArr[0] == "inv":
                output = "Inventory:\n"
                for itemKey in player.inv.keys():
                    if engine.world.isItem(itemKey):
                        itemDesc = engine.world.getItem(itemKey)
                        output += "  * " + itemDesc["name"] + "\n"
                        output += "      " + itemDesc["desc"] + "\n"
                    else:
                        output += "  * " + itemKey + "\n"
                self.printLines(output)
            elif self.saveEnabled and cmdArr[0] == "save":
                slot = 0
                if len(cmdArr) > 1:
                    slot = int(cmdArr[1])

                if slot >= 0 and slot <= 9:
                    player.save(engine.world, slot)
                else:
                    self.printLines("Please specify a slot from 0 to 9")
            elif self.saveEnabled and cmdArr[0] == "load":
                slot = 0
                if len(cmdArr) > 1:
                    slot = int(cmdArr[1])
                if slot >= 0 and slot <= 9:
                    loaded = player.load(engine.world, slot)
                    if loaded:
                        self.printLines("Loaded slot " + str(slot))
                        result = TextBasedInterface.INPUT_RESULT_ROOM_CHANGED
                    else:
                        self.printLines("Could not load slot " + str(slot))
                else:
                    self.printLines("Please specify a slot from 0 to 9")
            else:
                self.printLines("Unknown command: " + cmdArr[0])

        elif input == "?":
            self.showHelp()
        else:
            if engine.process(self, player, input):
                result = TextBasedInterface.INPUT_RESULT_ROOM_CHANGED

        return result

class ConsoleInterface(TextBasedInterface):
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
                self.printLines("\nUse !help or ? to get command help")

                player = JsonPlayer()
                engine.initPlayer(self, player)

                roomChanged = True
                while not (player.won or player.dead):
                    self.printLines("")
                    input = raw_input('> ').strip()
                    result = self.handleInput(engine, player, input)
                    if result == TextBasedInterface.INPUT_RESULT_QUIT:
                        playing = False
                        break

                if not playing:
                    break
                elif player.won:
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
            self.retVal += "  \"" + room + "\" [ style=\"filled\", fillcolor=\"red\"]\n"
        for actionId, action in actions.iteritems():
            edges = []
            for adjRoom in self.getAllDestinations(action):
                if adjRoom not in edges:
                    edges.append(adjRoom)
                    self.retVal += "  \"" + room + "\" -> \"" + adjRoom + "\" [ label=\"" + actionId + "\" ]\n"

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

        roomActions = self.world.getRoomActions(room)
        for actionType in ["pre", "post"]:
            if actionType in roomActions:
                self.onAction(room, "roomAction-" + actionType, roomActions[actionType])

    def onAction(self, room, actionId, action):
        if "action" in action:
            if "library" in action:
                self.warn(room, actionId, action, "Found 'library' and 'action' in same block")
            if "actions" in action:
                self.warn(room, actionId, action, "Found 'actions' and 'action' in same block")
            if "choice" in action:
                self.warn(room, actionId, action, "Found 'choice' and 'action' in same block")
            self.checkAction(room, actionId, action)

        elif "library" in action:
            if "actions" in action:
                self.warn(room, actionId, action, "Found 'actions' and 'library' in same block")
            if "choice" in action:
                self.warn(room, actionId, action, "Found 'choice' and 'library' in same block")
            libAction = self.world.getLibraryAction(action["library"])
            if len(libAction) == 0:
                self.warn(room, actionId, action, "Action Library item " + str(action["library"]) + " does not exist or is empty.")
            self.onAction(room, "actionId", libAction)

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

        if actionType not in ['die', 'win', 'message', 'move', 'state_set', 'state_unset', 'state_inc', 'state_dec', 'item_take', 'item_drop']:
            self.error(room, actionId, action, "Found unknown action type: " + actionType)

        validKeys = ['action', 'conditions']
        requiredKeys = []
        if actionType in ['die', 'win', 'message']:
            validKeys += ['message']
            requiredKeys += ['message']

        if actionType in ['move']:
            validKeys += ['room']
            requiredKeys += ['room']

        if actionType in ['state_set', 'state_unset', 'state_inc', 'state_dec']:
            validKeys += ['var']
            requiredKeys += ['var']

        if actionType in ['state_set', 'state_inc', 'state_dec']:
            validKeys += ['val']

        if actionType in ['item_take', 'item_drop']:
            validKeys += ['item', 'count']
            requiredKeys += ['item']

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

        if conditionType not in ["extra", "state", "item", "library", "compound"]:
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
                if condition["op"] not in ["set", "unset", "=", "eq", "!=", "ne",
                        "<=", "le", "<", "lt", ">=", "ge", ">", "gt"]:
                    self.error(room, actionId, action, "Unknown op '" + condition["op"] + "' for condition " + conditionType)
                elif condition["op"] not in ["set", "unset"]:
                    validKeys += ["val"]
                    requiredKeys += ["val"]

        if conditionType in ["item"]:
            validKeys += ["max", "min", "item"]
            requiredKeys += ["item"]

        if conditionType in ["library"]:
            validKeys += ["ref"]
            requiredKeys += ["ref"]

            if "ref" in condition:
                if len(self.world.getLibraryCondition(condition["ref"])) == 0:
                    self.warn(room, actionId, action, "Action Condition item " + str(condition["ref"]) + " does not exist or is empty.")

        if conditionType in ["compound"]:
            validKeys += ["conditions"]
            requiredKeys += ["conditions"]

            if "conditions" in condition:
                for subCondition in condition["conditions"]:
                    self.checkCondition(room, actionId, action, subCondition)

        for key in condition.keys():
            if key not in validKeys:
                self.warn(room, actionId, action, "Unexpected key '" + key + "' for condition " + conditionType)
            if key in requiredKeys:
                requiredKeys.remove(key)

        if len(requiredKeys) > 0:
            self.error(room, actionId, action, "One or more missing required keys for condition type " + conditionType + ": " + str(requiredKeys))

class DevToolSteveUnit(TextBasedInterface):
    def __init__(self, engine):
        self.engine = engine

    def printLines(self, lines):
        for line in lines.split("\n"):
            print "> " + line

    def run(self, actions):
        import shlex

        results = {}
        player = StevePlayer()
        self.engine.initPlayer(self, player)

        line = 0
        asserts = 0
        passed = 0
        commands = 0
        failed = False
        for action in actions:
            line += 1

            cmd = action.strip()
            if cmd == "" or cmd.startswith("#"):
                continue
            if cmd.startswith("?"):
                asserts += 1
                if not failed:
                    cmd = shlex.split(cmd[1:])

                    assertType = cmd[0]
                    assertArgs = cmd[1:]

                    msg = ""

                    if assertType == "assertDead":
                        failed = not player.dead
                    elif assertType == "assertAlive":
                        failed = player.dead
                    elif assertType == "assertWon":
                        failed = not player.won
                    elif assertType == "assertNotWon":
                        failed = player.won
                    elif assertType == "assertInRoom":
                        if len(assertArgs) < 1:
                            msg = "No room id specified on line " + str(line)
                            failed = True
                            continue
                        else:
                            roomId = assertArgs[0]
                            assertArgs = assertArgs[1:]
                            failed = roomId != player.room
                    elif assertType == "assertNotInRoom":
                        if len(assertArgs) < 1:
                            msg = "No room id specified on line " + str(line)
                            failed = True
                            continue
                        else:
                            roomId = assertArgs[0]
                            assertArgs = assertArgs[1:]
                            failed = roomId == player.room
                    elif assertType == "assertItemCount":
                        if len(assertArgs) < 2:
                            msg = "Item id or count missing on line " + str(line)
                            failed = True
                            continue
                        else:
                            itemId = assertArgs[0]
                            itemCount = int(assertArgs[1])
                            found = 0
                            if itemId in player.inv:
                                found = player.inv[itemId]["count"]
                            if found != itemCount:
                                failed = True
                                msg = "Expected count of " + str(itemCount) + ", got " + str(found) + " of " + itemId + ". " + assertArgs[1:]
                    else:
                        msg = "Unrecognized assert type: " + assertType
                        failed = True
                    if msg == "":
                        msg = " ".join(assertArgs)

                    if failed:
                        print assertType + " failed on line " + str(line) + " in room " + player.room + ": " + msg

                    passed += 1
            elif not failed:
                commands += 1
                print "< " + cmd
                self.handleInput(self.engine, player, cmd)

        results["lines"] = line
        results["assertTotal"] = asserts
        results["assertPassed"] = passed
        results["passed"] = not failed
        return results

def main(args=sys.argv):
    args = args[1:]

    worldName = "default"
    devMode = ""
    saveEnabled = False
    unitFiles = None

    if len(args) > 0:
        if args[0][0] != '-':
            worldName = args[0]
            args = args[1:]
        while len(args) > 0:
            if args[0] == '--dev':
                if len(args) > 1:
                    devMode = args[1]
                    args = args[2:]
                    if devMode == "test":
                        if len(args) > 0:
                            unitFiles = args
                            args = []
                        else:
                            print "--dev test requires a unit test file!"
                            return 1
                else:
                    print "--dev option requires mode argument"
                    return 1
            elif args[0] == '--enable-save':
                saveEnabled = True
                args = args[1:]
            else:
                print "Unknown option(s): '" + "' '".join(args) + "'"
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
    elif devMode == "test":
        if len(unitFiles) == 0:
            print "No steveunit files specified!"
        else:
            steveUnit = DevToolSteveUnit(SteveEngine(world))
            for unitFile in unitFiles:
                print "Running " + unitFile
                with open(unitFile) as fp:
                    print "----------------------------------------"
                    results = steveUnit.run(fp.read().splitlines())
                    print "----------------------------------------"
                    if results["passed"]:
                        print "Tests: PASSED"
                    else:
                        print "Tests: FAILED"
                    print "Processed " + str(results["lines"]) + " lines"
                    print "Passed Tests: " + str(results["assertPassed"]) + "/" + str(results["assertTotal"])
    elif devMode == "":
        engine = SteveEngine(world)
        interface = ConsoleInterface()
        interface.saveEnabled = saveEnabled
        interface.run(engine)
    return 0

if __name__ == "__main__":
    sys.exit(main())
