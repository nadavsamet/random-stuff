"""
Spider game

Back move doesn't cost
"""

# TODO: Clear a deck once completed!
# TODO: Implement 'back' feature!
# TODO: Implement heuristic solver!

import random
from copy import deepcopy
import traceback

class Constants(object):
    class Series(object):
        HEART = 0
        DIAMOND = 1
        CLUB = 2
        SPADE = 3

        TYPES = [HEART, DIAMOND, CLUB, SPADE]

        TYPE_TO_DISPLAY_NAME = {HEART: "Heart",
                                DIAMOND: "Diamond",
                                CLUB: "Club",
                                SPADE: "Spade"}

    class Score(object):
        INITIAL = 500
        MOVE_COST = 1
        COMPLETED_DECK_BONUS = 100

    class Deck(object):
        class Type(object):
            FULL = 0
            SIDE = 1
            
        FULL_DECK_SIZE = 13
        SIDE_DECK_SIZE = 10

    NUM_DECKS = 8
    NUM_SIDE_DECKS = 6
    NUM_COLUMNS = 10
    NUM_INITIAL_DECKS_TO_DEAL = 2

class Card(object):
    def __init__(self, series_type, value, is_revealed=False):
        self.seriesType = series_type
        self.value = value
        self.isRevealed = is_revealed

    def reveal(self):
        if (self.isRevealed):
            raise Exception("Card is already revealed")
        else:
            self.isRevealed = True
        
class Deck(object):
    def __init__(self, mixed=False, deck_type=Constants.Deck.Type.FULL, series_type=None, cards=()):
        if (mixed):
            assert series_type == None
            if (deck_type == Constants.Deck.Type.FULL):
                assert len(cards) == Constants.Deck.FULL_DECK_SIZE
            elif (deck_type == Constants.Deck.Type.SIDE):
                assert len(cards) == Constants.Deck.SIDE_DECK_SIZE
            else:
                raise Exception("Invalid mixed deck")
            
            self.cards = deepcopy(cards)
        else:
            assert deck_type == Constants.Deck.Type.FULL
            assert series_type in Constants.Series.TYPES
            assert cards == ()
            
            self.cards = []
            for x in xrange(Constants.Deck.FULL_DECK_SIZE):
                self.cards.append(Card(series_type, x))
            random.shuffle(self.cards)
            
        self.seriesType = series_type

    def isEmpty(self):
        return len(self.cards) == 0

    def dealCard(self):
        if (self.isEmpty()):
            raise Exception("Can't deal cards from an empty deck")
        else:
            return self.cards.pop()

