# The Adventures of Steve

## How to play

Run "steve.py" to play.

If you want to play a non—default world, pass the woridname on the command line
(ie. `./steve.py zork`)

While in the game, use "!help" or "?" to get command help:

	Command Help
	------------
	?,!help      - This help text
	!quit        - Exits the game
    !inv         - Displays your current inventory

*Note:* State saving can be enabled by passing --enable-save on the command line
(ie `./steve.py --enable-save`). It is disabled by default

## World Building

### World File

Every world is rooted in a single world json file:

	{
		"motd" : [
			"MOTD Line 1",
			"MOTD Line 2"
		],
		"items" : {
			"key" : {
				"name" : "House Key",
				"desc" : "Locks and unlocks my house!"
			},
			"handkerchief" : {
				"name" : "Soiled Handkerchief",
				"desc" : "Its a handkerchief... used. Bleh."
			}
		},
		"library" : {
			"conditions" : {
				"hungry" : {
					...
				}
			},
			"actions" : {
				"eat_food" : {
					...
				}
			}
		},
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

### Items Section

The items section is used to define items the user might find in the world. It
provides an area to give a human readable name and description to the item.
The items section is a dictonary where the key is the item id, and the value
is the item description. For example:

	"key" : {
		"name" : "House Key",
		"desc" : "Locks and unlocks my house!"
	}

This describes the item whose id is "key". The name of the key (when printed
to the user) is "House Key" and the description is "Locks and unlocks my
house!"

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

For example, a single move action:

    { "action" : "move", "room" : "super room xyz" }

Compound actions such as "actions" or "choice" consist of an array of
subactions. These subactions may be single actions or nested compound actions.
With the "actions" property, each action is executed in order. If one fails to
execute, then no further actions are executed and the entire block is marked
as failed. With the "choice" propertiy, each action is executed in order, until
one succeeds, then no further actions in the list are evaluated.

A 'choice' section may look like:

    {
		"choice" : [
			{
				"conditions" : [
					{
						"type" : "state",
						"op" : "set",
						"var" : "fed"
					}
				],
				"actions" : [
					{
						"action" : "message",
						"message" : "You aren't feeling that hungry."
					}
				]
			},
			{
				"action" : "message",
				"message" : "Man! Am I starved! I could really eat something!"
			}
		]
	}

While 'actions' looks like this:

    {
		"actions" : [
			{
				"action" : "message",
				"message" : "You are no longer hungry!"
			},
			{
				"action" : "state_set",
				"state" : "fed"
			}	
		]
	}

Library actions can also be invoked. If the property "library" is available,
the action id in the property is used to look up the action to execute.

A library action looks like this:

    { "library" : "eat_food" }

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

### Action Type: item_take

This action type add items to the player inventory. Count is optional, and
defaults to 1.

	"atm" : { "action" : "item_take", "item" : "coins", "count" : 7 }

This action (triggered by "atm") adds 7 coins to the player's inventory.

### Action Type: item_drop

This action type removes items to the player inventory. Count is optional, and
defaults to 1.

	"pay" : { "action" : "item_drop", "item" : "coins", "count" : 5 }

This action (triggered by "pay") drops 5 coins to the player's inventory.

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

### Condition Type: item

This condition checks to ensure the player has (or doesn't have) a certain
item. It has optional parameters "min" (defaults to 1) and "max" (defaults
to unlimited).

By setting max to 0, it enforces that the player does not have any of the
specified items.

For example:

	{
		"type" : "item",
		"item" : "key",
		"max" : 0 
	}

### Condition Type: compound

This condition groups a set of conditions together. The sub-conditions are in
an array called "conditions".

For example:

    {
		"type" : "compound",
		"conditions" : [
			{
				"type" : "item",
				"item" : "key",
				"max" : 0 
			},
			{
				"type" : "state",
				"op" : "set",
				"var" : "eaten"
			}	
		]
	}


### Condition Type: library

This condition evaluates a condition from the world's condition library. The
condition ID to evaluate is stored in the parameter 'ref'.

For example:

    {
		"type" : "library",
		"ref" : "ensure_fed"
	}

### Development Tools

The steve executable provides some dev tools to aid with your dungeoneering.

  * `graphviz` — Prints the world as a graphviz diagram
  * `stats` — Gathers stats about the world, printing various counts
  * `check` - Checks the world file for problems
  * `test` - Runs steveunit files against a world

### Development Tools — Graphviz

Usage (requires the graphviz package):

	./steve.py [worldname] --dev graphviz | dot -Tpng > out.png

Draws the dungeon as a directed graph.

### Development Tools — Stats

Usage:

	./steve.py [worldname] --dev stats

Example Output:

	Action actions ............... 6
	Action choice ................ 4
	Action die ................... 1
	Action message ............... 8
	Action move ................. 15
	Action state_set ............. 2
	Command east ................. 5
	Command enter ................ 1
	Command feed ................. 1
	Command north ................ 2
	Command ride ................. 1
	Command west ................. 6
	Room Count ................... 9

### Development Tools — Check

Usage:

	./steve.py [worldname] --dev check

Output when no errors:

	OK!

Output when problems are detected:

	ERROR outsideCave{enter} - Found unknown condition type: extraa
	WARN outsideCave{enter} - Unexpected key 'extra' for condition extraa

Errors are formatted as follows:

	ErrorType RoomId{ActionId} - ProblemMessage

### Development Tools — Test

Usage:

	./steve.py [worldname] --dev check [test1.steveunit] [[test2.steveunit] ...]

The game will play itself and print the input and output of the game, followed
by a summary. Below is an example of a successful test:

	Running default.quickdeath.steveunit
	----------------------------------------
	> You are standing in a field beside a pile of trash. There is a goat path to the north.
	< n
	> You find yourself on a goat path. There is an easy, slow path to the east, a dangerous path heading down a cliff side to the west, and a small opening that appears to lead into the mountain to the north.
	< w
	> You attempt to make your way down the path, slipping and falling to your death. A goat you are not.
	----------------------------------------
	Tests: PASSED
	Processed 6 lines
	Passed Tests: 1/1

While a failed test looks like (same test run on a different world file):

	Running default.quickdeath.steveunit
	----------------------------------------
	> Syncing with InfoNet... We seem to be in an old asteroid prospector town on Omicron 12. Specifically an adventure-less alley, lets move on. It exits north.
	< n
	> It appears that we seem to be just outside the spaceport. A drinking establishment appears to be to the north, while our ship lies to the east.
	< w
	> I can't go that way.
	assertDead failed on line 6 in room omicron-12-spaceport: Falling down this cliff should have killed you
	----------------------------------------
	Tests: FAILED
	Processed 6 lines
	Passed Tests: 1/1

#### steveunit Files

A steveunit file is processed line by line. A line that starts with a hash (#)
is a command, while a line that starts with a question mark (?) is an assert
statement. All other lines are commands feed verbatim into the engine.

Example steveunit file:

	# This is a comment
	# This instructs the player to move north
	n
	w
	# This checks that the player has died, and print the message if they have not.
	?assertDead "Falling down this cliff should have killed you"

The assert types are as follows:

  * `assertDead {Fail Message}` - Asserts that the player is dead
  * `assertAlive {Fail Message}` - Asserts that the player is alive
  * `assertWon {Fail Message}` - Asserts that the player has won
  * `assertNotWon {Fail Message}` - Asserts that the player has not won
  * `assertInRoom {Room Id} {Fail Message}` - Asserts that the player is in a certain room
  * `assertNotInRoom {Room Id} {Fail Message}` - Asserts that the player is not in a certain room
