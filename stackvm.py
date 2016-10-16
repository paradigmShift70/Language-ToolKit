import itertools
import operator as op
import math
import copy


class Environment( object ):
   SAVE = [ ]

   def __init__( self, parent=None ):
      self._parent  = parent
      self._locals        = { }

   def parentEnv( self ):
      return self._parent

   def resetLocal( self ):
      self._locals        = { }

   def declLocal( self, aSymbol, aValue=None ):
      self._locals[ aSymbol ] = aValue

   def set( self, aSymbol, aValue ):
      self._set( aSymbol, aValue, self )

   def get( self, aSymbol ):
      if aSymbol in self._locals:
         return self._locals[ aSymbol ]
      elif self._parent is None:
         return None
      else:
         return self._parent.get( aSymbol )

   def _set( self, aSymbol, aValue, localScope ):
      if aSymbol in self._locals:
         self._locals[ aSymbol ] = aValue
      elif self._parent is None:
         localScope.declLocal( aSymbol, aValue )
      else:
         self._parent._set( aSymbol, aValue, localScope )

   def isDefined( self, aSymbol ):
      if aSymbol in self._locals:
         return True
      elif self._parent is None:
         return False
      else:
         return self._parent.isDefined( aSymbol )

   def saveSymTab( self ):
      PkEnvironment.SAVE.append( self._locals.copy() )

   def restoreSymTab( self ):
      self._locals = PkEnvironment.SAVE.pop( )

   def __iter__( self ):
      if self._parent is None:
         return iter( self._locals )
      else:
         return itertools.chain( self._locals, self._parent )


