The Adventures of Steve
=======================

Run "steve.py" to play.

If you want to play a non—default world, pass the woridname on the command line
(ie. "./steve.py enginetest")

World Building
--------------

### World File

Every world is rooted in a single world json file:

	{
		"motd" : [
			"MOTD Line 1",
			"MOTD Line 2"
		],
		"rooms" : {
			"start" : {
				"desc" : "quick description of start",
				"actions" : {
					"north": { "action" : "move", "room" : "super room xyz" }
				}
			},
			"super room xyz" : {
				"desc" : "description of room xyz",
				"actions" : {
					"west" : {
						...
					},
					...
				}
			}
		}
	}

The default world is named "default.world.json", to create a new world, it
should be in a file ending in ".world.json". Ie. "enginetest.world.json",
which could be started with "./steve.py enginetest"

### MOTD Section

The MOTD (message of the day) is an array of string, where each string is
printed on its own line when the game begins.

### Room Section

The room section is a dictionary of rooms, where the key is the room id, and
the value is the room definition. Each room as "desc" property, which is
printed when the player enters the room.

The "actions" property of a room defines the actions that can be taken. Some
actions (such as "north", "west", "east", "south") have built in short commands
(such as "n", "w", "e", "s") that will be mapped to the long forms. The actions
section should use the long form in lower case, as commands are lowercased
before being evaluated.

### Action Definition

An action maybe a single action (triggered by the property "action’) or a
compound action (triggered by the property "actions" or "choice")

Single actions execute have a single fixed property "action" which defines the
type of action. Each action type has its own set of additional properties.

Compound actions such as "actions" or "choice" consist of an array of
subactions. These subactions may be single actions or nested compound actions.
With the "actions" property, each action is executed in order. If one fails to
execute, then no further actions are executed and the entire block is marked
as failed. With the "choice" propertiy, each action is executed in order, until
one succeeds, then no further actions in the list are evaluated.

### Action Type: move

The move action changes the players location to a new room, as specified by the
"room" property.

	"north": { "action" : "move", "room" : "super room xyz" }

This action (triggered by "north") moves the player into the room labelled
"super room xyz".

### Action Type: die

The die action kills the player and prints a short message, then askes the
player if they would like to start again.

	"east": { "action" : "die", "message" :
		"You trip and fall to your death down the seemingly safe path." }

This action (triggered by "east") kills the player with the message
"You trip and fall to your death down the seemingly safe path."

### Action Type: state_set

This action type sets player state to true, or a specified value (as denoted by
the optional parameter "value").

	"eat" : { "action" : "state_set", "var" : "eaten" }
	
This action (triggered by "eat") sets the player state variable "eaten" to
True.

### Action Type: state_unset

This action type unsets player state.

	"eat" : { "action" : "state_unset", "var" : "hungry" }

This action (triggered by "eat") removes the player state value for "hungry".

### Conditions

All action blocks (single and compound actions) also may have conditions that
guard the action from being executed.

	"eat": {
		"conditions" : [
			{
				"type" : "extra",
				"extra": [["trolls"]]
			}
		],
		"action" : {
			"action" : "move",
			"room" : "bridge"
		}
	}

The above condition only executes when the text "eat trolls" is typed as a
command.

Multiple conditions can be specified, and each one needs to evaluate to true
for an action to be executed.

### Condition Type: extra

This condition requires that the player adds extra text after the command. The
extra text is an array of arrays in the property "extra". Any single array must
match the text after the command for the condition to pass.

	"eat": {
		"conditions" : [
			{
				"type" : "extra",
				"extra": [["trolls"]]
			}
		],
		"action" : ...
	}

The above only executes if "eat trolls" is typed into the console.

### Condition Type: state

This condition checks the player state. The state variable is specified by the
"var" property, while the operation to test is set by the "op" property.
Optionally, some state checks require a value to be checked against, specified
by the "val" property.

Available operations are:

  * set
  * unset

For example:
  
	{
		"type" : "state",
		"op" : "set",
		"var" : "eaten"
	}

The above only evaluates to true if the state "eaten" has been set.

### Development Tools

The steve executable provides some (one at the time of this writing) dey tools
to aid with your dungeoneering.

  * graphviz — Prints the world as a graphviz diagram

### Development Tools — Graphviz

Usage (requires the graphviz package):

	./steve.py [worldname] --dev graphviz | dot -Tpng > out.png

Draws the dungeon as a directed graph.
