from copy import deepcopy
from pyincore import globals as pyglobals

import pandas as pd
import operator as op
import math

logger = pyglobals.LOGGER


class VarContainer:
    """
    All matrix variable(tables) in the GAMS model is flatten to a array to make a better
    interface to the solver.

    AllVarList stores all initial values of varibles used in the GAMS model in an array.
    It also has a indexing system for looking up.

    Attributes:
        namelist: A dictionary with all stored GAMS variables and its information.
        nvars: The length of the array, i.e. the size of all matrix variables summed up.
        initialVals: Stored initial values of all variables

   """

    def __init__(self):
        """
          Initialize to an empty list
        """
        self.namelist = {}
        self.initialVals = []
        self.nvars = 0
        self.LO = []
        self.UP = []

    def add(self, name, rows=None, cols=None):
        """
        :param name:
        :param rows:
        :param cols:
        :return:
        """
        if rows is not None and cols is not None:
            size = len(rows) * len(cols)
            self.namelist[name] = { \
                'nrows': len(rows), \
                'ncols': len(cols), \
                'rows': rows, \
                'cols': cols, \
                'start': self.nvars, \
                'size': size
            }
        elif rows is not None and cols is None:
            size = len(rows)
            self.namelist[name] = {
                'nrows': len(rows), \
                'rows': rows, \
                'start': self.nvars, \
                'size': size
            }
        else:
            size = 1
            self.namelist[name] = {'start': self.nvars, 'size': 1}

        self.initialVals.extend([None] * size)
        self.LO.extend([None] * size)
        self.UP.extend([None] * size)
        self.nvars += size

        return ExprM(self, name=name, rows=rows, cols=cols)

    def set_value(self, name, values, target):
        """
        An internal method for setting the initial values or UPs and LOs for variables

        :param name: Name of the variable in GAMS
        :param value: a pandas DataFrame, pandas Series, int or float with initial values
        :param target: target array to be set

        :return: None
        """
        if type(values) == int or type(values) == float:
            info = self.namelist[name]
            if 'nrows' in info and 'ncols' in info:
                values = pd.DataFrame(index=info['rows'], columns=info['cols']).fillna(values)
            elif 'nrows' in info and 'ncols' not in info:
                values = pd.Series(index=info['rows'], dtype='float64').fillna(values)

        if type(values) == pd.DataFrame:
            rows = values.index.tolist()
            cols = values.columns.tolist()
            for i in rows:
                for j in cols:
                    target[self.getIndex(name, row=i, col=j)] = float(values.loc[i][j])
        elif type(values) == pd.Series:
            rows = values.index.tolist()
            for i in rows:
                target[self.getIndex(name, row=i)] = float(values.loc[i])
        else:
            target[self.getIndex(name)] = values

    def init(self, name, initialValue):
        """
        Flatten the table variable and add to the list.
        Also set the initial variable values array.

        :param name: Name of the variable in GAMS
        :param initialValue: a pandas DataFrame or pandas Series with initial values

        :return: None.
        """
        self.set_value(name, initialValue, self.initialVals)

    def inList(self, name):
        """
        Check if a GAMS varible is added to the container

        :param name(str): name of GAMS variable you want to look up
        :return: Boolean, whether the variable is added.
        """
        return name in self.namelist

    def getInfo(self, name):
        """
        Get the information about a GAMS variable

        :param name(str): name of GAMS variable you want to look up
        :return: a dictionary with all information
        """
        return self.namelist[name]

    def getIndex(self, name, row=None, col=None):
        """
        Look up the index by providing the variable name and label information

        :param name: name of GAMS variable you want to look up
        :param row: row label of the position you want to look up index for(if it has row labels)
        :param col: column label of the position you want to look up index for(if it has column labels)
        :return: the index of the position in the array
        """
        info = self.namelist[name]
        result = info['start']
        if row is not None and col is not None:
            result += info['rows'].index(row) * info['ncols'] + info['cols'].index(col)
        elif row is not None:
            result += info['rows'].index(row)
        return result

    def getLabel(self, index):
        """
        Look up variable name and label information by providing the index

        :param index: the index in the array
        :return: its information including the variable name, row label and column label if applicable
        """
        result = []
        for i in self.namelist.keys():
            if index >= self.namelist[i]['start'] and index < self.namelist[i]['start'] + self.namelist[i]['size']:
                result.append(i)
                if self.namelist[i]['size'] > 1:
                    diff = index - self.namelist[i]['start']
                    if 'ncols' in self.namelist[i]:
                        result.append(self.namelist[i]['rows'][int(diff / self.namelist[i]['ncols'])])
                        result.append(self.namelist[i]['cols'][diff % self.namelist[i]['ncols']])
                    else:
                        result.append(self.namelist[i]['rows'][diff])
                return result

    def get_all_variable_printed(self, output=None):
        if output is None:
            output = self.initialVals
        for i in range(len(output)):
            label = self.getLabel(i)
            if len(label) == 1:
                logger.debug(label[0] + '=' + '{0:.7f}'.format(output[i]) + ';')
            elif len(label) == 2:
                logger.debug(label[0] + '(\'' + label[1] + '\')' + '=' + '{0:.7f}'.format(output[i]) + ';')
            elif len(label) == 3:
                logger.debug(
                    label[0] + '(\'' + label[1] + '\',\'' + label[2] + '\')' + '=' + '{0:.7f}'.format(output[i]) + ';')

    def get(self, name, x=None):
        """
          Returns a Dataframe, Series, or a variable based on the given name and the result array returned from the solver

          :param name: GAMS variable name
          :return: if x is not given, it returns the initial values
            if x is set to the result, returns the result variable value
        """
        if x is None:
            x = self.initialVals

        info = self.namelist[name]
        if 'nrows' in info and 'ncols' in info:
            ret = pd.DataFrame(index=info['rows'], columns=info['cols']).fillna(0.0)
            for i in info['rows']:
                for j in info['cols']:
                    ret.at[i, j] = x[self.getIndex(name, row=i, col=j)]
        elif 'nrows' in info and 'ncols' not in info:
            ret = pd.Series(index=info['rows'], dtype='float64').fillna(0.0)
            for i in info['rows']:
                ret.at[i] = x[self.getIndex(name, row=i)]
        elif 'nrows' not in info and 'ncols' not in info:
            ret = x[self.getIndex(name)]

        return ret

    def lo(self, name, value):
        """
          Set the LOs of a GAMS variable providing the LOs with a Dataframe, Series, int or float

          :param name: GAMS variable name
          :param value: The lower bound to be set
          :return: None
        """
        self.set_value(name, value, self.LO)

    def up(self, name, value):
        """
          Set the UPs of a GAMS variable providing the LOs with a Dataframe, Series, int or float

          :param name: GAMS variable name
          :param value: The upper bound to be set
          :return: None
        """
        self.set_value(name, value, self.UP)

    def write(self, filename):
        """
          Write(append) the variables to a file, in the format of setting ipopt model variables

          :param filename: the output filename
          :return: None
        """
        with open(filename, 'a') as f:
            for i in range(self.nvars):
                lower = -1e20 if self.LO[i] is None else self.LO[i]
                upper = 1e20 if self.UP[i] is None else self.UP[i]
                value = 0 if math.isnan(self.initialVals[i]) else self.initialVals[i]

                # tmp_list = ['CG','CH','CN','CPI','CPIN','CPIH','CX','D','DD','DS','FD','GCP','GCP1','HH','HN','HW','IGT','KS']
                '''tmp_list = ['CG','CH','CN','CPI','CPIN','CPIH','CX','D','DD','DS','FD','GCP','GCP1','HH','HN','HW','IGT','KS','LAS','M','N','NKI','LNFOR','KPFOR','GVFOR','P','PD','PVA']                        
                if self.getLabel(i)[0] in tmp_list:
                    f.write('model.x' + str(i) + ' = Var(bounds=(' + str(lower) + ',' + str(upper) + '),initialize=' + str(self.initialVals[i]) + ')' + '\n')
                else:
                    f.write('model.x' + str(i) + ' = Var(bounds=(' + str(self.initialVals[i]-1e-3) + ',' + str(self.initialVals[i]+1e-3) + '),initialize=' + str(self.initialVals[i]) + ')' + '\n')
                '''
                # if i == 1507:
                #  f.write('model.x' + str(i) + ' = Var(bounds=(' + str(value) + ',' + str(value*10) + '),initialize=' + str(value) + ')' + '\n')
                # else:
                #  f.write('model.x' + str(i) + ' = Var(bounds=(' + str(lower) + ',' + str(upper) + '),initialize=' + str(value) + ')' + '\n')
                f.write('model.x' + str(i) + ' = Var(bounds=(' + str(lower) + ',' + str(upper) + '),initialize=' + str(
                    value) + ')' + '\n')