class StackVM( object ):
   # Flags
   NO_ERROR              = 0
   CARRY                 = 1
   STACK_OF              = 2
   STACK_UF              = 3
   UNKNOWN_UNRECOVERABLE = 4
   BAD_ADDRESS           = 8
   HALT                  = 9
   
   def __init__( self ):
      self.reboot( [ ] )

   def reboot( self, CS, SS=None, HS=None, ENV=None ):
      if CS is None:
         CS = [ ]

      if SS is None:
         SS = [ ]

      self.CS      = CS    # The Code Segment
      self.CP      = 0     # The Code Pointer
      
      self.SS      = SS    # The Stack Segment
      self.SP      = 0     # The Stack Pointer (running value for len(_SS))
      
      self.ENV     = Environment() # The Environment
      
      self.IR      = ''    # Instruction Register
      self.BP      = 0                         # Base Pointer
      self.FLG     = 0                         # Flag Register
   
   def run( self, CS ):
      self.reboot( CS )
      while True:
         self.IR = self.CS[ self.CP ]
         func = getattr( self, 'op_' + self.IR )
         func( )
         
         if self.FLG != 0:
            if self.FLG == self.HALT:
               break
  
   def run_withTrace( self, CS ):
      self.reboot( CS )
      while True:
         self.IR = self.CS[ self.CP ]
         
         self._trace_instruction( )
         
         func = getattr( self, 'op_' + self.IR )
         func( )
         
         if self.FLG != 0:
            if self.FLG == self.HALT:
               break
 
   def _trace_instruction( self ):
      opcode = self.IR
      
      trace = [ ]
      for operand in self.CS[self.CP + 1 : ]:
         if isinstance( operand, (int,float,bool) ):
            trace.append( str(operand) )
         elif isinstance( operand, str ):
            if getattr( self, 'op_' + operand, False ):
               break
            else:
               trace.append( operand[:12] )
         elif isinstance( operand, list ):
            trace.append( '[...]' )
         elif isinstance( operand, tuple ):
            trace.append( '(...)' )
         else:
            raise Exception( )
      
      peek = ', '.join( trace ).rstrip()
      stackTrace = str(self.SS)[-40:]
      print( '{0:06d}:  {1:10s}  {2:10}  ||  {3:s}'.format( self.CP, self.IR, peek, stackTrace ) )
 
   def _trace_stack( self, fieldSize=50 ):
      return str(self.SS)[-fieldSize:]

   # #######
   # PROBES & OPCODE implementation tools
   def top( self, num ):
      return self.SS[ 0 - num : ]

   def IDENTITY( self, arg ):
      return arg
   
   def UNARY_OP( self, type1, fn ):
      arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(arg1) )
      self.CP += 1
   
   def BINARY_OP( self, fn, type1, type2 ):
      arg2 = self.SS.pop( )
      arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(self.SS[-1]), type2(arg2) )
      self.CP += 1
   
   #def BINARY_OP( self, fn, type1, type2 ):
      # Weakly Typed Version
      #self.SS[-1] = (lambda x: self.SS[-1]   +   x)(self.SS.pop())
      #self.CP += 1
      
      # Strongly Typed Version
      #self.SS[-1] = (lambda x: type1(self.SS[-1])   +   type2(x))(self.SS.pop())
      #self.CP += 1
   
   def BINARY_OP2( self, fn, type1, type2 ):
      '''Same as above but swapps the args to fn()'''
      arg2 = self.SS.pop( )
      arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(arg2), type2(arg1) )
      self.CP += 1
   
   #def BINARY_OP2( self, fn, type1, type2 ):
      #self.SS[-1] = (lambda x: x   +   self.SS[-1])(self.SS.pop())
      #self.CP += 1
      
   
   def JUMP_OP( self ):
      self.CP = self.CS[ self.CP + 1 ]
   
   def CJUMP_OP( self, fn ):
      arg1 = self.SS.pop( )
      if fn(arg1):
         self.CP = self.CS[ self.CP + 1 ]
      else:
         self.CP += 2
   
   # #######
   # OPCODES
   
   # patterns
   # - to get the top n items:
   #     arg1, arg2 = self._SS[ -2 : ]
   # - to replace stack top (push without popping)
   #     self._[ -1 ] = val
   # - to get an operand (which follows an opcode)
   #  operand = self._CS[ self._CP + 1 ]    # get operand
   
   # Stack Operations
   def op_PUSH( self ):
      '''
      PUSH <value>
      [ ... ]  =>  [ ..., <value> ]
      '''
      operand = self.CS[ self.CP + 1 ]    # get operand
      self.SS.append( operand )
      self.CP += 2
   
   def op_POP( self ):                      # POP <count>
      '''POP
      [ ... ]  =>  [ ... ]
      Remove 1 item from the top of the stack.
      '''
      self.SS.pop( )
      self.CP += 1
   
   def op_POPn( self ):                     # POPn <count>
      '''POP <count>
      [ ... ]  =>  [ ... ]
      Remove <count> items from the top of the stack
      '''
      operand = self.CS[ self.CP + 1 ]    # get operand
      result = self.SS[ 0 - operand : ]
      del self.SS[ 0 - operand : ]
      self.CP =+ 2

   def op_TOPSET( self ):                   # TOPSET <val>
      operand = self.CS[ self.CP + 1 ]    # get operand
      self.SS[ -1 ] = val      
      self.CP += 2
   
   def op_PUSHnth( self ):                  # PUSHNTH <offset>
      operand = self.CS[ self.CP + 1 ]    # get operand
      self.SS.append( self.SS[ 0 - operand ] )      
      self.CP += 2

   def op_SWAPXY( self ):
      self.SS[ 0 - 2 ], self.SS[ 0 - 1 ] = self.SS[ 0 - 2 : ]
      self.CP += 1

   # Environment Management
   def op_DEF( self ):        # [ obj, name ]  =>  [ obj ]
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.declLocal( name, obj )
      self.CP += 1
   
   def op_SET( self ):        # [ obj, name ]  =>  [ obj ]
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.set( name, obj )
      self.CP += 1
   
   def op_GET( self ):        # [ name ]  =>  [ obj ]
      name = self.SS[-1]
      self.SS[-1] = self.ENV.get( name )
      self.CP += 1
   
   def op_ISDEF( self ):      # [ name ]  =>  [ obj ]
      name = self.SS[-1]
      self.SS[-1] = self.ENV.isDefined( name )
      self.CP += 1

   def op_OPEN( self ):       # open a new (nested) scope.
      self.ENV = Environment( self.ENV )
      self.CP += 1
   
   def op_CLOSE( self ):
      self.ENV = self.ENV.parentEnv( )
      self.CP += 1

   # Register Controls
   def op_PUSHFLG( self ):
      self.SS.append( self.FLG )
      return self.CP + 1

   def op_POPFLG( self ):
      self.FLG = self.SS.pop( )
      return self.CP + 1

   #def op_CALL( self ):             # [ ..., arg2, arg1, NewCodeSeg, numArgs ]
      # Prepare new Stack Frame & Return Info
      #numArgs = self.SS.pop( )
      #newCodeSeg = self.SS.pop( )
   def op_CALL( self ):             # [ ..., arg2, arg1, NewCodeSeg ]
      # Prepare new Stack Frame & Return Info
      newCodeSeg = self.CS[self.CP+1]
      numArgs    = self.CS[self.CP+2]
      self.SP    = len(self.SS) - 1
      
      # Save current stack frame
      returnInfo = [numArgs, self.CS, self.CP+3, self.SP+1, self.BP]
      self.SS.append( returnInfo )
      
      # Construct new stack frame
      self.SP += 1
      self.BP = self.SP          # BP points to returnInfo
      self.CS = newCodeSeg
      self.CP = 0
   
   def op_RECURSE( self ):
      CS = self.CS
      CP = self.CP
      SS = self.SS
      SP = self.SP
      BP = self.BP
      # Prepare new Stack Frame & Return Info
      newCodeSeg = self.CS
      numArgs    = self.CS[self.CP+1]
      self.SP    = len(self.SS) - 1       # SP is the index of the top item of the stack
      
      # Save current stack frame
      returnInfo = [numArgs, self.CS, self.CP+2, self.SP+1, self.BP]
      self.SS.append( returnInfo )
      
      # Construct new stack frame
      self.SP += 1
      self.BP = self.SP          # BP points to returnInfo
      self.CS = newCodeSeg
      self.CP = 0

   def op_RET( self ):
      returnValue = self.SS.pop( )        # Save a copy of the return value
      
      numArgs, self.CS, self.CP, self.SP, self.BP = self.SS[ self.BP ]  # Restore the caller's stack frame
      
      del self.SS[ self.SP - numArgs : ]  # Pop all of the caller's arguments
      
      self.SS.append( returnValue )       # Restore the return value to the top of the stack
      self.SP = len(self.SS) - 1          # SP is index of top stack item
   
   def op_PUSH_BPOFF( self ):
      '''PUSH_BPOFF
      Push an element at the indicated offset from the Base Pointer.
      '''
      offset = self.CS[ self.CP + 1 ]
      self.SS.append( self.SS[self.BP + offset] )
      self.CP += 2

   # Basic Branching
   def op_HALT( self ):
      self.FLG = self.HALT
      self.CP += 1

   def op_JMP( self ):
      self.JUMP_OP( )

   def op_JMP_T( self ):
      self.CJUMP_OP( lambda x: x == True )

   def op_JMP_F( self ):
      self.CJUMP_OP( lambda x: x == False )

   def op_JMP_EQ( self ):
      self.CJUMP_OP( lambda x: x == 0 )

   def op_JMP_NE( self ):
      self.CJUMP_OP( lambda x: x != 0 )

   def op_JMP_LT( self ):
      self.CJUMP_OP( lambda x: x < 0 )

   def op_JMP_LE( self ):
      self.CJUMP_OP( lambda x: x <= 0 )

   def op_JMP_GT( self ):
      self.CJUMP_OP( lambda x: x > 0 )

   def op_JMP_GE( self ):
      self.CJUMP_OP( lambda x: x >= 0 )

   # Boolean Operations
   def op_bNEG( self ):
      self.BINARY_OP( op.not_, bool )

   def op_bAND( self ):
      self.BINARY_OP( lambda x,y: x and y, bool, bool )

   def op_bOR( self ):
      self.BINARY_OP( lambda x,y: x or y, bool, bool )

   # Bitwise Operations
   def op_iNOT( self ):
      self.BINARY_OP( op.invert, int )

   def op_iAND( self ):
      self.BINARY_OP( op.and_, int, int )
   
   def op_iOR( self ):
      self.BINARY_OP( op.or_, int, int )

   def op_iXOR( self ):
      self.BINARY_OP( op.xor, int, int )

   def op_iSHL( self ):
      self.BINARY_OP( op.lshift, int, int )

   def op_iSHR( self ):
      self.BINARY_OP( op.rshift, int, int )

   def op_iROR( self, n ):
      pass

   def op_iROL( self, n ):
      pass

   # Integer Oprations
   def op_iABS( self ):
      self.UNARY_OP( abs, int )

   def op_iCHSIGN( self ):
      self.UNARY_OP( op.neg, int )

   def op_iPROMOTE( self ): # int -> float
      self.UNARY_OP( float, int )

   def op_iEQ( self ):
      self.BINARY_OP( op.__eq__, int, int )
   
   def op_iNE( self ):
      self.BINARY_OP( op.__ne__, int, int )
   
   def op_iGT( self ):
      self.BINARY_OP( op.__gt__, int, int )
   
   def op_iGE( self ):
      self.BINARY_OP( op.__ge__, int, int )
   
   def op_iLT( self ):
      self.BINARY_OP( op.__lt__, int, int )
   
   def op_iLE( self ):
      self.BINARY_OP( op.__le__, int, int )
   
   def op_iCMP( self ):
      self.BINARY_OP( op.sub, int, int )

   def op_iINC( self ):
      self.UNARY_OP( lambda x: x + 1, int )
   
   def op_iDEC( self ):
      self.UNARY_OP( lambda x: x - 1, int )

   def op_iADD( self ):
      SS = self.SS
      SS[-1] = int(SS.pop()) + int(SS[-1])
      self.CP += 1
      #self.BINARY_OP( op.add, int, int )

   def op_iSUB( self ):
      SS = self.SS
      SS[-1] = (lambda x: int(SS[-1]) - int(x))(SS.pop())
      self.CP += 1
      #self.BINARY_OP( op.sub, int, int )

   def op_iMUL( self ):   
      self.BINARY_OP( op.mul, int, int )

   def op_iDIV( self ):
      self.BINARY_OP( op.floordiv, int, int )
   
   def op_iMOD( self ):
      self.BINARY_OP( op.mod, int, int )
   
   # IEEE Float Operations
   def op_fABS( self ):
      self.UNARY_OP( abs, float )

   def op_fCHSIGN( self ):
      self.UNARY_OP( op.neg, float )

   def op_fTRUNC( self ):
      self.UNARY_OP( int, float )

   def op_fFRAC( self ):
      self.UNARY_OP( lambda x:x - int(x), float )

   def op_fEQ( self ):
      self.BINARY_OP( op.__eq__, float, float )
   
   def op_fNE( self ):
      self.BINARY_OP( op.__ne__, float, float )
   
   def op_fGT( self ):
      self.BINARY_OP( op.__gt__, float, float )
   
   def op_fGE( self ):
      self.BINARY_OP( op.__ge__, float, float )
   
   def op_fLT( self ):
      self.BINARY_OP( op.__lt__, float, float )
   
   def op_fLE( self ):
      self.BINARY_OP( op.__le__, float, float )
   
   def op_fCMP( self ):
      op2 = self.SS.pop()
      op1 = self.SS[-1]
      if op1 < op2:
         self.SS[-1] = 1
      elif op2 < op1:
         self.SS[-1] = -1
      else:
         self.SS[-1] = 0
      self.CP += 1

   def op_fADD( self ):
      self.BINARY_OP( op.__add__, float, float )

   def op_fSUB( self ):
      self.BINARY_OP( op.__sub__, float, float )
   
   def op_fMUL( self ):   
      self.BINARY_OP( op.__mul__, float, float )

   def op_fDIV( self ):
      self.BINARY_OP( op.__div__, float, float )
   
   def op_fPOW( self ):
      self.BINARY_OP( op.pow, float, float )

   def op_fLOG( self ):
      self.BINARY_OP2( op.log, float, float )
   
   def op_fSIN( self ):
      self.UNARY_OP( math.sin, float )

   def op_fASIN( self ):
      self.UNARY_OP( math.asin, float )

   def op_fCOS( self ):
      self.UNARY_OP( math.cos, float )

   def op_fACOS( self ):
      self.UNARY_OP( math.acos, float )

   def op_fTAN( self ):
      self.UNARY_OP( math.tan, float )

   def op_fTAN2( self ):
      self.BINARY_OP( math.atan2, float, float )

   def op_fATAN( self ):
      self.UNARY_OP( math.atan, float )

   # String Manipulation
   def op_sLEN( self ):    # [ ..., string ]  =>  [ ..., len(string) ]
      theString = self.SS[-1]
      self.SS[-1] = len(theString)
      self.CP += 1
   
   def op_sAT( self ):     # [ ..., string, index ]  =>  [ ..., character ]
      index = self.SS.pop()
      theString = self.SS[ -1 ]
      self.SS[ -1 ] = theString[index]
      self.CP += 1

   def op_sCAT( self ):
      '''CAT
      [ ..., string1, string2 ]  =>  [ ..., string1 + string2 ]
      '''
      string2 = self.SS.pop()
      string1 = self.SS[-1]
      self.SS[-1] = string1 + string2
      self.CP += 1
   
   def op_sJOIN( self ):
      '''JOIN
      [ ..., [ string1, string2, ...], joinStr ]  =>  [ ..., string1 + joinStr + string2 + joinStr + ... ]
      '''
      joinStr = self.SS.pop()
      strList = self.SS[-1]
      self.SS[-1] = joinStr.join( *strList )
      self.CP += 1

   def op_sSPLIT( self ):
      '''SPLIT
      [ ..., string, index ]  =>  [ ..., string[ : index ], string[ index : ] ]
      '''
      index = self.SS.pop()
      theString = self.SS[-1]
      start = theString[ : index ]
      end   = theString[ index : ]
      self.SS[-1] = start
      self.SS.push(end)
      self.CP += 1
   
   def op_sTOINT( self ):  # [ ..., string ]  =>  [ ..., int(string) ]
      theString = self.SS[-1]
      self.SS[-1] = int(theString)
      self.CP += 1
   
   def op_sTOFLOAT( self ): # [ ..., string ]  =>  [ ..., float(string) ]
      theString = self.SS[-1]
      self.SS[-1] = float(theString)
      self.CP += 1
   
   def op_sCMP( self ):    # [ ..., string1, string2 ]  =>  [ ..., int ]
      str2 = self.SS.pop().casefold()
      str1 = self.SS[-1].casefold()
      result = 0
      for c1,c2 in zip(str1,str2):
         if c1 < c2:
            result = 1
            break
         elif c1 > c2:
            result = -1
            break
      self.SS[-1] = result
      self.CP += 1

   # List Operations
   def op_lPACK( self ):       # [ obj1, obj2, ... objCount ]  =>  [ ..., [obj1, obj2, ...] ]
      count  = self.SS.pop( )
      values = self.SS[ 0 - count : ]
      del self.SS[ 0 - count - 1 : ]
      self.SS[ -1 ] = values
      self.CP += 1
   
   def op_lUNPACK( self ):     # [ list ] <- SP   =>   [ list-contents ] <- SP
      values = self.SS.pop( )
      count  = len(values)
      values.append( count )
      self.SS.extend( values )
      self.CP += 1
   
   def op_lLEN( self ):        # [ ..., list ]  =>  [ ..., len(list) ]
      theList = self.SS[ -1 ]
      self.SS[-1] = len(theList)
      self.CP += 1

   def op_lAT( self ):         # [ list, list-index ] <- SP  =>  [ list, list-item ]
      index = self.SS[ -1 ]
      aList = self.SS[ -2 ]
      self.SS[ -1 ] = aList[ index ]
      self.CP += 1
   
   def op_lATSET( self ):      # [ list, list-index, newValue ]  ;; modify list at list-index with newValue
      newValue = self.SS.pop( )
      index    = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList[ index ] = newValue
      self.CP += 1
   
   def op_lPUSH( self ):       # [ list, newItem ]
      newItem  = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList.push( newItem )
      self.CP += 1
   
   def op_lPOP( self ):        # [ list ]  =>  [ oldListTop ]
      theList  = self.SS[ -1 ]
      value    = theList.pop( )
      self.SS.append( value )
      self.CP += 1
   
   def op_lCAT( self ):        # [ list1, list2 ]  => [ <list-1-contents> <list-2-contents> ]
      list2 = self.SS.pop()
      list1 = self.SS[ -1 ]
      self.SS[ -1 ] = list1 + list2
      self.CP += 1
   
   def op_lSPLIT( self ):      # [ ..., aList, size ]  =>  [ ..., aList[ : size ], aList[ size : ] ]
      count = self.SS.pop( )
      theList = self.SS[ -1 ]
      self.SS[ -1 ] = theList[ : count ]
      self.SS.append( theList[ count : ] )
      self.CP += 1

   def op_lCOPY( self ):
      top = self.SS[ -1 ]
      top = copy.copy( top )
      self.SS.push( top )
      self.CP += 1
   
   def op_lSWAPSTACK( self ):  # [ ..., stack-A ] => [ ..., oldStack ]
      '''SWAPSTACK
      SS = currentStack           SS = alternateStack
      [..., alternateStack ]  =>  [ ..., currentStack ]
      '''
      newStack = self.SS.pop( )
      oldStack = self.SS
      self.SS = newStack
      newStack.push( oldStack )
      self.CP += 1
   
   def op_lPUSHNEWLIST( self ):      # push a new empty list onto the stack.
      self.SS.push( list() )
      self.CP += 1