class Game(object):
    def __init__(self):
        self.score = Constants.Score.INITIAL
        self.columns = []
        for x in xrange(Constants.NUM_COLUMNS):
            self.columns.append([])

        decks = []
        for seriesType in Constants.Series.TYPES:
            for y in xrange(Constants.NUM_DECKS/len(Constants.Series.TYPES)):
                decks.append(Deck(series_type=seriesType))

        cards = []
        for deck in decks:
            while (not deck.isEmpty()):
                cards.append(deck.dealCard())

        # Shuffles the cards
        random.shuffle(cards)

        # Deals 44 cards to the table and keeps 6 side decks apart
        self.decks = []
        for x in xrange(len(cards)-(Constants.NUM_SIDE_DECKS*Constants.Deck.SIDE_DECK_SIZE)):
            self.columns[x % Constants.NUM_COLUMNS].append(cards[x])
            
        for x in xrange(len(cards)-(Constants.NUM_SIDE_DECKS*Constants.Deck.SIDE_DECK_SIZE), len(cards), Constants.Deck.SIDE_DECK_SIZE):
            deck = Deck(mixed=True, deck_type=Constants.Deck.Type.SIDE, cards=cards[x:x+Constants.Deck.SIDE_DECK_SIZE])
            self.decks.append(deck)
        
        self.dealDeck()
        
    def dealDeck(self, is_revealed=True):
        """
        Doesn't decrement the score
        """
        # Checks if any decks left
        if (len(self.decks) > 0):
            canDealDeck = False
            if (len(self.decks) == Constants.NUM_DECKS):
                # Only then it's ok to deal a deck when column(s) are empty
                canDealDeck = True
            else:
                # Checks if all columns contain at least one card
                for column in self.columns:
                    if (len(column) == 0):
                        raise Exception("All columns must contain at least one card to deal cards")

                canDealDeck = True

            if (canDealDeck):
                # Deals the cards
                num_card = 0
                deck = self.decks.pop()
                while (not deck.isEmpty()):
                    # Puts the card in the corresponding column
                    card = deck.dealCard()
                    self.columns[num_card % Constants.NUM_COLUMNS].append(card)
                    
                    # Reveals the top card
                    if (is_revealed):
                        card.reveal()
                    num_card += 1
            else:
                raise Exception("Can't deal deck")

            self.checkForCompletedColumns()
        else:
            raise Exception("No decks left")

    def moveCard(self, from_column, num_card_in_column, to_column):
        """
        @param num_card_in_column - (int) starts with 0 as the last card of the column

        Decrements score by Constants.Score.MOVE_COST
        """
        # Checks if card exists
        if (num_card_in_column >= len(self.columns[from_column])):
            raise Exception("Card doesn't exist in the index required of this column")
        else:
            # Checks if card can move from the original column
            if (self.canCardMove(from_column, num_card_in_column)):
                # Checks if card can move to the destination column
                if ((len(self.columns[to_column]) == 0) or
                    ((self.columns[to_column][-1].isRevealed) and
##                     (self.columns[to_column][-1].seriesType == self.columns[from_column][len(self.columns[from_column])-num_card_in_column-1].seriesType) and
                     (self.columns[to_column][-1].value-1 == self.columns[from_column][len(self.columns[from_column])-num_card_in_column-1].value))):
                    # Moves the card and its tail if exists
                    cut_position = len(self.columns[from_column])-num_card_in_column-1
                    cards_to_move = self.columns[from_column][cut_position:]
                    self.columns[to_column].extend(cards_to_move)
                    self.columns[from_column] = self.columns[from_column][:cut_position]

                    # Reveals the top card if necessary
                    if (len(self.columns[from_column]) > 0):
                        if (not self.columns[from_column][-1].isRevealed):
                            self.columns[from_column][-1].reveal()

                    self.checkForCompletedColumn(to_column)
                else:
                    raise Exception("Can't move card to the desired destination")
            else:
                raise Exception("Can't move the desired card")

    def canCardMove(self, num_column, num_card_in_column):
        """
        Assumes that the place in column is valid.
        """
        if (not self.columns[num_column][-num_card_in_column-1].isRevealed):
            return False
        elif (num_card_in_column == 0):
            return True
        else:
            can_move = True
            column = self.columns[num_column]
            for x in xrange(num_card_in_column, 0, -1):
                previous_card = column[-x-1]
                current_card = column[-x]
                if (not ((current_card.seriesType == previous_card.seriesType) and
                        (current_card.value == previous_card.value-1))):
                    can_move = False
                    break

            return can_move
        
    def printState(self):
        matrix = []
        num_cards = max([len(column) for column in self.columns])
        for x in xrange(Constants.NUM_COLUMNS):
            matrix.append([])
            for y in xrange(num_cards):
                matrix[x].append(" ")

        for num_column, column in enumerate(self.columns):
            for num_card, card in enumerate(column):
                if (card.isRevealed):
                    card_representation = "%s %s" % (card.value, Constants.Series.TYPE_TO_DISPLAY_NAME[card.seriesType])
                else:
                    card_representation = "x"
                matrix[num_column][num_card] = card_representation

        import pprint
        pprint.pprint(matrix)
        print "remaining decks:", len(self.decks)

    def isColumnCompleted(self, num_column):
        column = self.columns[num_column]
        isCompleted = True
        if (len(column) < Constants.Deck.FULL_DECK_SIZE):
            isCompleted = False
        else:
            series_type = column[-1].seriesType
            pos = 0
            while (pos < Constants.Deck.FULL_DECK_SIZE):
                if ((column[-pos-1].isRevealed) and
                    (column[-pos-1].value == pos)):
                    pos += 1
                else:
                    isCompleted = False
                    break

        return isCompleted

    def checkForCompletedColumns(self):
        # Back feature supported
        for i in xrange(len(self.columns)):
            self.checkForCompletedColumn(i)

    def checkForCompletedColumn(self, num_column):
        if (self.isColumnCompleted(num_column)):
            self.column[num_column] = self.column[num_column][:-Constants.Deck.FULL_DECK_SIZE-1]
            self.score += Constants.Score.COMPLETED_DECK_BONUS
    
if (__name__ == "__main__"):
    game = Game()
    game.printState()
    while True:
        print "what to do? (d, m <x y z>, q)"
        op = raw_input()
        try:
            if (op == "d"):
                game.dealDeck()
                
            elif (op.startswith("m ")):
                m, from_column, num_card, to_column = op.split(" ")
                from_column = int(from_column)
                num_card = int(num_card)
                to_column = int(to_column)

                game.moveCard(from_column, num_card, to_column)
            elif (op == "q"):
                break
            else:
                print "unrecognized action"
        except Exception, ex:
            print "No can do: (%s) ; %s" % (ex, traceback.format_exc())
            
        game.printState()
