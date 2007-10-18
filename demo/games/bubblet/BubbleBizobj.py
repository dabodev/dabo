# -*- coding: utf-8 -*-
import dabo
import dabo.biz as biz
from dabo.dLocalize import _
import random
import time
import os

class BubbleBizobj(biz.dBizobj):
	def beforeInit(self):
		#self.DataSource = "Bubble"
		self.bubbles = []
		self.selCount = 0
		self.__score = 0
		self.__message = ""
		self.__callbackFunc = None
		self.__gameOver = False
		self.__isNewHighGame = False

	
	def initProperties(self):
		self.BasePrefKey = dabo.dAppRef.BasePrefKey
		
	
	def newGame(self):
		for rr in self.bubbles:
			for cc in rr:
				cc.Selected = False
				cc.setRandomColor(True)
		self.Score = 0
		self.GameOver = False
		self.IsNewHighGame = False
	
	
	def bubbleClick(self, bubble):
		ret = 0
		if bubble.Selected:
			ret = self.popBubbles()
			self.unselectBubbles()
			self.Message = _("You scored %s points!" % ret)
		else:
			self.unselectBubbles()
			self.selectBubbles(bubble)
			self.Message = _("Bubble Points: ") + str( self.BubbleScore )
		return ret
		

	def popBubbles(self):
		ret = self.BubbleScore
		self.Score += self.BubbleScore
		for rr in self.bubbles:
			for cc in rr:
				if cc.Selected:
					cc.Color = None
					cc.Selected = False
		self.selCount = 0
		self.shiftBubbles()
		self.fillEmptyCols()
		return ret
	
	
	def fillEmptyCols(self):
		isEmpty = True
		rows = len(self.bubbles)
		cols = len(self.bubbles[0])
		
		# Check if the lowest bubble is empty.
		toFill = 0
		for cc in range(cols):
			if self.bubbles[rows-1][cc].Color is None:
				toFill += 1
		
		if toFill:
			# Set the callback, so that the calling object knows that further
			# work is left
			self.__callbackFunc = self.callbackShift
			
			# Fill the columns
			for cc in range(toFill):
				num = random.randrange(rows) + 1
				for ii in range(rows-num, rows):
					bub = self.bubbles[ii][cc]
					bub.Selected = False
					bub.setRandomColor(True)
		else:
			# See if there are any moves remaining.
			self.checkGameOver()
	
	
	def shiftBubbles(self):
		""" This can vary, depending on the type of Bubblet game. For now,
		stick with the standard "megashift", where both rows and columns
		are collapsed.
		"""
		# First, clear the callback
		self.__callbackFunc = None
		rows = len(self.bubbles)
		cols = len(self.bubbles[0])
		for cc in range(cols):
			gap = False
			for rr in range(rows):
				if self.bubbles[rr][cc].Color is not None:
					gap = True
				else:
					if gap:
						for rAbove in range(rr, 0, -1):
							self.bubbles[rAbove][cc].Color = self.bubbles[rAbove-1][cc].Color
						self.bubbles[0][cc].Color = None
		# Now shift columns to the right
		for rr in range(rows):
			gap = False
			for cc in range(cols-1, 0, -1):
				currBub = self.bubbles[rr][cc]
				if currBub.Color is None:
					# See if there are any bubbles to the left that are not empty
					for cLeft in range(cc, -1, -1):
						leftBub = self.bubbles[rr][cLeft]
						if leftBub.Color is not None:
							currBub.Color = leftBub.Color
							leftBub.Color = None
							break	
		
	
	def callbackShift(self, recallFunc=None):
		self.shiftBubbles()
		self.checkGameOver()
		if recallFunc:
			recallFunc()
		
	
	def checkGameOver(self):
		""" Determine if there are any more moves possible. IOW, find at least
		one bubble with a matching neighbor.
		"""
		self.GameOver = True
		rows = len(self.bubbles)
		cols = len(self.bubbles[0])
		for rr in range(rows-1, -1,-1):
			for cc in range(cols-1, -1, -1):
				if self.hasMatchingNeighbor(self.bubbles[rr][cc]):
					self.GameOver = False
					break
			if not self.GameOver:
				break
		if self.GameOver:
			self.NumberOfGames += 1
			self.TotalPoints += self.Score
			if self.Score > self.HighGame:
				self.HighGame = self.Score
				self.IsNewHighGame = True
			# Set the message
			self.Message = _("Game Over!")
		return self.GameOver


	def hasMatchingNeighbor(self, bubble):		
		""" Need to try for matches above, below, left and right. """
		rr, cc = bubble.row, bubble.col
		color = bubble.Color
		if color is None:
			return False
		rows = len(self.bubbles)
		cols = len(self.bubbles[0])
		
		# Above
		if rr > 0:
			try:
				bub = self.bubbles[rr-1][cc]
				if bub.Color == color:
					return True
			except: pass
		# Below
		if rr < rows:
			try:
				bub = self.bubbles[rr+1][cc]
				if bub.Color == color:
					return True
			except: pass
		# Left
		if cc > 0:
			try:
				bub = self.bubbles[rr][cc-1]
				if bub.Color == color:
					return True
			except: pass
		# Right
		if cc < cols:
			try:
				bub = self.bubbles[rr][cc+1]
				if bub.Color == color:
					return True
			except: pass
		return False
		
	
	def selectBubbles(self, bubble):
		if bubble.Selected:
			return
		color = bubble.Color
		if color is None:
			# They clicked on an empty space
			return
		bubble.Selected = True
		hasMatch = False
		rr, cc = bubble.row, bubble.col
		rows = len(self.bubbles)
		cols = len(self.bubbles[0])
		
		# We need to check the bubbles on top, bottom, left and right.
		# Above
		if rr > 0:
			try:
				bub = self.bubbles[rr-1][cc]
				if bub.Color == color:
					hasMatch = True
					self.selectBubbles(bub)
			except: pass
		# Below
		if rr < rows:
			try:
				bub = self.bubbles[rr+1][cc]
				if bub.Color == color:
					hasMatch = True
					self.selectBubbles(bub)
			except: pass
		# Left
		if cc > 0:
			try:
				bub = self.bubbles[rr][cc-1]
				if bub.Color == color:
					hasMatch = True
					self.selectBubbles(bub)
			except: pass
		# Right
		if cc < cols:
			try:
				bub = self.bubbles[rr][cc+1]
				if bub.Color == color:
					hasMatch = True
					self.selectBubbles(bub)
			except: pass
		
		if not hasMatch:
			bubble.Selected = False
		else:
			self.selCount += 1

	
	def unselectBubbles(self):
		for rr in self.bubbles:
			for cc in rr:
				cc.Selected = False
		self.selCount = 0
		self.Message = _("Bubble Points: 0")
		
	
	def resetStats(self):
		self.NumberOfGames = 0
		self.TotalPoints = 0
		self.HighGame = 0
		
	
	def getCallback(self):
		return self.__callbackFunc
		
	# Begin property definitions	
	def _getBubbleScore(self):
		return (self.selCount * (self.selCount-1))

	
	def _getGameOver(self):
		return self.__gameOver

	def _setGameOver(self, val):
		self.__gameOver = val
	

	def _getHighGame(self):
		ret = self.PreferenceManager.highgame
		if not isinstance(ret, int):
			ret = 0
		return ret

	def _setHighGame(self, val):
		self.PreferenceManager.highgame = val


	def _getIsNewHighGame(self):
		return self.__isNewHighGame

	def _setIsNewHighGame(self, val):
		self.__isNewHighGame = val


	def _getMessage(self):
		return self.__message

	def _setMessage(self, msg):
		self.__message = msg


	def _getGames(self):
		ret = self.PreferenceManager.numbergames
		if not isinstance(ret, int):
			ret = 0
		return ret

	def _setGames(self, val):
		self.PreferenceManager.numbergames = val


	def _getScore(self):
		return self.__score

	def _setScore(self, val):
		self.__score = val


	def _getTotalPoints(self):
		ret = self.PreferenceManager.totalpoints
		if not isinstance(ret, int):
			ret = 0
		return ret

	def _setTotalPoints(self, val):
		self.PreferenceManager.totalpoints = val
		

	BubbleScore = property(_getBubbleScore, None, None,
			_("Current score of bubbles"))

	GameOver = property(_getGameOver, _setGameOver, None,
			_("Status of the game"))

	HighGame = property(_getHighGame, _setHighGame, None,
		_("High score"))

	IsNewHighGame = property(_getIsNewHighGame, _setIsNewHighGame, None,
		_("Is the current game the new high game?"))

	Message = property(_getMessage, _setMessage, None,
			_("Status Message"))

	NumberOfGames = property(_getGames, _setGames, None,
		_("Number of games played"))

	Score = property(_getScore, _setScore, None,
		_("Current score of the game"))

	TotalPoints = property(_getTotalPoints, _setTotalPoints, None,
		_("Total number of points recorded"))
		

