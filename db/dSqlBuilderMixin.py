import dabo.dConstants as k

class dSqlBuilderMixin:
	""" Create SQL statements in a programmatic fashion.
	"""
	def __init__(self):
		self._fieldClause = ""
		self._fromClause = ""
		self._whereClause = ""
		self._groupByClause = ""
		self._orderByClause = ""
		self._limitClause = ""
		self._defaultLimit = 1000
		self.hasSqlBuilder = True


	def getFieldClause(self):
		""" Get the field clause of the sql statement.
		"""
		return self._fieldClause

	def setFieldClause(self, clause):
		""" Set the field clause of the sql statement.
		"""
		self._fieldClause = clause

	def addField(self, exp):
		""" Add a field to the field clause.
		"""
		if self._fieldClause:
			self._fieldClause = "%s, " % self._fieldClause
		self._fieldClause += exp


	def getFromClause(self):
		""" Get the from clause of the sql statement.
		"""
		return self._fromClause

	def setFromClause(self, clause):
		""" Set the from clause of the sql statement.
		"""
		self._fromClause = clause

	def addFrom(self, exp):
		""" Add a table to the sql statement.

		For joins, use setFromClause() to set the entire from clause
		explicitly.
		"""
		if self._fromClause:
			self._fromClause = "%s, " % self._fromClause
		self._fromClause += exp


	def getWhereClause(self):
		""" Get the where clause of the sql statement.
		"""

	def setWhereClause(self, clause):
		""" Set the where clause of the sql statement.
		"""
		self._whereClause = clause

	def addWhere(self, exp, comp="and"):
		""" Add an expression to the where clause.
		"""
		if self._whereClause:
			self._whereClause = "%s %s " % (self._whereClause, comp)
		self._whereClause += exp


	def getGroupByClause(self):
		""" Get the group-by clause of the sql statement.
		"""

	def setGroupByClause(self, clause):
		""" Set the group-by clause of the sql statement.
		"""
		self._groupByClause = clause

	def addGroupBy(self, exp):
		""" Add an expression to the group-by clause.
		"""
		if self._groupByClause:
			self._groupByClause = "%s, " % self._groupByClause
		self._groupByClause += exp


	def getOrderByClause(self):
		""" Get the order-by clause of the sql statement.
		"""

	def setOrderByClause(self, clause):
		""" Set the order-by clause of the sql statement.
		"""
		self._orderByClause = clause

	def addOrderBy(self, exp):
		""" Add an expression to the order-by clause.
		"""
		if self._orderByClause:
			self._orderByClause = "%s, " % self._orderByClause
		self._orderByClause += exp


	def getLimitClause(self):
		""" Get the limit clause of the sql statement.
		"""

	def setLimitClause(self, clause):
		""" Set the limit clause of the sql statement.
		"""
		self._limitClause = clause


	def getSQL(self):
		""" Get the complete SQL statement from all the parts.
		"""
		fieldClause = self._fieldClause
		fromClause = self._fromClause
		whereClause = self._whereClause
		groupByClause = self._groupByClause
		orderByClause = self._orderByClause
		limitClause = self._limitClause

		if not fieldClause:
			fieldClause = "*"
		fieldClause = 'select %s ' % fieldClause

		if fromClause: 
			fromClause = ' from %s' % fromClause
		if whereClause:
			whereClause = ' where %s' % whereClause
		if groupByClause:
			groupByClause = ' group by %s' % groupByClause
		if orderByClause:
			orderByClause = ' order by %s' % orderByClause            
		if limitClause:
			limitClause = ' limit %s' % limitClause
		else:
			limitClause = ' limit %s' % self._defaultLimit

		return "%s%s%s%s%s%s" % (fieldClause, fromClause, whereClause, 
								groupByClause, orderByClause, limitClause)


	def getStructureOnlySql(self):
		holdWhere = self._whereClause
		self.setWhereClause("1 = 0")
		ret = self.getSQL()
		self.setWhereClause(holdWhere)
		return ret

	def executeSQL(self, *args, **kwargs):
		self.execute(self.createSQL(), *args, **kwargs)