class Variable:
    """
      A GMAS variable, initialized by given the GAMS variable value and its label
    """

    def __init__(self, vars, name, row=None, col=None):
        """
          Initialize it with a variable container, the GAMS name, the labels

          :param vars: the variable container that already added the GAMS variable
          :param name: GAMS variable name
          :param row: GAMS row label if there is
          :param col: GAMS col label if there is
          :return: None
        """
        try:
            self.index = vars.getIndex(name, row, col)
        except Exception as e:
            logger.debug(e)
            # print("invalid name for a variable")

    def __str__(self):
        """
          returns the variable in the format of "model.x#" if gets printed,
          with # being the index in the array in the container

          :return: String
        """
        return 'model.x' + str(self.index) + ''
        # return 'x[' + str(self.index) + ']'

    def debug_test_str(self):
        return 'x[' + str(self.index) + ']'


class ExprItem:
    '''
      You can construct it with a variable, a constant or a deepcopy of another ExprItem
    '''

    def __init__(self, v, const=1):
        self.varList = []
        self.const = const
        if type(v) == Variable:
            self.varList.append(v)
        elif type(v) == int or type(v) == float:
            self.const = v
        elif type(v) == ExprItem:
            self.const = deepcopy(v.const)
            self.varList = deepcopy(v.varList)
        else:
            logger.debug("invalid parameter to create a item")

    '''
      You could multiply it with a number, a variable, a ExprItem or Expression
    '''

    def __mul__(self, rhs):
        copy = ExprItem(self)
        if type(rhs) == int or type(rhs) == float:
            copy.const = copy.const * rhs
        elif type(rhs) == Variable:
            copy.varList.append(rhs)
        elif type(rhs) == ExprItem:
            copy.const *= rhs.const
            copy.varList.extend(deepcopy(rhs.varList))
        elif type(rhs) == Expr:
            if rhs.isComposite:
                if rhs.operator == '/':
                    return rhs * copy
                else:
                    copy.varList.append(Expr(rhs))
            else:
                copyrhs = Expr(rhs)
                copyrhs.itemList = [i * copy for i in copyrhs.itemList]
                return copyrhs
        return copy

    def __str__(self):
        # if abs(self.const) > 0.1:
        #  result = '' + str(round(self.const,3))
        # else:
        #  result = '' + str(self.const)
        # result = '' + str(round(self.const,7))
        result = '' + str(self.const)
        for i in range(len(self.varList)):
            result += "*" + self.varList[i].__str__()
        return result

    def debug_test_str(self):
        # if abs(self.const) > 0.1:
        #  result = '' + str(round(self.const,3))
        # else:
        #  result = '' + str(self.const)
        result = '' + str(self.const)
        for i in range(len(self.varList)):
            result += "*" + self.varList[i].debug_test_str()
        return result

    def is_empty(self):
        if abs(self.const) < 0.00000001:
            return True
        else:
            return False

    def is_one(self):
        if abs(self.const - 1) < 0.0000001 and len(self.varList) == 0:
            return True
        else:
            return False


