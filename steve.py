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
            return ""
        if not "actions" in self.__world["rooms"][room]:
            return ""
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
            pass

def main(args=sys.argv):
    engine = SteveEngine(JsonWorld("default.world.json"))
    interface = ConsoleInterface()
    interface.run(engine)

if __name__ == "__main__":
    main()