import threading
import time
from queue import PriorityQueue

class Agent( threading.Thread ):
   requestID = 0
   
   def __init__( self, requestsQueue, resultsQueue, **kwds ):
      super().__init__( **kwds )
      self.setDaemon( 1 )
      self.workRequestQueue = PriorityQueue
      self.resultQueue      = PriorityQueue
      self.start( )
   
   def performWork( self, priority, callable, *args, **kwds ):
      Agent.requestID += 1
      self.workRequestQueue.put( (priority, (Agent.requestID, callable, args, kwds)) )
      return Agent.requestID

   def run( self ):
      while True:
         priority, request = self.workRequestQueue.get( )
         requestID, callable, args, kwds = request
         self.resultQueue.put( (requestID, callable(*args,**kwds)) )

def systemClockAgent( seconds=0.10 ):
   time.sleep( seconds )
   return 'clock-tick'
   

class InterruptableStackVM( StackVM ):
   def __init__( self ):
      super().__init__( )
 
   def run( self, CS ):
      self.reboot( CS )
      while True:
         self.handleIRQ( )
         self.IR = self.CS[ self.CP ]
         func = getattr( self, 'op_' + self.IR )
         func( )
         
         if self.FLG != 0:
            if self.FLG == self.HALT:
               break
   
   def handleIRQ( self ):
      irq,payload = self.IRQ.get( )
      
      func = getattr( self, 'irq_' + self.irq )
      func(payload)
  
   def reboot( self, CS, SS=None, ENV=None ):
      super().reboot( CS, SS, ENV )
      
      self.IRQ     = [ ]                       # Interrupts
      self.IV      = [ ]                       # Interrupt Handler Vector

   def op_IRQ_SEND( self ):
      '''Generate an interrupt request.'''
      pass
   
   def op_IRQ_SUSPEND( self ):
      '''Suspend interrupt handling.'''
      pass
   
   def op_IRQ_RESUME( self ):
      '''Resume interrupt handling.'''
      pass
   
   def irq_1( self, payload ):
      pass
   
   def irq_2( self, payload ):
      pass
   
   

def assemble( aProg ):
   # Two-Pass Assembler
   codeSeg     = [ ]
   localLables = { }
   
   # Pass 1 - Catalog Labels
   address = 0
   for line in aProg:
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         localLables[opcode] = address
         
         opcode   = line[1]
         operands = line[2:]
      
      address += 1 + len(operands)

   # Pass 2 - Replace Jump Labels
   for address,line in enumerate(aProg):
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         opcode   = line[1]
         operands = line[2:]
      
      codeSeg.append( opcode )
      
      for operand in operands:
         if isinstance( operand, str ) and (operand[-1] == ':'):
            operand = localLables[operand]
         
         codeSeg.append( operand )

   return codeSeg

def static_link( codeSeg, symbolTable ):
   linkedProgram = [ ]
   for instruction in codeSeg:
      opCode, *operands = instruction
      
      linkedOperands = [ ]
      for operand in operands:
         if isinstance( operand, str ):
            operand = symbolTable[ operand ]
         
         linkedOperands.append( operand )
   
      linkedProgram.append( opCode, *linkedOperands )
   
   return linkedProgram