class Expr:

    def __init__(self, item):
        self.itemList = []
        self.isComposite = False
        if type(item) == ExprItem or type(item) == Variable or type(item) == int or type(item) == float:
            self.itemList.append(ExprItem(item))
        elif type(item) == Expr:
            self.itemList = [
                ExprItem(item.itemList[i]) if type(item.itemList[i]) == ExprItem else Expr(item.itemList[i]) for i in
                range(len(item.itemList))]
            try:
                self.isComposite = deepcopy(item.isComposite)
            except Exception as e:
                pass
            try:
                self.operator = deepcopy(item.operator)
            except Exception as e:
                pass
            try:
                self.first = Expr(item.first)
            except Exception as e:
                pass
            try:
                self.second = Expr(item.second)
            except Exception as e:
                pass
        else:
            logger.debug("invalid parameter for creating a Expr")

        self.clear_empty()

    def __add__(self, rhs):
        copy = Expr(self)
        if self.isComposite:
            tmp = Expr(self)
            copy.itemList = [tmp]
            copy.isComposite = False
        if type(rhs) == Expr:
            if rhs.isComposite:
                rhscopy = Expr(rhs)
                copy.itemList.append(rhscopy)
            else:
                rhscopy = Expr(rhs)
                copy.itemList = copy.itemList + rhscopy.itemList
        elif type(rhs) == ExprItem or type(rhs) == int or type(rhs) == float or type(rhs) == Variable:
            copy.itemList.append(ExprItem(rhs))
        return copy

    def __sub__(self, rhs):
        copy = Expr(self)
        return copy + rhs * -1

    def __mul__(self, rhs):
        copy = Expr(self)
        if type(rhs) == int or type(rhs) == float or type(rhs) == ExprItem:
            if copy.isComposite:
                if copy.operator == '/':
                    copy.first = copy.first * rhs
                elif copy.opeartor == '**':
                    return ExprItem(rhs) * copy
            else:
                result = []
                for i in copy.itemList:
                    result.append(i * rhs)
                copy.itemList = result


        elif type(rhs) == Expr:
            if copy.isComposite and not rhs.isComposite:
                if copy.operator == '/':
                    copy.first = copy.first * rhs
                else:
                    copy.itemList = [i * copy for i in rhs.itemList]
                    copy.isComposite = False
            elif not copy.isComposite and not rhs.isComposite:
                # print('copy',copy)
                # print('rhs',rhs)

                if len(copy.itemList) * len(rhs.itemList) > 10:

                    tmpItem = ExprItem(1)
                    tmpItem.varList.append(Expr(copy))
                    tmpItem.varList.append(Expr(rhs))
                    copy.itemList = [tmpItem]

                else:

                    # The expanding way is super slow for long equations

                    result = []
                    for i in copy.itemList:
                        for j in rhs.itemList:
                            if type(i) == Expr:
                                tmp = Expr(i)
                            elif type(i) == ExprItem:
                                tmp = ExprItem(i)
                            result.append(tmp * j)
                    copy.itemList = result

            elif not self.isComposite and rhs.isComposite:
                return rhs * copy
            else:
                # both are composite
                if copy.operator == '/' and rhs.operator == '/':
                    copy.first = copy.first * rhs.first
                    copy.second = copy.second * rhs.second
                elif copy.operator == '**' and rhs.operator == '**':
                    copy.first = copy.first * rhs.first
                    copy.second = copy.second + rhs.second
                elif copy.operator == '/' and rhs.operator == '**':
                    copy.first = copy.first * rhs
                elif copy.operator == '**' and rhs.operator == '/':
                    copyrhs = Expr(rhs)
                    copyrhs.first = copyrhs.first * copy
        return copy

    def __truediv__(self, rhs):
        copy = Expr(self)
        tmp = Expr(copy)
        copy.isComposite = True
        copy.operator = '/'
        copy.first = tmp
        copy.second = Expr(rhs)
        return copy

    def __pow__(self, rhs):
        copy = Expr(self)
        tmp = Expr(copy)
        copy.isComposite = True
        copy.operator = '**'
        copy.first = tmp
        copy.second = Expr(rhs)
        return copy

    def __str__(self):
        if self.isComposite:
            result = "(" + self.first.__str__() + self.operator + self.second.__str__() + ")"
        else:
            if len(self.itemList) == 0:
                return '0'
            result = ''
            for i in self.itemList[0:-1]:
                result += "(" + i.__str__() + ")" + "+"
            result += "(" + self.itemList[-1].__str__() + ")"
            if len(self.itemList) > 1:
                result = "(" + result + ")"
        return result

    def debug_test_str(self):
        if self.isComposite:
            result = "(" + self.first.debug_test_str() + self.operator + self.second.debug_test_str() + ")"
        else:
            if len(self.itemList) == 0:
                return '0'
            result = ''
            for i in self.itemList[0:-1]:
                result += "(" + i.debug_test_str() + ")" + "+"
            result += "(" + self.itemList[-1].debug_test_str() + ")"
            if len(self.itemList) > 1:
                result = "(" + result + ")"
        return result

    def is_empty(self):
        if not self.isComposite and len(self.itemList) == 0:
            return True
        else:
            return False

    def clear_empty(self):
        result = []
        if self.isComposite == False:
            for i in range(len(self.itemList)):
                if type(self.itemList[i]) == ExprItem:
                    if not self.itemList[i].is_empty():
                        result.append(self.itemList[i])
                if type(self.itemList[i]) == Expr:
                    self.itemList[i].clear_empty()
                    if not self.itemList[i].is_empty():
                        result.append(self.itemList[i])
            self.itemList = result
        """
        else:
          if self.operator == '**' and is_empty(self.second):
            self.isComposite = False
            self.itemList = []
            self.itemList.append(ExprItem(1))
        """


