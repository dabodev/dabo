# -*- coding: utf-8 -*-
import dabo
import dabo.ui
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import dBitmap


class Card(dBitmap):
    """Class representing an individual playing card."""

    def updPic(self):
        """Sets the Picture property for this card to match
        its Suit and Rank.
        """
        if not self.FaceUp or not self.Rank or not self.Suit:
            # Card isn't set yet, or card is face-down:
            pic = "%s/back" % self.Parent.DeckDirectory
        else:
            if self.AlternatePicture:
                # The game has set an alternate pic for the card
                pic = self.AlternatePicture
            else:
                rank = self.Rank
                suit = self.Suit.lower()
                pic = "%s/%s%s" % (self.Parent.DeckDirectory, suit, ustr(rank))
        self.Picture = pic

    def _getDesc(self):
        rank = self.Rank
        suit = self.Suit
        if suit[0] == "J":
            ret = "Joker"
        else:
            if rank == 1:
                ret = "Ace"
            elif rank == 11:
                ret = "Jack"
            elif rank == 12:
                ret = "Queen"
            elif rank == 13:
                ret = "King"
            else:
                ret = ustr(rank)
            suitNames = {"S": "Spades", "D": "Diamonds", "H": "Hearts", "C": "Clubs"}
            ret += " of %s" % suitNames[suit]
        return ret

    def _getAlternatePicture(self):
        if hasattr(self, "_alternatePicture"):
            v = self._alternatePicture
        else:
            v = self._alternatePicture = None
        return v

    def _setAlternatePicture(self, val):
        self._alternatePicture = val
        self.updPic()

    def _getFaceUp(self):
        if hasattr(self, "_faceUp"):
            v = self._faceUp
        else:
            v = self._faceUp = False
        return v

    def _setFaceUp(self, val):
        if self.FaceUp != val:
            self._faceUp = bool(val)
            self.updPic()

    def _getRank(self):
        if hasattr(self, "_rank"):
            v = self._rank
        else:
            v = self._rank = None
        return v

    def _setRank(self, val):
        if self.Rank != val:
            self._rank = val
            self.updPic()

    def _getSuit(self):
        if hasattr(self, "_suit"):
            v = self._suit
        else:
            v = self._suit = None
        return v

    def _setSuit(self, val):
        suit = val[0].upper()
        if self.Suit != suit:
            if suit in ("H", "D", "S", "C"):
                self._suit = suit
                self.updPic()

    AlternatePicture = property(
        _getAlternatePicture,
        _setAlternatePicture,
        None,
        _("Alternate picture to show on face of card, overriding default behavior."),
    )

    Description = property(
        _getDesc,
        None,
        None,
        _("Descriptive name for this card, such as 'King of Clubs'  (str)"),
    )

    FaceUp = property(
        _getFaceUp,
        _setFaceUp,
        None,
        _("Specifies whether the card value is revealed.  (bool)"),
    )

    Rank = property(_getRank, _setRank, None, _("Rank for this card (int)"))

    Suit = property(
        _getSuit,
        _setSuit,
        None,
        _("Suit for this card (Spades, Hearts, Diamonds, Clubs)"),
    )


class Deck(list):
    """Class representing a deck of any number of cards.

    This is an abstract class, and should be overridden to define a particular
    playing card deck.
    """

    def __init__(self, board):
        self.board = board
        self.createDeck()

    def createDeck(self):
        """Create the Deck, which is a list of Card objects.

        Subclasses must override.
        """
        pass

    def appendCard(self, suit, rank):
        """Append a Card object with the passed suit and rank."""
        newCard = Card(self.board, Suit=suit, Rank=rank, RegID="%s%s" % (suit, rank))
        self.append(newCard)
        return newCard

    def faceUpAll(self):
        """Turn all cards face up."""
        for card in self:
            card.FaceUp = True

    def faceDownAll(self):
        """Turn all cards face down."""
        for card in self:
            card.FaceUp = False


class PokerDeck(Deck):
    def createDeck(self):
        """Create a standard 52-card Poker deck, no jokers."""
        for suit in "SHDC":
            for rank in range(1, 14):
                self.appendCard(suit, rank)