class ExprM:
    """
    Three ways to create a ExprMatrix:
    1. Give it the variable name, selected rows and cols(could be empty),
      The constructor will create a Expression matrix from the variable matrix
    2. Give it a pandas Series or DataFrame, it will create the Expression matrix
      with the content in the Series or DataFrame as constants
    3. Give it a ExprMatrix, will return a deep copy of it
    """

    def __init__(self, vars, name=None, rows=None, cols=None, m=None, em=None):
        self.vars = vars
        self.hasCondition = False
        if em is None:
            # if these are the variables, we need to create an Expression by the variable name
            if name is not None:
                if self.vars.inList(name):
                    self.info = deepcopy(self.vars.getInfo(name))
                else:
                    logger.debug("Can't find this variable in the all variable list")

                self.info['height'] = 1
                self.info['width'] = 1
                self.info['rows'] = deepcopy(rows)
                self.info['cols'] = deepcopy(cols)
                if cols is not None:
                    self.info['width'] = len(cols)
                if rows is not None:
                    self.info['height'] = len(rows)

                if cols is not None:  # if it is a DataFrame
                    self.m = [[Expr(Variable(self.vars, name, i, j)) for j in cols] for i in rows]
                elif rows is not None:  # if it is a Series
                    self.m = [[Expr(Variable(self.vars, name, i))] for i in rows]
                else:  # if it is a variable
                    self.m = [[Expr(Variable(self.vars, name))]]

            # otherwise these are just constants
            else:
                self.info = {}
                self.info['height'] = 1
                self.info['width'] = 1
                self.info['rows'] = None
                self.info['cols'] = None
                if type(m) == pd.DataFrame:
                    self.info['rows'] = m.index.tolist()
                    self.info['height'] = len(self.info['rows'])
                    self.info['cols'] = m.columns.tolist()
                    self.info['width'] = len(self.info['cols'])
                    self.m = [[Expr(float(m.loc[i, j])) for j in self.info['cols']] for i in self.info['rows']]
                elif type(m) == pd.Series:
                    self.info['rows'] = m.index.tolist()
                    self.info['height'] = len(self.info['rows'])
                    self.m = [[Expr(float(m.loc[i]))] for i in self.info['rows']]
                else:
                    self.m = [[Expr(float(m))]]
        else:
            # make deep copy
            self.info = deepcopy(em.info)
            self.m = [[Expr(em.m[i][j]) for j in range(em.info['width'])] for i in range(em.info['height'])]

    def operation(self, rhs, oper):
        copy = ExprM(self.vars, em=self)

        if type(rhs) == int or type(rhs) == float:
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    copy.m[i][j] = oper(copy.m[i][j], Expr(rhs))

        elif type(rhs) == pd.DataFrame or type(rhs) == pd.Series:
            return self.operation(ExprM(self.vars, m=rhs), oper)

        elif type(rhs) == ExprM:
            if copy.info['rows'] == rhs.info['rows'] and copy.info['cols'] == rhs.info['cols']:
                # same size, apply operation element-wise
                for i in range(self.info['height']):
                    for j in range(self.info['width']):
                        copy.m[i][j] = oper(copy.m[i][j], rhs.m[i][j])
            elif copy.info['rows'] == rhs.info['rows'] and copy.info['width'] == 1:
                # for each column in rhs
                result = [[Expr(0) for j in range(rhs.info['width'])] for i in range(self.info['height'])]
                for i in range(self.info['height']):
                    for j in range(rhs.info['width']):
                        result[i][j] = oper(copy.m[i][0], rhs.m[i][j])
                copy.m = result
                copy.info['width'] = rhs.info['width']
                copy.info['cols'] = deepcopy(rhs.info['cols'])
            elif copy.info['rows'] == rhs.info['rows'] and rhs.info['width'] == 1:
                # for each column in lhs
                for i in range(self.info['height']):
                    for j in range(self.info['width']):
                        copy.m[i][j] = oper(copy.m[i][j], rhs.m[i][0])
            elif copy.info['height'] == 1 and copy.info['cols'] == rhs.info['cols']:
                # for each row in rhs
                result = [[Expr(0) for j in range(rhs.info['width'])] for i in range(rhs.info['height'])]
                for i in range(rhs.info['height']):
                    for j in range(rhs.info['width']):
                        result[i][j] = oper(copy.m[0][j], rhs.m[i][j])
                copy.m = result
                copy.info['height'] = rhs.info['height']
                copy.info['rows'] = deepcopy(rhs.info['rows'])
            elif rhs.info['height'] == 1 and copy.info['cols'] == rhs.info['cols']:
                # for each row in lhs
                for i in range(self.info['height']):
                    for j in range(self.info['width']):
                        copy.m[i][j] = oper(copy.m[i][j], rhs.m[0][j])
            elif (self.info['width'] == rhs.info['height'] and self.info['cols'] == rhs.info['rows']) or \
                    (self.info['height'] == rhs.info['width'] and self.info['rows'] == rhs.info['cols']):
                # flip the matrix
                return oper(self, ~rhs)

            else:
                logger.debug(copy.info['rows'], copy.info['cols'], rhs.info['rows'], rhs.info['cols'])
                logger.debug(copy.info['height'], copy.info['width'], rhs.info['height'], rhs.info['width'])
                logger.debug("Invalid size for ", str(oper))
        return copy

    def __add__(self, rhs):
        return self.operation(rhs, op.add)

    def __radd__(self, lhs):
        return self + lhs

    def __sub__(self, rhs):
        return self.operation(rhs, op.sub)

    def __rsub__(self, lhs):
        return self * -1 + lhs

    def __mul__(self, rhs):
        return self.operation(rhs, op.mul)

    def __truediv__(self, rhs):
        return self.operation(rhs, op.truediv)

    def __pow__(self, rhs):
        return self.operation(rhs, op.pow)

    def __xor__(self, rhs):
        """
          create 2d list out of 2 single lists
        """
        # has to be 2 single lists
        if self.info['width'] != 1 or rhs.info['width'] != 1:
            logger.debug("Invalid size for creating a 2-D matrix")
        else:
            copy = ExprM(self.vars, em=self)
            copy.m = [[copy.m[i][0] * rhs.m[j][0] for j in range(rhs.info['height'])] for i in
                      range(copy.info['height'])]
            copy.info['cols'] = deepcopy(rhs.info['rows'])
            copy.info['width'] = deepcopy(rhs.info['height'])
            return copy

    def __invert__(self):
        """
          Return the transpose of a Expression matrix
        """
        copy = ExprM(self.vars, em=self)
        result = [[copy.m[i][j] for i in range(copy.info['height'])] for j in range(copy.info['width'])]
        copy.info['height'], copy.info['width'] = copy.info['width'], copy.info['height']
        copy.info['rows'], copy.info['cols'] = copy.info['cols'], copy.info['rows']
        copy.m = result
        return copy

    def __str__(self):
        result = ''
        for i in self.m:
            for j in i:
                result += j.__str__() + '\n'
            result += '///////////////////\n'
        return result

    def loc(self, rows=None, cols=None):
        """
          get a subset of the matrix by labels
        """
        copy = ExprM(self.vars, em=self)
        if cols is not None:
            result = [[Expr(copy.m[self.info['rows'].index(i)][self.info['cols'].index(j)]) for j in cols] for i in
                      rows]
            copy.m = result
            copy.info['rows'] = deepcopy(rows)
            copy.info['height'] = len(copy.info['rows'])
            copy.info['cols'] = deepcopy(cols)
            copy.info['width'] = len(copy.info['cols'])
            return copy
        elif rows is not None:
            result = [[Expr(copy.m[self.info['rows'].index(i)][0])] for i in rows]
            copy.m = result
            copy.info['rows'] = deepcopy(rows)
            copy.info['height'] = len(copy.info['rows'])
            return copy
        else:
            return copy

    def sum(self, label=None):
        copy = ExprM(self.vars, em=self)
        if label == None:
            result = Expr(0)
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    result = result + copy.m[i][j]
            copy.m = [[result]]
            copy.info['width'] = 1
            copy.info['height'] = 1
            copy.info['rows'] = None
            copy.info['cols'] = None

        elif label == self.info['rows'] or label == 0:
            result = [[Expr(0) for j in range(self.info['width'])]]
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                        result[0][j] = result[0][j] + copy.m[i][j]
            copy.m = result
            copy.info['height'] = 1
            copy.info['rows'] = None

        elif label == self.info['cols'] or label == 1:
            result = [[Expr(0)] for i in range(self.info['height'])]
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                        result[i][0] = result[i][0] + copy.m[i][j]
            copy.m = result
            copy.info['width'] = 1
            copy.info['cols'] = None
        return copy

    def prod(self, label):
        copy = ExprM(self.vars, em=self)
        if label == self.info['rows'] or label == 0:
            result = [[Expr(1) for j in range(self.info['width'])]]
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                        result[0][j] = result[0][j] * copy.m[i][j]
            copy.m = result
            copy.info['height'] = 1
            copy.info['rows'] = None
        elif label == self.info['cols'] or label == 1:
            result = [[Expr(1)] for i in range(self.info['height'])]
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                        result[i][0] = result[i][0] * copy.m[i][j]
            copy.m = result
            copy.info['width'] = 1
            copy.info['cols'] = None
        return copy

    def setCondition(self, matrix, operator=None, value=None):
        self.hasCondition = True
        mappings = {'LT': op.lt, 'LE': op.le, 'EQ': op.eq, 'INEQ': op.ne}  # not complete list
        if type(matrix) == pd.DataFrame:
            self.mark = [[False for j in range(self.info['width'])] for i in range(self.info['height'])]
            for i in range(self.info['height']):
                for j in range(self.info['width']):
                    if operator == None:
                        self.mark[i][j] = op.ne(matrix.loc[self.info['rows'][i]][self.info['cols'][j]], 0)
                    else:
                        self.mark[i][j] = mappings[operator](matrix.loc[self.info['rows'][i]][self.info['cols'][j]],
                                                             value)

        if type(matrix) == pd.Series:
            self.mark = [[False] for i in range(self.info['height'])]
            for i in range(self.info['height']):
                if operator == None:
                    self.mark[i][0] = op.ne(matrix.loc[self.info['rows'][i]], 0)
                else:
                    self.mark[i][0] = mappings[operator](matrix.loc[self.info['rows'][i]], value)

    def write(self, count, filename):
        f = open(filename, 'a')
        for i in range(self.info['height']):
            for j in range(self.info['width']):
                if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                    f.write(
                        'model.equality' + str(count[0]) + ' = Constraint(expr=' + self.m[i][j].__str__() + ' == 0)\n')
                    count[0] += 1
        f.close()

    def test(self, x):
        for i in range(self.info['height']):
            for j in range(self.info['width']):
                if not self.hasCondition or self.hasCondition and self.mark[i][j]:
                    fun = lambda x: eval(self.m[i][j].debug_test_str())
                    logger.debug(i, j, fun(x))
